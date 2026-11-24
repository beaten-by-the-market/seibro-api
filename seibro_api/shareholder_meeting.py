"""종목별 주주총회 권리기준일·개최 정보·안건을 SEIBRO Open API로 조회."""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd

from .openapi import SeibroClient, retry_transient
from .openapi.dates import split_date_windows


def _date(value: str | date) -> str:
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    text = value.strip().replace("-", "").replace("/", "")
    if len(text) != 8 or not text.isascii() or not text.isdigit():
        raise ValueError("날짜는 YYYYMMDD, YYYY-MM-DD 또는 YYYY/MM/DD로 입력하세요.")
    return datetime.strptime(text, "%Y%m%d").strftime("%Y%m%d")


def get_shareholder_meetings(
    stock_code: str,
    start_dt: str | date,
    end_dt: str | date,
    *,
    client: SeibroClient | None = None,
) -> dict[str, pd.DataFrame]:
    """종목과 권리기준일 범위로 주총 기준일, 개최 정보, 안건을 따로 반환한다.

    각 표의 컬럼은 SEIBRO 응답 필드명이다. 개최 정보와 안건은
    `ISSUCO_CUSTNO`, `RGT_STD_DT`, `ISSUIN_NO`로 대조할 수 있다.
    """
    start, end = _date(start_dt), _date(end_dt)
    windows = split_date_windows(start, end)

    client = client or SeibroClient()
    company = retry_transient(client.get_issuco_custno, stock_code=stock_code)
    customer = company["issuco_custno"]
    dates = pd.concat(
        [retry_transient(client.get_rights_record_dates, customer, begin, finish) for begin, finish in windows],
        ignore_index=True,
    )
    if not dates.empty:
        meeting_kind = dates["RGT_RACD"].isin({"001", "002", "003"})
        meeting_name = dates["RGT_RACD_NM"].str.contains(r"총회\s*$", na=False)
        in_range = dates["RGT_STD_DT"].between(start, end)
        dates = dates.loc[(meeting_kind | meeting_name) & in_range].drop_duplicates().sort_values("RGT_STD_DT")

    meetings, agendas = [], []
    if not dates.empty:
        for record_dt in dates["RGT_STD_DT"].unique():
            meetings.append(retry_transient(client.get_meeting_details, customer, record_dt))
            agendas.append(retry_transient(client.get_meeting_agendas, customer, record_dt))

    return {
        "record_dates": dates.reset_index(drop=True),
        "meetings": pd.concat(meetings, ignore_index=True) if meetings else pd.DataFrame(),
        "agendas": pd.concat(agendas, ignore_index=True) if agendas else pd.DataFrame(),
    }
