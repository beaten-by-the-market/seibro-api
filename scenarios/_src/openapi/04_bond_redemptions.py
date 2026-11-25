# %% [markdown]
# # 사채별 상환 옵션 행사 내역
#
# 채권 표준코드로 SEIBRO Open API의 상환 옵션 행사 내역을 조회합니다.
# 채권 상세의 옵션 보유 여부와 실제 행사 데이터는 별개의 자료입니다.

# %%
from IPython.display import display

from seibro_api import SeibroClient

BOND_ISIN = "KR6317772E29"  # 엑스페릭스 2BW

# %%
redemptions = SeibroClient().get_bond_redemptions(BOND_ISIN)
if redemptions.empty:
    print("SEIBRO에 조회된 상환 옵션 행사 내역이 없습니다.")
else:
    display(redemptions)

# %% [markdown]
# 표는 SEIBRO 응답 컬럼을 그대로 보여 줍니다. 주식으로 전환하거나 신주인수권을 행사한 내역은
# `SeibroClient.get_bond_exercises(BOND_ISIN)`에서 따로 조회합니다.
