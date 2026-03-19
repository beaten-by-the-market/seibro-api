"""
법인정보 로더: DART 웹 + Seibro OpenAPI 데이터를 종목코드로 맵핑하여 제공.

사용법:
    from corp_loader import load_corps
    df = load_corps()                   # 캐시 있으면 캐시 사용
    df = load_corps(refresh=True)       # 강제 새로고침
"""

import os
import time
import requests
import pandas as pd
from io import BytesIO
from time import sleep
from datetime import datetime
from tqdm import tqdm
from .client import SeibroClient
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CACHE_FILE = os.path.join(os.getcwd(), "corp_master.pkl")

DART_CORP_TYPES = {
    "P": "유가",
    "A": "코스닥",
    "N": "코넥스",
    "E": "기타",
}

SEIBRO_MARKETS = ["유가", "코스닥", "K-OTC", "코넥스"]


def _fetch_dart():
    """DART 기업개황 엑셀 다운로드 (시장유형별 4회 호출)"""
    url = "https://dart.fss.or.kr/dsae001/downloadExcel.do"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "Referer": "https://dart.fss.or.kr/dsae001/main.do",
    }
    params_base = {
        "currentPage": 1, "maxResults": "", "maxLinks": "", "sort": "",
        "series": "", "gubun": "", "selectKey": "", "searchIndex": "",
        "textCrpCik": "", "autoSearch": "true", "businessCode": "all",
        "bsnRgsNo": "", "textCrpNm": "", "bsnRgsNo_1": "", "bsnRgsNo_2": "",
        "bsnRgsNo_3": "", "crpRgsNo": "",
    }

    dfs = []
    for code, name in tqdm(DART_CORP_TYPES.items(), desc="DART 수집"):
        params = {**params_base, "corporationType": code}
        resp = requests.get(url, params=params, headers=headers, verify=False, timeout=60)
        resp.raise_for_status()
        df = pd.read_excel(BytesIO(resp.content))
        df["시장구분"] = name
        print(f"  [DART-{name}] {len(df)}건")
        dfs.append(df)
        sleep(1)

    result = pd.concat(dfs, ignore_index=True)
    print(f"  DART 합계: {len(result)}건")
    return result


def _fetch_seibro():
    """Seibro OpenAPI 종목 명부 (시장별 호출, 예탁원 고객번호 포함)"""
    client = SeibroClient()
    df = client.get_stock_registry(SEIBRO_MARKETS)
    print(f"  Seibro 합계: {len(df)}건")
    return df


def _merge(dart_df, seibro_df):
    """종목코드 기준으로 Seibro + DART outer join"""
    # DART: 종목코드를 6자리 문자열로 정규화
    dart_df["종목코드"] = dart_df["종목코드"].astype(str).str.strip().str.zfill(6)

    # Seibro: SHOTN_ISIN을 6자리 문자열로 정규화
    seibro_df["SHOTN_ISIN"] = seibro_df["SHOTN_ISIN"].astype(str).str.strip().str.zfill(6)

    # Seibro 중복 제거
    seibro_unique = seibro_df.drop_duplicates(subset="SHOTN_ISIN")

    # 상장사 DART 데이터
    listed = dart_df[dart_df["시장구분"].isin(["유가", "코스닥", "코넥스"])].copy()
    unlisted = dart_df[~dart_df["시장구분"].isin(["유가", "코스닥", "코넥스"])].copy()

    # outer join: Seibro에만 있는 종목도 포함
    merged = seibro_unique.merge(
        listed,
        left_on="SHOTN_ISIN",
        right_on="종목코드",
        how="outer",
    )
    # 종목코드 통합 (양쪽 중 있는 값 사용)
    merged["종목코드"] = merged["종목코드"].fillna(merged["SHOTN_ISIN"])
    merged.drop(columns=["SHOTN_ISIN"], inplace=True)

    # 비상장(기타)은 Seibro 정보 없이 합치기
    result = pd.concat([merged, unlisted], ignore_index=True)

    # 맵핑 통계
    both = merged["ISSUCO_CUSTNO"].notna() & merged["회사이름"].notna()
    dart_only = merged["ISSUCO_CUSTNO"].isna() & merged["회사이름"].notna()
    seibro_only = merged["ISSUCO_CUSTNO"].notna() & merged["회사이름"].isna()
    print(f"\n맵핑 결과:")
    print(f"  양쪽 매칭: {both.sum()}건")
    print(f"  DART에만: {dart_only.sum()}건")
    print(f"  Seibro에만: {seibro_only.sum()}건")
    print(f"  비상장(기타): {len(unlisted)}건")

    return result


def load_corps(refresh=False):
    """
    법인 마스터 데이터를 로드.
    캐시(corp_master.pkl)가 당일자면 재사용, 아니면 새로 수집.

    Args:
        refresh: True면 캐시 무시하고 새로 수집
    Returns:
        DataFrame: DART 기업개황 + Seibro 예탁원고객번호 맵핑 데이터
    """
    today = datetime.now().strftime("%Y%m%d")

    # 캐시 확인
    if not refresh and os.path.exists(CACHE_FILE):
        mtime = datetime.fromtimestamp(os.path.getmtime(CACHE_FILE)).strftime("%Y%m%d")
        if mtime == today:
            df = pd.read_pickle(CACHE_FILE)
            print(f"캐시 로드: {len(df)}건 ({CACHE_FILE})")
            return df

    # 수집
    total_start = time.time()
    print("=" * 50)
    print("법인 마스터 데이터 수집 시작")
    print("=" * 50)

    print("\n[1/3] DART 기업개황 수집")
    t0 = time.time()
    dart_df = _fetch_dart()
    print(f"  → {time.time() - t0:.1f}초 소요")

    print("\n[2/3] Seibro 종목 명부 수집")
    t0 = time.time()
    seibro_df = _fetch_seibro()
    print(f"  → {time.time() - t0:.1f}초 소요")

    print("\n[3/3] 데이터 맵핑 및 저장")
    t0 = time.time()
    result = _merge(dart_df, seibro_df)

    # 캐시 저장
    result.to_pickle(CACHE_FILE)
    csv_path = os.path.join(os.getcwd(), "corp_master.csv")
    result.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"  → {time.time() - t0:.1f}초 소요")

    print(f"\n{'=' * 50}")
    print(f"완료: {len(result)}건 저장 (총 {time.time() - total_start:.1f}초)")
    print(f"  → corp_master.pkl / corp_master.csv")
    print(f"{'=' * 50}")

    return result


if __name__ == "__main__":
    df = load_corps(refresh=True)
    print("\n" + "=" * 50)
    print(f"전체: {len(df)}건")
    print(f"\n시장별 건수:")
    print(df.groupby("시장구분").size())
    print(f"\n컬럼: {list(df.columns)}")

    # 상장사 맵핑 확인
    cols = df.columns.tolist()
    listed = df[df[cols[-1]].isin(["유가", "코스닥", "코넥스"])]
    print(f"\n상장사 중 Seibro 매칭: {listed['ISSUCO_CUSTNO'].notna().sum()}/{len(listed)}")
    print(listed[[cols[2], cols[3], "ISSUCO_CUSTNO", cols[-1]]].head(10))
