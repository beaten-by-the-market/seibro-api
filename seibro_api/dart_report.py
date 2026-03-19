"""DART 사업보고서/반기보고서 조회 및 SUB_PIS 테이블 추출 모듈

종목코드를 입력하면:
1. 가장 최근 사업보고서 + 반기보고서를 DART에서 조회
2. [첨부정정] 공시는 원본 rcept_no를 추적 (rcept_no_new)
3. XML 원문을 다운로드
4. SUB_PIS aclass 테이블을 파싱하여 DataFrame으로 반환 + CSV 저장
"""

import os
import re
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def _init_dart():
    """OpenDartReader 초기화"""
    import OpenDartReader
    load_dotenv()
    dart_key = os.getenv("DART_API_KEY")
    if not dart_key:
        raise ValueError("DART_API_KEY가 .env 파일이나 환경변수에 없습니다.")
    return OpenDartReader(dart_key)


def _get_rcept_no_new(rcept_no: str, report_nm: str) -> str:
    """[첨부정정] 공시인 경우 원본 rcept_no를 DART 페이지에서 찾아 반환"""
    if "[첨부정정]" not in str(report_nm):
        return rcept_no

    url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "lxml")

    family = soup.find(id="family")
    if not family:
        return rcept_no

    options = [opt for opt in family.find_all("option") if opt["value"] != "null"]
    if not options:
        return rcept_no

    first_url = f"https://dart.fss.or.kr/dsaf001/main.do?{options[0]['value']}"
    return first_url[-14:]


def _parse_aclass_table(xml_text: str, aclass: str) -> tuple[list[dict], dict]:
    """XML 원문에서 특정 aclass의 table-group 데이터를 파싱

    dual-TABLE 대응: 단위표(작은 테이블)와 실제 데이터(큰 테이블)를 구분.
    가장 데이터 행이 많은 테이블을 본 데이터로 선택.

    Returns:
        (records, meta) - records: 본 데이터 행 리스트, meta: 단위표 등 메타 정보
    """
    soup = BeautifulSoup(xml_text, "lxml")
    group = soup.find("table-group", attrs={"aclass": aclass})

    if not group:
        return [], {}

    # table-group 내 모든 TABLE에서 데이터 추출
    all_tables_data = []
    for tbl in group.find_all("table"):
        tbody = tbl.find("tbody") or tbl
        rows_data = []
        for r in tbody.find_all("tr"):
            if r.find(["th"]):
                continue
            cells = r.find_all(["te", "tu"])
            record = {
                (cell.get("acode") or cell.get("aunit")): cell.get_text(strip=True)
                for cell in cells
                if cell.get("acode") or cell.get("aunit")
            }
            if record:
                rows_data.append(record)
        if rows_data:
            all_tables_data.append(rows_data)

    if not all_tables_data:
        return [], {}

    if len(all_tables_data) == 1:
        return all_tables_data[0], {}

    # 가장 행이 많은 테이블 = 본 데이터, 나머지 = 메타(단위표 등)
    all_tables_data.sort(key=lambda x: len(x), reverse=True)
    main_data = all_tables_data[0]

    # 나머지 작은 테이블들의 데이터를 메타 정보로 합침
    meta = {}
    for small_table in all_tables_data[1:]:
        for row in small_table:
            meta.update(row)

    return main_data, meta


# ── SUB_PIS 칼럼명 한글 변환 ─────────────────────────────────
SUB_PIS_RENAME = {
    "BSS_PIS_CMPY": "발행회사",
    "BSS_PIS_KNN": "증권종류",
    "BSS_PIS_STC": "발행방법",
    "BSS_PIS_DAT": "발행일자",
    "BSS_PIS_MON": "발행총액",
    "BSS_PIS_RATE": "이자율(%)",
    "BSS_PIS_LEV": "신용등급",
    "BSS_PIS_LAS": "만기일",
    "BSS_PIS_REC": "상환여부",
    "BSS_PIS_SUC": "주관회사",
    "BSS_PIS_MONT": "합계_발행총액",
    "BSS_PIS_RATET": "합계_이자율",
    "BSS_PIS_LEVT": "합계_신용등급",
    "BSS_PIS_RECT": "합계_상환여부",
    "BSS_PIS_SUCT": "합계_주관회사",
    "BASE_DT": "기준일",
    "WONPERCENT": "단위",
}


# ── CB 칼럼명 한글 변환 ──────────────────────────────────────
CB_RENAME = {
    "CB_KND": "사채종류",
    "CB_SEQ": "회차",
    "CB_DT": "발행일",
    "CB_FDT": "만기일",
    "CB_EN": "발행총액",
    "CB_KN": "전환주식종류",
    "CB_PE": "전환청구기간",
    "CB_RAT": "전환비율(%)",
    "CB_PR": "전환가액(원)",
    "CB_AMN": "미상환잔액",
    "CB_CN": "전환가능주식수",
    "NOTE": "비고",
    "CB_ENT": "합계_발행총액",
    "CB_KNT": "합계_전환주식종류",
    "CB_RATT": "합계_전환비율",
    "CB_PRT": "합계_전환가액",
    "CB_AMNT": "합계_미상환잔액",
    "CB_CNT": "합계_전환가능주식수",
    "NOTET": "합계_비고",
    "BASE_DT": "기준일",
    "WONSTOCK": "단위",
}

# ── BW 칼럼명 한글 변환 ──────────────────────────────────────
BW_RENAME = {
    "BW_KND": "사채종류",
    "BW_SEQ": "회차",
    "BW_DT": "발행일",
    "BW_FDT": "만기일",
    "BW_EN": "발행총액",
    "BW_KN": "행사주식종류",
    "BW_PE": "행사기간",
    "BW_RAT": "행사비율(%)",
    "BW_PR": "행사가액(원)",
    "BW_AMN": "미상환잔액",
    "BW_CN": "행사가능주식수",
    "NOTE": "비고",
    "BW_ENT": "합계_발행총액",
    "BW_KNT": "합계_행사주식종류",
    "BW_RATT": "합계_행사비율",
    "BW_PRT": "합계_행사가액",
    "BW_AMNT": "합계_미상환잔액",
    "BW_CNT": "합계_행사가능주식수",
    "NOTET": "합계_비고",
    "BASE_DT": "기준일",
    "WONSTOCK": "단위",
}

# ── EB 칼럼명 한글 변환 ──────────────────────────────────────
EB_RENAME = {
    "EB_KND": "사채종류",
    "EB_SEQ": "회차",
    "EB_DT": "발행일",
    "EB_FDT": "만기일",
    "EB_EN": "발행총액",
    "EB_KN": "교환주식종류",
    "EB_PE": "교환청구기간",
    "EB_RAT": "교환비율(%)",
    "EB_PR": "교환가액(원)",
    "EB_AMN": "미상환잔액",
    "EB_CN": "교환가능주식수",
    "NOTE": "비고",
    "EB_ENT": "합계_발행총액",
    "EB_KNT": "합계_교환주식종류",
    "EB_RATT": "합계_교환비율",
    "EB_PRT": "합계_교환가액",
    "EB_AMNT": "합계_미상환잔액",
    "EB_CNT": "합계_교환가능주식수",
    "NOTET": "합계_비고",
    "BASE_DT": "기준일",
    "WONSTOCK": "단위",
}


def _identify_report_period(report_nm: str) -> str:
    """보고서명에서 기간 정보 추출 (예: '2025.12', '2025.06')"""
    match = re.search(r"\((\d{4}\.\d{2})\)", str(report_nm))
    return match.group(1) if match else ""


def _fetch_report_xmls(stock_code: str) -> list[dict]:
    """최근 사업보고서 + 반기보고서의 XML 원문을 다운로드하여 반환 (공통 Step 1~3)

    Returns:
        targets 리스트. 각 항목: {type, row, rcept_no_new, xml_text}
    """
    dart = _init_dart()

    end_dt = datetime.today().strftime("%Y%m%d")
    start_dt = (datetime.today() - timedelta(days=2 * 365)).strftime("%Y%m%d")

    print(f"\n[1/3] {stock_code} 최근 사업/반기보고서 조회 중...")
    print(f"  기간: {start_dt} ~ {end_dt}")

    try:
        df_list = dart.list(corp=stock_code, kind="A", start=start_dt, end=end_dt, final=True)
    except Exception as e:
        print(f"  조회 실패: {e}")
        return []

    if df_list is None or df_list.empty:
        print(f"  {stock_code}의 보고서가 없습니다.")
        return []

    mask_annual = df_list["report_nm"].str.contains("사업보고서", na=False) & ~df_list["report_nm"].str.contains("반기", na=False)
    mask_semi = df_list["report_nm"].str.contains("반기보고서", na=False)

    df_annual = df_list[mask_annual].sort_values("rcept_dt", ascending=False)
    df_semi = df_list[mask_semi].sort_values("rcept_dt", ascending=False)

    targets = []
    if not df_annual.empty:
        row = df_annual.iloc[0]
        targets.append({"type": "사업보고서", "row": row})
        print(f"  -> 사업보고서: {row['report_nm']} ({row['rcept_dt']})")
    else:
        print(f"  -> 사업보고서: 해당 없음")

    if not df_semi.empty:
        row = df_semi.iloc[0]
        targets.append({"type": "반기보고서", "row": row})
        print(f"  -> 반기보고서: {row['report_nm']} ({row['rcept_dt']})")
    else:
        print(f"  -> 반기보고서: 해당 없음")

    if not targets:
        return []

    targets.sort(key=lambda x: x["row"]["rcept_dt"], reverse=True)

    # rcept_no_new 확보
    print(f"\n[2/3] rcept_no_new 확보 중...")
    for t in targets:
        row = t["row"]
        rcept_no_new = _get_rcept_no_new(row["rcept_no"], row["report_nm"])
        t["rcept_no_new"] = rcept_no_new
        if row["rcept_no"] != rcept_no_new:
            print(f"  [첨부정정] {row['rcept_no']} -> 원본: {rcept_no_new}")
        else:
            print(f"  {t['type']}: {rcept_no_new}")
        time.sleep(0.5)

    # XML 원문 다운로드
    print(f"\n[3/3] XML 원문 다운로드 중...")
    for t in targets:
        rcept_no_new = t["rcept_no_new"]
        try:
            xml_text = dart.document(rcept_no_new)
            t["xml_text"] = xml_text
            print(f"  OK {t['type']} ({rcept_no_new}) - {len(xml_text):,}자")
        except Exception as e:
            print(f"  FAIL {t['type']} ({rcept_no_new}): {e}")
            t["xml_text"] = None
        time.sleep(1)

    return targets


def _extract_aclass(targets: list[dict], aclass: str, rename_map: dict,
                    stock_code: str, label: str, save_csv: bool) -> pd.DataFrame:
    """targets(XML 포함)에서 특정 aclass 테이블을 파싱하여 DataFrame 반환 (공통 Step 4~5)"""
    print(f"\n[파싱] {label} (aclass={aclass}) ...")
    all_dfs = []

    for t in targets:
        xml_text = t.get("xml_text")
        if not xml_text:
            print(f"  {t['type']}: XML 없음, 스킵")
            continue

        row = t["row"]
        report_period = _identify_report_period(row["report_nm"])
        records, meta = _parse_aclass_table(xml_text, aclass)

        if records:
            df_parsed = pd.DataFrame(records)
            df_parsed["회사명"] = row["corp_name"]
            df_parsed["보고서유형"] = t["type"]
            df_parsed["보고서기간"] = report_period
            df_parsed["접수번호"] = row["rcept_no"]
            df_parsed["rcept_no_new"] = t["rcept_no_new"]
            df_parsed["접수일"] = row["rcept_dt"]
            for k, v in meta.items():
                df_parsed[k] = v
            all_dfs.append(df_parsed)
            print(f"  {t['type']}({report_period}): {len(records)}건 (메타: {meta})")
        else:
            print(f"  {t['type']}({report_period}): 데이터 없음")

    if not all_dfs:
        print(f"  {label} 데이터를 찾을 수 없습니다.")
        return pd.DataFrame()

    df_result = pd.concat(all_dfs, ignore_index=True)

    # 칼럼명 한글화
    df_result.rename(columns={k: v for k, v in rename_map.items() if k in df_result.columns}, inplace=True)

    # 식별 칼럼을 앞쪽으로 배치
    id_cols = ["회사명", "보고서유형", "보고서기간", "접수번호", "rcept_no_new", "접수일"]
    other_cols = [c for c in df_result.columns if c not in id_cols]
    df_result = df_result[id_cols + other_cols]

    print(f"\n  총 {len(df_result)}건")

    if save_csv and not df_result.empty:
        company = targets[0]["row"]["corp_name"].replace(" ", "_")
        filename = f"{label}_{stock_code}_{company}.csv"
        df_result.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"  -> {filename} 저장 완료")

    return df_result


def get_sub_pis(stock_code: str, save_csv: bool = True, _targets: list = None) -> pd.DataFrame:
    """종목의 최근 사업보고서 + 반기보고서에서 SUB_PIS(채무증권 발행실적) 테이블 추출"""
    targets = _targets or _fetch_report_xmls(stock_code)
    if not targets:
        return pd.DataFrame()
    return _extract_aclass(targets, "SUB_PIS", SUB_PIS_RENAME, stock_code, "sub_pis", save_csv)


def get_cb_from_report(stock_code: str, save_csv: bool = True, _targets: list = None) -> pd.DataFrame:
    """종목의 최근 사업보고서 + 반기보고서에서 CB(전환사채) 테이블 추출"""
    targets = _targets or _fetch_report_xmls(stock_code)
    if not targets:
        return pd.DataFrame()
    return _extract_aclass(targets, "CB", CB_RENAME, stock_code, "cb", save_csv)


def get_bw_from_report(stock_code: str, save_csv: bool = True, _targets: list = None) -> pd.DataFrame:
    """종목의 최근 사업보고서 + 반기보고서에서 BW(신주인수권부사채) 테이블 추출"""
    targets = _targets or _fetch_report_xmls(stock_code)
    if not targets:
        return pd.DataFrame()
    return _extract_aclass(targets, "BW", BW_RENAME, stock_code, "bw", save_csv)


def get_eb_from_report(stock_code: str, save_csv: bool = True, _targets: list = None) -> pd.DataFrame:
    """종목의 최근 사업보고서 + 반기보고서에서 EB(교환사채) 테이블 추출"""
    targets = _targets or _fetch_report_xmls(stock_code)
    if not targets:
        return pd.DataFrame()
    return _extract_aclass(targets, "EB", EB_RENAME, stock_code, "eb", save_csv)


def get_bonds_from_report(stock_code: str, save_csv: bool = True) -> dict[str, pd.DataFrame]:
    """종목의 최근 사업/반기보고서에서 CB/BW/EB를 한 번에 추출 (XML 1회 다운로드)

    Args:
        stock_code: 단축종목코드
        save_csv: True이면 각각 CSV 저장

    Returns:
        {"cb": DataFrame, "bw": DataFrame, "eb": DataFrame}
        데이터가 없는 유형은 빈 DataFrame
    """
    targets = _fetch_report_xmls(stock_code)
    if not targets:
        return {"cb": pd.DataFrame(), "bw": pd.DataFrame(), "eb": pd.DataFrame()}

    results = {}
    for aclass, rename_map, label in [
        ("CB", CB_RENAME, "cb"),
        ("BW", BW_RENAME, "bw"),
        ("EB", EB_RENAME, "eb"),
    ]:
        df = _extract_aclass(targets, aclass, rename_map, stock_code, label, save_csv)
        results[label] = df

    return results


if __name__ == "__main__":
    import sys

    code = sys.argv[1] if len(sys.argv) > 1 else "005930"
    df = get_sub_pis(code)
    if not df.empty:
        print(f"\n{df.head(10).to_string()}")
