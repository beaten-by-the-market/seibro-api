# %% [markdown]
# # 주식관련사채의 현황과 공시 이력
#
# SEIBRO의 채권별 현황, DART 발행결정 공시, DART 정기보고서 기재 잔액을 함께 봅니다.
# 세 표의 시점과 식별자가 다르므로 원문 공시와 함께 확인합니다.

# %%
from IPython.display import display

from seibro_api import get_bonds_from_report, get_dart_cb_events, get_stock_bonds

STOCK_CODE = "317770"  # 엑스페릭스
YEARS = 3
# 이 시나리오는 SEIBRO_API_KEY와 DART_API_KEY를 사용합니다.

# %%
current = get_stock_bonds(STOCK_CODE, save_csv=False)
print(f"SEIBRO 사채 현황 · {len(current)}건")
display(current.filter(items=["채권코드", "채권명", "CB/BW/EB", "발행일", "만기일", "미상환잔액", "전환/행사가"]))

# %%
events = get_dart_cb_events(STOCK_CODE, years=YEARS, save_csv=False)
if "접수번호" in events:
    events["DART 원문"] = events["접수번호"].map(lambda n: f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={n}")
print(f"DART 발행결정 공시 · {len(events)}건")
display(events.filter(items=[
    "공시유형", "사채종류_회차", "권면총액(원)", "이사회결의일", "납입일", "사채만기일", "DART 원문",
]))

# %%
reports = get_bonds_from_report(STOCK_CODE, save_csv=False)
for kind, frame in reports.items():
    details = frame.dropna(subset=["회차"]) if "회차" in frame else frame
    if "rcept_no_new" in details:
        details = details.assign(
            DART_원문=details["rcept_no_new"].map(lambda n: f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={n}"),
        ).rename(columns={"DART_원문": "DART 원문"})
    print(f"DART 정기보고서 {kind.upper()} · {len(details)}건")
    if not details.empty:
        display(details.filter(items=[
            "보고서유형", "보고서기간", "회차", "발행일", "만기일", "미상환잔액", "기준일", "단위", "DART 원문",
        ]))

# %% [markdown]
# 같은 채권의 보고서 잔액과 조회 시점 잔액을 원 단위로 비교하려면
# [미상환 CB·BW 잔액 대조](02_outstanding_bond_reconciliation.md)를 사용합니다.
