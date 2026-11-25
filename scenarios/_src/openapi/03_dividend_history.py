# %% [markdown]
# # 권리기준일별 배당 이력과 지급일
#
# SEIBRO Open API에서 회사의 배당일정과 배당분배금내역을 권리기준일 단위로 조회합니다.
# 분기 배당도 포함되며 보통주와 우선주는 표준코드로 구별합니다.

# %%
from IPython.display import display

from seibro_api import get_dividend_history

STOCK_CODE = "005930"  # 삼성전자
START_DT = "20240101"
END_DT = "20251231"

# %%
df = get_dividend_history(STOCK_CODE, START_DT, END_DT, save_csv=False)
if df.empty:
    print("해당 기간에 조회된 배당 이력이 없습니다.")
else:
    display(df.filter(items=[
        "회사명", "표준코드", "종목명", "주식종류", "권리기준일", "배당구분", "확정구분",
        "주당배당금", "시가배당률(%)", "현금배당지급일",
    ]))

# %% [markdown]
# 배당 기준일이 범위 안에 있으면 지급일이 범위 밖일 수 있습니다.
# 결산연도 기준 배당성향은 [웹 배당내역상세](../web/01_dividend_details.md)에 있습니다.
