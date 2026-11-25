# %% [markdown]
# # 최근 4개 결산연도 보통주·우선주 배당
#
# SEIBRO WebSquare의 배당내역상세에서 결산연도별 주당배당금, 시가배당률,
# 배당금과 배당성향을 확인합니다. 종목을 찾는 단계부터 웹만 사용합니다.

# %%
from IPython.display import display

from seibro_api import get_dividend_details

STOCK_CODE = "005930"  # 삼성전자

# %%
data = get_dividend_details(STOCK_CODE, save_csv=False, use_openapi=False)
if data.empty:
    print("조회된 배당내역이 없습니다.")
else:
    display(data)

# %% [markdown]
# 화면은 최근 4개 결산연도를 반환합니다. 권리기준일별 배당과 지급일은
# [공식 API 배당 이력](../openapi/03_dividend_history.md)에서 조회할 수 있습니다.
