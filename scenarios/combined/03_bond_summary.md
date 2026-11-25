# 주식관련사채의 현황과 공시 이력

[노트북](03_bond_summary.ipynb) · [Colab에서 열기](https://colab.research.google.com/github/beaten-by-the-market/seibro-api/blob/main/scenarios/combined/03_bond_summary.ipynb)

엑스페릭스의 주식관련사채를 SEIBRO 현황, DART 발행결정 공시, DART 정기보고서 순서로 확인합니다. 공시에는 발행 당시 조건과 원문 링크가, 보고서에는 해당 기준일의 잔액과 단위가 표시됩니다.

`SEIBRO_API_KEY`와 `DART_API_KEY`가 필요합니다. 한 사채의 잔액 차이는 [미상환잔액 대조](02_outstanding_bond_reconciliation.md)에서 계산합니다.
