"""Transport for the SEIBRO and KSD public WebSquare screens."""

from __future__ import annotations

from xml.etree import ElementTree

import requests


WEB_CALL_URL = "https://seibro.or.kr/websquare/engine/proworks/callServletService.jsp"
TASK = "ksd.safe.bip.cnts.Company.process.EntrSkedulPTask"
DEFAULT_MENU_NO = "21"


def post_xml(
    session: requests.Session,
    payload: str,
    *,
    headers: dict[str, str],
    url: str = WEB_CALL_URL,
    timeout: int = 30,
) -> requests.Response:
    response = session.post(url, headers=headers, data=payload.encode("utf-8"), timeout=timeout)
    response.raise_for_status()
    return response


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
        response = post_xml(
            self.session,
            payload,
            headers={
                "Referer": self._referer(w2x_path, reason_code),
                "submissionid": submission_id,
            },
        )
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
        response = post_xml(
            self.session,
            payload,
            headers={
                "Referer": self._referer(w2x_path, reason_code),
                "submissionid": submission_id,
            },
        )
        return _parse_records(response.text), _result_count(response.text)

    def search_company(self, search_string: str) -> list[dict[str, str]]:
        payload = (
            '<reqParam action="searchCompanyContentList" '
            'task="ksd.safe.bip.cmuc.User.process.SearchPTask">'
            '<IS_FF value=""/>'
            f'<search_string value="{_xml_escape(search_string)}"/>'
            "</reqParam>"
        )
        response = post_xml(
            self.session,
            payload,
            headers={
                "Referer": "https://seibro.or.kr/websquare/control.jsp?w2xPath=/IPORTAL/user/etc/BIP_CMUC01024P.xml",
                "submissionid": "P_submission_contentList",
            },
        )
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
