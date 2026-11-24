"""주식관련사채(CB/BW/EB) 잔여 행사물량 조회 모듈.

1. get_bond_web_info: SEIBro 웹 "채권 종목상세"(BIP_CNTS03004V) 화면의 WebSquare 호출 2종
   (issuInfoViewEL1 기본정보 + exerInfoView 행사정보)을 재현한다. key 불필요.
2. get_stock_linked_bond_status: 주식 하나에 연결된 사채별로 발행·잔액·현재 행사가·
   누적 행사 실적을 한 표로 모은다. Open API(key 필요) + 웹 호출.

전환·행사 가능 주식수는 여기서 계산하지 않는다. 사채 종류별로 맞는 계산이 다르다.
  - CB: 미상환잔액 × 행사비율 ÷ 현재 전환가. 전환하면 사채가 소멸하므로 잔액이 곧 미전환분이다.
  - BW: 신주인수권은 사채와 따로 움직인다. 현금 납입이면 행사해도 사채 잔액이 줄지 않고,
    사채를 조기상환해도 신주인수권(특히 분리형)은 남는다. 그래서
    "발행금액 × 행사비율 − 누적 행사금액"(= 미행사 신주인수권 금액)이 더 맞다.
  - EB: 이미 발행된 주식(주로 자기주식)과 교환하므로 발행주식수가 늘지 않는다.
"""

from __future__ import annotations

from time import sleep
from xml.etree.ElementTree import ParseError

import pandas as pd
import requests

from .openapi import SeibroClient, SeibroAPIError, retry_transient
from .web.bond_detail import _web_session, get_bond_web_info


def _bond_kind(kind_name: str) -> str:
    k = str(kind_name or "")
    if "BW" in k:
        return "BW"
    if "EB" in k:
        return "EB"
    if "CB" in k:
        return "CB"
    return k or "기타"


def get_stock_linked_bond_status(
    stock_code: str,
    client: SeibroClient = None,
    session: requests.Session | None = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """주식 하나에 연결된 주식관련사채별 발행·잔액·현재 행사가·누적 행사 실적.

    호출 순서: getStkStatInfo(종목 ISIN) → getXrcStkStatInfo(연결 사채 목록) →
    사채마다 웹 기본정보·행사정보(get_bond_web_info) + getXrcStkOptionXrcInfo(행사 내역).
    웹 호출이 실패하면 getBondStatInfo로 금액만 채운다.

    Returns:
        사채 1개 1행. 주요 칼럼:
        채권코드, 채권명, 구분(CB/BW/EB), 종류(원문: 비분리형BW 등), 모집방법, 옵션,
        발행일, 만기일, 발행금액, 미상환잔액, 행사비율, 현재행사가, 목록행사가(Open API),
        신주대금납입, 행사횟수, 누적행사금액, 누적행사주식수, 최근행사일,
        행사가능시작일, 행사가능종료일(행사 내역이 있을 때만 알 수 있음)
        금액·수량·가격은 숫자, 날짜는 Timestamp.
    """
    if client is None:
        client = SeibroClient()
    session = session or _web_session()
    code = str(stock_code).strip().zfill(6)

    stk = retry_transient(client.get_stock_info, stock_code=code)
    if stk.empty:
        raise ValueError(f"종목을 찾지 못했습니다: {code}")
    stock_isin = stk.iloc[0]["ISIN"]
    if verbose:
        print(f"[Seibro] {stk.iloc[0]['KOR_SECN_NM']}({code}, {stock_isin}) 주식관련사채 조회")

    bonds = retry_transient(client.get_stock_linked_bonds, stock_isin)
    if bonds.empty:
        if verbose:
            print("  -> 연결된 주식관련사채 없음")
        return pd.DataFrame()

    rows = []
    for _, b in bonds.iterrows():
        isin = b["BOND_ISIN"]
        row = {"채권코드": isin, "채권명": b.get("BOND_SECN_NM"), "종류": b.get("BOND_KIND_NM"),
               "목록행사가": b.get("XRC_PRICE"), "목록행사비율": b.get("XRC_RATIO")}
        web_err = None
        try:
            web = get_bond_web_info(isin, session=session)
            row.update({k: v for k, v in web.items() if k not in ("채권명", "종류") or not row.get(k)})
        except (requests.RequestException, ParseError, ValueError) as e:
            web_err = type(e).__name__
        if row.get("발행금액"):
            row["상세출처"] = "웹"
        else:
            try:
                d = retry_transient(client.get_bond_detail, isin)
                if not d.empty:
                    r = d.iloc[0]
                    row.update({"발행일": r.get("ISSU_DT"), "만기일": r.get("XPIR_DT"),
                                "발행금액": r.get("FIRST_ISSU_AMT"), "미상환잔액": r.get("ISSU_REMA"),
                                "표면이자율": r.get("COUPON_RATE")})
                row["상세출처"] = f"OpenAPI(웹 {web_err or '빈 응답'})"
            except SeibroAPIError:
                row["상세출처"] = "없음"
        sleep(0.3)

        try:
            ex = retry_transient(client.get_bond_exercises, isin)
        except SeibroAPIError:
            ex = None
        if ex is None:
            row["행사내역"] = "조회실패"
        elif ex.empty:
            row.update({"행사내역": "없음", "행사횟수": 0, "누적행사금액": 0, "누적행사주식수": 0})
        else:
            amt = pd.to_numeric(ex["XRC_AMT"], errors="coerce")
            qty = pd.to_numeric(ex["XRC_QTY"], errors="coerce")
            row.update({
                "행사내역": "있음",
                "행사횟수": len(ex),
                "누적행사금액": amt.sum(),
                "누적행사주식수": qty.sum(),
                "최근행사일": ex["RGT_STD_DT"].max(),
                "행사가능시작일": ex["XRC_POSS_BEGIN_DT"].min(),
                "행사가능종료일": ex["XRC_POSS_EXPRY_DT"].max(),
            })
        rows.append(row)
        sleep(0.3)

    order = ["채권코드", "채권명", "구분", "종류", "모집방법", "옵션", "발행일", "만기일",
             "발행금액", "미상환잔액", "표면이자율", "행사비율", "현재행사가", "목록행사가",
             "신주대금납입", "행사내역", "행사횟수", "누적행사금액", "누적행사주식수", "최근행사일",
             "행사가능시작일", "행사가능종료일", "상세출처"]
    df = pd.DataFrame(rows)
    for col in order + ["목록행사비율"]:  # 행사 내역이 하나도 없어도 칼럼은 늘 같게
        if col not in df.columns:
            df[col] = None
    df["구분"] = df["종류"].map(_bond_kind)
    df["현재행사가"] = df["현재행사가"].replace("", None).fillna(df["목록행사가"])
    df["행사비율"] = df["행사비율"].replace("", None).fillna(df["목록행사비율"])
    for col in ("발행금액", "미상환잔액", "표면이자율", "행사비율", "현재행사가", "목록행사가",
                "행사횟수", "누적행사금액", "누적행사주식수"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ("발행일", "만기일", "최근행사일", "행사가능시작일", "행사가능종료일"):
        df[col] = pd.to_datetime(df[col], format="%Y%m%d", errors="coerce")
    df = df[order]
    if verbose:
        print(f"  -> {len(df)}건: " + ", ".join(f"{k} {v}" for k, v in df["구분"].value_counts().items()))
    return df


if __name__ == "__main__":
    import sys

    code = sys.argv[1] if len(sys.argv) > 1 else "276730"
    print(get_stock_linked_bond_status(code).to_string(index=False))
