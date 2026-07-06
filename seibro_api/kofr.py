"""KOFR(무위험지표금리) 일별 공시 조회 모듈 (KSD kofr.kr WebSquare 호출).

한국예탁결제원(KSD)이 운영하는 KOFR 공시 사이트(https://www.kofr.kr)의 금리조회
화면(rate.jsp)이 쓰는 WebSquare XML POST(getGridRateList)를 재현한다. Open API
key 없이 동작하며, 기간(YYYYMMDD)을 넣으면 공시일자별 KOFR·지수·30/90/180일
복리평균을 돌려준다.

KOFR = Korea Overnight Financing Repo rate. 국채·통안증권 담보 익일물 RP 거래에서
산출하는 무위험지표금리로, LIBOR 대체 RFR의 한국판. KSD가 산출·공시한다.

seibro.or.kr 계열(dividend.py 등)과 호스트만 다를 뿐(www.kofr.kr) 동일한 WebSquare
callServletService.jsp 구조라 같은 방식으로 호출한다.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import date, datetime

import pandas as pd
import requests

CALL_URL = "https://www.kofr.kr/websquare/engine/proworks/callServletService.jsp"
TASK = "ksd.rfr.user.rate.process.RatePTask"
ACTION = "getGridRateList"
SUBMISSION_ID = f"{TASK}.{ACTION}"
REFERER = "https://www.kofr.kr/rate/rate.jsp"
ORIGIN = "https://www.kofr.kr"

# FIX_RATE_TPCD: 1 = 확정치(정규 공시). rate.jsp 기본값.
FIX_RATE_TPCD = "1"

RENAME = {
    "RFR_PUBN_DT": "공시일자",
    "RFR_PUBN_ISSN": "공시회차",
    "RFR_PUBN_MR": "KOFR",
    "RFR_INDEX": "KOFR지수",
    "D30_AVG_MR": "30일평균",
    "D90_AVG_MR": "90일평균",
    "D180_AVG_MR": "180일평균",
    "PUBN_MR_STD_DT": "기준일",
    "PUBN_DTTM": "공시일시",
}
NUM_COLS = ["KOFR", "KOFR지수", "30일평균", "90일평균", "180일평균"]
DISPLAY_ORDER = ["공시일자", "공시회차", "KOFR", "KOFR지수",
                 "30일평균", "90일평균", "180일평균", "공시일시"]


def _yyyymmdd(value: str | date | datetime | None, default: str) -> str:
    if value is None:
        return default
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y%m%d")
    text = str(value).strip().replace("-", "").replace("/", "").replace(".", "")
    if len(text) != 8 or not text.isdigit():
        raise ValueError(f"날짜는 YYYYMMDD 형식이어야 합니다: {value!r}")
    return text


def _session(session: requests.Session | None) -> requests.Session:
    s = session or requests.Session()
    s.headers.update(
        {
            "Accept": "application/xml",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": 'application/xml; charset="UTF-8"',
            "Origin": ORIGIN,
            "Referer": REFERER,
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131 Safari/537.36"
            ),
        }
    )
    return s


def _fetch_page(session: requests.Session, start: str, end: str, page: int) -> tuple[list[dict], int]:
    body = (
        f'<reqParam action="{ACTION}" task="{TASK}">'
        f'<SEARCH_START_DATE value="{start}"/>'
        f'<SEARCH_END_DATE value="{end}"/>'
        f'<CURR_PAGE value="{page}"/>'
        f'<FIX_RATE_TPCD value="{FIX_RATE_TPCD}"/>'
        f'<LANG value="kor"/></reqParam>'
    )
    resp = session.post(CALL_URL, headers={"submissionid": SUBMISSION_ID},
                        data=body.encode("utf-8"), timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    total = int(root.attrib.get("RECORD_COUNT", "0") or 0)
    rows = []
    for res in root.findall(".//data/result"):
        rows.append({child.tag: (child.attrib.get("value", "") or "").strip()
                     for child in res})
    return rows, total


def get_kofr_rates(
    start_dt: str | date | datetime = "20191126",
    end_dt: str | date | datetime | None = None,
    session: requests.Session | None = None,
    save_csv: bool = False,
) -> pd.DataFrame:
    """기간별 KOFR 일별 공시금리를 조회.

    KSD kofr.kr 금리조회(rate.jsp)의 WebSquare 호출(getGridRateList)을 재현한다.
    Open API key 불필요. 페이지네이션을 자동 처리해 기간 내 전건을 돌려준다.

    Args:
        start_dt: 조회 시작일 (YYYYMMDD / YYYY-MM-DD / date). 기본 20191126(KOFR 최초).
        end_dt: 조회 종료일. None이면 오늘.
        session: requests.Session. None이면 자동 생성.
        save_csv: True이면 kofr_<start>_<end>.csv 저장.

    Returns:
        공시일자 오름차순 DataFrame.
        칼럼: 공시일자/공시회차/KOFR/KOFR지수/30일평균/90일평균/180일평균/공시일시.
        (KOFR·지수·평균은 float)
    """
    start = _yyyymmdd(start_dt, "20191126")
    end = _yyyymmdd(end_dt, date.today().strftime("%Y%m%d"))
    sess = _session(session)

    collected: list[dict] = []
    page = 1
    total = None
    while True:
        rows, total = _fetch_page(sess, start, end, page)
        if not rows:
            break
        collected.extend(rows)
        if total and len(collected) >= total:
            break
        if len(rows) == 0:
            break
        page += 1
        if page > 500:  # 안전장치
            break

    if not collected:
        return pd.DataFrame(columns=DISPLAY_ORDER)

    df = pd.DataFrame(collected).rename(columns=RENAME)
    for c in NUM_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    cols = [c for c in DISPLAY_ORDER if c in df.columns]
    df = df[cols].drop_duplicates(subset=["공시일자"]).sort_values("공시일자").reset_index(drop=True)

    if save_csv:
        path = f"kofr_{start}_{end}.csv"
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"saved {path} ({len(df)} rows)")
    return df


if __name__ == "__main__":
    out = get_kofr_rates("20250825", "20250925")
    print(out.to_string(index=False))
