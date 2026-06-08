"""배당내역상세 조회 모듈 (SEIBro 웹 WebSquare 호출).

SEIBro 웹 메뉴 "배당내역상세"(BIP_CNTS01043V, menuNo=26)의 WebSquare XML POST를
재현한다. Open API key 없이 동작하며, 종목코드 하나만 입력하면 보통주/우선주
배당내역을 최근 4개 결산연도 기준으로 돌려준다.

서버 task(EntrFnafInfoPTask)는 "최신 4개 결산연도"를 하드코딩해서 반환한다.
연도/기간 파라미터(STD_YEAR, SETACC_YYMM 등)는 무시되므로, 이 API로는
과거(예: 5년 이전) 데이터를 조회할 수 없다.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from time import sleep

import pandas as pd
import requests

from .client import SeibroClient
from .schedule_reason import SeibroWebSquareClient, _resolve_stock

WEB_CALL_URL = "https://seibro.or.kr/websquare/engine/proworks/callServletService.jsp"
TASK = "ksd.safe.bip.cnts.Company.process.EntrFnafInfoPTask"
W2X_PATH = "/IPORTAL/user/company/BIP_CNTS01043V.xml"
MENU_NO = "26"

# 같은 입력(ISSUCO_CUSTNO)으로 호출되는 두 action — 보통주 / 우선주
DIVIDEND_CALLS = [
    ("entrDivResultsList", "보통주"),
    ("entrDivResultsList2", "우선주"),
]

# A1~A4 는 최신 → 과거 순서 (A1=SETACC_YYMM 연도, A4=3년 전)
VALUE_COLS = ["A1", "A2", "A3", "A4"]


def _call_dividend(session: requests.Session, action: str, issuco_custno: str) -> list[dict[str, str]]:
    """단일 action(보통주 또는 우선주) WebSquare 호출."""
    payload = (
        f'<reqParam action="{action}" task="{TASK}">'
        f'<MENU_NO value="{MENU_NO}"/>'
        f'<W2XPATH value="{W2X_PATH}"/>'
        f'<ISSUCO_CUSTNO value="{issuco_custno}"/>'
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


def _tidy(rows: list[dict[str, str]], stock_kind: str, stock: dict[str, str]) -> pd.DataFrame:
    """원천 행(A1~A4)을 연도 칼럼으로 펼친 wide 형태로 정리."""
    if not rows:
        return pd.DataFrame()

    base_year = None
    for row in rows:
        std = row.get("STD_YEAR") or (row.get("SETACC_YYMM", "")[:4])
        if std.isdigit():
            base_year = int(std)
            break

    if base_year is None:
        year_labels = VALUE_COLS
    else:
        year_labels = [str(base_year - offset) for offset in range(len(VALUE_COLS))]

    records = []
    for row in rows:
        record = {
            "종목코드": stock["stock_code"],
            "회사명": stock["company_name"],
            "주식종류": stock_kind,
            "항목": row.get("HB", ""),
        }
        for label, col in zip(year_labels, VALUE_COLS):
            record[label] = row.get(col, "")
        records.append(record)
    return pd.DataFrame(records)


def get_dividend_details(
    stock_code: str,
    client: SeibroClient | None = None,
    session: requests.Session | None = None,
    save_csv: bool = True,
    sleep_seconds: float = 0.3,
) -> pd.DataFrame:
    """단일 종목의 배당내역상세(보통주 + 우선주)를 조회.

    SEIBro 웹 "배당내역상세"(BIP_CNTS01043V) 화면의 WebSquare 호출을 재현한다.
    입력값은 종목코드 하나뿐이며, 최근 4개 결산연도가 자동 반환된다.

    Args:
        stock_code: 단축종목코드 (예: '005930')
        client: 종목코드→고객번호 해결용 SeibroClient. None이면 .env의 키로 자동
                생성을 시도하고, 키가 없으면 웹 회사검색으로 대체(키 불필요)
        session: requests.Session. None이면 자동 생성
        save_csv: True이면 dividend_<종목코드>.csv 저장
        sleep_seconds: 보통주/우선주 호출 사이 대기

    Returns:
        [종목코드, 회사명, 주식종류, 항목, <연도1>, <연도2>, <연도3>, <연도4>]
        형태의 DataFrame. 항목 예: 당기순이익(백만), 배당금(백만), 배당성향(%),
        DPS(원), 시가배당률(현금)(%) 등.
    """
    if session is None:
        session = requests.Session()
        session.headers.update(
            {
                "Accept": "application/xml",
                "Content-Type": 'application/xml; charset="UTF-8"',
                "Origin": "https://seibro.or.kr",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131 Safari/537.36"
                ),
            }
        )

    # Open API key가 있으면 client로, 없으면 웹 회사검색으로 고객번호 해결
    if client is None:
        try:
            client = SeibroClient()
        except ValueError:
            client = None
    web_client = SeibroWebSquareClient(session=session)
    stock = _resolve_stock(stock_code, client, web_client)
    print(f"\n[Seibro] 배당내역상세 조회")
    print(f"  -> {stock['company_name']} ({stock['stock_code']}, 고객번호: {stock['issuco_custno']})")

    frames = []
    for index, (action, stock_kind) in enumerate(DIVIDEND_CALLS):
        if index:
            sleep(sleep_seconds)
        try:
            rows = _call_dividend(session, action, stock["issuco_custno"])
        except Exception as exc:
            print(f"  FAIL {stock_kind}({action}): {exc}")
            continue
        df = _tidy(rows, stock_kind, stock)
        if not df.empty:
            frames.append(df)
            print(f"  OK {stock_kind}: {len(df)}개 항목")
        else:
            print(f"  - {stock_kind}: 데이터 없음")

    if not frames:
        print("  배당내역 데이터가 없습니다.")
        return pd.DataFrame()

    result = pd.concat(frames, ignore_index=True)

    if save_csv:
        filename = f"dividend_{stock['stock_code']}.csv"
        result.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"  -> {filename} 저장 완료")

    return result


if __name__ == "__main__":
    import sys

    code = sys.argv[1] if len(sys.argv) > 1 else "005930"
    df_result = get_dividend_details(code)
    if not df_result.empty:
        print()
        print(df_result.to_string(index=False))
