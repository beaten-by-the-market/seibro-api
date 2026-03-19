# seibro_api

한국예탁결제원(Seibro) Open API와 DART 전자공시 API를 활용한 **주식관련사채(CB/BW/EB) 데이터 수집 모듈**.

## 설치

```bash
pip install -r requirements.txt
```

`.env` 파일에 API 키 설정:

```
SEIBRO_API_KEY=your_seibro_api_key
DART_API_KEY=your_dart_api_key
```

## 파일 구성

```
seibro_api/
  __init__.py          # 모듈 진입점 (공개 함수 export)
  client.py            # Seibro Open API 기본 클라이언트
  corp_loader.py       # 법인정보 로더 (DART + Seibro 종목 맵핑)
  stock_bond.py        # 주식관련사채 조회 (Seibro API + DART API)
  dart_report.py       # 사업/반기보고서 XML 파싱 (CB/BW/EB/SUB_PIS)
  display.py           # 종합 조회 표출 스크립트
```

## 함수 목록

### client.py — Seibro API 클라이언트

| 함수 | 설명 |
|------|------|
| `SeibroClient(api_key=None)` | 클라이언트 초기화. api_key 미입력 시 `.env`에서 자동 로드 |
| `client.get_stock_registry(markets=None)` | 전체 상장종목 명부 조회 (종목코드 + 종목명 + 예탁원 고객번호) |

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

## 데이터 소스 비교

| 항목 | Seibro API | DART API | 정기보고서 XML |
|------|:----------:|:---------:|:---------------:|
| **함수** | `get_stock_bonds` | `get_dart_cb_events` | `get_bonds_from_report` |
| **시점** | 실시간 | 공시일 기준 | 보고서 기준일 |
| **대상** | CB/BW/EB 통합 | CB/BW/EB 개별 공시 | CB, BW 별도 테이블 |
| **미상환잔액** | O (실시간) | X (발행 시점만) | O (보고서 기준일) |
| **전환/행사가** | O (최신) | O (발행 시점) | O (보고서 기준일) |
| **전환가능주식수** | O (자동 계산) | O (공시 기재) | O (보고서 기재) |
| **신용등급** | O (KIS/NICE/한기평) | X | X |
| **옵션(CALL/PUT)** | O | X | X |
| **자금조달 목적** | X | O | X |
| **공시URL** | X | O | X |

## Jupyter 노트북

`bond_summary.ipynb`에서 종목코드만 바꾸면 전체 조회 결과를 시각적으로 확인할 수 있습니다.

## 공통 특징

- **재시도 로직**: 모든 API 호출에 최대 3회 재시도 + 점진적 대기 적용
- **코드 디코딩**: Seibro 코드값(모집방법, 옵션, 신용등급 등 20여 개)을 한글로 자동 변환
- **dual-TABLE 대응**: XML 파싱 시 단위표와 본 데이터 테이블을 자동 분리
- **[첨부정정] 처리**: DART 보고서의 첨부정정 공시는 원본 접수번호를 자동 추적
