# SEIBRO Python API

예탁결제원 원천 API의 전체 목록과 XML 필드는 [공식 Open API 명세](reference/README.md)에서 찾을 수 있습니다.

## 함수 목록

### openapi/client.py — SEIBRO Open API 클라이언트

| 함수 | 설명 |
|------|------|
| `SeibroClient(api_key=None)` | 클라이언트 초기화. api_key 미입력 시 `.env`에서 자동 로드 |
| `client.get_stock_registry(markets=None)` | 전체 상장종목 명부 조회 (종목코드 + 종목명 + 예탁원 고객번호) |
| `client.get_issuco_custno(stock_code=None, isin=None)` | 종목코드 → 발행회사고객번호 (`getIssucoCustnoByIsin`) |
| `client.get_dividend_schedules(...)` | 배당일정 원천 조회 (`getDivSchedulInfo`) |
| `client.get_dividend_payouts(...)` | 배당분배금내역 원천 조회 (`getDivInfo`) |
| `get_shareholder_meetings(stock_code, start_dt, end_dt)` | 종목별 주총 권리기준일·개최 정보·안건을 세 표로 조회. [예시](../scenarios/openapi/02_shareholder_meetings.md) |
| `client.get_bond_redemptions(isin)` | 채권 표준코드별 상환 옵션 행사 원천 조회. [예시](../scenarios/openapi/04_bond_redemptions.md) |

```python
from seibro_api import SeibroClient

client = SeibroClient()
df = client.get_stock_registry()                                  # 유가 + 코스닥
df = client.get_stock_registry(["유가", "코스닥", "K-OTC", "코넥스", "기타"])  # 전체
```

### corp_loader.py — 법인정보 로더

| 함수 | 설명 |
|------|------|
| `load_corps(refresh=False)` | DART + Seibro 데이터를 종목코드로 맵핑. 캐시 지원 |

```python
from seibro_api import load_corps

df = load_corps()               # 캐시 있으면 캐시 사용
df = load_corps(refresh=True)   # 강제 새로고침
```

### stock_issue.py — 주식수량 변동내역 조회

| 함수 | 데이터 소스 | 설명 |
|------|:----------:|------|
| `get_stock_issue_details(stock_code=None, isin=None, issuco_custno=None, issue_year=None)` | Seibro API | 발행회사별 주식수량 변동내역 조회 |

Seibro API ID는 `getStkIncdecDetails`입니다. `stock_code`, `isin`, `issuco_custno` 중 하나 이상을 입력해야 하며, `issue_year`는 선택값입니다.

```python
from seibro_api import get_stock_issue_details

# 삼성전자 2018년 주식수량 변동내역
df = get_stock_issue_details(stock_code="005930", issue_year=2018)

# 표준코드 또는 발행회사고객번호로도 조회 가능
df = get_stock_issue_details(isin="KR7005930003", issue_year=2018)
df = get_stock_issue_details(issuco_custno=593, issue_year=2018)
```

터미널에서 직접 실행:

```bash
python -m seibro_api.stock_issue 005930 2018
```

**주요 출력 칼럼:**

| 칼럼 | 설명 |
|------|------|
| 발행회사고객번호 / 종목번호 | 발행회사 및 종목 식별 |
| 종목종류코드 / 종목종류 | 보통주, 우선주 등 |
| 종목발행횟수 | 발행 이력을 관리하기 위한 순번 |
| 발행일자 / 발행가 / 발행수량 | 발행 조건 |
| 종목발행사유코드 / 종목발행사유명 | 액면분할, 무상증자 등 권리사유 |
| 상장일자 | 종목상장 적용일자 |

### stock_bond.py — 주식관련사채 조회

| 함수 | 데이터 소스 | 설명 |
|------|:----------:|------|
| `get_stock_bonds(stock_code)` | Seibro API | 단일 종목의 CB/BW/EB 실시간 현황 조회 |
| `get_dart_cb_events(stock_code, years=5)` | DART API | CB/BW/EB 발행결정 공시 이력 (최근 N년) |

```python
from seibro_api import get_stock_bonds, get_dart_cb_events

# Seibro 실시간 현황 (CSV 자동 저장)
df = get_stock_bonds("079160")

# DART 발행 공시 이력 (CB + BW + EB 통합)
df = get_dart_cb_events("079160", years=5)
```

**get_stock_bonds 출력 칼럼 (31개):**

| 칼럼 | 설명 |
|------|------|
| 채권코드 / 채권명 / CB/BW/EB | 사채 식별 |
| 주권코드 / 주식종목명 | 행사 대상 주식 |
| 채권종류 / 모집방법 / 발행방법 | 전환(CB)/교환(EB)/신주인수권(BW), 공모/사모 |
| 발행일 / 만기일 | 기간 |
| 발행금액 / 미상환잔액 / 표면이자율 | 금액 |
| 전환/행사가 / 행사비율 / 전환가능_주식수 | 전환 정보 (자동 계산) |
| 옵션 / 강제조기상환 / 금리변동 | 옵션 속성 |
| 보증 / 순위 / 이자지급방법 / 원금상환방법 | 채권 속성 |
| KIS_등급 / NICE_등급 / KR_등급 | 신용등급 |
| 상장일 / 상장폐지일 / 전자증권여부 | 기타 |

**get_dart_cb_events 주요 칼럼:**

| 칼럼 | 설명 |
|------|------|
| 회사명 / 사채종류_회차 / 사채종류_종류 | 사채 식별 |
| 권면총액(원) / 사채발행방법 | 발행 정보 |
| 이사회결의일 / 납입일 / 사채만기일 | 일정 |
| 전환가액(원/주) / 전환발행주식_주식수 | CB 전용 |
| 행사가액(원/주) / 행사발행주식_주식수 | BW 전용 |
| 교환가액(원/주) / 교환대상_주식수 | EB 전용 |
| 공시유형 | CB / BW / EB 구분 |

### dart_report.py — 사업/반기보고서 XML 파싱

| 함수 | aclass | 설명 |
|------|--------|------|
| `get_bonds_from_report(stock_code)` | CB + BW + EB | **CB/BW/EB 한 번에 조회 (XML 1회 다운로드)** |
| `get_cb_from_report(stock_code)` | CB | 전환사채 테이블 |
| `get_bw_from_report(stock_code)` | BW | 신주인수권부사채 테이블 |
| `get_eb_from_report(stock_code)` | EB | 교환사채 테이블 |
| `get_sub_pis(stock_code)` | SUB_PIS | 채무증권 발행실적 (전체 채권 포괄) |

```python
from seibro_api import get_bonds_from_report

# CB/BW/EB 한 번에 (XML 1회만 다운로드)
results = get_bonds_from_report("307750")
df_cb = results["cb"]   # 전환사채
df_bw = results["bw"]   # 신주인수권부사채
df_eb = results["eb"]   # 교환사채

# 개별 조회도 가능
from seibro_api import get_cb_from_report, get_sub_pis
df_cb = get_cb_from_report("079160")
df_pis = get_sub_pis("079160")
```

**CB/BW 출력 칼럼 (27개):**

| 칼럼 | 설명 |
|------|------|
| 회사명 / 보고서유형 / 보고서기간 | 사업보고서 or 반기보고서, 2025.12 등 |
| 접수번호 / rcept_no_new / 접수일 | DART 접수 정보 |
| 사채종류 / 회차 | 사채 식별 |
| 발행일 / 만기일 / 발행총액 / 미상환잔액 | 금액 정보 |
| 전환주식종류 / 전환청구기간 / 전환비율(%) / 전환가액(원) / 전환가능주식수 | CB 전용 |
| 행사주식종류 / 행사기간 / 행사비율(%) / 행사가액(원) / 행사가능주식수 | BW 전용 |
| 비고 / 기준일 / 단위 | 메타 |

**SUB_PIS 출력 칼럼 (23개):**

| 칼럼 | 설명 |
|------|------|
| 발행회사 / 증권종류 / 발행방법 | 회사채, 조건부자본증권 등 포괄 |
| 발행일자 / 발행총액 / 이자율(%) / 신용등급 | 금액 |
| 만기일 / 상환여부 / 주관회사 | 상태 |

### 사유별 권리일정 조회

회사의 특정 권리사유에 대해 기준일을 찾고, 지원하는 사유라면 기준일별 상세 내역을 조회합니다. 배당·주총 등 여러 사유의 일정일자를 한 번에 보려면 [회사별 권리 일정 달력](../scenarios/web/02_company_schedules.md)을 사용합니다.

#### 조회하기

```python
from seibro_api import get_schedule_reason_details

df = get_schedule_reason_details(
    "000100", reason_code="102", start_dt="2024-01-01", end_dt="2024-12-31",
    save_csv=False,
)
if not df.empty:
    print(df.groupby(["RGT_STD_DT", "DETAIL_TYPE"]).size())
```

터미널에서는 종목코드, 사유코드, 시작일, 종료일 순으로 입력합니다. 종료일을 생략하면 오늘까지 조회합니다.

```bash
python -m seibro_api.schedule_reason 000100 102 20240101 20241231
```

| 인자 | 설명 |
|---|---|
| `stock_code` | 종목코드. 회사 검색으로 예탁원 고객번호(`ISSUCO_CUSTNO`)를 확인합니다. |
| `reason_code` | 권리사유 코드. 기본값은 무상증자(`102`)입니다. |
| `start_dt`, `end_dt` | 권리기준일 조회 범위. 기본값은 2011년 1월 1일부터 오늘까지입니다. `YYYYMMDD`, `YYYY-MM-DD`, `YYYY/MM/DD`, Python 날짜 객체를 받습니다. |
| `save_csv` | 기본값은 `True`입니다. 조회 결과가 있으면 작업 디렉터리에 `schedule_reason_<종목코드>_<사유코드>_<시작일>_<종료일>.csv`로 저장합니다. |
| `include_standard_dates_only` | 기본값은 `True`입니다. 상세 조회가 구현되지 않은 사유에서 기준일 목록을 반환할지 정합니다. |

상세 내역은 WebSquare에서 조회합니다. 고객번호를 찾을 때 Open API 클라이언트가 있으면 먼저 사용하고, 키가 없으면 웹 회사 검색으로 조회할 수 있습니다.

#### 사유코드와 상세 조회 범위

표의 상세 조회 함수는 `seibro_api`에서 직접 가져올 수 있습니다. 함수가 표시되지 않은 사유는 `get_schedule_reason_details()`에서 기준일 목록을 조회할 수 있습니다.

| 코드 | 권리사유 | WebSquare 화면 | 상세 조회 함수 |
|---|---|---|---|
| `001` | 정기총회 | `BIP_CNTS01024V.xml` | — |
| `002` | 임시총회 | `BIP_CNTS01024V.xml` | — |
| `003` | 종류총회 | `BIP_CNTS01024V.xml` | — |
| `009` | 기타총회 | `BIP_CNTS01024V.xml` | — |
| `101` | 유상증자 | `BIP_CNTS01025V.xml` | — |
| `102` | 무상증자 | `BIP_CNTS01026V.xml` | `get_bonus_issue_details()` |
| `103` | 배당일정 | `BIP_CNTS01027V.xml` | `get_dividend_schedule_details()` |
| `201` | 액면분할 | `BIP_CNTS01028V.xml` | `get_face_value_split_details()` |
| `202` | 액면병합 | `BIP_CNTS01028V.xml` | `get_face_value_merge_details()` |
| `203` | 사무인수 | `BIP_CNTS01029V.xml` | — |
| `204` | 상호변경 | `BIP_CNTS01030V.xml` | — |
| `205` | 자본감소 | `BIP_CNTS01031V.xml` | `get_capital_reduction_details()` |
| `206` | 합병 | `BIP_CNTS01032V.xml` | — |
| `207` | 회사분할 | `BIP_CNTS01033V.xml` | — |
| `208` | 분할합병 | `BIP_CNTS01049V.xml` | — |
| `210` | 주식교환 | `BIP_CNTS01035V.xml` | — |
| `211` | 주식이전 | `BIP_CNTS01035V.xml` | — |
| `301` | 주식전환 | `BIP_CNTS01036V.xml` | — |
| `302` | 주식상환 | `BIP_CNTS01037V.xml` | — |
| `900` | 매수청구 | `BIP_CNTS01039V.xml` | — |

#### 결과 읽기

- `RGT_STD_DT`는 권리기준일입니다. 주총 개최일, 배당금 지급일 등 실제 일정일자는 별도로 확인합니다.
- `DETAIL_TYPE`은 응답 종류입니다. `basic`은 기본 내역, `pre_issued_stock`은 기발행 주식, `payment`는 지급 내역, `issued_stock`은 발행 내역입니다. 배당일정에는 `dividend`와 `stock_dividend`도 들어올 수 있습니다. `standard_date`는 기준일 목록입니다.
- 결과가 비어 있으면 콘솔의 기간 내 기준일 수와 상세 호출 결과를 확인합니다. 개별 상세 요청 실패는 `df.attrs.get("errors", [])`에서 날짜와 응답 종류를 확인할 수 있습니다.

### dividend.py — 배당내역상세 조회

| 함수 | 데이터 소스 | 설명 |
|------|:----------:|------|
| `get_dividend_details(stock_code)` | Seibro 웹 (WebSquare) | 보통주/우선주 배당내역 통합 조회 |

SEIBro 웹 "배당내역상세"(BIP_CNTS01043V) 화면의 WebSquare 호출을 재현합니다.
**Open API key 없이** 동작하며(키 없으면 웹 회사검색으로 고객번호 자동 해결),
입력값은 종목코드 하나뿐입니다.

```python
from seibro_api import get_dividend_details

df = get_dividend_details("005930")   # 삼성전자 (보통주 + 우선주)
```

터미널에서 직접 실행:

```bash
python -m seibro_api.dividend 005930
```

**출력 칼럼:** `종목코드 / 회사명 / 주식종류(보통주·우선주) / 항목 / <연도1~4>`

| 항목(HB) 예시 | 설명 |
|--------------|------|
| 당기순이익(백만) / 유보이익(백만) | 손익 |
| 배당금(백만) / 배당금(현금·주식)(백만) | 배당 총액 |
| 배당성향(%) | 순이익 대비 배당 |
| DPS(원) / DPS(현금·주식)(원) | 주당배당금 |
| 시가배당률(현금)(%) | 시가 대비 배당률 |

> **제약**: 서버가 **최신 4개 결산연도**만 하드코딩 반환합니다. 연도 파라미터
> (`STD_YEAR`, `SETACC_YYMM` 등)는 무시되므로 이 API로는 5년 이전 과거치를
> 조회할 수 없습니다.

### dividend_history.py — 배당 이력(일정 + 금액) 기간 조회

| 함수 | 데이터 소스 | 설명 |
|------|:----------:|------|
| `get_dividend_history(stock_code, start_dt, end_dt)` | Seibro Open API | 종목코드 → 고객번호 → 기간별 배당 일정·금액 통합 |
| `get_market_dividend_schedules(std_dt, detail_sort_cd=None)` | Seibro Open API | 특정 권리기준일 하루치 전 상장사 배당일정 |

공식 Open API 3종(`getIssucoCustnoByIsin` → `getDivSchedulInfo` + `getDivInfo`)을 묶은
고수준 함수. **`SEIBRO_API_KEY` 필요.** 서버의 3년 조회 상한을 구간 분할로 우회하므로
기간을 길게 줘도 된다.

```python
from seibro_api import get_dividend_history, get_market_dividend_schedules

# 삼성전자 2015~2025 배당 이력 (보통주 + 우선주, 분기배당 포함)
df = get_dividend_history("005930", "20150101", "20251231")

# 고객번호를 이미 알면 조회 1회 절약
df = get_dividend_history(issuco_custno=593, start_dt="20200101", end_dt="20251231")

# 2024 결산 기준일에 배당일정이 있는 전 상장사 (1,084건)
mkt = get_market_dividend_schedules("20241231")
mkt = get_market_dividend_schedules("20241231", detail_sort_cd="01")  # 주식배당만
```

터미널에서 직접 실행:

```bash
python -m seibro_api.dividend_history 005930 20150101 20251231
```

**출력 칼럼 (28개):**

| 칼럼 | 설명 |
|------|------|
| 종목코드 / 발행회사고객번호 / 회사명 | 입력 종목 및 발행회사 |
| 표준코드 / 종목명 / 주식종류 | 보통주·우선주 등 종목 단위 식별 |
| 권리기준일 / 권리락일 / 명부폐쇄시작일 / 명부폐쇄종료일 | 일정 |
| 배당구분 | 현금배당 / 주식배당 / 동시배당 / 무배당 |
| 결산구분 / 확정구분 / 배정방법 | 결산·반기·분기, 확정·예고·미정, 정율·정액 |
| **주당배당금** / 시가배당률(%) / 현금배당지급일 | 현금배당 |
| 주식배정비율(%) / 주식교부일 | 주식배당 |
| 액면가(현재) / 현금배정비율(%) | 원천값(주의: 아래 참고) |
| 대주주차등배당여부 / 자사주무배정여부 / 현금·주식·시가차등배당율 | 차등배당 |
| 전자증권여부 | |

> **주의 (실측 확인된 서버 동작)**
> - **주당배당금은 `주당배당금`(CASH_ALOC_AMT)만 쓸 것.** `현금배정비율(%)`은 *당시*
>   액면가 대비 %인데 `액면가(현재)`는 *현재* 액면가라, 둘을 곱해 역산하면
>   액면분할 이전 구간에서 틀린다(삼성전자 2016년 행의 액면가가 100으로 나옴).
> - **금액은 권리기준일 2003-06-30부터** 채워진다. 그 이전은 주당배당금·시가배당률이
>   0이고 `현금배정비율(%)`만 있다. 데이터 자체는 1987년까지 소급된다.
> - 같은 (종목, 권리기준일)에 2행이 나올 수 있다(주식배당·현금배당 별도 기록).
> - 배당내역상세(`get_dividend_details`)와는 **대체가 아니라 보완** 관계다.
>   그쪽은 최근 4개 결산연도 한정이지만 당기순이익·배당성향 등 재무항목을 준다.

### issued_share_change.py — 발행주식수증감내역 조회

| 함수 | 데이터 소스 | 설명 |
|------|:----------:|------|
| `get_issued_share_changes(stock_code, start_dt, end_dt)` | Seibro 웹 (WebSquare) | 발행주식수 증감 이력(액면분할·이익소각·합병 등) |

SEIBro 웹 "발행주식수증감내역(개별)"(BIP_CNTS01012V) 화면의 WebSquare 호출을
재현합니다. **Open API key 없이** 동작하며, 배당내역상세와 달리 **기간을 입력받아
과거 데이터까지** 조회할 수 있습니다.

```python
from seibro_api import get_issued_share_changes

# 삼성전자 2010~2025 발행주식수 증감내역
df = get_issued_share_changes("005930", "20100101", "20251231")

# 종목종류/발행사유 필터 (선택)
df = get_issued_share_changes("005930", secn_kacd="0201")        # 우선주만
df = get_issued_share_changes("005930", rgt_link_racd="201")     # 액면분할만
```

터미널에서 직접 실행:

```bash
python -m seibro_api.issued_share_change 005930 20100101 20251231
```

**출력 칼럼:** `종목코드 / 종목명 / 종목종류(보통주·우선주) / 발행일자 / 상장일자 /
발행횟수 / 발행사유(액면분할·이익소각·합병·무상소각 등) / 증감수량(감소는 음수) /
발행가 / 액면가 / 발행형태`

### display.py — 종합 조회 표출

| 함수 | 설명 |
|------|------|
| `display_bond_summary(stock_code)` | 예탁원 + DART API + 정기보고서 XML을 한 번에 조회하여 표출 |

```python
from seibro_api import display_bond_summary

results = display_bond_summary("307750")

# 개별 DataFrame 접근
df_seibro = results["seibro"]
df_dart = results["dart_events"]
df_cb = results["report_cb"]
df_bw = results["report_bw"]
```

터미널에서 직접 실행:

```bash
python -m seibro_api.display 307750
```

### kofr.py — KOFR(무위험지표금리) 조회

| 함수 | 소스 | 설명 |
|------|------|------|
| `get_kofr_rates(start_dt, end_dt)` | KSD kofr.kr (WebSquare) | 공시일자별 KOFR·지수·30/90/180일 복리평균 |

```python
from seibro_api import get_kofr_rates

df = get_kofr_rates("20250101", "20251231")   # 기간별 KOFR 일별공시금리
```

터미널에서 직접 실행:

```bash
python -m seibro_api.kofr
```

**출력 칼럼:** `공시일자 / 공시회차 / KOFR / KOFR지수 / 30일평균 / 90일평균 / 180일평균 / 공시일시`

> KOFR = Korea Overnight Financing Repo rate. 국채·통안증권 담보 익일물 RP 기반
> 무위험지표금리(RFR, LIBOR 대체 한국판). 한국예탁결제원(KSD) 산출·공시.

### lockup.py — 의무보유(보호예수) 예수·반환 조회

| 함수 | 데이터 소스 | 설명 |
|------|:----------:|------|
| `get_lockup_records(stock_code=None, issuco_custno=None, start_dt=None, end_dt=None, years=5)` | Seibro API | 예수·반환 내역을 365일 구간으로 나눠 모음(서버 1년 상한 우회) |
| `lockup_balance(records)` | - | 예수 건(사유·예수일)별 반환 수량을 빼서 잔여 수량 계산 |
| `LOCKUP_REASONS` | - | 보호예수 사유코드 → 한글 |

```python
from seibro_api import get_lockup_records, lockup_balance

recs = get_lockup_records(stock_code="276730", years=5)
bal = lockup_balance(recs)          # 잔여주식수 > 0 인 행이 아직 묶인 물량
```

> 감자·액면분할·병합 뒤에는 기존 기록이 반환 없이 남고 새 수량으로 다시 예수된다.
> 잔량을 그냥 더하면 중복된다. 조회 시작일 이전 예수분은 보이지 않는다.

### stock_linked.py — 주식관련사채 잔여 행사물량

| 함수 | 데이터 소스 | 설명 |
|------|:----------:|------|
| `get_stock_linked_bond_status(stock_code)` | Seibro API + 웹 | 사채별 발행금액·미상환잔액·현재 행사가·BW 납입방법·누적 행사금액/주식수 |
| `get_bond_web_info(bond_isin)` | Seibro 웹 (key 불필요) | 채권 종목상세 기본정보 + 행사정보(`issuInfoViewEL1`, `exerInfoView`) |

```python
from seibro_api import get_stock_linked_bond_status

df = get_stock_linked_bond_status("276730")
# CB: 미상환잔액 × 행사비율 ÷ 현재행사가
# BW: (발행금액 × 행사비율 − 누적행사금액) ÷ 현재행사가   ← 미상환잔액 기준은 현금납입 BW에서 틀림
# EB: 기존 주식과 교환 → 발행주식수 불변
```

### bond_issue.py — 일자별 발행 채권

| 함수 | 데이터 소스 | 설명 |
|------|:----------:|------|
| `get_issued_bonds(start_dt, end_dt=None, details=False)` | Seibro API | 발행일(기간이면 평일마다 호출) 채권 목록, `details=True`면 금액·금리·만기·등급 추가 |

```python
from seibro_api import get_issued_bonds

df = get_issued_bonds("2026-11-23", details=True)
df = get_issued_bonds("2026-11-02", "2026-11-24")   # 기간 (목록만)
```

### client.py 추가 메서드 (원천 칼럼)

`get_stock_info` (getStkStatInfo), `get_bond_issues` (getBondIssuInfo), `get_bond_detail` (getBondStatInfo),
`get_stock_linked_bonds` (getXrcStkStatInfo), `get_bond_exercises` (getXrcStkOptionXrcInfo),
`get_lockup_status` (getSafeDpDutyDepoStatus).

## 데이터 소스 비교

| 항목 | Seibro API | DART API | 정기보고서 XML |
|------|:----------:|:---------:|:---------------:|
| **함수** | `get_stock_bonds` | `get_dart_cb_events` | `get_bonds_from_report` |
| **시점** | 실시간 | 공시일 기준 | 보고서 기준일 |
| **대상** | CB/BW/EB 통합 | CB/BW/EB 개별 공시 | CB, BW, EB 별도 테이블 |
| **미상환잔액** | O (실시간) | X (발행 시점만) | O (보고서 기준일) |
| **전환/행사가** | O (최신) | O (발행 시점) | O (보고서 기준일) |
| **전환가능주식수** | O (자동 계산) | O (공시 기재) | O (보고서 기재) |
| **신용등급** | O (KIS/NICE/한기평) | X | X |
| **옵션(CALL/PUT)** | O | X | X |
| **자금조달 목적** | X | O | X |
| **공시URL** | X | O | X |
