"""배당 이력 조회 모듈 (SEIBRO 공식 Open API).

종목코드 하나로 발행회사고객번호를 해결한 뒤, 지정한 기간의 배당 **일정**과
**금액**을 한 장의 DataFrame으로 합쳐 돌려준다.

사용하는 공식 Open API 3종 (`SEIBRO_API_KEY` 필요):

| apiId | 단위 | 내용 |
|-------|------|------|
| `getIssucoCustnoByIsin` | 회사 | 종목코드 → 발행회사고객번호 |
| `getDivSchedulInfo` | 회사×기준일 | 권리기준일·권리락일·명부폐쇄·확정구분 (금액 없음) |
| `getDivInfo` | 종목×기준일 | 주당배당금·시가배당률·지급일·차등배당 (금액) |

서버 제약과 대응 (모두 실측 확인):

- **3년 상한**: 두 API 모두 `BEGIN_STD_DT` 기준 3년까지만 반환하고, 더 긴 구간을
  요청하면 **에러 없이 조용히 잘린다.** 이 모듈은 요청 기간을 3년 미만 구간으로
  쪼개 반복 호출한 뒤 합친다.
- **소급 범위**: 삼성전자 기준 1987년 데이터까지 조회됐다. 회사별로 다르다.
- **PVAL(액면가)은 조회 시점의 현재 액면가**다. 과거 기준일 행에도 현재 액면가가
  실려 나오므로(예: 삼성전자 2016년 기준일 행의 PVAL=100), `CASH_ALOC_RATIO`로
  배당금을 역산하면 틀린다. 주당배당금은 반드시 `CASH_ALOC_AMT`를 쓴다.
- **2003년 이전 기준일은 금액이 비어 있다.** 실측상 `CASH_ALOC_AMT`(주당배당금)와
  `MARTP_DIV_RATE`(시가배당률)는 **권리기준일 2003-06-30부터** 채워지고, 그 이전은
  0이며 `CASH_ALOC_RATIO`(당시 액면 대비 %)만 있다. PVAL이 현재 액면가라 이
  API만으로는 과거 금액을 복원할 수 없다. 이 모듈은 해당 구간이 섞이면 경고한다.
- **같은 (종목, 권리기준일)에 2행이 나올 수 있다.** 주식배당과 현금배당이 별도 행으로
  기록된 경우(예: 삼성전자 1998-12-31)이며, 원천 그대로 보존한다.
- **`getDivInfo` 출력에는 고객번호가 없다.** 조인용으로 이 모듈이 직접 붙인다.

배당내역상세([dividend.py](dividend.py), 웹 BIP_CNTS01043V)는 최근 4개 결산연도만
반환하는 대신 당기순이익·배당성향 같은 재무항목을 준다. 이 모듈은 기간 제약이
없는 대신 재무항목이 없다. 서로 대체가 아니라 보완 관계다.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from time import sleep
from typing import Union

import pandas as pd

from .client import SeibroClient

# 권리사유세부유형코드 (RGT_RSN_DTAIL_SORT_CD) — 배당 관련만
DIV_SORT_CODES = {
    "01": "주식배당",
    "02": "현금배당",
    "03": "동시배당",
    "04": "무배당",
    "11": "이익분배",
    "12": "청산분배",
    "90": "미정",
    "99": "기타",
}

# 배정방법코드 (ALOC_WHCD)
ALOC_METHOD_CODES = {"1": "정율", "2": "정액", "3": "정율+정액"}

# 결산구분코드 (SETACC_TPCD)
SETACC_CODES = {"1": "결산", "2": "반기", "3": "분기"}

# 확정구분코드 (FIX_TPCD)
FIX_CODES = {"1": "확정", "2": "예고", "3": "미정"}

# 서버가 한 번에 돌려주는 최대 기간(년). 넘기면 조용히 잘린다.
MAX_WINDOW_YEARS = 3

# CASH_ALOC_AMT(주당배당금)·MARTP_DIV_RATE(시가배당률)가 채워지기 시작하는 권리기준일.
# 이전 구간은 CASH_ALOC_RATIO(당시 액면 대비 %)만 제공된다.
AMOUNT_AVAILABLE_FROM = "20030630"

# 숫자로 변환할 칼럼 (".7" 같은 앞점 실수, 빈 문자열 포함)
NUMERIC_COLUMNS = [
    "액면가(현재)",
    "주식배정비율(%)",
    "현금배정비율(%)",
    "주당배당금",
    "시가배당률(%)",
    "현금차등배당금액",
    "현금차등배당율(%)",
    "주식차등배당율(%)",
    "시가차등배당율(%)",
]

SCHEDULE_RENAME = {
    "RGT_STD_DT": "권리기준일",
    "RGT_RSN_DTAIL_SORT_CD": "배당구분코드",
    "ALOC_WHCD": "배정방법코드",
    "SETACC_TPCD": "결산구분코드",
    "FIX_TPCD": "확정구분코드",
    "ROST_CLOSE_BEGIN_DT": "명부폐쇄시작일",
    "ROST_CLOSE_EXPRY_DT": "명부폐쇄종료일",
    "XRGT_DT": "권리락일",
    "ELTSC_YN": "전자증권여부",
}

PAYOUT_RENAME = {
    "ISIN": "표준코드",
    "KOR_SECN_NM": "종목명",
    "SECN_KACD_NM": "주식종류",
    "RGT_STD_DT": "권리기준일",
    "PVAL": "액면가(현재)",
    "STK_ALOC_RATIO": "주식배정비율(%)",
    "CASH_ALOC_RATIO": "현금배정비율(%)",
    "CASH_ALOC_AMT": "주당배당금",
    "MARTP_DIV_RATE": "시가배당률(%)",
    "TH1_PAY_TERM_BEGIN_DT": "현금배당지급일",
    "DELI_DT": "주식교부일",
    "MAJSHR_ETC_DIFF_ALOC_YN": "대주주차등배당여부",
    "TSTK_NOAGN_YN": "자사주무배정여부",
    "CASH_DIFF_DIVIAMT_VAL": "현금차등배당금액",
    "CASH_DIFF_DIVI_RATE": "현금차등배당율(%)",
    "STK_DIFF_DIVI_RATE": "주식차등배당율(%)",
    "MARTP_DIFF_DIVI_RATE": "시가차등배당율(%)",
}

OUTPUT_COLUMNS = [
    "종목코드",
    "발행회사고객번호",
    "회사명",
    "표준코드",
    "종목명",
    "주식종류",
    "권리기준일",
    "배당구분",
    "결산구분",
    "확정구분",
    "배정방법",
    "주당배당금",
    "시가배당률(%)",
    "현금배당지급일",
    "주식배정비율(%)",
    "주식교부일",
    "권리락일",
    "명부폐쇄시작일",
    "명부폐쇄종료일",
    "액면가(현재)",
    "현금배정비율(%)",
    "대주주차등배당여부",
    "자사주무배정여부",
    "현금차등배당금액",
    "현금차등배당율(%)",
    "주식차등배당율(%)",
    "시가차등배당율(%)",
    "전자증권여부",
]

DateLike = Union[str, int, date, datetime, None]


def _yyyymmdd(value: DateLike, default: str = None) -> str:
    """YYYYMMDD 문자열로 정규화."""
    if value is None or value == "":
        if default is None:
            raise ValueError("날짜가 필요합니다 (YYYYMMDD).")
        return default
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y%m%d")
    text = str(value).strip().replace("-", "").replace("/", "").replace(".", "")
    if len(text) != 8 or not text.isdigit():
        raise ValueError(f"날짜 형식이 올바르지 않습니다 (YYYYMMDD 기대): {value!r}")
    return text


def _plus_years(day: date, years: int) -> date:
    """윤년 2/29 안전한 N년 후."""
    try:
        return day.replace(year=day.year + years)
    except ValueError:  # 2/29 -> 평년
        return day.replace(year=day.year + years, month=2, day=28)


def _split_windows(begin_dt: str, end_dt: str, years: int = MAX_WINDOW_YEARS) -> list[tuple[str, str]]:
    """서버 3년 상한에 맞춰 [(begin, end), ...] 구간으로 분할.

    각 구간은 begin으로부터 3년 - 1일이라 서버가 자를 일이 없다.
    """
    start = datetime.strptime(begin_dt, "%Y%m%d").date()
    finish = datetime.strptime(end_dt, "%Y%m%d").date()
    if start > finish:
        raise ValueError(f"시작일({begin_dt})이 종료일({end_dt})보다 늦습니다.")

    windows = []
    cursor = start
    while cursor <= finish:
        window_end = min(_plus_years(cursor, years) - timedelta(days=1), finish)
        windows.append((cursor.strftime("%Y%m%d"), window_end.strftime("%Y%m%d")))
        cursor = window_end + timedelta(days=1)
    return windows


def _collect(fetch, windows: list[tuple[str, str]], label: str,
             sleep_seconds: float, verbose: bool) -> pd.DataFrame:
    """구간별로 fetch를 반복 호출하고 이어붙인다."""
    frames = []
    for index, (win_begin, win_end) in enumerate(windows):
        if index:
            sleep(sleep_seconds)
        df = fetch(win_begin, win_end)
        if verbose:
            print(f"  [{label}] {win_begin}~{win_end}: {len(df)}건")
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _to_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """금액·비율 칼럼을 숫자로. 빈 문자열은 NaN."""
    for column in NUMERIC_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column].astype(str).str.strip().replace({"": None}), errors="coerce"
            )
    return df


def get_dividend_history(
    stock_code: str = None,
    start_dt: DateLike = None,
    end_dt: DateLike = None,
    issuco_custno: Union[str, int] = None,
    client: SeibroClient = None,
    save_csv: bool = False,
    sleep_seconds: float = 0.3,
    verbose: bool = True,
) -> pd.DataFrame:
    """단일 종목의 기간별 배당 이력(일정 + 금액)을 조회.

    종목코드로 발행회사고객번호를 받아, 그 회사의 전 종목(보통주·우선주)에 대해
    권리기준일·주당배당금·지급일·권리락일 등을 한 장의 표로 돌려준다.
    3년 상한은 내부에서 구간 분할로 처리하므로 기간을 길게 줘도 된다.

    Args:
        stock_code: 단축종목코드 (예: "005930"). issuco_custno를 직접 주면 생략 가능.
        start_dt: 조회 시작 권리기준일 (YYYYMMDD / date / datetime).
        end_dt: 조회 종료 권리기준일. 미입력 시 오늘.
        issuco_custno: 발행회사고객번호를 이미 알고 있으면 직접 지정(조회 1회 절약).
        client: SeibroClient. None이면 .env의 SEIBRO_API_KEY로 생성.
        save_csv: True면 dividend_history_<종목코드>.csv 저장.
        sleep_seconds: 연속 호출 사이 대기(초).
        verbose: 진행 로그 출력.

    Returns:
        종목×권리기준일 단위 DataFrame. 칼럼은 `OUTPUT_COLUMNS` 참조.
        배당 이력이 없으면 빈 DataFrame.

        주의:
        - 주당배당금은 `주당배당금`(CASH_ALOC_AMT)을 쓴다. `현금배정비율(%)`은
          **당시 액면가 대비 %**인데 `액면가(현재)`는 현재 액면가라, 둘을 곱해
          역산하면 액면분할 이전 구간에서 틀린 값이 나온다.
        - 권리기준일 2003-06-30 이전은 주당배당금·시가배당률이 0이다
          (`AMOUNT_AVAILABLE_FROM` 참조).

    Raises:
        ValueError: 종목코드/고객번호가 모두 없거나 고객번호 조회에 실패한 경우.
    """
    if client is None:
        client = SeibroClient()

    if issuco_custno is None:
        if not stock_code:
            raise ValueError("stock_code 또는 issuco_custno 중 하나가 필요합니다.")
        info = client.get_issuco_custno(stock_code=stock_code)
        issuco_custno = info["issuco_custno"]
        company_name = info["rep_secn_nm"]
    else:
        issuco_custno = str(issuco_custno).strip()
        company_name = ""

    begin = _yyyymmdd(start_dt)
    finish = _yyyymmdd(end_dt, default=datetime.today().strftime("%Y%m%d"))
    windows = _split_windows(begin, finish)

    if verbose:
        label = f"{company_name} " if company_name else ""
        print(f"\n[Seibro] 배당 이력 조회 (Open API)")
        print(f"  -> {label}({stock_code or '-'}, 고객번호: {issuco_custno})")
        print(f"  -> 기간 {begin}~{finish}, {len(windows)}개 구간으로 분할 호출")

    schedules = _collect(
        lambda b, e: client.get_dividend_schedules(issuco_custno=issuco_custno, begin_dt=b, end_dt=e),
        windows, "배당일정", sleep_seconds, verbose,
    )
    sleep(sleep_seconds)
    payouts = _collect(
        lambda b, e: client.get_dividend_payouts(issuco_custno=issuco_custno, begin_dt=b, end_dt=e),
        windows, "배당분배금", sleep_seconds, verbose,
    )

    if schedules.empty and payouts.empty:
        if verbose:
            print("  해당 기간 배당 데이터가 없습니다.")
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    if not schedules.empty:
        if not company_name:
            company_name = str(schedules.iloc[0].get("REP_SECN_NM", "")).strip()
        schedules = schedules.rename(columns=SCHEDULE_RENAME)
        schedules = schedules[[c for c in SCHEDULE_RENAME.values() if c in schedules.columns]]
        # 같은 기준일이 중복되면 조인 시 행이 불어난다. 첫 건만 남기고 알린다.
        duplicated = schedules["권리기준일"].duplicated().sum()
        if duplicated and verbose:
            print(f"  ! 배당일정에 중복 권리기준일 {duplicated}건 → 첫 건만 사용")
        schedules = schedules.drop_duplicates(subset=["권리기준일"], keep="first")
    else:
        schedules = pd.DataFrame(columns=list(SCHEDULE_RENAME.values()))

    if not payouts.empty:
        payouts = payouts.rename(columns=PAYOUT_RENAME)
        payouts = payouts[[c for c in PAYOUT_RENAME.values() if c in payouts.columns]]
    else:
        payouts = pd.DataFrame(columns=list(PAYOUT_RENAME.values()))

    # 금액(종목 단위) ↔ 일정(회사 단위)을 권리기준일로 결합.
    # outer: 금액이 아직 없는 예고/미정 일정, 일정이 없는 금액 행도 모두 보존.
    merged = payouts.merge(schedules, on="권리기준일", how="outer")

    merged["종목코드"] = str(stock_code).strip().zfill(6) if stock_code else ""
    merged["발행회사고객번호"] = issuco_custno
    merged["회사명"] = company_name
    merged["배당구분"] = merged.get("배당구분코드", pd.Series(dtype=str)).map(DIV_SORT_CODES)
    merged["결산구분"] = merged.get("결산구분코드", pd.Series(dtype=str)).map(SETACC_CODES)
    merged["확정구분"] = merged.get("확정구분코드", pd.Series(dtype=str)).map(FIX_CODES)
    merged["배정방법"] = merged.get("배정방법코드", pd.Series(dtype=str)).map(ALOC_METHOD_CODES)

    for column in OUTPUT_COLUMNS:
        if column not in merged.columns:
            merged[column] = None

    result = merged[OUTPUT_COLUMNS].copy()
    result = _to_numeric(result)
    result = result.sort_values(
        ["권리기준일", "표준코드"], ascending=[False, True], na_position="last"
    ).reset_index(drop=True)

    if verbose:
        print(f"  -> 총 {len(result)}행 "
              f"({result['권리기준일'].min()}~{result['권리기준일'].max()})")
        old = (result["권리기준일"].astype(str) < AMOUNT_AVAILABLE_FROM).sum()
        if old:
            print(f"  ! 권리기준일 {AMOUNT_AVAILABLE_FROM} 이전 {old}행은 주당배당금·"
                  f"시가배당률이 0으로 비어 있습니다(현금배정비율(%)만 제공).")

    if save_csv:
        filename = f"dividend_history_{stock_code or issuco_custno}.csv"
        result.to_csv(filename, index=False, encoding="utf-8-sig")
        if verbose:
            print(f"  -> {filename} 저장 완료")

    return result


def get_market_dividend_schedules(
    std_dt: DateLike,
    detail_sort_cd: str = None,
    client: SeibroClient = None,
) -> pd.DataFrame:
    """특정 권리기준일 하루치, 전 상장사 배당일정 조회.

    `getDivSchedulInfo`는 고객번호를 주지 않으면 기간을 무시하고 `std_dt` 하루치만
    돌려준다(실측). 그래서 시장 전체를 훑으려면 기준일을 하루씩 돌려야 한다.
    결산기말(12/31·6/30·3/31·9/30)에 대부분 몰려 있다.

    금액은 포함되지 않는다. 이 결과에서 고객번호를 뽑아
    `get_dividend_history(issuco_custno=...)`로 넘기는 게 표준 파이프라인이다.

    Args:
        std_dt: 권리기준일 YYYYMMDD.
        detail_sort_cd: 01 주식배당 / 02 현금배당 / 03 동시배당 / 04 무배당.
        client: SeibroClient. None이면 자동 생성.

    Returns:
        [발행회사고객번호, 회사명, 권리기준일, 배당구분, 결산구분, 확정구분,
         배정방법, 권리락일, 명부폐쇄시작일, 명부폐쇄종료일, 전자증권여부]
    """
    if client is None:
        client = SeibroClient()

    day = _yyyymmdd(std_dt)
    df = client.get_dividend_schedules(begin_dt=day, detail_sort_cd=detail_sort_cd)
    if df.empty:
        return pd.DataFrame()

    df = df.rename(columns={**SCHEDULE_RENAME,
                            "ISSUCO_CUSTNO": "발행회사고객번호",
                            "REP_SECN_NM": "회사명"})
    df["배당구분"] = df.get("배당구분코드", pd.Series(dtype=str)).map(DIV_SORT_CODES)
    df["결산구분"] = df.get("결산구분코드", pd.Series(dtype=str)).map(SETACC_CODES)
    df["확정구분"] = df.get("확정구분코드", pd.Series(dtype=str)).map(FIX_CODES)
    df["배정방법"] = df.get("배정방법코드", pd.Series(dtype=str)).map(ALOC_METHOD_CODES)

    columns = ["발행회사고객번호", "회사명", "권리기준일", "배당구분", "결산구분",
               "확정구분", "배정방법", "권리락일", "명부폐쇄시작일",
               "명부폐쇄종료일", "전자증권여부"]
    return df[[c for c in columns if c in df.columns]].reset_index(drop=True)


if __name__ == "__main__":
    import sys

    code = sys.argv[1] if len(sys.argv) > 1 else "005930"
    begin = sys.argv[2] if len(sys.argv) > 2 else "20200101"
    finish = sys.argv[3] if len(sys.argv) > 3 else datetime.today().strftime("%Y%m%d")

    df_result = get_dividend_history(code, begin, finish, save_csv=True)
    if not df_result.empty:
        print()
        preview = ["권리기준일", "종목명", "주식종류", "배당구분", "결산구분",
                   "주당배당금", "시가배당률(%)", "현금배당지급일", "권리락일"]
        print(df_result[preview].to_string(index=False))
