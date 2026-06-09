"""발행주식수증감내역(개별) 조회 모듈 (SEIBro 웹 WebSquare 호출).

SEIBro 웹 메뉴 "발행주식수증감내역(개별)"(BIP_CNTS01012V, menuNo=53)의 WebSquare
XML POST를 재현한다. Open API key 없이 동작하며, 종목코드와 기간을 입력하면
액면분할·이익소각·무상증자 등 발행주식수 증감 이력을 돌려준다.

배당내역상세(dividend.py)와 달리 이 API는 기간(ISSU_DT_FROM~TO)을 받으므로
과거 데이터까지 조회할 수 있다.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import date, datetime

import pandas as pd
import requests

from .client import SeibroClient
from .schedule_reason import SeibroWebSquareClient, _resolve_stock

WEB_CALL_URL = "https://seibro.or.kr/websquare/engine/proworks/callServletService.jsp"
TASK = "ksd.safe.bip.cnts.Company.process.EntrFnafInfoPTask"
W2X_PATH = "/IPORTAL/user/company/BIP_CNTS01012V.xml"
MENU_NO = "53"
ACTION = "chgDetailsListEL1"

RENAME = {
    "ISSU_DT": "발행일자",
    "REP_SECN_NM": "종목명",
    "SECN_KACD": "종목종류코드",
    "SECN_KACD_NM": "종목종류",
    "SECN_ISSU_NTIMES": "발행횟수",
    "RGT_LINK_RACD": "발행사유코드",
    "RGT_LINK_RACD_NM": "발행사유",
    "PVAL": "액면가",
    "LIST_DT": "상장일자",
    "ISSU_QTY": "증감수량",
    "ISSU_FORM": "발행형태",
    "ISSUPRC": "발행가",
}

# 출력 칼럼 순서
DISPLAY_ORDER = [
    "종목코드", "종목명", "종목종류코드", "종목종류",
    "발행일자", "상장일자", "발행횟수",
    "발행사유코드", "발행사유", "증감수량", "발행가", "액면가", "발행형태",
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


def get_issued_share_changes(
    stock_code: str,
    start_dt: str | date | datetime = "20000101",
    end_dt: str | date | datetime | None = None,
    secn_kacd: str = "",
    rgt_link_racd: str = "",
    client: SeibroClient | None = None,
    session: requests.Session | None = None,
    save_csv: bool = True,
) -> pd.DataFrame:
    """단일 종목의 발행주식수증감내역을 조회.

    SEIBro 웹 "발행주식수증감내역(개별)"(BIP_CNTS01012V) 화면의 WebSquare 호출을
    재현한다. Open API key 없이 동작한다(키 없으면 웹 회사검색으로 고객번호 해결).

    Args:
        stock_code: 단축종목코드 (예: '005930')
        start_dt: 조회 시작일 (YYYYMMDD / YYYY-MM-DD / date). 기본 20000101
        end_dt: 조회 종료일. None이면 오늘
        secn_kacd: 종목종류코드 필터 ("" = 전체, "0101" = 보통주, "0201" = 우선주)
        rgt_link_racd: 발행사유코드 필터 ("" = 전체, "201" = 액면분할 등)
        client: SeibroClient. None이면 .env 키로 시도, 없으면 웹 검색 대체
        session: requests.Session. None이면 자동 생성
        save_csv: True이면 issued_share_change_<종목코드>.csv 저장

    Returns:
        발행일자 오름차순으로 정렬된 증감내역 DataFrame.
        칼럼: 종목코드/종목명/종목종류/발행일자/상장일자/발행횟수/발행사유/
        증감수량/발행가/액면가/발행형태 등.
    """
    start = _yyyymmdd(start_dt, "20000101")
    end = _yyyymmdd(end_dt, date.today().strftime("%Y%m%d"))
    if start > end:
        raise ValueError(f"start_dt must be <= end_dt: {start} > {end}")

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

    if client is None:
        try:
            client = SeibroClient()
        except ValueError:
            client = None
    web_client = SeibroWebSquareClient(session=session)
    stock = _resolve_stock(stock_code, client, web_client)

    print(f"\n[Seibro] 발행주식수증감내역(개별) 조회")
    print(f"  -> {stock['company_name']} ({stock['stock_code']}, 고객번호: {stock['issuco_custno']})")
    print(f"  기간: {start} ~ {end}")

    payload = (
        f'<reqParam action="{ACTION}" task="{TASK}">'
        f'<MENU_NO value="{MENU_NO}"/>'
        f'<W2XPATH value="{W2X_PATH}"/>'
        f'<ISSUCO_CUSTNO value="{stock["issuco_custno"]}"/>'
        f'<RGT_LINK_RACD value="{rgt_link_racd}"/>'
        f'<SECN_KACD value="{secn_kacd}"/>'
        f'<ISSU_DT_FROM value="{start}"/>'
        f'<ISSU_DT_TO value="{end}"/>'
        '<STARTPAGE value="1"/>'
        '<ENDPAGE value="100000"/>'
        "</reqParam>"
    )
    response = session.post(
        WEB_CALL_URL,
        headers={
            "Referer": f"https://seibro.or.kr/websquare/control.jsp?w2xPath={W2X_PATH}&menuNo={MENU_NO}",
            "submissionid": "submission_" + ACTION,
        },
        data=payload.encode("utf-8"),
        timeout=30,
    )
    response.raise_for_status()
    root = ET.fromstring(response.content.decode("utf-8", errors="replace"))
    rows = [
        {child.tag: child.attrib.get("value", "") for child in result}
        for result in root.findall(".//data/result")
    ]

    if not rows:
        print("  증감내역이 없습니다.")
        return pd.DataFrame()

    df = pd.DataFrame(rows).rename(columns=RENAME)
    df.insert(0, "종목코드", stock["stock_code"])

    if "발행일자" in df.columns:
        df = df.sort_values("발행일자").reset_index(drop=True)

    ordered = [c for c in DISPLAY_ORDER if c in df.columns]
    extras = [c for c in df.columns if c not in ordered]
    df = df[ordered + extras]

    print(f"  -> {len(df)}건 수집 완료")

    if save_csv:
        filename = f"issued_share_change_{stock['stock_code']}.csv"
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"  -> {filename} 저장 완료")

    return df


if __name__ == "__main__":
    import sys

    code = sys.argv[1] if len(sys.argv) > 1 else "005930"
    start_arg = sys.argv[2] if len(sys.argv) > 2 else "20000101"
    end_arg = sys.argv[3] if len(sys.argv) > 3 else None
    df_result = get_issued_share_changes(code, start_arg, end_arg)
    if not df_result.empty:
        print()
        print(df_result.to_string(index=False))
