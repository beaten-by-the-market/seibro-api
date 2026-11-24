"""Inclusive date windows for the SEIBRO Open API."""

from datetime import date, datetime, timedelta


def _plus_years(day: date, years: int) -> date:
    """윤년 2/29 안전한 N년 후."""
    try:
        return day.replace(year=day.year + years)
    except ValueError:  # 2/29 -> 평년
        return day.replace(year=day.year + years, month=2, day=28)


def split_date_windows(begin_dt: str, end_dt: str, years: int = 3) -> list[tuple[str, str]]:
    """서버 3년 상한에 맞춰 [(begin, end), ...] 구간으로 분할.

    각 구간은 begin으로부터 3년 - 1일이라 서버가 자를 일이 없다.
    """
    start = datetime.strptime(begin_dt, "%Y%m%d").date()
    finish = datetime.strptime(end_dt, "%Y%m%d").date()
    if start > finish:
        raise ValueError(f"시작일({begin_dt})이 종료일({end_dt})보다 늦습니다.")

    windows = []
    cursor = start
    while cursor <= finish:
        window_end = min(_plus_years(cursor, years) - timedelta(days=1), finish)
        windows.append((cursor.strftime("%Y%m%d"), window_end.strftime("%Y%m%d")))
        cursor = window_end + timedelta(days=1)
    return windows
