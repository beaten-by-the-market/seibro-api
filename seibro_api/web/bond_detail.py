"""Details published on the SEIBRO bond screen."""

from __future__ import annotations

import requests

from .client import _parse_records, _xml_escape, post_xml


BOND_DETAIL_TASK = "ksd.safe.bip.cnts.bone.process.BondSecnDetailPTask"
BOND_DETAIL_W2X = "/IPORTAL/user/bond/BIP_CNTS03004V.xml"
BOND_DETAIL_MENU_NO = "415"

# 웹 응답 태그 → 한글 칼럼 (필요한 것만)
WEB_RENAME = {
    "ISIN": "채권코드",
    "KOR_SECN_NM": "채권명",
    "REP_SECN_NM": "발행회사",
    "PARTICUL_BOND_KIND": "종류",
    "RECU_WHCD_NM": "모집방법",
    "OPTION_TPCD_NM": "옵션",
    "ISSU_DT": "발행일",
    "XPIR_DT": "만기일",
    "FIRST_ISSU_AMT": "발행금액",
    "ISSU_REMA": "미상환잔액",
    "COUPON_RATE": "표면이자율",
    "RANK_TPCD_NM": "순위",
    "PRCP_RED_WHCD_NM": "원금상환방법",
    "ISSU_FORM": "발행형태",
}
EXER_RENAME = {
    "XRC_STK_ISIN": "행사대상주식코드",
    "XRC_RATIO": "행사비율",
    "XRC_PRICE": "현재행사가",
    "PAYIN_MEANS_TPCD_NM": "신주대금납입",
    "SHAR_DELI_STD_CD_NM": "주식교부기준",
}


def _web_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(
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
    return s


def _web_call(session: requests.Session, action: str, isin: str) -> list[dict]:
    payload = (
        f'<reqParam action="{action}" task="{BOND_DETAIL_TASK}">'
        f'<ISIN value="{_xml_escape(isin)}"/></reqParam>'
    )
    r = post_xml(
        session,
        payload,
        headers={
            "Referer": (
                "https://seibro.or.kr/websquare/control.jsp?"
                f"w2xPath={BOND_DETAIL_W2X}&menuNo={BOND_DETAIL_MENU_NO}"
            ),
            "submissionid": "submission_" + action,
        },
    )
    return _parse_records(r.text)


def get_bond_web_info(bond_isin: str, session: requests.Session | None = None) -> dict:
    """채권 하나의 기본정보 + 행사정보 (SEIBro 웹, key 불필요).

    Returns:
        dict. 채권코드/채권명/발행회사/종류/모집방법/옵션/발행일/만기일/발행금액/
        미상환잔액/표면이자율/순위/원금상환방법/발행형태 + 행사대상주식코드/행사비율/
        현재행사가/신주대금납입(BW만: 현금·대용증권)/주식교부기준.
        행사정보가 없는 일반 사채면 행사 칼럼은 빠진다.
    """
    session = session or _web_session()
    out: dict = {}
    basic = _web_call(session, "issuInfoViewEL1", bond_isin)
    if basic:
        out.update({WEB_RENAME[k]: v for k, v in basic[0].items() if k in WEB_RENAME})
    exer = _web_call(session, "exerInfoView", bond_isin)
    if exer:
        out.update({EXER_RENAME[k]: v for k, v in exer[0].items() if k in EXER_RENAME})
    out.setdefault("채권코드", bond_isin)
    return out
