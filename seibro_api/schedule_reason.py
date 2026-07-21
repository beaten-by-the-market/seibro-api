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

DETAIL_CALLS_BY_REASON = {
    "102": BONUS_ISSUE_DETAIL_CALLS,
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
    ``DETAIL_CALLS_BY_REASON``: 102(무상증자), 201(액면분할), 202(액면병합),
    205(자본감소). For other reason codes, the function returns filtered
    standard dates when ``include_standard_dates_only`` is true.
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


if __name__ == "__main__":
    import sys

    code = sys.argv[1] if len(sys.argv) > 1 else "000100"
    reason_arg = sys.argv[2] if len(sys.argv) > 2 else "102"
    start_arg = sys.argv[3] if len(sys.argv) > 3 else "20110101"
    end_arg = sys.argv[4] if len(sys.argv) > 4 else None
    df_result = get_schedule_reason_details(code, reason_arg, start_arg, end_arg)
    if not df_result.empty:
        print(df_result.to_string(index=False))
