# 종목별 주주총회 일정과 안건

[노트북](02_shareholder_meetings.ipynb) · [Colab에서 열기](https://colab.research.google.com/github/beaten-by-the-market/seibro-api/blob/main/scenarios/1_stock/02_shareholder_meetings.ipynb)

종목코드와 권리기준일 범위를 주면 SEIBRO Open API에서 기준일, 개최 정보, 안건을 각각 조회합니다. 삼성전자 예시에서는 2025년 12월 31일 기준 주총 1건과 안건 9건을 확인했습니다.

```python
from seibro_api import get_shareholder_meetings

data = get_shareholder_meetings("005930", "20250101", "20261231")
data["meetings"]  # 개최일·시각·장소
data["agendas"]   # 안건과 세부안건
```

- `SEIBRO_API_KEY`가 필요합니다. 기준일 조회는 서버의 3년 제한에 맞춰 구간을 나눕니다.
- 개최일은 조회 범위 밖일 수 있습니다. 개최 정보와 안건은 고객번호·권리기준일·발행회차로 대조합니다.
- 정관 변경 조문은 [DART 소집공고 원문](https://opendart.fss.or.kr/guide/main.do?apiGrpCd=DS001)에서 확인합니다.
