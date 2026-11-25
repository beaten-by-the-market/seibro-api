---
name: seibro
description: SEIBRO 공식 Open API와 공개 WebSquare 화면에서 한국 주식의 권리일정, 주총 안건, 배당, 의무보유, 주식관련사채와 채권 발행·상환을 조회한다. SEIBRO 또는 예탁결제원 데이터로 조회하거나 DART 사채 공시와 대조할 때 사용한다.
---

# SEIBRO 조회와 분석

저장소 루트에서 `python -m pip install -e .`를 실행하고 아래 Python 함수를 사용한다. 키가 필요한 요청은 `SEIBRO_API_KEY` 또는 `DART_API_KEY`를 환경변수나 로컬 `.env`에서 읽는다. Colab 예제는 Secrets를 쓴다. 키 값과 인증정보가 든 요청 URL·원시 XML을 출력하지 않는다.

## 질문별 조회 함수

| 질문 | 출처 | Python 진입점 |
|---|---|---|
| 회사의 주총은 언제 열렸고 안건은 무엇인가 | 공식 Open API | `get_shareholder_meetings(stock_code, start_dt, end_dt)` |
| 기간 내 배당액과 지급일은 언제인가 | 공식 Open API | `get_dividend_history(stock_code, start_dt, end_dt, save_csv=False)` |
| 최근 결산연도의 배당성향과 보통주·우선주 배당은 얼마인가 | WebSquare | `get_dividend_details(stock_code, use_openapi=False, save_csv=False)` |
| 배당·주총 등 권리 일정은 언제인가 | WebSquare | `get_company_schedules(stock_code, start_dt, end_dt, use_openapi=False, save_csv=False)` |
| 어떤 채권이 발행됐고 상환 옵션을 행사했는가 | 공식 Open API | `get_issued_bonds(start_dt, end_dt)`, `SeibroClient().get_bond_redemptions(bond_isin)` |
| 의무보유·주식수 증감은 어떻게 변했는가 | 공식 Open API | `get_lockup_records(...)`, `get_stock_issue_details(...)` |
| 사채 잔액·현재 행사가·행사 내역은 얼마인가 | 공식 Open API와 WebSquare | `get_stock_linked_bond_status(stock_code)` |
| 발행결정·정기보고서의 사채 잔액은 어떻게 다른가 | DART와 SEIBRO | `get_dart_cb_events(..., save_csv=False)`, `get_bonds_from_report(..., save_csv=False)` |

함수는 `seibro_api`에서 가져온다. `use_openapi=False`로 지정하면 환경에 공식 API 키가 있어도 회사 검색부터 웹을 쓴다. `save_csv=False`를 지원하는 함수는 조회 결과를 작업 디렉터리에 쓸 필요가 있을 때만 CSV 저장을 켠다.

```python
from seibro_api import get_shareholder_meetings

data = get_shareholder_meetings("005930", "20250101", "20261231")
print(data["agendas"].head().to_string(index=False))
```

## 결과를 해석할 때

- 주총은 **권리기준일 기준으로 조회**한다. 실제 개최일·안건을 구별하고, 소집공고 원문과 정관 변경 조문은 DART에서 확인한다.
- 배당 이력의 기준일과 지급일, 정기보고서 잔액의 기준일과 SEIBRO 조회일을 각각 표기한다.
- 미상환잔액은 CB 전환가능분을 계산할 때 쓰인다. BW 미행사분은 신주인수권 행사 내역을 대조한다. 주식수 희석과 의무보유를 같이 해석할 때 [희석 분석 원본](../../scenarios/_src/combined/01_dilution.py)의 계산 전제를 확인한다.
- 빈 표, 부분 조회, 호출 오류를 구분하고 결과에 사용한 출처와 시점을 적는다.

호출 범위와 단위의 세부사항은 [데이터 소스](../../docs/data_sources.md), 인자·컬럼은 [Python 레퍼런스](../../docs/python_reference.md)를 읽는다. 예시를 실행하거나 비교할 때는 [시나리오 색인](../../scenarios/README.md)에서 공식 API·웹·혼합 분류를 찾는다.
