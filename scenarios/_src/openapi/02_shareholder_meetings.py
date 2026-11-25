# %% [markdown]
# # 종목별 주주총회 일정과 안건
#
# 종목과 권리기준일 범위를 입력하면 SEIBRO Open API에서 주총 기준일, 개최 정보,
# 안건을 조회합니다. 기준일과 실제 개최일을 각각 표시합니다.

# %%
from IPython.display import display

from seibro_api import get_shareholder_meetings

STOCK_CODE = "005930"  # 삼성전자
START_DT = "20250101"
END_DT = "20261231"

# %%
result = get_shareholder_meetings(STOCK_CODE, START_DT, END_DT)

for name, labels in (
    ("record_dates", {
        "ISSUCO_CUSTNO": "발행회사고객번호", "REP_SECN_NM": "회사명",
        "RGT_STD_DT": "권리기준일", "RGT_RACD_NM": "일정사유",
    }),
    ("meetings", {
        "ISSUIN_NO": "발행회차", "RGT_STD_DT": "권리기준일", "GMET_DT": "개최일",
        "GMET_TTM": "개최시각", "GMET_PLACE": "장소", "EVOTE_YN": "전자투표",
    }),
    ("agendas", {
        "ISSUIN_NO": "발행회차", "RGT_STD_DT": "권리기준일", "GMET_DT": "개최일",
        "AGENDA_NO": "안건번호", "AGENDA_NM": "안건명", "DTAIL_AGENDA_NO": "세부안건번호",
        "DTAIL_AGENDA_NM": "세부안건명", "GMET_RESULT_TPCD": "결과코드(원문)",
    }),
):
    print(f"{name} · {len(result[name])}건")
    if not result[name].empty:
        display(result[name].filter(items=labels).rename(columns=labels))

# %% [markdown]
# - 조회 기간은 **권리기준일** 기준입니다. 개최일이 조회 기간 밖이어도 해당 기준일의 주총이면 표시합니다.
# - 기준일이 같아도 주총이 여러 건이면 발행회차를 함께 확인합니다.
# - 소집공고의 정관 신구조문은 DART 원문에서 확인할 수 있습니다.
