# 사채별 상환 옵션 행사 내역

[노트북](04_bond_redemptions.ipynb) · [Colab에서 열기](https://colab.research.google.com/github/beaten-by-the-market/seibro-api/blob/main/scenarios/openapi/04_bond_redemptions.ipynb)

채권 표준코드로 `getBondOptionXrcInfo`를 조회합니다. 엑스페릭스 2BW 예시에서 상환 옵션 행사 3건을 확인했습니다. 원천에는 조기상환일, 옵션 코드, 상환금액과 잔액이 있습니다.

`SEIBRO_API_KEY`가 필요합니다. 주식 전환·신주인수권 행사 내역은 별도 호출인 `SeibroClient.get_bond_exercises()`에 있습니다.
