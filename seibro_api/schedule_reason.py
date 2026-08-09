"""Schedule reason records from SEIBro WebSquare calls."""

from __future__ import annotations

from datetime import date, datetime
from time import sleep
from typing import Iterable, NamedTuple
from xml.etree import ElementTree

import pandas as pd
import requests

from .client import SeibroClient


WEB_CALL_URL = "https://seibro.or.kr/websquare/engine/proworks/callServletService.jsp"
TASK = "ksd.safe.bip.cnts.Company.process.EntrSkedulPTask"
DEFAULT_MENU_NO = "21"
DEFAULT_REPM_DT = "19990514"

# 기간별 주요일정(BIP_CNTS01021V) — 회사 하나의 기간 내 모든 권리일정을 한 번에 조회
TERM_SCHEDULE_W2X = "/IPORTAL/user/company/BIP_CNTS01021V.xml"
TERM_SCHEDULE_MENU_NO = "274"
TERM_SCHEDULE_ACTION = "termByImptSkedulList"

# 기간별 주요일정 응답 태그 -> 한글 칼럼명
TERM_SCHEDULE_RENAME = {
    "DT_BEGIN_DT": "일정일자",
    "DT_TPNM": "일정종류",
    "RGT_RANM": "사유",
    "RGT_RACD_NM_DETAIL": "사유상세",
    "RGT_RACD": "사유코드",
    "RGT_STD_DT": "기준일",
    "DT_EXPRY_DT": "일정종료일",
    "STD_DT": "표시일자",
    "LIST_TPNM": "시장",
    "AG_ORG_TPNM": "명의개서대리인",
    "ROST_CLOSE_BEGIN_DT": "명부폐쇄시작",
    "ROST_CLOSE_EXPRY_DT": "명부폐쇄종료",
    "ISSUCO_NM": "회사명",
    "DT_TPCD": "일정종류코드",
}
TERM_SCHEDULE_DISPLAY_ORDER = [
    "종목코드", "회사명", "일정일자", "일정종류", "사유", "사유상세",
    "사유코드", "기준일", "일정종료일", "표시일자", "시장",
    "명부폐쇄시작", "명부폐쇄종료", "명의개서대리인",
]

# 대금지급일정(BIP_CNTS01022V) — 회사의 대금(배당금 등) 지급 예정 목록
COST_PAYMENT_W2X = "/IPORTAL/user/company/BIP_CNTS01022V.xml"
COST_PAYMENT_MENU_NO = "20"
COST_PAYMENT_ACTION = "costPaymentScheduleInfoListEL1"
COST_PAYMENT_COUNT_ACTION = "costPaymentScheduleInfoListCnt"

# 대금종류(PAY_COST_TPCD). 화면 드롭다운 라벨 기준.
PAY_COST_TYPES = {
    "1": "배당금지급일",
    "2": "단주대금지급일",
    "3": "현물배당지급일",
}
_PAY_COST_ALIASES = {
    "배당금": "1", "배당": "1", "배당금지급일": "1", "배당/분배금": "1",
    "단주대금": "2", "단주": "2", "단주대금지급일": "2",
    "현물배당": "3", "현물": "3", "현물배당지급일": "3",
}

COST_PAYMENT_RENAME = {
    "RGT_STD_DT": "기준일",
    "REP_SECN_NM": "종목명",
    "SHOTN_ISIN": "종목코드",
    "SECN_KACD": "종목종류",
    "PAY_COST_TPCD": "대금종류",
    "CALTOT_MART_TPCD": "시장",
    "RGT_RACD": "사유",
    "ISSU_FORM": "발행형태",
}
COST_PAYMENT_DISPLAY_ORDER = [
    "기준일", "종목코드", "종목명", "종목종류", "대금종류", "사유", "시장", "발행형태",
]

SCHEDULE_REASONS = {
    "001": {"name": "정기총회", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01024V.xml"},
    "002": {"name": "임시총회", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01024V.xml"},
    "003": {"name": "종류총회", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01024V.xml"},
    "009": {"name": "기타총회", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01024V.xml"},
    "101": {"name": "유상증자", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01025V.xml"},
    "102": {"name": "무상증자", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01026V.xml"},
    "103": {"name": "배당일정", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01027V.xml"},
    "201": {"name": "액면분할", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01028V.xml"},
    "202": {"name": "액면병합", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01028V.xml"},
    "203": {"name": "사무인수", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01029V.xml"},
    "204": {"name": "상호변경", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01030V.xml"},
    "205": {"name": "자본감소", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01031V.xml"},
    "206": {"name": "합병", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01032V.xml"},
    "207": {"name": "회사분할", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01033V.xml"},
    "208": {"name": "분할합병", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01049V.xml"},
    "210": {"name": "주식교환", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01035V.xml"},
    "211": {"name": "주식이전", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01035V.xml"},
    "301": {"name": "주식전환", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01036V.xml"},
    "302": {"name": "주식상환", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01037V.xml"},
    "900": {"name": "매수청구", "w2x_path": "/IPORTAL/user/company/BIP_CNTS01039V.xml"},
}


class DetailCall(NamedTuple):
    detail_type: str
    action: str
    submission_id: str
    needs_repm_dt: bool = False


BONUS_ISSUE_DETAIL_CALLS = [
    DetailCall("basic", "rissuBasicInfoViewEL1", "submission_rissuBasicInfoViewEL1"),
    DetailCall("pre_issued_stock", "preIssuStkDetailsList1", "submission_preIssuStkDetailsList1", True),
    DetailCall("payment", "payDetailsList", "submission_payDetailsList", True),
    DetailCall("issued_stock", "issuDetailsList1", "submission_issuDetailsList1", True),
]

# 액면분할(201)/액면병합(202): BIP_CNTS01028V. 두 사유가 같은 화면·action을 쓰고
# RGT_RACD로만 구분된다. (submission action명은 화면 XML에서 확인)
FACE_VALUE_SPLIT_MERGE_DETAIL_CALLS = [
    DetailCall("basic", "faceDiviMergBasicInfoListEL1", "submission_faceDiviMergBasicInfoListEL1"),
    DetailCall("pre_issued_stock", "preIssuStkDetailsList3", "submission_preIssuStkDetailsList3", True),
    DetailCall("payment", "payDetailsList2", "submission_payDetailsList2", True),
    DetailCall("issued_stock", "issuDetailsList3", "submission_issuDetailsList3", True),
]

# 자본감소(205): BIP_CNTS01031V.
CAPITAL_REDUCTION_DETAIL_CALLS = [
    DetailCall("basic", "capDecBasicInfoViewEL1", "submission_capDecBasicInfoViewEL1"),
    DetailCall("pre_issued_stock", "preIssuStkDetailsList5", "submission_preIssuStkDetailsList5", True),
    DetailCall("payment", "payDetailsList3", "submission_payDetailsList3", True),
    DetailCall("issued_stock", "issuDetailsList6", "submission_issuDetailsList6", True),
]

# 배당일정(103): BIP_CNTS01027V. 배당내역상세(dividend.py, BIP_CNTS01043V)와는
# 다른 화면 — 이쪽은 기준일별 배당 일정/금액(DPS·시가배당률·지급일)을 준다.
# "dividend"(issuDetailsList2)가 핵심 배당 데이터, "stock_dividend"(knDivDetailsList1)는
# 주식배당(현물)용이라 현금배당 종목에선 보통 비어 있다.
DIVIDEND_SCHEDULE_DETAIL_CALLS = [
    DetailCall("basic", "divSkedulView", "submission_divSkedulView"),
    DetailCall("pre_issued_stock", "preIssuStkDetailsList2", "submission_preIssuStkDetailsList2", True),
    DetailCall("dividend", "issuDetailsList2", "submission_issuDetailsList2", True),
    DetailCall("stock_dividend", "knDivDetailsList1", "submission_knDivDetailsList1", True),
    DetailCall("payment", "payDetailsList1", "submission_payDetailsList1", True),
]

DETAIL_CALLS_BY_REASON = {
    "102": BONUS_ISSUE_DETAIL_CALLS,
    "103": DIVIDEND_SCHEDULE_DETAIL_CALLS,
    "201": FACE_VALUE_SPLIT_MERGE_DETAIL_CALLS,
    "202": FACE_VALUE_SPLIT_MERGE_DETAIL_CALLS,
    "205": CAPITAL_REDUCTION_DETAIL_CALLS,
}


def _yyyymmdd(value: str | date | datetime | None) -> str:
    if value is None:
        return date.today().strftime("%Y%m%d")
    if isinstance(value, datetime):
        return value.strftime("%Y%m%d")
    if isinstance(value, date):
        return value.strftime("%Y%m%d")

    text = str(value).strip().replace("-", "").replace("/", "")
    if len(text) != 8 or not text.isdigit():
        raise ValueError(f"date must be YYYYMMDD, YYYY-MM-DD, YYYY/MM/DD, or date: {value!r}")
    return text


def _xml_escape(value: object) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _parse_records(xml_text: str) -> list[dict[str, str]]:
    root = ElementTree.fromstring(xml_text.strip())
    result_nodes = root.findall(".//data/result")
    if not result_nodes and root.tag == "result":
        result_nodes = [root]

    rows: list[dict[str, str]] = []
    for result in result_nodes:
        row = {child.tag: child.attrib.get("value", "") for child in result}
        if row:
            rows.append(row)
    return rows


def _result_count(xml_text: str) -> int:
    root = ElementTree.fromstring(xml_text.strip())
    raw = root.attrib.get("result")
    if raw and raw.isdigit():
        return int(raw)
    return len(_parse_records(xml_text))


def _reason_info(reason_code: str) -> dict[str, str]:
    code = str(reason_code).strip().zfill(3)
    if code not in SCHEDULE_REASONS:
        raise ValueError(f"unknown schedule reason code: {reason_code!r}")
    return {"code": code, **SCHEDULE_REASONS[code]}


class SeibroWebSquareClient:
    """Small client for recorded SEIBro WebSquare XML POSTs."""

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/xml",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "Content-Type": 'application/xml; charset="UTF-8"',
                "Origin": "https://seibro.or.kr",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131 Safari/537.36"
                ),
            }
        )

    def call(
        self,
        action: str,
        submission_id: str,
        params: dict[str, object],
        w2x_path: str,
        reason_code: str,
    ) -> list[dict[str, str]]:
        payload = self._payload(action, params, w2x_path)
        response = self.session.post(
            WEB_CALL_URL,
            headers={
                "Referer": self._referer(w2x_path, reason_code),
                "submissionid": submission_id,
            },
            data=payload.encode("utf-8"),
            timeout=30,
        )
        response.raise_for_status()
        return _parse_records(response.text)

    def call_with_count(
        self,
        action: str,
        submission_id: str,
        params: dict[str, object],
        w2x_path: str,
        reason_code: str,
    ) -> tuple[list[dict[str, str]], int]:
        payload = self._payload(action, params, w2x_path)
        response = self.session.post(
            WEB_CALL_URL,
            headers={
                "Referer": self._referer(w2x_path, reason_code),
                "submissionid": submission_id,
            },
            data=payload.encode("utf-8"),
            timeout=30,
        )
        response.raise_for_status()
        return _parse_records(response.text), _result_count(response.text)

    def search_company(self, search_string: str) -> list[dict[str, str]]:
        payload = (
            '<reqParam action="searchCompanyContentList" '
            'task="ksd.safe.bip.cmuc.User.process.SearchPTask">'
            '<IS_FF value=""/>'
            f'<search_string value="{_xml_escape(search_string)}"/>'
            "</reqParam>"
        )
        response = self.session.post(
            WEB_CALL_URL,
            headers={
                "Referer": "https://seibro.or.kr/websquare/control.jsp?w2xPath=/IPORTAL/user/etc/BIP_CMUC01024P.xml",
                "submissionid": "P_submission_contentList",
            },
            data=payload.encode("utf-8"),
            timeout=30,
        )
        response.raise_for_status()
        return _parse_records(response.text)

    @staticmethod
    def _payload(action: str, params: dict[str, object], w2x_path: str) -> str:
        fields = [
            f'<MENU_NO value="{DEFAULT_MENU_NO}"/>',
            '<CMM_BTN_ABBR_NM value="total_search,openall,print,hwp,word,pdf,searchIcon,seach,"/>',
            f'<W2XPATH value="{_xml_escape(w2x_path)}"/>',
        ]
        fields.extend(f'<{key} value="{_xml_escape(value)}"/>' for key, value in params.items())
        return f'<reqParam action="{action}" task="{TASK}">{"".join(fields)}</reqParam>'

    @staticmethod
    def _referer(w2x_path: str, reason_code: str) -> str:
        return (
            "https://seibro.or.kr/websquare/control.jsp?"
            f"w2xPath={w2x_path}&menuNo={DEFAULT_MENU_NO}&reason={reason_code}"
        )


def _resolve_stock(
    stock_code: str,
    client: SeibroClient | None,
    web_client: SeibroWebSquareClient,
) -> dict[str, str]:
    code = str(stock_code).strip().zfill(6)

    if client is not None:
        df = client._call_api("getStkStatInfo", {"SHOTN_ISIN": code})
        if not df.empty:
            row = df.iloc[0]
            return {
                "stock_code": code,
                "isin": str(row.get("ISIN", "")),
                "company_name": str(row.get("KOR_SECN_NM", "")),
                "issuco_custno": str(row.get("ISSUCO_CUSTNO", "")),
            }

    rows = web_client.search_company(code)
    exact = [row for row in rows if row.get("SHOTN_ISIN") == code]
    row = exact[0] if exact else (rows[0] if rows else None)
    if not row:
        raise ValueError(f"SEIBro stock not found for stock_code={code}")

    return {
        "stock_code": code,
        "isin": row.get("ISIN", ""),
        "company_name": row.get("REP_SECN_NM", ""),
        "issuco_custno": row.get("ISSUCO_CUSTNO", ""),
    }


def _filter_standard_dates(
    rows: Iterable[dict[str, str]],
    start_dt: str,
    end_dt: str,
) -> list[dict[str, str]]:
    result = []
    for row in rows:
        std_dt = row.get("CODE") or row.get("RGT_STD_DT") or ""
        if start_dt <= std_dt <= end_dt:
            item = dict(row)
            item["RGT_STD_DT"] = std_dt
            result.append(item)
    return result


def _add_common_columns(
    df: pd.DataFrame,
    stock: dict[str, str],
    reason: dict[str, str],
    std_dt: str,
    label: str,
    detail_type: str,
) -> pd.DataFrame:
    df.insert(0, "DETAIL_TYPE", detail_type)
    df.insert(0, "RGT_STD_DT", std_dt)
    df.insert(0, "F_STD_DT", label)
    df.insert(0, "RGT_RACD_NM", reason["name"])
    df.insert(0, "RGT_RACD", reason["code"])
    df.insert(0, "STOCK_CODE", stock["stock_code"])
    df.insert(0, "COMPANY_NAME", stock["company_name"])
    return df


def get_schedule_reason_details(
    stock_code: str,
    reason_code: str = "102",
    start_dt: str | date | datetime = "20110101",
    end_dt: str | date | datetime | None = None,
    client: SeibroClient | None = None,
    web_client: SeibroWebSquareClient | None = None,
    save_csv: bool = True,
    sleep_seconds: float = 0.2,
    include_standard_dates_only: bool = True,
) -> pd.DataFrame:
    """Collect SEIBro schedule reason records by stock code and date range.

    Detailed calls are implemented for the reason codes in
    ``DETAIL_CALLS_BY_REASON``: 102(무상증자), 103(배당일정), 201(액면분할),
    202(액면병합), 205(자본감소). For other reason codes, the function returns
    filtered standard dates when ``include_standard_dates_only`` is true.
    """
    start = _yyyymmdd(start_dt)
    end = _yyyymmdd(end_dt)
    if start > end:
        raise ValueError(f"start_dt must be <= end_dt: {start} > {end}")

    reason = _reason_info(reason_code)
    web_client = web_client or SeibroWebSquareClient()
    if client is None:
        try:
            client = SeibroClient()
        except ValueError:
            client = None

    print(f"\n[Seibro] 사유별 일정내역 수집")
    print(f"  종목코드: {str(stock_code).strip().zfill(6)}")
    print(f"  일정사유: {reason['name']} ({reason['code']})")
    print(f"  기간: {start} ~ {end}")

    stock = _resolve_stock(stock_code, client, web_client)
    issuco_custno = stock["issuco_custno"]
    print(
        "  -> "
        f"{stock['company_name']} "
        f"(ISSUCO_CUSTNO: {issuco_custno}, ISIN: {stock['isin']})"
    )

    common_params = {
        "ISSUCO_CUSTNO": issuco_custno,
        "RGT_RACD": reason["code"],
    }
    std_rows, dropdown_count = web_client.call_with_count(
        "getRgtStdDtByConoList",
        "submission_getRgtStdDtByConoList",
        common_params,
        reason["w2x_path"],
        reason["code"],
    )
    selected_dates = _filter_standard_dates(std_rows, start, end)

    print(f"\n[1/2] 드랍다운 기준일 전체 {dropdown_count}개")
    print(f"      설정 기간 내 기준일 {len(selected_dates)}개")
    for row in selected_dates:
        print(f"      - {row.get('F_STD_DT') or row['RGT_STD_DT']} ({row['RGT_STD_DT']})")

    if not selected_dates:
        print("\n설정 기간 안에 해당 일정사유 기준일이 없습니다.")
        return pd.DataFrame()

    detail_calls = DETAIL_CALLS_BY_REASON.get(reason["code"], [])
    if not detail_calls:
        if not include_standard_dates_only:
            print("\n해당 일정사유는 아직 상세 조회 action이 구현되어 있지 않습니다.")
            return pd.DataFrame()

        df = pd.DataFrame(selected_dates)
        df.insert(0, "DETAIL_TYPE", "standard_date")
        df.insert(0, "RGT_RACD_NM", reason["name"])
        df.insert(0, "RGT_RACD", reason["code"])
        df.insert(0, "STOCK_CODE", stock["stock_code"])
        df.insert(0, "COMPANY_NAME", stock["company_name"])
        print("\n[2/2] 상세 조회 action 미구현: 기준일 목록만 반환")
        print(f"\n수집 완료: 총 {len(df)}건")
        if save_csv:
            filename = f"schedule_reason_{stock['stock_code']}_{reason['code']}_{start}_{end}.csv"
            df.to_csv(filename, index=False, encoding="utf-8-sig")
            print(f"  -> {filename} 저장 완료")
        return df

    frames = []
    errors = []
    print(f"\n[2/2] 기준일별 상세 수집")
    for index, std_row in enumerate(selected_dates, 1):
        std_dt = std_row["RGT_STD_DT"]
        label = std_row.get("F_STD_DT") or std_dt
        print(f"  [{index}/{len(selected_dates)}] {label} 수집 시작")

        for detail_call in detail_calls:
            params = {**common_params, "RGT_STD_DT": std_dt}
            if detail_call.needs_repm_dt:
                params["REPM_DT"] = DEFAULT_REPM_DT

            try:
                rows = web_client.call(
                    detail_call.action,
                    detail_call.submission_id,
                    params,
                    reason["w2x_path"],
                    reason["code"],
                )
            except Exception as exc:
                errors.append(
                    {
                        "RGT_STD_DT": std_dt,
                        "DETAIL_TYPE": detail_call.detail_type,
                        "ERROR": str(exc),
                    }
                )
                print(f"      FAIL {detail_call.detail_type}: {exc}")
                continue

            if rows:
                df = _add_common_columns(
                    pd.DataFrame(rows),
                    stock,
                    reason,
                    std_dt,
                    label,
                    detail_call.detail_type,
                )
                frames.append(df)
                print(f"      OK {detail_call.detail_type}: {len(df)}건")
            else:
                print(f"      empty {detail_call.detail_type}")

        sleep(sleep_seconds)

    result = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if errors:
        result.attrs["errors"] = errors
        print(f"\n주의: {len(errors)}개 상세 호출 실패")

    print(f"\n수집 완료: 총 {len(result)}건")
    if save_csv and not result.empty:
        filename = f"schedule_reason_{stock['stock_code']}_{reason['code']}_{start}_{end}.csv"
        result.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"  -> {filename} 저장 완료")

    return result


def get_bonus_issue_details(
    stock_code: str,
    start_dt: str | date | datetime = "20110101",
    end_dt: str | date | datetime | None = None,
    **kwargs,
) -> pd.DataFrame:
    """Backward-compatible wrapper for bonus issue schedule details."""
    return get_schedule_reason_details(
        stock_code=stock_code,
        reason_code="102",
        start_dt=start_dt,
        end_dt=end_dt,
        **kwargs,
    )


def get_dividend_schedule_details(
    stock_code: str,
    start_dt: str | date | datetime = "20000101",
    end_dt: str | date | datetime | None = None,
    **kwargs,
) -> pd.DataFrame:
    """배당일정(103) 상세내역 조회 wrapper (BIP_CNTS01027V).

    기준일별 배당 일정/금액(DPS·시가배당률·지급개시일 등)을 돌려준다.
    재무성 배당내역상세(dividend.get_dividend_details, BIP_CNTS01043V)와는
    다른 화면이다.
    """
    return get_schedule_reason_details(
        stock_code=stock_code,
        reason_code="103",
        start_dt=start_dt,
        end_dt=end_dt,
        **kwargs,
    )


def get_face_value_split_details(
    stock_code: str,
    start_dt: str | date | datetime = "20000101",
    end_dt: str | date | datetime | None = None,
    **kwargs,
) -> pd.DataFrame:
    """액면분할(201) 상세내역 조회 wrapper (BIP_CNTS01028V)."""
    return get_schedule_reason_details(
        stock_code=stock_code,
        reason_code="201",
        start_dt=start_dt,
        end_dt=end_dt,
        **kwargs,
    )


def get_face_value_merge_details(
    stock_code: str,
    start_dt: str | date | datetime = "20000101",
    end_dt: str | date | datetime | None = None,
    **kwargs,
) -> pd.DataFrame:
    """액면병합(202) 상세내역 조회 wrapper (BIP_CNTS01028V)."""
    return get_schedule_reason_details(
        stock_code=stock_code,
        reason_code="202",
        start_dt=start_dt,
        end_dt=end_dt,
        **kwargs,
    )


def get_capital_reduction_details(
    stock_code: str,
    start_dt: str | date | datetime = "20000101",
    end_dt: str | date | datetime | None = None,
    **kwargs,
) -> pd.DataFrame:
    """자본감소(205) 상세내역 조회 wrapper (BIP_CNTS01031V)."""
    return get_schedule_reason_details(
        stock_code=stock_code,
        reason_code="205",
        start_dt=start_dt,
        end_dt=end_dt,
        **kwargs,
    )


def get_company_schedules(
    stock_code: str,
    start_dt: str | date | datetime = "20000101",
    end_dt: str | date | datetime | None = None,
    reason_code: str = "",
    dt_tpcd: str = "",
    list_tpcd: str = "",
    client: SeibroClient | None = None,
    web_client: SeibroWebSquareClient | None = None,
    save_csv: bool = True,
) -> pd.DataFrame:
    """회사 하나의 기간 내 '기간별 주요일정'을 한 번에 조회 (BIP_CNTS01021V).

    사유별(get_schedule_reason_details)과 달리, 회사(ISSUCO_CUSTNO)를 지정하면
    기간 안의 모든 권리일정(정기총회·배당·권리락일·총회개최일·배당금지급일 등)을
    이벤트 단위로 한 번에 돌려준다. 각 행은 하나의 일정 이벤트다.

    Args:
        stock_code: 단축종목코드 (예: '005930'). 회사(custno)로 변환되어 사용된다.
        start_dt: 조회 시작일 (FROMDATE). 기본 20000101.
        end_dt: 조회 종료일 (TODATE). None이면 오늘.
        reason_code: 권리사유 필터(RGT_RACD). ""=전체, "103"=배당/분배 등.
        dt_tpcd: 일정종류 필터(DT_TPCD). ""=전체.
        list_tpcd: 시장구분 필터(LIST_TPCD). ""=전체.
        client: 종목코드→고객번호 해결용. None이면 자동 시도(키 없으면 웹검색).
        web_client: SeibroWebSquareClient. None이면 자동 생성.
        save_csv: True이면 company_schedules_<종목코드>_<기간>.csv 저장.

    Returns:
        일정일자(DT_BEGIN_DT) 오름차순 DataFrame. 칼럼: 종목코드/회사명/일정일자/
        일정종류/사유/사유상세/기준일/일정종료일/시장/명부폐쇄기간 등.

    Note:
        웹 화면은 최대 1년 범위로 제한하지만, API 자체는 더 넓은 범위도 받는다
        (검증됨). 넓은 기간을 넣으면 그만큼 많은 행이 반환된다.
    """
    start = _yyyymmdd(start_dt)
    end = _yyyymmdd(end_dt)
    if start > end:
        raise ValueError(f"start_dt must be <= end_dt: {start} > {end}")

    web_client = web_client or SeibroWebSquareClient()
    if client is None:
        try:
            client = SeibroClient()
        except ValueError:
            client = None
    stock = _resolve_stock(stock_code, client, web_client)

    print(f"\n[Seibro] 기간별 주요일정 조회")
    print(f"  -> {stock['company_name']} ({stock['stock_code']}, 고객번호: {stock['issuco_custno']})")
    print(f"  기간: {start} ~ {end}" + (f", 사유코드={reason_code}" if reason_code else ""))

    payload = (
        f'<reqParam action="{TERM_SCHEDULE_ACTION}" task="{TASK}">'
        f'<MENU_NO value="{TERM_SCHEDULE_MENU_NO}"/>'
        '<CMM_BTN_ABBR_NM value="total_search,openall,print,hwp,word,pdf,searchIcon,seach,xls,"/>'
        f'<W2XPATH value="{TERM_SCHEDULE_W2X}"/>'
        f'<ISSUCO_CUSTNO value="{stock["issuco_custno"]}"/>'
        f'<DT_TPCD value="{_xml_escape(dt_tpcd)}"/>'
        f'<FROMDATE value="{start}"/>'
        f'<TODATE value="{end}"/>'
        f'<LIST_TPCD value="{_xml_escape(list_tpcd)}"/>'
        f'<RGT_RACD value="{_xml_escape(reason_code)}"/>'
        "</reqParam>"
    )
    response = web_client.session.post(
        WEB_CALL_URL,
        headers={
            "Referer": (
                "https://seibro.or.kr/websquare/control.jsp?"
                f"w2xPath={TERM_SCHEDULE_W2X}&menuNo={TERM_SCHEDULE_MENU_NO}"
            ),
            "submissionid": "submission_" + TERM_SCHEDULE_ACTION,
        },
        data=payload.encode("utf-8"),
        timeout=60,
    )
    response.raise_for_status()
    rows = _parse_records(response.text)

    if not rows:
        print("  해당 기간 내 일정이 없습니다.")
        return pd.DataFrame()

    df = pd.DataFrame(rows).rename(columns=TERM_SCHEDULE_RENAME)
    df.insert(0, "종목코드", stock["stock_code"])
    if "일정일자" in df.columns:
        df = df.sort_values("일정일자").reset_index(drop=True)

    ordered = [c for c in TERM_SCHEDULE_DISPLAY_ORDER if c in df.columns]
    extras = [c for c in df.columns if c not in ordered and c != "SCH_DTTM"]
    df = df[ordered + extras]

    print(f"  -> {len(df)}건 수집 완료")
    if save_csv:
        filename = f"company_schedules_{stock['stock_code']}_{start}_{end}.csv"
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"  -> {filename} 저장 완료")
    return df


def _resolve_pay_cost_type(pay_cost_type: str) -> str:
    """대금종류를 PAY_COST_TPCD 코드('1'~'3')로 정규화."""
    key = str(pay_cost_type).strip()
    if key in PAY_COST_TYPES:
        return key
    normalized = key.replace(" ", "")
    if normalized in _PAY_COST_ALIASES:
        return _PAY_COST_ALIASES[normalized]
    raise ValueError(
        f"대금종류를 알 수 없습니다: {pay_cost_type!r}. "
        f"코드('1'~'3') 또는 {list(PAY_COST_TYPES.values())} 중 하나를 사용하세요."
    )


def get_cost_payment_schedules(
    stock_code: str,
    start_dt: str | date | datetime | None = None,
    end_dt: str | date | datetime | None = None,
    pay_cost_type: str = "1",
    market: str = "",
    ag_org: str = "",
    client: SeibroClient | None = None,
    web_client: SeibroWebSquareClient | None = None,
    save_csv: bool = True,
) -> pd.DataFrame:
    """회사의 대금지급일정(배당금 등)을 조회 (BIP_CNTS01022V).

    기준일(RGT_STD_DT) 범위 내에서 회사가 지급하는 대금(배당금/단주대금/현물배당)
    지급일정 목록을 돌려준다. 지급 예정 성격이라 기본 기간은 오늘~+1년(미래)이다.

    Args:
        stock_code: 단축종목코드 (예: '005930'). 회사(custno)로 변환되어 사용된다.
        start_dt: 기준일 시작(RGT_STD_DT_FROM). None이면 오늘.
        end_dt: 기준일 종료(RGT_STD_DT_TO). None이면 오늘+1년.
        pay_cost_type: 대금종류(PAY_COST_TPCD). 코드('1'~'3') 또는
            '배당금'/'단주대금'/'현물배당'. 기본 '1'(배당금지급일).
        market: 시장구분 필터(CALTOT_MART_TPCD). ""=전체.
        ag_org: 명의개서대리인 필터(AG_ORG_TPCD). ""=전체.
        client: 종목코드→고객번호 해결용. None이면 자동 시도(키 없으면 웹검색).
        web_client: SeibroWebSquareClient. None이면 자동 생성.
        save_csv: True이면 cost_payment_<종목코드>_<기간>.csv 저장.

    Returns:
        기준일 오름차순 DataFrame. 칼럼: 기준일/종목코드/종목명/종목종류/
        대금종류/사유/시장/발행형태.
    """
    start = _yyyymmdd(start_dt)
    if end_dt is None:
        today = date.today()
        try:
            end_date = today.replace(year=today.year + 1)
        except ValueError:  # 2/29
            end_date = today.replace(year=today.year + 1, day=28)
        end = end_date.strftime("%Y%m%d")
    else:
        end = _yyyymmdd(end_dt)
    if start > end:
        raise ValueError(f"start_dt must be <= end_dt: {start} > {end}")

    pay_code = _resolve_pay_cost_type(pay_cost_type)
    web_client = web_client or SeibroWebSquareClient()
    if client is None:
        try:
            client = SeibroClient()
        except ValueError:
            client = None
    stock = _resolve_stock(stock_code, client, web_client)

    print(f"\n[Seibro] 대금지급일정 조회")
    print(f"  -> {stock['company_name']} ({stock['stock_code']}, 고객번호: {stock['issuco_custno']})")
    print(f"  기간(기준일): {start} ~ {end}, 대금종류: {PAY_COST_TYPES[pay_code]}")

    payload = (
        f'<reqParam action="{COST_PAYMENT_ACTION}" task="{TASK}">'
        f'<ISSUCO_CUSTNO value="{stock["issuco_custno"]}"/>'
        f'<CALTOT_MART_TPCD value="{_xml_escape(market)}"/>'
        f'<PAY_COST_TPCD value="{pay_code}"/>'
        f'<AG_ORG_TPCD value="{_xml_escape(ag_org)}"/>'
        f'<RGT_STD_DT_FROM value="{start}"/>'
        f'<RGT_STD_DT_TO value="{end}"/>'
        '<STARTPAGE value="1"/>'
        '<ENDPAGE value="100000"/>'
        f'<MENU_NO value="{COST_PAYMENT_MENU_NO}"/>'
        '<CMM_BTN_ABBR_NM value="total_search,openall,print,hwp,word,pdf,searchIcon,seach,xls,"/>'
        f'<W2XPATH value="{COST_PAYMENT_W2X}"/>'
        "</reqParam>"
    )
    response = web_client.session.post(
        WEB_CALL_URL,
        headers={
            "Referer": (
                "https://seibro.or.kr/websquare/control.jsp?"
                f"w2xPath={COST_PAYMENT_W2X}&menuNo={COST_PAYMENT_MENU_NO}"
            ),
            "submissionid": "submission_" + COST_PAYMENT_ACTION,
        },
        data=payload.encode("utf-8"),
        timeout=60,
    )
    response.raise_for_status()
    rows = _parse_records(response.text)

    if not rows:
        print("  해당 기간 내 대금지급일정이 없습니다.")
        return pd.DataFrame()

    df = pd.DataFrame(rows).rename(columns=COST_PAYMENT_RENAME)
    if "기준일" in df.columns:
        df = df.sort_values("기준일").reset_index(drop=True)

    ordered = [c for c in COST_PAYMENT_DISPLAY_ORDER if c in df.columns]
    extras = [c for c in df.columns if c not in ordered]
    df = df[ordered + extras]

    print(f"  -> {len(df)}건 수집 완료")
    if save_csv:
        filename = f"cost_payment_{stock['stock_code']}_{start}_{end}.csv"
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"  -> {filename} 저장 완료")
    return df


if __name__ == "__main__":
    import sys

    code = sys.argv[1] if len(sys.argv) > 1 else "000100"
    reason_arg = sys.argv[2] if len(sys.argv) > 2 else "102"
    start_arg = sys.argv[3] if len(sys.argv) > 3 else "20110101"
    end_arg = sys.argv[4] if len(sys.argv) > 4 else None
    df_result = get_schedule_reason_details(code, reason_arg, start_arg, end_arg)
    if not df_result.empty:
        print(df_result.to_string(index=False))
