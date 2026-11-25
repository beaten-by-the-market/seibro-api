# %% [markdown]
# # 2-01 일자별 발행 채권 — 그날 어떤 회사가 어떤 조건으로 채권을 냈나
#
# **질문 예시:** "11월 23일에 발행된 회사채 보여줘", "이번 주에 CB 발행한 회사는?", "요즘 사모채 금리는 몇 %야?"
#
# | 항목 | 데이터 출처 |
# |---|---|
# | 발행일별 채권 목록(발행회사·채권코드·채권명) | SEIBRO Open API `getBondIssuInfo` (`ISSU_DT`) |
# | 발행금액·표면이자율·만기·모집방법·옵션·신용등급 | SEIBRO Open API `getBondStatInfo` (채권마다 1회) |
# | 유형(CB·BW·EB·P-CBO·일반) | 채권명 표기 + `PARTICUL_BOND_KIND_TPCD` |
#
# `getBondIssuInfo`는 **하루치만** 받습니다(기간 파라미터 없음). 패키지 함수 `get_issued_bonds(시작, 끝)`이 날짜마다 나눠 부르고,
# `details=True`면 채권마다 상세를 한 번 더 불러 붙입니다.

# %%
DAY = "2026-11-23"                          # 자세히 볼 발행일
PERIOD = ("2026-11-02", "2026-11-24")       # 기간 요약 (평일만 조회)

from seibro_api import SeibroClient, get_issued_bonds

client = SeibroClient()   # 키는 환경변수 SEIBRO_API_KEY (위 준비 셀)

# %% [markdown]
# ## 1. 하루치 목록
# 목록 자체는 칼럼이 5개뿐입니다(발행일·발행회사·고객번호·채권코드·채권명).

# %%
day_list = get_issued_bonds(DAY, client=client)
day_list.head(10)

# %% [markdown]
# 상세를 붙이면 조건을 비교할 수 있습니다. 발행금액은 억 원, 만기는 발행일부터 만기일까지의 햇수입니다.

# %%
day = get_issued_bonds(DAY, details=True, client=client)
cols = ["발행회사", "채권명", "유형", "모집방법", "발행금액", "표면이자율", "만기(년)", "옵션", "순위", "KIS_등급", "NICE_등급", "KR_등급"]
view = day[cols].copy()
view["발행금액(억)"] = view.pop("발행금액") / 1e8
view = view.sort_values("발행금액(억)", ascending=False).reset_index(drop=True)
view.style.format({"발행금액(억)": "{:,.0f}", "표면이자율": "{:.3f}", "만기(년)": "{:.1f}"}, na_rep="")

# %%
def summarize(df):
    g = df.groupby("유형").agg(건수=("채권코드", "size"), 발행금액=("발행금액", "sum"),
                              평균금리=("표면이자율", "mean"), 평균만기=("만기(년)", "mean"))
    g.loc["합계"] = [len(df), df["발행금액"].sum(), df["표면이자율"].mean(), df["만기(년)"].mean()]
    g["발행금액(억)"] = g.pop("발행금액") / 1e8
    return g


print(f"{DAY} 발행 {len(day)}건, 총 {won(day['발행금액'].sum())}원")
summarize(day).style.format({"건수": "{:,.0f}", "발행금액(억)": "{:,.0f}", "평균금리": "{:.2f}%", "평균만기": "{:.1f}년"})

# %% [markdown]
# ## 2. 기간 요약
# 같은 함수에 시작·끝을 주면 평일마다 한 번씩 부릅니다. 상세까지 받으면 채권 수만큼 호출이 더 늘어납니다(수십 건이면 1분 안쪽).

# %%
period = get_issued_bonds(*PERIOD, details=True, client=client)
summarize(period).style.format({"건수": "{:,.0f}", "발행금액(억)": "{:,.0f}", "평균금리": "{:.2f}%", "평균만기": "{:.1f}년"})

# %%
daily = period.pivot_table(index="발행일", columns="유형", values="발행금액", aggfunc="sum", fill_value=0) / 1e8
days = pd.bdate_range(*PERIOD)
daily = daily.reindex(days, fill_value=0)
ax = daily.plot(kind="bar", stacked=True, figsize=(10, 4), width=0.8)
ax.set_xticklabels([d.strftime("%m-%d") for d in daily.index], rotation=0)
ax.set_ylabel("발행금액(억 원)")
ax.set_title(f"일자별 회사채 발행금액 ({PERIOD[0]} ~ {PERIOD[1]}, SEIBRO getBondIssuInfo)")
ax.grid(axis="y", alpha=.3)
plt.tight_layout()

# %% [markdown]
# ## 3. 기간 중 주식관련사채(CB·BW·EB)
# 주식으로 바뀔 수 있는 사채입니다. 발행회사의 희석 효과는 `combined/01_dilution` 노트북으로 이어서 볼 수 있습니다.

# %%
eq = period[period["유형"].isin(["CB", "BW", "EB"])].copy()
eq["발행금액(억)"] = eq["발행금액"] / 1e8
eq["발행일"] = eq["발행일"].dt.strftime("%Y-%m-%d")
eq[["발행일", "발행회사", "채권명", "유형", "채권종류", "모집방법", "발행금액(억)", "표면이자율", "만기(년)", "옵션"]] \
    .style.format({"발행금액(억)": "{:,.0f}", "표면이자율": "{:.2f}", "만기(년)": "{:.1f}"}, na_rep="")

# %% [markdown]
# ## 결과 읽는 법과 한계
# - **대상은 SEIBRO에 등록된 회사채**(일반 공모·사모, P-CBO 기초자산, CB·BW·EB, 일부 공기업 채권)입니다. 국고채·통안채·은행채·여전채가 다 들어 있는지는 이 API 문서로 확인되지 않았습니다. 시장 전체 발행 통계로 쓰지 마세요.
# - **당일 발행분은 하루 늦게 잡히기도** 합니다. 기간 끝 날짜가 0건이면 다음 날 다시 확인하세요.
# - `유형`은 채권명 괄호 표기(예: `5CB(사모/전환/풋)`, `(PCBO사모/콜)`)로 붙인 것입니다. 정식 구분은 `채권종류`(전환·교환·신주인수권) 칼럼을 보세요. P-CBO는 `채권종류`가 "해당없음"으로 나옵니다.
# - `표면이자율`은 발행 조건입니다. 사모 CB·BW는 0~3%대가 흔한데, 주식 전환권의 대가라 일반 사채 금리와 바로 비교하면 안 됩니다.
# - 신용등급은 공모채에만 대체로 있습니다. 사모채·P-CBO 기초채권은 비어 있는 게 정상입니다.
# - `getBondStatInfo`가 일부 BW(신종 비분리형 등)에서 오류를 내면 그 채권은 상세 칼럼이 비어 있습니다.
