# %% [markdown]
# # 회사별 권리 일정 달력
#
# 배당 기준일·권리락일·지급일과 주총 개최일을 SEIBRO WebSquare에서 조회합니다.
# 일정일자와 권리기준일을 함께 보면 한 권리에 연결된 여러 일정을 구별할 수 있습니다.

# %%
from IPython.display import display

from seibro_api import get_company_schedules

STOCK_CODE = "005930"  # 삼성전자
START_DT = "20260101"
END_DT = "20260630"
REASON_CODE = ""  # 전체. 배당/분배만 보려면 "103"

# %%
events = get_company_schedules(
    STOCK_CODE, START_DT, END_DT, reason_code=REASON_CODE, save_csv=False, use_openapi=False,
)
if events.empty:
    print("조회된 권리 일정이 없습니다.")
else:
    counts = events.groupby(["사유", "일정종류"], dropna=False).size().rename("건수").reset_index()
    display(counts)
    display(events.filter(items=["일정일자", "일정종류", "사유", "사유상세", "기준일", "일정종료일"]))

# %% [markdown]
# 각 행은 일정 하나입니다. 같은 기준일에 연결된 기준일·지급일·권리락일을 각각 집계합니다.
# 주총 안건이 필요하면 [공식 API 주총 조회](../openapi/02_shareholder_meetings.md)를 사용합니다.
