# %% [markdown]
# # 미상환 CB·BW 잔액 대조
#
# 한 종목의 DART 정기보고서 기준 잔액과 조회 시점의 SEIBRO 잔액을 비교합니다.
# 유형·회차·발행일·만기일이 모두 일치하며 양쪽에서 각각 한 건인 경우에만 차액을 계산합니다.
# 보고서에 나타난 잔액은 보고서의 단위를 원으로 환산합니다.

# %%
import os
import re

import pandas as pd
from IPython.display import display

from seibro_api import get_bonds_from_report, get_stock_linked_bond_status

STOCK_CODE = "317770"  # 엑스페릭스
REPORT_PERIOD = None  # 기본은 추출된 최근 기간. 예시 "2025.12"
assert os.getenv("DART_API_KEY"), "DART_API_KEY를 Colab Secrets 또는 .env에 등록하세요."

DATE_COLS = ["발행일", "만기일"]
KEYS = ["사채유형", "회차", *DATE_COLS]
REPORT_COLS = ["회차", "보고서유형", "보고서기간", "기준일", "단위", "미상환잔액", "rcept_no_new"]
LIVE_COLS = ["채권코드", "채권명", "미상환잔액", "상세출처"]
UNITS = {"원": 1, "천원": 1_000, "만원": 10_000, "백만원": 1_000_000,
         "억원": 100_000_000, "십억원": 1_000_000_000}


def normalized_dates(values):
    text = values.astype("string").str.strip()
    text = text.str.replace(r"\s*(?:[./-]|년|월)\s*", "-", regex=True).str.rstrip("일")
    return pd.to_datetime(text, format="mixed", errors="coerce").dt.strftime("%Y-%m-%d")


def report_unit(value):
    text = re.sub(r"\s+", "", str(value))
    currencies = re.findall(r"(?:십억|백만|천|만|억)?원|USD|EUR|JPY|CNY|달러|유로|엔", text, flags=re.I)
    if len(currencies) == 1:
        return UNITS.get(currencies[0])
    return None


def amount(values):
    return pd.to_numeric(values.astype("string").str.replace(",", "").str.strip(), errors="coerce")


# %%
source_reports = get_bonds_from_report(STOCK_CODE, save_csv=False)
dart = pd.concat([
    source_reports[kind].reindex(columns=[*DATE_COLS, *REPORT_COLS]).assign(사채유형=kind.upper())
    for kind in ("cb", "bw")
], ignore_index=True)
period = REPORT_PERIOD or (dart["보고서기간"].dropna().max() if dart["보고서기간"].notna().any() else None)
dart = dart.loc[dart["보고서기간"].eq(period)].copy()
dart = dart.dropna(how="all", subset=["회차", "미상환잔액", *DATE_COLS])
dart["회차"] = dart["회차"].astype("string").str.extract(r"^\s*(?:제\s*)?(\d+)", expand=False)
dart["DART 잔액(원)"] = amount(dart["미상환잔액"]) * pd.to_numeric(dart["단위"].map(report_unit), errors="coerce")
dart["DART 원문"] = dart["rcept_no_new"].map(
    lambda number: f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={number}" if pd.notna(number) else ""
)

live = get_stock_linked_bond_status(STOCK_CODE, verbose=False)
live = live.reindex(columns=["구분", *DATE_COLS, *LIVE_COLS]).rename(columns={"구분": "사채유형"})
live = live.loc[live["사채유형"].isin(["CB", "BW"])].copy()
live["회차"] = live["채권명"].astype("string").str.extract(r"(?<!\d)(\d+)\s*(?:CB|BW)\b", flags=re.I, expand=False)
live["SEIBRO 잔액(원)"] = amount(live["미상환잔액"])
live["SEIBRO 조회일"] = pd.Timestamp.now(tz="Asia/Seoul").strftime("%Y-%m-%d")

for frame in (dart, live):
    frame["회차"] = pd.to_numeric(frame["회차"], errors="coerce").astype("Int64")
    for column in DATE_COLS:
        frame[column] = normalized_dates(frame[column])

# %%
duplicate_keys = pd.concat([frame.loc[frame.duplicated(KEYS, keep=False), KEYS] for frame in (dart, live)])
excluded = pd.MultiIndex.from_frame(duplicate_keys)
dart_matches = dart[KEYS].notna().all(axis=1) & ~pd.MultiIndex.from_frame(dart[KEYS]).isin(excluded)
live_matches = live[KEYS].notna().all(axis=1) & ~pd.MultiIndex.from_frame(live[KEYS]).isin(excluded)
dart_view = [*KEYS, "보고서유형", "보고서기간", "기준일", "단위", "DART 잔액(원)", "DART 원문"]
live_view = [*KEYS, "채권코드", "채권명", "SEIBRO 잔액(원)", "SEIBRO 조회일", "상세출처"]
comparison = dart.loc[dart_matches, dart_view].merge(
    live.loc[live_matches, live_view], on=KEYS, how="outer", indicator="매칭", validate="one_to_one",
)
comparison["차액(원)"] = comparison["SEIBRO 잔액(원)"] - comparison["DART 잔액(원)"]
comparison["매칭"] = comparison["매칭"].map({
    "both": "양쪽 확인", "left_only": "DART 한쪽에서 확인", "right_only": "SEIBRO 한쪽에서 확인",
})

print(f"DART 보고서기간 {period or '확인된 표 없음'} · SEIBRO 조회 {pd.Timestamp.now(tz='Asia/Seoul'):%Y-%m-%d}")
display(comparison)
for label, frame, eligible, columns in (
    ("DART", dart, dart_matches, dart_view), ("SEIBRO", live, live_matches, live_view),
):
    if (~eligible).any():
        print(f"{label} · 회차·날짜 누락 또는 중복으로 대조 보류")
        display(frame.loc[~eligible, columns])

# %% [markdown]
# 잔액 차이는 기준일 사이에 발생한 전환·행사·상환 또는 데이터 반영 시차에서 생길 수 있습니다.
# 회차나 날짜가 빠졌거나 중복된 사채, 한쪽에서만 확인되는 사채, 통화·단위가 불명확한 금액은 차액을 비워 둡니다.
