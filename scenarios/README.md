# SEIBRO 시나리오 노트북

질문에 맞는 데이터 출처를 고른 뒤 노트북의 **Colab에서 열기**를 누릅니다. GitHub에서는 각 노트북의 실행 결과를 바로 볼 수 있습니다.

## 공식 Open API

`SEIBRO_API_KEY`가 필요합니다.

| 시나리오 | 조회 내용 |
|---|---|
| [일자별 발행 채권](openapi/01_issued_bonds_by_date.md) | 발행일별 채권 목록·상세 |
| [종목별 주총 일정과 안건](openapi/02_shareholder_meetings.md) | 권리기준일·개최일·안건 |
| [권리기준일별 배당 이력](openapi/03_dividend_history.md) | 보통주·우선주 배당 일정, 주당배당금, 지급일 |
| [사채별 상환 옵션 행사](openapi/04_bond_redemptions.md) | 채권 표준코드별 상환 옵션 행사 내역 |

## 공개 WebSquare

회사 검색과 데이터 조회에 WebSquare를 사용합니다. Colab Secrets 등록이 필요 없습니다.

| 시나리오 | 조회 내용 |
|---|---|
| [결산연도별 보통주·우선주 배당](web/01_dividend_details.md) | 최근 4개 결산연도의 배당금·주당배당금·배당성향 |
| [회사별 권리 일정 달력](web/02_company_schedules.md) | 배당·주총 등 권리가 발생하는 일정과 기준일 |

## 데이터 출처 혼합

| 시나리오 | 조회 내용 | 필요한 키 |
|---|---|---|
| [희석주식수 분석](combined/01_dilution.md) | KRX 상장주식수와 SEIBRO 사채·행사·의무보유·주식 증감 | `SEIBRO_API_KEY`, `KRX_ID`·`KRX_PW` |
| [미상환 CB·BW 잔액 대조](combined/02_outstanding_bond_reconciliation.md) | DART 보고서 기준 잔액과 SEIBRO 조회 시점 잔액 | `SEIBRO_API_KEY`, `DART_API_KEY` |
| [주식관련사채 현황과 공시 이력](combined/03_bond_summary.md) | SEIBRO 사채 현황, DART 발행결정 공시와 정기보고서 | `SEIBRO_API_KEY`, `DART_API_KEY` |

## 실행과 수정

- Colab에서는 필요한 키만 왼쪽 **Secrets**에 등록하고 노트북 액세스를 켭니다. 첫 셀이 GitHub에서 패키지를 설치합니다.
- 로컬에서는 레포 루트의 `.env`를 사용합니다. 희석 분석에 필요한 [`krx-data-api`](https://github.com/beaten-by-the-market/krx-data-api)는 `python -m pip install git+https://github.com/beaten-by-the-market/krx-data-api.git`로 설치할 수 있습니다. 레포를 편집 설치했으면 해당 레포의 `.env`도 읽습니다.
- 원본은 `_src/<분류>/`의 `# %%` Python 파일입니다. 빌더가 Colab 배지와 준비 셀을 붙이고 실행된 노트북을 저장 전 검사합니다.

```bash
python -m pip install -e ".[dev]"
python -m pip install ipykernel matplotlib
python scenarios/_tools/build.py web
python scenarios/_tools/build.py openapi/02
python scenarios/_tools/show.py scenarios/web/01_dividend_details.ipynb
```
