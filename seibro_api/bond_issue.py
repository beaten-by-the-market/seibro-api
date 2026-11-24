"""일자별 발행 채권 조회 모듈 (Seibro Open API, key 필요).

Seibro API ID: getBondIssuInfo (+ 상세는 getBondStatInfo)

getBondIssuInfo는 발행일 하루치만 받는다(기간 파라미터 없음). 기간을 주면 날짜마다
나눠 부른다. 목록에는 발행일·발행회사·종목코드·종목명 5개 칼럼뿐이라, 발행금액·
금리·만기가 필요하면 details=True로 채권마다 getBondStatInfo를 한 번씩 더 부른다.

대상 (실측, 2026-11): 일반 회사채(공모·사모), P-CBO, CB·BW·EB, 공기업 채권(한국수력원자력 등).
2026년 10월 한 달 322건. 당일 발행분은 다음 날에야 잡히기도 한다.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from time import sleep
from typing import Union

import pandas as pd

from .openapi import SeibroClient, SeibroAPIError, retry_transient
from .stock_bond import _decode_codes

LIST_RENAME = {
    "ISSU_DT": "발행일",
    "ISSUCO_CUSTNO": "발행회사고객번호",
    "ISSUCO_CUST_NM": "발행회사",
    "ISIN": "채권코드",
    "KOR_SECN_NM": "채권명",
}

# getBondStatInfo 상세 중 붙일 칼럼 (원천명 → 한글)
DETAIL_RENAME = {
    "XPIR_DT": "만기일",
    "FIRST_ISSU_AMT": "발행금액",
    "ISSU_REMA": "미상환잔액",
    "COUPON_RATE": "표면이자율",
    "SECN_KACD": "종목종류코드",
}
# _decode_codes가 만드는 한글 칼럼 중 붙일 것
DECODED_COLS = ["채권종류", "모집방법", "옵션", "보증", "순위", "이자지급방법", "원금상환방법",
                "KIS_등급", "NICE_등급", "KR_등급"]


def _to_date(value: Union[str, date, datetime]) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value).strip().replace("-", "").replace("/", ""), "%Y%m%d").date()


def bond_type_from_name(name: str) -> str:
    """채권명 괄호 표기로 대략적인 유형을 붙인다: CB / BW / EB / P-CBO / 일반.

    예: '보로노이 5CB(사모/전환/풋)' → CB, '아모텍9(PCBO사모/콜)' → P-CBO.
    공식 분류가 아니다. 정확한 구분은 details=True의 '채권종류'(PARTICUL_BOND_KIND_TPCD)를 쓴다.
    """
    n = str(name or "")
    if re.search(r"\d\s*CB|\(.*전환", n):
        return "CB"
    if re.search(r"\d\s*BW|\(.*신[/)]", n):
        return "BW"
    if re.search(r"\d\s*EB|\(.*교환", n):
        return "EB"
    if "PCBO" in n.upper() or "P-CBO" in n.upper():
        return "P-CBO"
    return "일반"


def get_issued_bonds(
    start_dt: Union[str, date, datetime],
    end_dt: Union[str, date, datetime] = None,
    details: bool = False,
    skip_weekends: bool = True,
    client: SeibroClient = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """발행일(또는 기간)별 발행 채권 목록.

    Args:
        start_dt: 발행일 (YYYYMMDD / YYYY-MM-DD / date). end_dt가 없으면 이 하루만.
        end_dt: 기간 끝(포함). 날짜마다 1회씩 호출한다.
        details: True면 채권마다 getBondStatInfo를 불러 만기·발행금액·금리·
                 모집방법·옵션·신용등급 등을 붙인다(채권 수만큼 추가 호출).
        skip_weekends: 토·일은 부르지 않는다(주말 발행 건은 사실상 없음).
        client: SeibroClient. None이면 자동 생성.
        verbose: 진행 상황 출력.

    Returns:
        발행일, 발행회사, 발행회사고객번호, 채권코드, 채권명, 유형(채권명 기준) [+ 상세 칼럼]
    """
    if client is None:
        client = SeibroClient()
    start = _to_date(start_dt)
    end = _to_date(end_dt) if end_dt else start
    if start > end:
        raise ValueError(f"start_dt must be <= end_dt: {start} > {end}")

    frames = []
    day = start
    while day <= end:
        if not (skip_weekends and day.weekday() >= 5):
            df = retry_transient(client.get_bond_issues, issue_dt=day.strftime("%Y%m%d"))
            if not df.empty:
                frames.append(df)
            sleep(0.15)
        day += timedelta(days=1)

    cols = ["발행일", "발행회사", "발행회사고객번호", "채권코드", "채권명", "유형"]
    if not frames:
        if verbose:
            print(f"[Seibro] {start}~{end} 발행 채권 없음")
        return pd.DataFrame(columns=cols)

    out = pd.concat(frames, ignore_index=True).rename(columns=LIST_RENAME)
    out["발행일"] = pd.to_datetime(out["발행일"], format="%Y%m%d", errors="coerce")
    out["유형"] = out["채권명"].map(bond_type_from_name)
    out = out[cols].sort_values(["발행일", "발행회사", "채권코드"]).reset_index(drop=True)
    if verbose:
        print(f"[Seibro] {start}~{end} 발행 채권 {len(out)}건")

    if details:
        rows = []
        for isin in out["채권코드"]:
            try:
                d = retry_transient(client.get_bond_detail, isin)
            except SeibroAPIError:
                d = pd.DataFrame()
            if not d.empty:
                d = _decode_codes(d.copy())
                r = d.iloc[0]
                rec = {"채권코드": isin}
                rec.update({v: r.get(k) for k, v in DETAIL_RENAME.items()})
                rec.update({c: r.get(c) for c in DECODED_COLS if c in d.columns})
                rows.append(rec)
            sleep(0.2)
        det = pd.DataFrame(rows)
        if not det.empty:
            for c in ("발행금액", "미상환잔액", "표면이자율"):
                det[c] = pd.to_numeric(det[c], errors="coerce")
            det["만기일"] = pd.to_datetime(det["만기일"], format="%Y%m%d", errors="coerce")
            out = out.merge(det, on="채권코드", how="left")
            out["만기(년)"] = ((out["만기일"] - out["발행일"]).dt.days / 365.25).round(1)
        if verbose:
            print(f"  -> 상세 {len(det)}/{len(out)}건")
    return out


if __name__ == "__main__":
    import sys

    s = sys.argv[1] if len(sys.argv) > 1 else (date.today() - timedelta(days=1)).strftime("%Y%m%d")
    e = sys.argv[2] if len(sys.argv) > 2 else None
    print(get_issued_bonds(s, e, details=True).to_string(index=False))
