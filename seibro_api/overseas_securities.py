"""외화증권(해외증권) 국가별 통계 조회 모듈 (SEIBro 웹 WebSquare 호출).

SEIBro 웹 메뉴 "외화증권 국가별 통계"(BIP_CNTS10013V, menuNo=921) 화면의
WebSquare XML POST를 재현한다. Open API key 없이 동작한다. 이 한 화면은
두 개의 데이터(탭)를 제공하며, action만 다르고 나머지 호출 골격은 동일하다:

    getImptFrcurStkSetlAmtList  -> 결제대금 (매수/매도/합계/순매수)  : get_overseas_settlement_amounts()
    getImptFrcurStkCusRemaList  -> 보관잔고 (기준일 스냅샷)          : get_overseas_holdings()

기존 회사(Company) 계열 API와 달리 task 네임스페이스가
``ksd.safe.bip.cnts.OvsSec.process.OvsSecIsinPTask`` 이고, 종목코드/고객번호가
아니라 국가(S_COUNTRY)를 키로 받는다.

공통 파라미터 (동작으로 확인됨):
    S_COUNTRY : 국가코드 (예: 'HK' 홍콩, 'US' 미국). COUNTRY_CODES 참고.
    START_DT/END_DT : 조회 기간 (YYYYMMDD).
        - 결제대금: 기간 합계.
        - 보관잔고: END_DT(기준일) 스냅샷만 유효, START_DT는 무시됨.
    D_TYPE    : 결제대금에서만 의미. 정렬 기준 칼럼을 결정한다.
                1=매수대금, 2=매도대금, 3=매수+매도대금, 4=순매수.
                (보관잔고는 금액이 하나라 D_TYPE 무의미.)
    S_TYPE    : 어떤 값(1/2/3)을 넣어도 결과가 동일해 이 화면에서는 무의미.
                관측 캡처값을 기본으로 전달만 한다.
    PG_START/PG_END : 서버가 무시한다. 두 탭 모두 상위 최대 50건 고정 반환.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import date, datetime

import pandas as pd
import requests

WEB_CALL_URL = "https://seibro.or.kr/websquare/engine/proworks/callServletService.jsp"
TASK = "ksd.safe.bip.cnts.OvsSec.process.OvsSecIsinPTask"
W2X_PATH = "/IPORTAL/user/ovsSec/BIP_CNTS10013V.xml"
MENU_NO = "921"
CMM_BTN_ABBR_NM = "total_search,openall,print,hwp,word,pdf,seach,"

SETTLE_ACTION = "getImptFrcurStkSetlAmtList"
HOLDINGS_ACTION = "getImptFrcurStkCusRemaList"

# 결제대금 구분(D_TYPE). 응답 정렬 기준 칼럼을 결정한다(동작으로 확인됨).
SETTLE_TYPES = {
    "1": "매수대금",
    "2": "매도대금",
    "3": "매수+매도대금",
    "4": "순매수",
}

# 한글/영문 별칭 -> D_TYPE 코드
_SETTLE_ALIASES = {
    "매수대금": "1", "매수": "1", "buy": "1",
    "매도대금": "2", "매도": "2", "sell": "2",
    "매수+매도대금": "3", "매수매도대금": "3", "매수매도": "3", "buysell": "3", "buy_sell": "3",
    "순매수": "4", "순매수대금": "4", "net": "4", "netbuy": "4", "net_buy": "4",
}

# 자주 쓰는 국가코드(참고용). 목록에 없는 코드도 그대로 전달된다.
COUNTRY_CODES = {
    "HK": "홍콩",
    "US": "미국",
    "JP": "일본",
    "CN": "중국",
    "GB": "영국",
    "DE": "독일",
    "SG": "싱가포르",
    "VN": "베트남",
}

# 응답 XML 태그 -> 한글 칼럼명 (실제 응답으로 확인됨).
_RENAME_COMMON = {
    "RNUM": "순번",
    "NATION_NM": "국가명",
    "ISIN": "ISIN",
    "KOR_SECN_NM": "종목명",
}
SETTLE_RENAME = {
    **_RENAME_COMMON,
    "SUM_FRSEC_BUY_AMT": "매수대금",
    "SUM_FRSEC_SELL_AMT": "매도대금",
    "SUM_FRSEC_TOT_AMT": "매수매도대금",
    "SUM_FRSEC_NET_BUY_AMT": "순매수대금",
}
HOLDINGS_RENAME = {
    **_RENAME_COMMON,
    "SUM_FRSEC_AMT": "보관잔고금액",
}

_SETTLE_AMOUNT_COLUMNS = ["매수대금", "매도대금", "매수매도대금", "순매수대금"]
_HOLDINGS_AMOUNT_COLUMNS = ["보관잔고금액"]

SETTLE_DISPLAY_ORDER = [
    "국가코드", "국가명", "결제대금구분", "순번",
    "ISIN", "종목명", "매수대금", "매도대금", "매수매도대금", "순매수대금",
]
HOLDINGS_DISPLAY_ORDER = [
    "국가코드", "국가명", "기준일", "순번", "ISIN", "종목명", "보관잔고금액",
]


def _yyyymmdd(value: str | date | datetime | None, default: str) -> str:
    if value is None:
        return default
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y%m%d")
    text = str(value).strip().replace("-", "").replace("/", "")
    if len(text) != 8 or not text.isdigit():
        raise ValueError(f"날짜는 YYYYMMDD 형식이어야 합니다: {value!r}")
    return text


def _resolve_settle_type(settle_type: str) -> str:
    """결제대금 구분을 D_TYPE 코드('1'~'4')로 정규화."""
    key = str(settle_type).strip()
    if key in SETTLE_TYPES:
        return key
    normalized = key.lower().replace(" ", "")
    if normalized in _SETTLE_ALIASES:
        return _SETTLE_ALIASES[normalized]
    raise ValueError(
        f"결제대금 구분을 알 수 없습니다: {settle_type!r}. "
        f"코드('1'~'4') 또는 {list(SETTLE_TYPES.values())} 중 하나를 사용하세요."
    )


def _default_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/xml",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": 'application/xml; charset="UTF-8"',
            "Origin": "https://seibro.or.kr",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131 Safari/537.36"
            ),
        }
    )
    return session


def _call(
    action: str,
    country_code: str,
    start: str,
    end: str,
    s_type: str,
    d_type: str,
    session: requests.Session,
) -> list[dict[str, str]]:
    """BIP_CNTS10013V 화면의 action 하나를 호출하고 result 행 목록을 반환."""
    payload = (
        f'<reqParam action="{action}" task="{TASK}">'
        f'<MENU_NO value="{MENU_NO}"/>'
        f'<CMM_BTN_ABBR_NM value="{CMM_BTN_ABBR_NM}"/>'
        f'<W2XPATH value="{W2X_PATH}"/>'
        '<PG_START value="1"/>'
        '<PG_END value="50"/>'
        f'<START_DT value="{start}"/>'
        f'<END_DT value="{end}"/>'
        f'<S_TYPE value="{s_type}"/>'
        f'<S_COUNTRY value="{country_code}"/>'
        f'<D_TYPE value="{d_type}"/>'
        "</reqParam>"
    )
    response = session.post(
        WEB_CALL_URL,
        headers={
            "Referer": f"https://seibro.or.kr/websquare/control.jsp?w2xPath={W2X_PATH}&menuNo={MENU_NO}",
            "submissionid": "submission_" + action,
        },
        data=payload.encode("utf-8"),
        timeout=30,
    )
    response.raise_for_status()
    root = ET.fromstring(response.content.decode("utf-8", errors="replace"))
    return [
        {child.tag: child.attrib.get("value", "") for child in result}
        for result in root.findall(".//data/result")
    ]


def _to_int(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df


def _reorder(df: pd.DataFrame, order: list[str]) -> pd.DataFrame:
    ordered = [c for c in order if c in df.columns]
    extras = [c for c in df.columns if c not in ordered]
    return df[ordered + extras]


def get_overseas_settlement_amounts(
    country: str,
    settle_type: str = "매수+매도대금",
    start_dt: str | date | datetime | None = None,
    end_dt: str | date | datetime | None = None,
    s_type: str = "2",
    session: requests.Session | None = None,
    save_csv: bool = True,
) -> pd.DataFrame:
    """외화증권 국가별 결제대금을 조회 (BIP_CNTS10013V, getImptFrcurStkSetlAmtList).

    Args:
        country: 국가코드 (예: 'HK', 'US'). COUNTRY_CODES 참고. 목록에 없어도 그대로 전달.
        settle_type: 결제대금 구분(정렬 기준). 코드('1'~'4') 또는
            '매수대금'/'매도대금'/'매수+매도대금'/'순매수'. 기본 매수+매도대금.
        start_dt: 조회 시작일 (YYYYMMDD / YYYY-MM-DD / date). None이면 종료일-1개월.
        end_dt: 조회 종료일. None이면 오늘.
        s_type: S_TYPE. 이 화면에서는 무의미(값 무관 동일 결과). 기본 '2'.
        session: requests.Session. None이면 자동 생성.
        save_csv: True이면 overseas_settlement_<국가>_<구분>.csv 저장.

    Returns:
        결제대금 DataFrame (settle_type 기준 내림차순, 최대 50건).
        칼럼: 국가코드/국가명/결제대금구분/순번/ISIN/종목명/
        매수대금/매도대금/매수매도대금/순매수대금.
        (응답에는 4개 금액이 모두 오며, settle_type은 정렬 기준만 바꾼다.)
    """
    end = _yyyymmdd(end_dt, date.today().strftime("%Y%m%d"))
    if start_dt is None:
        end_date = datetime.strptime(end, "%Y%m%d").date()
        month = end_date.month - 1 or 12
        year = end_date.year - (1 if end_date.month == 1 else 0)
        day = min(end_date.day, 28)
        start = date(year, month, day).strftime("%Y%m%d")
    else:
        start = _yyyymmdd(start_dt, end)
    if start > end:
        raise ValueError(f"start_dt must be <= end_dt: {start} > {end}")

    d_type = _resolve_settle_type(settle_type)
    country_code = str(country).strip().upper()
    session = session or _default_session()

    print("\n[Seibro] 외화증권 국가별 결제대금 조회")
    print(f"  국가: {country_code} ({COUNTRY_CODES.get(country_code, '?')})")
    print(f"  결제대금 구분: {SETTLE_TYPES[d_type]} (D_TYPE={d_type})")
    print(f"  기간: {start} ~ {end}")

    rows = _call(SETTLE_ACTION, country_code, start, end, s_type, d_type, session)
    if not rows:
        print("  결제대금 내역이 없습니다.")
        return pd.DataFrame()

    df = pd.DataFrame(rows).rename(columns=SETTLE_RENAME)
    df.insert(0, "결제대금구분", SETTLE_TYPES[d_type])
    df.insert(0, "국가코드", country_code)
    df = _reorder(_to_int(df, _SETTLE_AMOUNT_COLUMNS), SETTLE_DISPLAY_ORDER)

    print(f"  -> {len(df)}건 수집 완료")
    if save_csv:
        filename = f"overseas_settlement_{country_code}_{d_type}.csv"
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"  -> {filename} 저장 완료")
    return df


def get_overseas_holdings(
    country: str,
    as_of: str | date | datetime | None = None,
    session: requests.Session | None = None,
    save_csv: bool = True,
) -> pd.DataFrame:
    """외화증권 국가별 보관잔고를 조회 (BIP_CNTS10013V, getImptFrcurStkCusRemaList).

    기준일(as_of) 시점의 국가별 보관잔고 금액 상위 목록을 돌려준다.
    결제대금과 달리 기간이 아니라 기준일 하나만 의미가 있다(END_DT 스냅샷).

    Args:
        country: 국가코드 (예: 'HK', 'US'). COUNTRY_CODES 참고.
        as_of: 기준일 (YYYYMMDD / YYYY-MM-DD / date). None이면 오늘.
        session: requests.Session. None이면 자동 생성.
        save_csv: True이면 overseas_holdings_<국가>_<기준일>.csv 저장.

    Returns:
        보관잔고 DataFrame (보관잔고금액 내림차순, 최대 50건).
        칼럼: 국가코드/국가명/기준일/순번/ISIN/종목명/보관잔고금액.
    """
    ref = _yyyymmdd(as_of, date.today().strftime("%Y%m%d"))
    country_code = str(country).strip().upper()
    session = session or _default_session()

    print("\n[Seibro] 외화증권 국가별 보관잔고 조회")
    print(f"  국가: {country_code} ({COUNTRY_CODES.get(country_code, '?')})")
    print(f"  기준일: {ref}")

    # 보관잔고는 END_DT만 유효. S_TYPE/D_TYPE은 무의미하나 사이트값을 그대로 전달.
    rows = _call(HOLDINGS_ACTION, country_code, ref, ref, "1", "3", session)
    if not rows:
        print("  보관잔고 내역이 없습니다.")
        return pd.DataFrame()

    df = pd.DataFrame(rows).rename(columns=HOLDINGS_RENAME)
    df.insert(0, "기준일", ref)
    df.insert(0, "국가코드", country_code)
    df = _reorder(_to_int(df, _HOLDINGS_AMOUNT_COLUMNS), HOLDINGS_DISPLAY_ORDER)

    print(f"  -> {len(df)}건 수집 완료")
    if save_csv:
        filename = f"overseas_holdings_{country_code}_{ref}.csv"
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"  -> {filename} 저장 완료")
    return df


if __name__ == "__main__":
    import sys

    kind = sys.argv[1] if len(sys.argv) > 1 else "settlement"
    country_arg = sys.argv[2] if len(sys.argv) > 2 else "HK"
    if kind in ("holdings", "보관잔고", "rema"):
        as_of_arg = sys.argv[3] if len(sys.argv) > 3 else None
        df_result = get_overseas_holdings(country_arg, as_of_arg)
    else:
        settle_arg = sys.argv[3] if len(sys.argv) > 3 else "매수+매도대금"
        start_arg = sys.argv[4] if len(sys.argv) > 4 else None
        end_arg = sys.argv[5] if len(sys.argv) > 5 else None
        df_result = get_overseas_settlement_amounts(country_arg, settle_arg, start_arg, end_arg)
    if not df_result.empty:
        print()
        print(df_result.to_string(index=False))
