# 미상환 CB·BW 잔액 대조

[노트북](02_outstanding_bond_reconciliation.ipynb) · [Colab에서 열기](https://colab.research.google.com/github/beaten-by-the-market/seibro-api/blob/main/scenarios/combined/02_outstanding_bond_reconciliation.ipynb)

DART의 최근 사업·반기보고서에 기재된 잔액과 SEIBRO를 조회한 날의 잔액을 비교합니다. `DART_API_KEY`와 `SEIBRO_API_KEY`가 필요합니다. DART 원문 링크, 보고서 기준일, SEIBRO 상세 출처가 결과에 표시됩니다.

- 유형·회차·발행일·만기일이 양쪽에서 유일하게 일치하고 금액을 원으로 비교할 수 있을 때 차액을 계산합니다. `REPORT_PERIOD`로 보고서기간을 선택할 수 있습니다.
- 엑스페릭스 예시에서 2026년 반기보고서와 2026년 11월 25일 SEIBRO 조회를 대조한 결과, 양쪽에서 확인된 5건의 잔액이 일치했습니다. SEIBRO에서만 2건이 확인됐습니다.
- 기준일 사이의 전환·행사·상환이나 반영 시차가 차이를 만들 수 있습니다. 한쪽에서만 확인된 건의 차액은 비워 둡니다.
