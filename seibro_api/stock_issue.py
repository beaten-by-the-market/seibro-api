"""주식수량 변동내역 조회 모듈."""

import pandas as pd
from typing import Union

from .client import SeibroClient


SECN_KACD_MAP = {
    "0101": "보통주",
    "0201": "우선주",
    "0301": "후배주",
    "0401": "혼합주",
}

STOCK_ISSUE_RENAME = {
    "ISSUCO_CUSTNO": "발행회사고객번호",
    "ISIN": "종목번호",
    "SECN_KACD": "종목종류코드",
    "SECN_ISSU_NTIMES": "종목발행횟수",
    "ISSU_DT": "발행일자",
    "ISSUPRC": "발행가",
    "ISSU_QTY": "발행수량",
    "SECN_ISSU_RACD": "종목발행사유코드",
    "SECN_ISSU_NM": "종목발행사유명",
    "LIST_DT": "상장일자",
}


def _format_stock_issue_details(df: pd.DataFrame) -> pd.DataFrame:
    """Seibro 원천 칼럼을 분석하기 쉬운 한글 칼럼으로 정리."""
    if df.empty:
        return df

    result = df.copy()

    if "SECN_KACD" in result.columns:
        result["종목종류"] = result["SECN_KACD"].map(SECN_KACD_MAP).fillna(result["SECN_KACD"])

    result.rename(
        columns={k: v for k, v in STOCK_ISSUE_RENAME.items() if k in result.columns},
        inplace=True,
    )

    preferred_cols = [
        "발행회사고객번호",
        "종목번호",
        "종목종류코드",
        "종목종류",
        "종목발행횟수",
        "발행일자",
        "발행가",
        "발행수량",
        "종목발행사유코드",
        "종목발행사유명",
        "상장일자",
    ]
    ordered_cols = [c for c in preferred_cols if c in result.columns]
    other_cols = [c for c in result.columns if c not in ordered_cols]
    return result[ordered_cols + other_cols]


def get_stock_issue_details(
    stock_code: str = None,
    isin: str = None,
    issuco_custno: Union[str, int] = None,
    issue_year: Union[str, int] = None,
    client: SeibroClient = None,
    save_csv: bool = True,
) -> pd.DataFrame:
    """주식수량 변동내역을 조회.

    Args:
        stock_code: 단축코드(SHOTN_ISIN). 예: "005930"
        isin: 표준코드(ISIN). 예: "KR7005930003"
        issuco_custno: 발행회사고객번호(ISSUCO_CUSTNO).
        issue_year: 발행연도(ISSU_YEAR). 예: 2018
        client: SeibroClient 인스턴스. None이면 자동 생성.
        save_csv: True이면 CSV 파일로 저장.

    Returns:
        주식수량 변동내역 DataFrame.
    """
    if client is None:
        client = SeibroClient()

    print("\n[Seibro] 주식수량 변동내역 조회")
    if stock_code:
        print(f"  단축코드: {str(stock_code).zfill(6)}")
    if isin:
        print(f"  표준코드: {isin}")
    if issuco_custno is not None:
        print(f"  발행회사고객번호: {issuco_custno}")
    if issue_year is not None:
        print(f"  발행연도: {issue_year}")

    df = client.get_stock_issue_details(
        stock_code=stock_code,
        isin=isin,
        issuco_custno=issuco_custno,
        issue_year=issue_year,
    )
    df_result = _format_stock_issue_details(df)

    if df_result.empty:
        print("  해당 내역이 없습니다.")
        return df_result

    print(f"  -> {len(df_result)}건 조회 완료")

    if save_csv:
        key = stock_code or isin or issuco_custno
        year = issue_year or "all"
        filename = f"stock_issue_details_{key}_{year}.csv"
        df_result.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"  -> {filename} 저장 완료")

    return df_result


if __name__ == "__main__":
    import sys

    code = sys.argv[1] if len(sys.argv) > 1 else "005930"
    year = sys.argv[2] if len(sys.argv) > 2 else None
    result = get_stock_issue_details(stock_code=code, issue_year=year)
    if not result.empty:
        print(result.to_string(index=False))
