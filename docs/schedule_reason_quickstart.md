# 사유별 일정내역 빠른 사용 가이드

이 문서는 SEIBro 사유별 일정내역을 실제로 조회할 때 필요한 최소 사용법만 정리한다.

## 1. 가장 기본적인 사용법

현재 바로 사용할 수 있는 구현은 무상증자 내역 조회다.

```python
from seibro_api import get_schedule_reason_details

df = get_schedule_reason_details("000100", reason_code="102", start_dt="20110101")
```

위 코드는 다음 작업을 자동으로 수행한다.

1. 종목코드 `000100`으로 SEIBro 내부 고객번호를 찾는다.
2. 무상증자 사유 코드 `102`로 기준일 드랍다운 목록을 가져온다.
3. `2011-01-01`부터 오늘까지의 기준일만 골라낸다.
4. 기준일별 상세 내역을 순회 수집한다.
5. 결과를 `DataFrame`으로 반환하고 CSV로 저장한다.

## 2. 터미널에서 실행하기

```bash
python -m seibro_api.schedule_reason 000100 102 20110101
```

종료일을 직접 지정하려면 세 번째 인자를 넣는다.

```bash
python -m seibro_api.schedule_reason 000100 102 20110101 20260506
```

## 3. 파라미터

| 파라미터 | 예시 | 설명 |
|---|---|---|
| `stock_code` | `"000100"` | 6자리 종목코드 |
| `reason_code` | `"102"` | 일정사유 코드. `102`는 무상증자 |
| `start_dt` | `"20110101"` | 조회 시작일 |
| `end_dt` | `"20260506"` | 조회 종료일. 생략하면 오늘 |
| `save_csv` | `True` | CSV 저장 여부 |

날짜는 아래 형식을 사용할 수 있다.

```python
get_schedule_reason_details("000100", reason_code="102", start_dt="20110101")
get_schedule_reason_details("000100", reason_code="102", start_dt="2011-01-01")
get_schedule_reason_details("000100", reason_code="102", start_dt="2011/01/01")
```

## 4. 실행 중 출력되는 내용

실행하면 중간 상태가 콘솔에 표시된다.

```text
[Seibro] 무상증자 내역 수집
  종목코드: 000100
  기간: 20110101 ~ 20260506
  -> 유한양행 (ISSUCO_CUSTNO: 10, ISIN: ...)

[1/2] 드랍다운 기준일 전체 30개
      설정 기간 내 기준일 9개
      - 2024/01/01 (20240101)
      - 2023/01/01 (20230101)

[2/2] 기준일별 상세 수집
  [1/9] 2024/01/01 수집 시작
      OK basic: 1건
      OK pre_issued_stock: 2건
      OK payment: 2건
      OK issued_stock: 1건
```

이 출력으로 다음을 바로 확인할 수 있다.

- 드랍다운에 기준일이 총 몇 개 있는지
- 내가 지정한 기간 안에 기준일이 몇 개 있는지
- 어떤 기준일을 순회하는지
- 기준일별 상세 조회가 성공했는지

## 5. 결과 확인

함수는 `pandas.DataFrame`을 반환한다.

```python
df = get_schedule_reason_details("000100", reason_code="102", start_dt="20110101")

print(df.head())
print(df["DETAIL_TYPE"].value_counts())
```

`DETAIL_TYPE`은 상세 내역 종류를 뜻한다.

| 값 | 의미 |
|---|---|
| `basic` | 기본 정보 |
| `pre_issued_stock` | 기발행 주식 내역 |
| `payment` | 지급/단주대금 내역 |
| `issued_stock` | 발행 내역 |

CSV 파일은 기본적으로 현재 작업 디렉터리에 저장된다.

```text
schedule_reason_000100_102_20110101_20260506.csv
```

CSV 저장이 필요 없으면 다음처럼 실행한다.

```python
df = get_schedule_reason_details("000100", reason_code="102", start_dt="20110101", save_csv=False)
```

## 6. 다른 종목 조회하기

종목코드만 바꾸면 된다.

```python
df = get_schedule_reason_details("005930", reason_code="102", start_dt="20110101")
```

SEIBro 내부 고객번호인 `ISSUCO_CUSTNO`는 직접 알 필요가 없다. 함수가 종목코드로 자동 검색한다.

## 7. 다른 일정사유를 조회하려면

현재 바로 함수로 제공되는 것은 무상증자다.

다른 일정사유의 기준일 목록은 같은 구조로 확장할 수 있지만, 상세 조회 action은 사유별로 다를 수 있다.

주요 일정사유 코드는 다음과 같다.

| 코드 | 일정사유 |
|---:|---|
| `101` | 유상증자 |
| `102` | 무상증자 |
| `103` | 배당일정 |
| `201` | 액면분할 |
| `202` | 액면병합 |
| `204` | 상호변경 |
| `205` | 자본감소 |
| `206` | 합병 |
| `207` | 회사분할 |
| `208` | 분할합병 |
| `900` | 매수청구 |

전체 코드표와 내부 호출 구조는 `docs/schedule_reason_usage.md`를 참고한다.

## 8. 자주 만나는 상황

### 결과가 비어 있을 때

설정한 기간 안에 해당 사유의 기준일이 없을 수 있다. 출력의 `설정 기간 내 기준일` 개수를 먼저 확인한다.

### API 키가 없을 때

무상증자 조회는 SEIBro 웹 화면의 기업 검색 호출을 사용하므로 `SEIBRO_API_KEY` 없이도 동작한다.

### 화면 개편 후 실패할 때

SEIBro WebSquare 내부 호출을 재현하는 방식이라, SEIBro 화면 XML이나 action 이름이 바뀌면 다시 녹화해서 갱신해야 한다.
