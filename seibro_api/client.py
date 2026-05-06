import os
import requests
import pandas as pd
from time import sleep
from typing import Union
from xml_to_dict import XMLtoDict
from dotenv import load_dotenv

import warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')


class SeibroClient:
    """Seibro Open API 클라이언트"""

    BASE_URL = "http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp"

    # 시장구분 코드
    MARKET_CODES = {
        "유가": "11",
        "코스닥": "12",
        "K-OTC": "13",
        "코넥스": "14",
        "기타": "50",
    }

    def __init__(self, api_key: str = None):
        if api_key:
            self.api_key = api_key
        else:
            load_dotenv()
            self.api_key = os.getenv("SEIBRO_API_KEY")
            if not self.api_key:
                raise ValueError("SEIBRO_API_KEY가 .env 파일이나 환경변수에 없습니다.")
        self._xd = XMLtoDict()

    def _call_api(self, api_id: str, params: dict, max_retries: int = 3) -> pd.DataFrame:
        """Seibro API 공통 호출 메서드

        네트워크 에러, 타임아웃, 파싱 실패 시 max_retries 횟수만큼 재시도.
        재시도 간격은 점진적으로 증가 (1초, 2초, 3초...).
        """
        params_str = ",".join(f"{k}:{v}" for k, v in params.items())
        url = f"{self.BASE_URL}?key={self.api_key}&apiId={api_id}&params={params_str}"

        for attempt in range(max_retries):
            try:
                raw = requests.get(url, verify=False, timeout=30)
                raw.raise_for_status()
                data_dict = self._xd.parse(raw.content.decode("utf-8"))
                result = data_dict["SeibroAPI"]["vector"]["@result"]

                if result == "0":
                    return pd.DataFrame()
                elif result == "1":
                    data_list = data_dict["SeibroAPI"]["vector"]["data"]
                    result_data = data_list["result"]
                    record = {k: v["@value"] for k, v in result_data.items()}
                    return pd.DataFrame([record])
                else:
                    data_list = data_dict["SeibroAPI"]["vector"]["data"]
                    records = [
                        {k: v["@value"] for k, v in item["result"].items()}
                        for item in data_list
                    ]
                    return pd.DataFrame(records)

            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.HTTPError) as e:
                wait = (attempt + 1) * 2
                if attempt < max_retries - 1:
                    print(f"  [{api_id}] 네트워크 에러 (시도 {attempt+1}/{max_retries}): {e}")
                    print(f"  → {wait}초 후 재시도...")
                    sleep(wait)
                else:
                    print(f"  [{api_id}] 네트워크 에러로 {max_retries}회 모두 실패: {e}")
                    raise

            except Exception as e:
                wait = (attempt + 1) * 2
                if attempt < max_retries - 1:
                    print(f"  [{api_id}] 시도 {attempt+1}/{max_retries} 실패: {e}")
                    print(f"  → {wait}초 후 재시도...")
                    sleep(wait)
                else:
                    print(f"  [{api_id}] {max_retries}회 모두 실패: {e}")
                    raise

    def get_stock_registry(self, markets: list[str] = None) -> pd.DataFrame:
        """전체 상장종목 명부 조회 (종목코드 + 종목명 + 예탁원 고객번호)

        Args:
            markets: 조회할 시장 목록. 기본값은 ["유가", "코스닥"]
                     사용 가능: "유가", "코스닥", "K-OTC", "코넥스", "기타"

        Returns:
            DataFrame with columns: SHOTN_ISIN, KOR_SECN_NM, ISSUCO_CUSTNO, MART_TPCD, MART_NM
        """
        if markets is None:
            markets = ["유가", "코스닥"]

        dfs = []
        failed = []

        for mkt_name in markets:
            mkt_code = self.MARKET_CODES.get(mkt_name)
            if not mkt_code:
                print(f"알 수 없는 시장명: {mkt_name} (사용 가능: {list(self.MARKET_CODES.keys())})")
                continue

            print(f"  [{mkt_name}({mkt_code})] 종목 데이터 수집 중...")
            sleep(1)
            try:
                df = self._call_api("getShotnByMart", {"MART_TPCD": mkt_code})
            except Exception:
                failed.append(mkt_name)
                continue

            if not df.empty:
                df["MART_TPCD"] = mkt_code
                df["MART_NM"] = mkt_name
                dfs.append(df)
                print(f"  [{mkt_name}] {len(df)}개 종목 수집 완료")
            else:
                print(f"  [{mkt_name}] 데이터 없음")

        if failed:
            print(f"\n실패한 시장 재시도 중: {failed}")
            sleep(5)
            for mkt_name in failed:
                mkt_code = self.MARKET_CODES[mkt_name]
                print(f"  [{mkt_name}] 재시도...")
                try:
                    df = self._call_api("getShotnByMart", {"MART_TPCD": mkt_code})
                    if not df.empty:
                        df["MART_TPCD"] = mkt_code
                        df["MART_NM"] = mkt_name
                        dfs.append(df)
                        print(f"  [{mkt_name}] 재시도 성공: {len(df)}개 종목")
                    else:
                        print(f"  [{mkt_name}] 재시도 성공했으나 데이터 없음")
                except Exception as e:
                    print(f"  [{mkt_name}] 재시도도 실패: {e}")

        if not dfs:
            return pd.DataFrame()

        result = pd.concat(dfs, ignore_index=True)
        print(f"\n총 {len(result)}개 종목 수집 완료")
        return result

    def get_stock_issue_details(
        self,
        stock_code: str = None,
        isin: str = None,
        issuco_custno: Union[str, int] = None,
        issue_year: Union[str, int] = None,
    ) -> pd.DataFrame:
        """주식수량 변동내역 조회.

        Seibro API ID: getStkIncdceDetails

        Args:
            stock_code: 단축코드(SHOTN_ISIN). 예: "005930"
            isin: 표준코드(ISIN). 예: "KR7005930003"
            issuco_custno: 발행회사고객번호(ISSUCO_CUSTNO).
            issue_year: 발행연도(ISSU_YEAR). 예: 2018

        Returns:
            DataFrame with Seibro 원천 칼럼.
        """
        params = {}

        if stock_code:
            params["SHOTN_ISIN"] = str(stock_code).strip().zfill(6)
        if isin:
            params["ISIN"] = str(isin).strip()
        if issuco_custno is not None:
            params["ISSUCO_CUSTNO"] = str(issuco_custno).strip()
        if issue_year is not None:
            params["ISSU_YEAR"] = str(issue_year).strip()

        if not any(k in params for k in ("SHOTN_ISIN", "ISIN", "ISSUCO_CUSTNO")):
            raise ValueError("stock_code, isin, issuco_custno 중 하나 이상이 필요합니다.")

        return self._call_api("getStkIncdceDetails", params)
