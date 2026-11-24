"""의무보유(의무보호예수) 예수·반환 내역 조회 모듈 (Seibro Open API, key 필요).

Seibro API ID: getSafeDpDutyDepoStatus

1. get_lockup_records: 종목 하나의 예수·반환 내역을 기간(기본 최근 5년) 동안 모은다.
   서버의 1년 조회 상한을 365일 구간으로 나눠 우회한다.
2. lockup_balance: 예수 건별(사유·예수일)로 반환 수량을 빼서 남은 수량을 계산한다.

주의 (실측):
  - 조회는 "예수일이 기간 안인 예수 건"과 "반환일이 기간 안인 반환 건"이다. 조회 시작일
    이전에 예수된 주식은 보이지 않는다. 그런 주식이 아직 묶여 있으면 잔량이 과소 추정된다.
  - 자본감소·액면분할·액면병합이 있으면 예탁원은 기존 예수 기록을 반환 처리하지 않고
    바뀐 수량으로 새 예수 기록을 만든다. 단순 합계는 같은 주식을 두 번 센다.
    (예: 한울앤제주 2026-04 10:1 감자 뒤 647,249주, 2026-07 1:5 분할 뒤 3,236,245주가
    새로 예수됐지만 6,472,491주·647,249주 기록은 반환 없이 남아 있음)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Union

import pandas as pd

from .client import SeibroClient, retry_transient


# 의무보호예수 사유코드(DUTY_SAFEDP_RACD).
LOCKUP_REASONS = {
    "00": "해당없음", "01": "일반", "02": "모집(전매제한)",
    "03": "최대주주(상장)", "04": "최대주주(코스닥)", "43": "최대주주(기술성장기업)",
    "05": "투자회사(상장)", "06": "초과유상증자", "07": "지정취소", "08": "질권담보",
    "09": "등록주선인", "10": "외국인양수(변동제한)", "11": "벤처금융", "12": "기관투자가",
    "13": "합병(상장)", "14": "합병(코스닥)", "15": "부동산(상장)", "16": "부동산(코스닥)",
    "17": "법원M&A", "18": "주식교환(코스닥)", "19": "벤처금융(주식교환)", "20": "벤처금융(합병)",
    "21": "기관투자가(합병)", "44": "기관투자가(코넥스)", "22": "기관투자가(주식교환)",
    "23": "제3자배정최대주주(코스닥)", "24": "선박(상장)", "25": "채권기관협의회",
    "26": "주식교환(상장)", "27": "영업자산양도&제3자배정(상장)",
    "28": "영업자산양도&제3자배정(코스닥)", "29": "제3자배정유상증자(상장)",
    "30": "제3자배정유상증자(코스닥)", "31": "최대주주(제3자배정)",
    "32": "SPAC(상장)", "33": "SPAC(코스닥)", "34": "SPAC합병(상장)", "35": "SPAC합병(코스닥)",
    "36": "명목회사(상장)", "37": "명목회사(코스닥)", "38": "자발적보호예수", "39": "우회상장",
    "40": "상장주선인(국내기업)", "48": "상장주선인(외국기업)", "41": "전매제한",
    "42": "기타(특정금전신탁편입등)", "45": "크라우드펀딩", "46": "크라우드펀딩(최대주주)",
    "49": "모집(전매제한)-크라우드펀딩전문투자자", "47": "주관회사(금투협)",
    "50": "상장주선인(50%미만)", "51": "상장주선인(50%이상)", "52": "최대주주변경(법인 또는 …)",
    "90": "기타의무예수", "99": "기타", "53": "상장적격성실질심사",
    "54": "기타보호예수필요주주", "55": "주식매수선택권",
}

MARKET_NAMES = {"11": "유가", "12": "코스닥", "13": "K-OTC", "14": "코넥스", "50": "기타"}

RENAME = {
    "ISSUCO_CUSTNO": "발행회사고객번호",
    "SHOTN_ISIN": "종목코드",
    "KOR_SECN_NM": "종목명",
    "SECN_KACD": "종목종류",
    "DUTY_SAFEDP_RACD": "사유코드",
    "SAFEDP_DT": "예수일",
    "SAFEDP_QTY": "예수주식수",
    "RETURN_DT": "반환일",
    "RETURN_QTY": "반환주식수",
    "TOTAL_STK_CNT": "현재발행주식총수",
}

DISPLAY_ORDER = [
    "종목코드", "종목명", "종목종류", "시장", "구분", "사유코드", "사유",
    "예수일", "예수주식수", "반환일", "반환주식수", "현재발행주식총수", "발행회사고객번호",
]


def _to_date(value: Union[str, date, datetime, None], default: date) -> date:
    if value is None:
        return default
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip().replace("-", "").replace("/", "")
    return datetime.strptime(text, "%Y%m%d").date()


def _windows(start: date, end: date) -> list[tuple[date, date]]:
    """[start, end]를 뒤에서부터 365일(양 끝 포함) 이하 구간으로 나눈다.

    date.replace(year=...)를 쓰지 않으므로 2월 29일에도 깨지지 않는다.
    """
    out = []
    cur_end = end
    while cur_end >= start:
        cur_begin = max(start, cur_end - timedelta(days=364))
        out.append((cur_begin, cur_end))
        cur_end = cur_begin - timedelta(days=1)
    return out


def get_lockup_records(
    stock_code: str = None,
    issuco_custno: Union[str, int] = None,
    start_dt: Union[str, date, datetime] = None,
    end_dt: Union[str, date, datetime] = None,
    years: int = 5,
    client: SeibroClient = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """종목(발행회사) 하나의 의무보유 예수·반환 내역을 기간 동안 모은다.

    Args:
        stock_code: 단축종목코드. issuco_custno가 없으면 이것으로 고객번호를 찾는다.
        issuco_custno: 발행회사고객번호.
        start_dt: 조회 시작일. None이면 end_dt에서 `years`년 전(365일 × years).
        end_dt: 조회 종료일. None이면 오늘.
        years: start_dt가 없을 때 거슬러 올라갈 햇수.
        client: SeibroClient. None이면 자동 생성(.env/환경변수의 SEIBRO_API_KEY).
        verbose: 진행 상황 출력.

    Returns:
        예수·반환 행이 섞인 DataFrame(구분 = 예수/반환). 수량은 정수, 날짜는 Timestamp.
        한 회사가 보통주·우선주를 함께 가지면 둘 다 나온다(종목코드로 거를 것).
    """
    if client is None:
        client = SeibroClient()
    if issuco_custno is None:
        if not stock_code:
            raise ValueError("stock_code 또는 issuco_custno 중 하나가 필요합니다.")
        issuco_custno = retry_transient(client.get_issuco_custno, stock_code=stock_code)["issuco_custno"]

    end = _to_date(end_dt, date.today())
    start = _to_date(start_dt, end - timedelta(days=365 * years - 1))
    if start > end:
        raise ValueError(f"start_dt must be <= end_dt: {start} > {end}")

    windows = _windows(start, end)
    if verbose:
        print(f"[Seibro] 의무보유 예수·반환 조회: 고객번호 {issuco_custno}, "
              f"{start:%Y-%m-%d} ~ {end:%Y-%m-%d} ({len(windows)}개 구간 × 예수/반환)")

    frames = []
    for begin, stop in windows:
        for biz in ("1", "2"):
            df = retry_transient(
                client.get_lockup_status,
                begin.strftime("%Y%m%d"), stop.strftime("%Y%m%d"), biz, issuco_custno,
            )
            if not df.empty:
                frames.append(df)

    if not frames:
        if verbose:
            print("  -> 내역 없음")
        return pd.DataFrame(columns=DISPLAY_ORDER)

    df = pd.concat(frames, ignore_index=True).drop_duplicates()
    df["구분"] = df["OCCR_SEQ"].map({"1": "예수", "2": "반환"}).fillna(df["OCCR_SEQ"])
    df["사유"] = df["DUTY_SAFEDP_RACD"].map(LOCKUP_REASONS).fillna(df["DUTY_SAFEDP_RACD"])
    df["시장"] = df["MART_TPCD"].map(MARKET_NAMES).fillna(df["MART_TPCD"])
    df = df.rename(columns=RENAME)
    for col in ("예수주식수", "반환주식수", "현재발행주식총수"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int64")
    for col in ("예수일", "반환일"):
        df[col] = pd.to_datetime(df[col], format="%Y%m%d", errors="coerce")
    df = df[[c for c in DISPLAY_ORDER if c in df.columns]]
    df = df.sort_values(["예수일", "구분", "반환일"]).reset_index(drop=True)
    if verbose:
        n = df["구분"].value_counts()
        print(f"  -> 예수 {n.get('예수', 0)}건, 반환 {n.get('반환', 0)}건")
    return df


def lockup_balance(records: pd.DataFrame) -> pd.DataFrame:
    """예수 건(종목·사유·예수일)별로 반환 수량을 빼서 남은 의무보유 수량을 계산한다.

    반환 행은 원래 예수일·사유코드를 갖고 있어 그 둘로 맞춘다. 조회 기간보다 먼저
    예수된 건의 반환 행은 맞출 예수 건이 없으므로 버린다.

    Returns:
        종목코드, 종목명, 사유코드, 사유, 예수일, 예수주식수, 반환주식수, 마지막반환일, 잔여주식수
    """
    cols = ["종목코드", "종목명", "사유코드", "사유", "예수일",
            "예수주식수", "반환주식수", "마지막반환일", "잔여주식수"]
    if records is None or records.empty:
        return pd.DataFrame(columns=cols)
    key = ["종목코드", "사유코드", "예수일"]
    dep = (records[records["구분"] == "예수"]
           .groupby(key, as_index=False)
           .agg(종목명=("종목명", "first"), 사유=("사유", "first"), 예수주식수=("예수주식수", "sum")))
    ret = (records[records["구분"] == "반환"]
           .groupby(key, as_index=False)
           .agg(반환주식수=("반환주식수", "sum"), 마지막반환일=("반환일", "max")))
    out = dep.merge(ret, on=key, how="left")
    out["반환주식수"] = out["반환주식수"].fillna(0).astype("int64")
    out["잔여주식수"] = out["예수주식수"] - out["반환주식수"]
    return out[cols].sort_values("예수일").reset_index(drop=True)


if __name__ == "__main__":
    import sys

    code = sys.argv[1] if len(sys.argv) > 1 else "276730"
    recs = get_lockup_records(stock_code=code)
    print(recs.to_string(index=False))
    print()
    print(lockup_balance(recs).to_string(index=False))
