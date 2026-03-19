"""주식관련사채(CB/BW/EB) 조회 모듈

1. get_stock_bonds: Seibro API로 단일 종목의 CB/BW/EB 현황 조회
2. get_dart_cb_events: DART API로 단일 종목의 전환사채 발행 공시 이력 조회
"""

import pandas as pd
from datetime import datetime, timedelta
from time import sleep
from .client import SeibroClient


# ── 코드 디코딩 테이블 ──────────────────────────────────────
CODE_TABLES = {
    "RECU_WHCD": {
        "name": "모집방법",
        "map": {"11": "공모", "12": "사모", "13": "일반(국채,지방채,특수채)", "14": "CBO기초사모", "21": "매출"},
    },
    "PARTICUL_BOND_KIND_TPCD": {
        "name": "채권종류",
        "map": {"1": "전환(CB)", "2": "교환(EB)", "3": "신주인수권(BW)", "4": "분리형BW", "6": "이익참가", "9": "해당없음"},
    },
    "OPTION_TPCD": {
        "name": "옵션",
        "map": {"9401": "CALL", "9402": "PUT", "9403": "CALL+PUT", "9404": "NOTE", "0000": "해당없음"},
    },
    "FORC_ERLY_RED_YN": {
        "name": "강제조기상환",
        "map": {"Y": "YES", "N": "NO"},
    },
    "MR_CHG_TPCD": {
        "name": "금리변동",
        "map": {"1": "고정", "2": "변동", "3": "고정+변동"},
    },
    "GRTY_TPCD": {
        "name": "보증",
        "map": {"1": "보증", "2": "무보증", "3": "담보부", "4": "일반"},
    },
    "RANK_TPCD": {
        "name": "순위",
        "map": {"1": "선순위", "2": "후순위", "3": "중순위", "9": "해당없음"},
    },
    "PRCP_RED_WHCD": {
        "name": "원금상환방법",
        "map": {"11": "만기상환", "21": "중도상환", "31": "조기상환", "41": "이익분배", "51": "자동상환", "14": "수시상환", "12": "균등분할", "13": "불균등분할"},
    },
    "ISSU_WHCD": {
        "name": "발행방법",
        "map": {"1": "실물발행", "2": "전액등록", "3": "부분등록", "4": "청약증거금영수증발행", "5": "전액불소지", "6": "부분불소지"},
    },
    "INT_PAY_WAY_TPCD": {
        "name": "이자지급방법",
        "map": {"1": "이표", "2": "할인", "3": "복리", "4": "단리"},
    },
    "ELTSC_YN": {
        "name": "전자증권여부",
        "map": {"Y": "전자등록", "N": "-"},
    },
}

CREDIT_GRADE_MAP = {
    "110": "AAA", "111": "AAA+", "112": "AAA0", "113": "AAA-",
    "120": "AA", "121": "AA+", "122": "AA0", "123": "AA-",
    "130": "A", "131": "A+", "132": "A0", "133": "A-",
    "210": "BBB", "211": "BBB+", "212": "BBB0", "213": "BBB-",
    "220": "BB", "221": "BB+", "222": "BB0", "223": "BB-",
    "230": "B", "231": "B+", "232": "B0", "233": "B-",
    "310": "CCC", "320": "CC", "330": "C", "440": "D",
    "900": "유보", "999": "취소",
}


def _decode_codes(df: pd.DataFrame) -> pd.DataFrame:
    """코드 칼럼을 한글명으로 변환"""
    for code_col, info in CODE_TABLES.items():
        if code_col in df.columns:
            df[info["name"]] = df[code_col].map(info["map"]).fillna(df[code_col])

    for grade_col in ["KIS_VALAT_GRD_CD", "NICE_VALAT_GRD_CD", "SCI_VALAT_GRD_CD", "KR_VALAT_GRD_CD"]:
        if grade_col in df.columns:
            label = grade_col.replace("_VALAT_GRD_CD", "")
            df[f"{label}_등급"] = df[grade_col].map(CREDIT_GRADE_MAP).fillna(df[grade_col])

    return df


def get_stock_bonds(stock_code: str, client: SeibroClient = None, save_csv: bool = True) -> pd.DataFrame:
    """단일 종목의 주식관련사채(CB/BW/EB) 정보를 조회

    Args:
        stock_code: 단축종목코드 (예: '001140', '005930')
        client: SeibroClient 인스턴스. None이면 자동 생성 (.env 사용)
        save_csv: True이면 CSV 파일로 저장

    Returns:
        사채 정보가 담긴 DataFrame
    """
    if client is None:
        client = SeibroClient()

    # ── Step 1: 종목 표준코드(ISIN) 확보 ─────────────────────
    print(f"\n[1/4] 종목 {stock_code}의 표준코드 조회 중...")
    df_stk = client._call_api("getStkStatInfo", {"SHOTN_ISIN": stock_code})

    if df_stk.empty:
        print(f"  종목코드 {stock_code}에 해당하는 종목을 찾을 수 없습니다.")
        return pd.DataFrame()

    isin = df_stk.iloc[0].get("ISIN", "")
    company_name = df_stk.iloc[0].get("KOR_SECN_NM", "")
    cust_no = df_stk.iloc[0].get("ISSUCO_CUSTNO", "")
    print(f"  -> {company_name} (고객번호: {cust_no}, ISIN: {isin})")

    # ── Step 2: 주식관련사채 목록 조회 ────────────────────────
    print(f"\n[2/4] 주식관련사채(CB/BW/EB) 목록 조회 중...")
    sleep(0.5)
    df_bonds = client._call_api("getXrcStkStatInfo", {"XRC_STK_ISIN": isin})

    if df_bonds.empty:
        print(f"  {company_name}({stock_code})에 연결된 주식관련사채가 없습니다.")
        return pd.DataFrame()

    # 칼럼명 통일
    if "XRC_STK_ISIN" in df_bonds.columns:
        df_bonds.rename(columns={"XRC_STK_ISIN": "ISU_CD"}, inplace=True)

    print(f"  -> {len(df_bonds)}건의 사채 발견")
    for _, row in df_bonds.iterrows():
        print(f"     {row.get('BOND_SECN_NM', '')} ({row.get('BOND_KIND_NM', '')})")

    # ── Step 3: 각 사채별 상세정보 조회 ───────────────────────
    print(f"\n[3/4] 사채별 상세정보 조회 중...")
    df_details = pd.DataFrame()
    errors = []

    for bond_isin in df_bonds["BOND_ISIN"]:
        sleep(0.3)
        try:
            df_detail = client._call_api("getBondStatInfo", {"ISIN": bond_isin})
            if not df_detail.empty:
                df_detail["BOND_ISIN"] = bond_isin
                df_details = pd.concat([df_details, df_detail], ignore_index=True)
                print(f"  OK {bond_isin}")
            else:
                print(f"  - {bond_isin} (데이터 없음)")
        except Exception as e:
            print(f"  FAIL {bond_isin} 실패: {e}")
            errors.append(bond_isin)

    # 실패 건 재시도
    if errors:
        print(f"\n  실패 {len(errors)}건 재시도 중...")
        sleep(3)
        for bond_isin in errors:
            try:
                df_detail = client._call_api("getBondStatInfo", {"ISIN": bond_isin})
                if not df_detail.empty:
                    df_detail["BOND_ISIN"] = bond_isin
                    df_details = pd.concat([df_details, df_detail], ignore_index=True)
                    print(f"  OK {bond_isin} (재시도 성공)")
            except Exception:
                print(f"  FAIL {bond_isin} (재시도도 실패)")

    # ── Step 4: 데이터 통합 + 코드 디코딩 ─────────────────────
    print(f"\n[4/4] 데이터 통합 및 정리 중...")

    # 사채 목록 + 상세정보 결합
    df_merged = df_bonds.merge(df_details, how="left", on="BOND_ISIN")

    # 코드값 한글 디코딩
    df_merged = _decode_codes(df_merged)

    # 전환/행사 가능 주식수 계산
    if "ISSU_REMA" in df_merged.columns and "XRC_PRICE" in df_merged.columns:
        df_merged["ISSU_REMA"] = pd.to_numeric(df_merged["ISSU_REMA"], errors="coerce")
        df_merged["XRC_PRICE"] = pd.to_numeric(df_merged["XRC_PRICE"], errors="coerce")
        df_merged["전환가능_주식수"] = (df_merged["ISSU_REMA"] // df_merged["XRC_PRICE"]).astype("Int64")

    # 출력용 칼럼 정리
    display_cols = [
        "BOND_ISIN", "BOND_SECN_NM", "BOND_KIND_NM",
        "ISU_CD", "STK_SECN_NM",
        "채권종류", "모집방법", "발행방법",
        "ISSU_DT", "XPIR_DT",
        "FIRST_ISSU_AMT", "ISSU_REMA", "COUPON_RATE",
        "XRC_PRICE", "XRC_RATIO", "전환가능_주식수",
        "옵션", "강제조기상환", "금리변동", "보증", "순위",
        "이자지급방법", "원금상환방법",
        "XPIR_GUAR_PRATE", "XPIRED_RATE",
        "KIS_등급", "NICE_등급", "KR_등급",
        "APLI_DT", "DLIST_DT", "전자증권여부",
    ]
    # 존재하는 칼럼만 선택
    final_cols = [c for c in display_cols if c in df_merged.columns]
    df_result = df_merged[final_cols].copy()

    # 칼럼명 한글화
    rename_map = {
        "BOND_ISIN": "채권코드", "BOND_SECN_NM": "채권명", "BOND_KIND_NM": "CB/BW/EB",
        "ISU_CD": "주권코드", "STK_SECN_NM": "주식종목명",
        "ISSU_DT": "발행일", "XPIR_DT": "만기일",
        "FIRST_ISSU_AMT": "발행금액", "ISSU_REMA": "미상환잔액",
        "COUPON_RATE": "표면이자율",
        "XRC_PRICE": "전환/행사가", "XRC_RATIO": "행사비율",
        "XPIR_GUAR_PRATE": "만기보장수익율", "XPIRED_RATE": "만기상환율",
        "APLI_DT": "상장일", "DLIST_DT": "상장폐지일",
    }
    df_result.rename(columns={k: v for k, v in rename_map.items() if k in df_result.columns}, inplace=True)

    # 결과 출력
    print(f"\n{'='*60}")
    print(f"  {company_name}({stock_code}) 주식관련사채 조회 결과")
    print(f"  총 {len(df_result)}건")
    print(f"{'='*60}")

    if not df_result.empty:
        for i, row in df_result.iterrows():
            print(f"\n  [{i+1}] {row.get('채권명', '')}")
            print(f"      유형: {row.get('CB/BW/EB', '')} | {row.get('채권종류', '')} | {row.get('모집방법', '')}")
            print(f"      기간: {row.get('발행일', '')} ~ {row.get('만기일', '')}")
            issu_rema = row.get('미상환잔액', '')
            xrc_price = row.get('전환/행사가', '')
            xrc_shares = row.get('전환가능_주식수', '')
            print(f"      미상환잔액: {issu_rema} | 전환/행사가: {xrc_price} | 전환가능주식수: {xrc_shares}")

    # CSV 저장
    if save_csv and not df_result.empty:
        filename = f"stock_bond_{stock_code}.csv"
        df_result.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"\n-> {filename} 저장 완료")

    return df_result


# ── DART 칼럼명 한글 변환 테이블 ────────────────────────────
# CB/BW/EB 공통
DART_RENAME_COMMON = {
    "rcept_no": "접수번호",
    "corp_cls": "법인구분",
    "corp_code": "고유번호",
    "corp_name": "회사명",
    "bd_tm": "사채종류_회차",
    "bd_knd": "사채종류_종류",
    "bd_fta": "권면총액(원)",
    "atcsc_rmislmt": "정관상_잔여발행한도(원)",
    "ovis_fta": "해외발행_총액",
    "ovis_fta_crn": "해외발행_통화단위",
    "ovis_ster": "해외발행_기준환율",
    "ovis_isar": "해외발행_발행지역",
    "ovis_mktnm": "해외발행_상장시장명",
    "fdpp_fclt": "자금목적_시설자금(원)",
    "fdpp_bsninh": "자금목적_영업양수자금(원)",
    "fdpp_op": "자금목적_운영자금(원)",
    "fdpp_dtrp": "자금목적_채무상환자금(원)",
    "fdpp_ocsa": "자금목적_타법인증권취득(원)",
    "fdpp_etc": "자금목적_기타(원)",
    "bd_intr_ex": "표면이자율(%)",
    "bd_intr_sf": "만기이자율(%)",
    "bd_mtd": "사채만기일",
    "bdis_mthn": "사채발행방법",
    "abmg": "합병관련사항",
    "sbd": "청약일",
    "pymd": "납입일",
    "rpmcmp": "대표주관회사",
    "grint": "보증기관",
    "bddd": "이사회결의일",
    "od_a_at_t": "사외이사_참석(명)",
    "od_a_at_b": "사외이사_불참(명)",
    "adt_a_atn": "감사_참석여부",
    "rs_sm_atn": "증권신고서_제출대상",
    "ex_sm_r": "제출면제_사유",
    "ovis_ltdtl": "해외발행_대차거래내역",
    "ftc_stt_atn": "공정위_신고대상",
}

# CB 전용
DART_RENAME_CB = {
    "cv_rt": "전환비율(%)",
    "cv_prc": "전환가액(원/주)",
    "cvisstk_knd": "전환발행주식_종류",
    "cvisstk_cnt": "전환발행주식_주식수",
    "cvisstk_tisstk_vs": "전환발행주식_총수대비(%)",
    "cvrqpd_bgd": "전환청구기간_시작일",
    "cvrqpd_edd": "전환청구기간_종료일",
    "act_mktprcfl_cvprc_lwtrsprc": "최저조정가액(원)",
    "act_mktprcfl_cvprc_lwtrsprc_bs": "최저조정가액_근거",
    "rmislmt_lt70p": "70%미만_조정가능_잔여한도(원)",
}

# BW 전용
DART_RENAME_BW = {
    "ex_rt": "행사비율(%)",
    "ex_prc": "행사가액(원/주)",
    "ex_prc_dmth": "행사가액_결정방법",
    "bdwt_div_atn": "사채_인수권_분리여부",
    "nstk_pym_mth": "신주대금_납입방법",
    "nstk_isstk_knd": "행사발행주식_종류",
    "nstk_isstk_cnt": "행사발행주식_주식수",
    "nstk_isstk_tisstk_vs": "행사발행주식_총수대비(%)",
    "expd_bgd": "권리행사기간_시작일",
    "expd_edd": "권리행사기간_종료일",
    "act_mktprcfl_cvprc_lwtrsprc": "최저조정가액(원)",
    "act_mktprcfl_cvprc_lwtrsprc_bs": "최저조정가액_근거",
    "rmislmt_lt70p": "70%미만_조정가능_잔여한도(원)",
}

# EB 전용
DART_RENAME_EB = {
    "ex_rt": "교환비율(%)",
    "ex_prc": "교환가액(원/주)",
    "ex_prc_dmth": "교환가액_결정방법",
    "extg": "교환대상_종류",
    "extg_stkcnt": "교환대상_주식수",
    "extg_tisstk_vs": "교환대상_총수대비(%)",
    "exrqpd_bgd": "교환청구기간_시작일",
    "exrqpd_edd": "교환청구기간_종료일",
}


def get_dart_cb_events(stock_code: str, years: int = 5, save_csv: bool = True) -> pd.DataFrame:
    """DART 전자공시에서 단일 종목의 CB/BW/EB 발행 공시 이력 조회

    Args:
        stock_code: 단축종목코드 (예: '079160')
        years: 조회 기간 (오늘 기준 N년 전부터). 기본값 5년
        save_csv: True이면 CSV 파일로 저장

    Returns:
        CB/BW/EB 발행 공시 내역이 통합된 DataFrame
    """
    import OpenDartReader
    import os
    from dotenv import load_dotenv

    load_dotenv()
    dart_key = os.getenv("DART_API_KEY")
    if not dart_key:
        raise ValueError("DART_API_KEY가 .env 파일이나 환경변수에 없습니다.")

    dart = OpenDartReader(dart_key)

    end_dt = datetime.today().strftime("%Y%m%d")
    start_dt = (datetime.today() - timedelta(days=years * 365)).strftime("%Y%m%d")

    print(f"\n[DART] {stock_code} 주식관련사채 발행 공시 조회")
    print(f"  기간: {start_dt} ~ {end_dt} ({years}년)")

    # CB / BW / EB 세 가지 이벤트 조회
    event_config = [
        ("전환사채발행", "CB", DART_RENAME_CB),
        ("신주인수권부사채발행", "BW", DART_RENAME_BW),
        ("교환사채발행", "EB", DART_RENAME_EB),
    ]

    dfs = []
    for event_name, bond_type, rename_specific in event_config:
        print(f"\n  [{bond_type}] {event_name} 조회 중...")
        sleep(0.2)
        try:
            df = dart.event(stock_code, event_name, start=start_dt, end=end_dt)
        except Exception as e:
            print(f"    조회 실패: {e}")
            continue

        if df is None or df.empty:
            print(f"    해당 없음")
            continue

        df["공시유형"] = bond_type
        df["stock_code"] = stock_code

        # 칼럼명 한글 변환 (공통 + 유형별)
        rename_map = {**DART_RENAME_COMMON, **rename_specific}
        df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

        dfs.append(df)
        print(f"    -> {len(df)}건")

    if not dfs:
        print(f"\n  {stock_code}의 CB/BW/EB 발행 공시가 없습니다.")
        return pd.DataFrame()

    df_result = pd.concat(dfs, ignore_index=True)
    print(f"\n  총 {len(df_result)}건 조회 완료 (CB/BW/EB 통합)")

    if save_csv and not df_result.empty:
        filename = f"dart_bond_{stock_code}.csv"
        df_result.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"  -> {filename} 저장 완료")

    return df_result


if __name__ == "__main__":
    import sys

    code = sys.argv[1] if len(sys.argv) > 1 else "079160"
    mode = sys.argv[2] if len(sys.argv) > 2 else "all"

    if mode in ("all", "seibro"):
        df_seibro = get_stock_bonds(code)
    if mode in ("all", "dart"):
        df_dart = get_dart_cb_events(code)
