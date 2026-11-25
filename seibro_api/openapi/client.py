import os
import requests
import pandas as pd
from time import sleep
from typing import Union
from xml_to_dict import XMLtoDict
from dotenv import load_dotenv

from urllib.parse import quote, quote_plus


class SeibroAPIError(RuntimeError):
    """Seibro Open API가 정상 vector 응답을 주지 않은 경우.

    필수 파라미터 누락 시 서버는 `<SeibroAPI><RES .../></SeibroAPI>` 만 돌려준다.
    재시도해도 결과가 달라지지 않으므로 즉시 올린다.
    """


class _TransientAPIError(RuntimeError):
    """서버가 header/error(code 003 등)로 일시 오류를 알린 경우. _call_api 안에서 재시도한다."""


def retry_transient(fn, *args, tries: int = 3, **kwargs):
    """SeibroAPIError가 나면 잠깐 쉬고 다시 부른다.

    서버 일시 오류(header error 003)는 _call_api가 이미 재시도한다. 이 함수는 그래도 실패했거나
    원인 표시 없이 vector가 빠진 응답이 왔을 때 한 번 더 감싸는 바깥 재시도다.
    서버가 validErrorMsg로 이유를 밝힌 오류("서버 오류")는 다시 불러도 같으므로 바로 올린다.
    """
    for attempt in range(tries):
        try:
            return fn(*args, **kwargs)
        except SeibroAPIError as e:
            if "서버 오류" in str(e) or attempt == tries - 1:
                raise
            sleep(1 + attempt)


class SeibroClient:
    """Seibro Open API 클라이언트"""

    BASE_URL = "https://seibro.or.kr/OpenPlatform/callOpenAPI.jsp"

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

    def _redact(self, text: object) -> str:
        """메시지에서 API 키를 가린다. Open API는 키를 URL 쿼리에 넣기 때문에
        requests 예외 메시지(…?key=…)에 키가 그대로 들어간다."""
        text = str(text)
        for key in {self.api_key, quote(self.api_key, safe=""), quote_plus(self.api_key)}:
            text = text.replace(key, "***")
        return text

    def _call_api(self, api_id: str, params: dict, max_retries: int = 3) -> pd.DataFrame:
        """Seibro API 공통 호출 메서드

        네트워크 에러, 타임아웃, 파싱 실패 시 max_retries 횟수만큼 재시도.
        재시도 간격은 점진적으로 증가 (1초, 2초, 3초...).

        출력·예외 메시지에는 키를 넣지 않는다. 최종 실패는 원래 예외 대신
        키를 가린 SeibroAPIError로 올린다(원래 예외는 URL을 담고 있어 체인도 끊는다).
        """
        params_str = ",".join(f"{k}:{v}" for k, v in params.items())
        query = {"key": self.api_key, "apiId": api_id, "params": params_str}

        for attempt in range(max_retries):
            try:
                raw = requests.get(self.BASE_URL, params=query, timeout=30, allow_redirects=False)
                if 300 <= raw.status_code < 400:
                    raise SeibroAPIError(f"[{api_id}] ???? ?? API ????")
                raw.raise_for_status()
                data_dict = self._xd.parse(raw.content.decode("utf-8"))
                api_root = data_dict.get("SeibroAPI") or {}
                if "vector" not in api_root:
                    # 일시 오류: <header><error><code value="003"/><content value="서비스 호출 중
                    # 오류가 발생하였습니다."/></error></header> (실측 약 8%, 같은 요청 재시도로 회복)
                    header = api_root.get("header") if isinstance(api_root, dict) else None
                    herr = header.get("error") if isinstance(header, dict) else None
                    if isinstance(herr, dict):
                        code = (herr.get("code") or {}).get("@value", "")
                        content = (herr.get("content") or {}).get("@value", "")
                        raise _TransientAPIError(f"서버 일시 오류 {code} {content}")
                    res = api_root.get("RES") if isinstance(api_root, dict) else None
                    err = (res or {}).get("validErrorMsg") if isinstance(res, dict) else None
                    server_msg = err.get("@value") if isinstance(err, dict) else None
                    if server_msg:
                        raise SeibroAPIError(f"[{api_id}] 서버 오류: {server_msg} {params}")
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
                msg = self._redact(e)
                if attempt < max_retries - 1:
                    print(f"  [{api_id}] 네트워크 에러 (시도 {attempt+1}/{max_retries}): {msg}")
                    print(f"  → {wait}초 후 재시도...")
                    sleep(wait)
                else:
                    print(f"  [{api_id}] 네트워크 에러로 {max_retries}회 모두 실패: {msg}")
                    raise SeibroAPIError(f"[{api_id}] 네트워크 에러: {msg}") from None

            except Exception as e:
                wait = (attempt + 1) * 2
                msg = self._redact(e)
                if attempt < max_retries - 1:
                    if not isinstance(e, _TransientAPIError):  # 흔한 일시 오류는 조용히 재시도
                        print(f"  [{api_id}] 시도 {attempt+1}/{max_retries} 실패: {msg}")
                        print(f"  → {wait}초 후 재시도...")
                    sleep(wait)
                else:
                    print(f"  [{api_id}] {max_retries}회 모두 실패: {msg}")
                    raise SeibroAPIError(f"[{api_id}] 호출 실패: {msg}") from None

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

        Seibro API ID: getStkIncdecDetails

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

        return self._call_api("getStkIncdecDetails", params)

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

    # ── 주식·채권 기본 조회 (원천 칼럼 그대로) ──────────────────────

    def get_stock_info(self, stock_code: str = None, isin: str = None) -> pd.DataFrame:
        """종목 기본정보 조회.

        Seibro API ID: getStkStatInfo

        Returns:
            DataFrame (Seibro 원천 칼럼). 주요 칼럼: ISSUCO_CUSTNO, KOR_SECN_NM, ISIN,
            SHOTN_ISIN, PVAL, SECN_KACD, TOTAL_STK_CNT(현재 발행주식총수 — 발행됐지만
            아직 상장되지 않은 주식도 포함), ELTSC_YN
        """
        params = {}
        if stock_code:
            params["SHOTN_ISIN"] = str(stock_code).strip().zfill(6)
        if isin:
            params["ISIN"] = str(isin).strip()
        if not params:
            raise ValueError("stock_code 또는 isin 중 하나가 필요합니다.")
        return self._call_api("getStkStatInfo", params)

    def get_rights_record_dates(self, issuco_custno: Union[str, int], start_dt: str, end_dt: str) -> pd.DataFrame:
        """권리기준일 목록(getStddtInfo). 날짜는 YYYYMMDD이며 한 호출은 최대 3년을 반환한다."""
        return self._call_api("getStddtInfo", {
            "ISSUCO_CUSTNO": issuco_custno,
            "BEGIN_STD_DT": start_dt,
            "EXPRY_STD_DT": end_dt,
        })

    def get_meeting_details(self, issuco_custno: Union[str, int], record_dt: str) -> pd.DataFrame:
        """고객번호·권리기준일로 주총 개최 정보 조회(getGmeetInfo)."""
        return self._call_api("getGmeetInfo", {"ISSUCO_CUSTNO": issuco_custno, "RGT_STD_DT": record_dt})

    def get_meeting_agendas(self, issuco_custno: Union[str, int], record_dt: str) -> pd.DataFrame:
        """고객번호·권리기준일로 주총 안건 조회(getGmeetMeasureInfo)."""
        return self._call_api("getGmeetMeasureInfo", {"ISSUCO_CUSTNO": issuco_custno, "RGT_STD_DT": record_dt})

    def get_bond_issues(
        self,
        issue_dt: Union[str, int] = None,
        issuco_custno: Union[str, int] = None,
    ) -> pd.DataFrame:
        """채권 발행 목록 조회 (발행일 하루치 또는 발행회사별).

        Seibro API ID: getBondIssuInfo

        서버 동작 (실측, 2026-11):
          - ISSU_DT만 주면 그날 발행된 회사채(일반·P-CBO·CB·BW·EB 등) 목록.
            2026년 10월 한 달 322건. 당일분은 다음 날에야 잡히기도 한다.
          - ISSUCO_CUSTNO만 주면 그 회사의 발행 채권 목록.
          - 둘을 같이 주면 빈 결과가 온다. 기간(from~to) 파라미터는 없다.

        Returns:
            DataFrame: ISSU_DT, ISSUCO_CUSTNO, ISSUCO_CUST_NM, ISIN, KOR_SECN_NM
        """
        params = {}
        if issue_dt:
            params["ISSU_DT"] = str(issue_dt).strip().replace("-", "")
        if issuco_custno is not None:
            params["ISSUCO_CUSTNO"] = str(issuco_custno).strip()
        if not params:
            raise ValueError("issue_dt 또는 issuco_custno 중 하나가 필요합니다.")
        return self._call_api("getBondIssuInfo", params)

    def get_bond_detail(self, isin: str) -> pd.DataFrame:
        """채권 종목 상세(발행금액·미상환잔액·표면이자율·만기·옵션·신용등급 코드 등).

        Seibro API ID: getBondStatInfo

        일부 BW(예: 신종 비분리형 BW)는 서버가 vector 없는 응답을 줘서 SeibroAPIError가
        난다. 그럴 땐 `stock_linked.get_bond_web_info()`(웹 화면 호출)로 대신 받을 수 있다.
        """
        return self._call_api("getBondStatInfo", {"ISIN": str(isin).strip()})

    def get_bond_redemptions(self, isin: str) -> pd.DataFrame:
        """채권 표준코드별 상환 옵션 행사 내역(getBondOptionXrcInfo)."""
        isin = str(isin).strip().upper()
        if len(isin) != 12 or not isin.isascii() or not isin.isalnum():
            raise ValueError("채권 표준코드는 영문과 숫자를 합쳐 12자리입니다.")
        return self._call_api("getBondOptionXrcInfo", {"ISIN": isin})

    def get_stock_linked_bonds(self, stock_isin: str) -> pd.DataFrame:
        """주식(행사대상) 표준코드 → 연결된 주식관련사채(CB/BW/EB) 목록.

        Seibro API ID: getXrcStkStatInfo

        Returns:
            DataFrame: BOND_ISIN, BOND_SECN_NM, BOND_KIND_NM(CB/비분리형BW/분리형BW/EB),
            XRC_STK_ISIN, STK_SECN_NM, WRTB_ISIN, XRC_RATIO, XRC_PRICE, ...
        """
        return self._call_api("getXrcStkStatInfo", {"XRC_STK_ISIN": str(stock_isin).strip()})

    def get_bond_exercises(self, bond_isin: str) -> pd.DataFrame:
        """주식관련사채 권리행사(전환·신주인수권 행사·교환) 내역.

        Seibro API ID: getXrcStkOptionXrcInfo

        Returns:
            DataFrame: 행사 1건당 1행. BOND_ISIN, BOND_KOR_SECN_NM, BOND_KIND_NM,
            XRC_STK_ISIN, RGT_STD_DT(행사일), XRC_POSS_BEGIN_DT/XRC_POSS_EXPRY_DT(행사기간),
            XRC_AMT(행사금액), XRC_QTY(행사주식수), XRC_PRICE(당시 행사가), LIST_DT(신주 상장일)
            행사가 한 번도 없으면 빈 DataFrame.
        """
        return self._call_api("getXrcStkOptionXrcInfo", {"BOND_ISIN": str(bond_isin).strip()})

    def get_lockup_status(
        self,
        begin_dt: Union[str, int],
        end_dt: Union[str, int],
        biz_tpcd: Union[str, int] = 1,
        issuco_custno: Union[str, int] = None,
    ) -> pd.DataFrame:
        """의무보호예수(의무보유) 예수·반환 현황.

        Seibro API ID: getSafeDpDutyDepoStatus

        서버 제약 (실측, 2026-11):
          - 조회기간은 1년(양 끝 포함 365일) 이하. 넘으면 "조회기간은 1년을 초과 할 수
            없습니다." 오류. 긴 기간은 `lockup.get_lockup_records()`처럼 나눠 부른다.
          - biz_tpcd=1(예수): SAFEDP_DT(예수일)가 기간 안인 예수 건.
            biz_tpcd=2(반환): RETURN_DT(반환일)가 기간 안인 반환 건. 반환 행에도 원래
            예수일(SAFEDP_DT)과 사유코드가 있어 예수 건과 맞춰 볼 수 있다.
          - issuco_custno를 빼면 전 종목.

        Returns:
            DataFrame: ISSUCO_CUSTNO, KOR_SECN_NM, SECN_KACD, SHOTN_ISIN, MART_TPCD,
            OCCR_SEQ(1 예수/2 반환), SAFEDP_DT, SAFEDP_QTY, DUTY_SAFEDP_RACD(사유코드),
            RETURN_DT, RETURN_QTY, TOTAL_STK_CNT(현재 발행주식총수. 예수 당시 값이 아니다)
        """
        params = {}
        if issuco_custno is not None:
            params["ISSUCO_CUSTNO"] = str(issuco_custno).strip()
        params["BEGIN_DT"] = str(begin_dt).strip().replace("-", "")
        params["EXPRY_DT"] = str(end_dt).strip().replace("-", "")
        params["BIZ_TPCD"] = str(biz_tpcd).strip()
        return self._call_api("getSafeDpDutyDepoStatus", params)
