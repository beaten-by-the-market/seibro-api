import os
import requests
import pandas as pd
from time import sleep
from typing import Union
from xml_to_dict import XMLtoDict
from dotenv import load_dotenv

import warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')


class SeibroAPIError(RuntimeError):
    """Seibro Open API가 정상 vector 응답을 주지 않은 경우.

    필수 파라미터 누락 시 서버는 `<SeibroAPI><RES .../></SeibroAPI>` 만 돌려준다.
    재시도해도 결과가 달라지지 않으므로 즉시 올린다.
    """


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
                api_root = data_dict.get("SeibroAPI") or {}
                if "vector" not in api_root:
                    raise SeibroAPIError(
                        f"[{api_id}] 응답에 vector가 없습니다. 필수 파라미터 누락 가능성: {params}"
                    )
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

            except SeibroAPIError:
                raise

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

    def get_issuco_custno(self, stock_code: str = None, isin: str = None) -> dict:
        """종목코드 → 발행회사고객번호 조회.

        Seibro API ID: getIssucoCustnoByIsin

        Args:
            stock_code: 단축종목코드(SHOTN_ISIN). 예: "005930"
            isin: 표준종목코드(ISIN). 예: "KR7005930003"

        Returns:
            {"issuco_custno": "593", "rep_secn_nm": "삼성전자"}

        Raises:
            ValueError: 입력이 없거나, 조회 결과가 없거나, 2건 이상인 경우.

        Note:
            존재하지 않는 코드를 넣으면 서버가 **빈 결과가 아니라 엉뚱한 회사 여러
            건**을 돌려주기도 한다(실측: "000000" → 에어로시스템·서울창업투자).
            유효한 코드는 항상 1건이므로, 1건이 아니면 실패로 처리한다.
        """
        params = {}
        if stock_code:
            params["SHOTN_ISIN"] = str(stock_code).strip().zfill(6)
        if isin:
            params["ISIN"] = str(isin).strip()
        if not params:
            raise ValueError("stock_code 또는 isin 중 하나가 필요합니다.")

        df = self._call_api("getIssucoCustnoByIsin", params)
        if df.empty:
            raise ValueError(
                f"고객번호를 찾지 못했습니다: {params}. "
                "상장폐지·비상장 종목일 수 있습니다. issuco_custno를 직접 입력해 보세요."
            )
        if len(df) > 1:
            candidates = df.to_dict("records")
            raise ValueError(
                f"종목코드가 유일하게 매칭되지 않습니다: {params} → {len(df)}건 {candidates}. "
                "존재하지 않는 코드일 가능성이 큽니다. issuco_custno를 직접 입력하세요."
            )
        row = df.iloc[0]
        return {
            "issuco_custno": str(row.get("ISSUCO_CUSTNO", "")).strip(),
            "rep_secn_nm": str(row.get("REP_SECN_NM", "")).strip(),
        }

    def get_dividend_schedules(
        self,
        issuco_custno: Union[str, int] = None,
        begin_dt: Union[str, int] = None,
        end_dt: Union[str, int] = None,
        detail_sort_cd: str = None,
    ) -> pd.DataFrame:
        """배당일정 정보 조회 (회사×권리기준일 단위, 금액 없음).

        Seibro API ID: getDivSchedulInfo

        서버 제약 (실측):
          - `issuco_custno`가 없으면 `end_dt`가 **무시되고 begin_dt 하루치**만 반환된다.
          - `issuco_custno`가 있으면 begin_dt로부터 **3년**까지만 반환된다.
            3년을 넘겨 요청해도 에러 없이 조용히 잘리므로, 장기 조회는
            `dividend_history.get_dividend_history()`처럼 구간을 쪼개 호출해야 한다.

        Args:
            issuco_custno: 발행회사고객번호. None이면 전체 회사(하루치).
            begin_dt: 시작 권리기준일 YYYYMMDD (필수).
            end_dt: 종료 권리기준일 YYYYMMDD.
            detail_sort_cd: 권리사유세부유형코드.
                            01 주식배당 / 02 현금배당 / 03 동시배당 / 04 무배당.

        Returns:
            DataFrame (Seibro 원천 칼럼). 주요 칼럼:
            ISSUCO_CUSTNO, REP_SECN_NM, RGT_RACD, RGT_RSN_DTAIL_SORT_CD, RGT_STD_DT,
            ALOC_WHCD, SETACC_TPCD, FIX_TPCD, ROST_CLOSE_BEGIN_DT, ROST_CLOSE_EXPRY_DT,
            XRGT_DT, ELTSC_YN
        """
        if not begin_dt:
            raise ValueError("begin_dt(YYYYMMDD)는 필수입니다.")

        params = {}
        if issuco_custno is not None:
            params["ISSUCO_CUSTNO"] = str(issuco_custno).strip()
        params["BEGIN_STD_DT"] = str(begin_dt).strip()
        if end_dt:
            params["EXPRY_STD_DT"] = str(end_dt).strip()
        if detail_sort_cd:
            params["RGT_RSN_DTAIL_SORT_CD"] = str(detail_sort_cd).strip()

        return self._call_api("getDivSchedulInfo", params)

    def get_dividend_payouts(
        self,
        issuco_custno: Union[str, int],
        begin_dt: Union[str, int],
        end_dt: Union[str, int] = None,
    ) -> pd.DataFrame:
        """배당분배금내역 조회 (종목×권리기준일 단위, 금액 포함).

        Seibro API ID: getDivInfo

        서버 제약 (실측): begin_dt로부터 **3년**까지만 반환된다. 더 긴 구간을
        요청해도 에러 없이 조용히 잘린다. `issuco_custno`는 필수라 전체 조회는 불가.

        Args:
            issuco_custno: 발행회사고객번호 (필수).
            begin_dt: 시작 권리기준일 YYYYMMDD (필수).
            end_dt: 종료 권리기준일 YYYYMMDD. 미입력 시 begin_dt 하루치.

        Returns:
            DataFrame (Seibro 원천 칼럼). 주요 칼럼:
            ISIN, KOR_SECN_NM, SECN_KACD_NM, RGT_STD_DT, PVAL, STK_ALOC_RATIO,
            CASH_ALOC_RATIO, CASH_ALOC_AMT, MARTP_DIV_RATE, TH1_PAY_TERM_BEGIN_DT,
            DELI_DT, MAJSHR_ETC_DIFF_ALOC_YN, TSTK_NOAGN_YN, CASH_DIFF_DIVIAMT_VAL,
            CASH_DIFF_DIVI_RATE, STK_DIFF_DIVI_RATE, MARTP_DIFF_DIVI_RATE

            출력에 ISSUCO_CUSTNO가 없으므로, 일정 정보와 조인하려면 요청에 쓴
            고객번호를 호출자가 직접 붙여야 한다.
        """
        if issuco_custno is None:
            raise ValueError("issuco_custno는 필수입니다.")
        if not begin_dt:
            raise ValueError("begin_dt(YYYYMMDD)는 필수입니다.")

        params = {
            "ISSUCO_CUSTNO": str(issuco_custno).strip(),
            "BEGIN_STD_DT": str(begin_dt).strip(),
        }
        if end_dt:
            params["EXPRY_STD_DT"] = str(end_dt).strip()

        return self._call_api("getDivInfo", params)
