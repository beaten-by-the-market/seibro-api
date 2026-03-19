"""주식관련사채 종합 조회 및 표출 모듈

종목코드를 입력하면:
1. 예탁원(Seibro) 실시간 현황 - 전체 출력
2. DART 주요사항보고서 이력 - 주요 칼럼만
3. DART 정기보고서(사업/반기) CB/BW 이력 - 주요 칼럼만
"""

import pandas as pd
from .stock_bond import get_stock_bonds, get_dart_cb_events
from .dart_report import get_bonds_from_report


def display_bond_summary(stock_code: str, save_csv: bool = False) -> dict[str, pd.DataFrame]:
    """주식관련사채 종합 조회 + 표출

    Args:
        stock_code: 단축종목코드 (예: '079160')
        save_csv: True이면 각 섹션별 CSV 저장

    Returns:
        {"seibro": df, "dart_events": df, "report_cb": df, "report_bw": df}
    """

    results = {}

    # ================================================================
    # 1. 예탁원(Seibro) 실시간 현황 - 전체 출력
    # ================================================================
    print("\n" + "=" * 70)
    print("  [1] 예탁원(Seibro) 주식관련사채 현황")
    print("=" * 70)

    df_seibro = get_stock_bonds(stock_code, save_csv=save_csv)
    results["seibro"] = df_seibro

    if not df_seibro.empty:
        print(f"\n  {len(df_seibro)}건")
        print(df_seibro.to_string(index=False))
    else:
        print("\n  해당 없음")

    # ================================================================
    # 2. DART 주요사항보고서 이력 (CB/BW/EB 발행 공시)
    # ================================================================
    print("\n\n" + "=" * 70)
    print("  [2] DART 주요사항보고서 이력 (CB/BW/EB 발행결정 공시)")
    print("=" * 70)

    df_dart = get_dart_cb_events(stock_code, save_csv=save_csv)
    results["dart_events"] = df_dart

    if not df_dart.empty:
        # 공시URL 생성
        if "접수번호" in df_dart.columns:
            df_dart["공시URL"] = df_dart["접수번호"].apply(
                lambda x: f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={x}"
            )

        # 표출 칼럼 선택
        display_cols = [
            "회사명", "사채종류_회차", "사채발행방법",
            "권면총액(원)", "이사회결의일", "납입일",
            "사채만기일", "공시유형", "공시URL",
        ]
        cols_exist = [c for c in display_cols if c in df_dart.columns]
        df_dart_display = df_dart[cols_exist]

        print(f"\n  {len(df_dart_display)}건")
        print(df_dart_display.to_string(index=False))
    else:
        print("\n  해당 없음")

    # ================================================================
    # 3/4. DART 정기보고서 이력 (사업/반기보고서 XML CB/BW)
    # ================================================================
    print("\n\n" + "=" * 70)
    print("  [3] DART 정기보고서 이력 (사업/반기보고서 CB/BW)")
    print("=" * 70)

    report_results = get_bonds_from_report(stock_code, save_csv=save_csv)
    df_cb = report_results.get("cb", pd.DataFrame())
    df_bw = report_results.get("bw", pd.DataFrame())
    results["report_cb"] = df_cb
    results["report_bw"] = df_bw

    # CB 표출
    cb_display_cols = [
        "보고서유형", "보고서기간", "사채종류", "회차",
        "발행일", "만기일", "발행총액", "미상환잔액",
    ]

    if not df_cb.empty:
        cols_exist = [c for c in cb_display_cols if c in df_cb.columns]
        df_cb_display = df_cb[cols_exist].dropna(subset=["사채종류"], how="all") if "사채종류" in df_cb.columns else df_cb[cols_exist]
        print(f"\n  -- CB(전환사채) : {len(df_cb_display)}건 --")
        print(df_cb_display.to_string(index=False))
    else:
        print("\n  -- CB(전환사채) : 해당 없음 --")

    # BW 표출
    bw_display_cols = [
        "보고서유형", "보고서기간", "사채종류", "회차",
        "발행일", "만기일", "발행총액", "미상환잔액",
    ]

    if not df_bw.empty:
        cols_exist = [c for c in bw_display_cols if c in df_bw.columns]
        df_bw_display = df_bw[cols_exist].dropna(subset=["사채종류"], how="all") if "사채종류" in df_bw.columns else df_bw[cols_exist]
        print(f"\n  -- BW(신주인수권부사채) : {len(df_bw_display)}건 --")
        print(df_bw_display.to_string(index=False))
    else:
        print("\n  -- BW(신주인수권부사채) : 해당 없음 --")

    print("\n" + "=" * 70)
    return results


if __name__ == "__main__":
    import sys
    code = sys.argv[1] if len(sys.argv) > 1 else "079160"
    display_bond_summary(code)
