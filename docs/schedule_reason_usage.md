# SEIBro 사유별 일정내역 사용 문서

이 문서는 SEIBro 웹 화면에서 사용하는 사유별 일정내역 조회 흐름을 정리한 것이다.
현재 구현된 코드는 무상증자 일정(`RGT_RACD=102`)을 기준으로 동작하며, 기준일 목록 조회 구조는 다른 일정사유에도 재사용할 수 있다.

## 전체 흐름

1. 종목코드를 입력한다.
2. SEIBro 기업 검색 WebSquare 호출로 `ISSUCO_CUSTNO`를 찾는다.
3. 일정사유 코드(`RGT_RACD`)를 지정한다.
4. 해당 기업과 사유의 기준일 드랍다운 목록을 조회한다.
5. 사용자가 설정한 날짜 기간에 포함되는 기준일만 필터링한다.
6. 각 기준일을 순회하며 사유별 상세 조회 호출을 실행한다.
7. 결과를 `DataFrame`과 CSV로 저장한다.

## 종목코드에서 ISSUCO_CUSTNO 찾기

SEIBro 웹 화면의 기업 검색 팝업은 아래 WebSquare action을 사용한다.

```text
action: searchCompanyContentList
task: ksd.safe.bip.cmuc.User.process.SearchPTask
```

예를 들어 종목코드 `000100`을 검색하면 응답에서 다음 값을 얻을 수 있다.

```text
ISSUCO_CUSTNO = 10
REP_SECN_NM = 유한양행
```

따라서 SEIBro Open API 키가 없어도 웹 화면과 같은 방식으로 `ISSUCO_CUSTNO`를 확보할 수 있다.

## 일정사유 코드표

녹화 세션의 `scheduleKind_2.xml`에서 확인한 일정사유 코드는 다음과 같다.

| 코드 | 일정사유 | 화면 XML |
|---:|---|---|
| `001` | 정기총회 | `BIP_CNTS01024V.xml` |
| `002` | 임시총회 | `BIP_CNTS01024V.xml` |
| `003` | 종류총회 | `BIP_CNTS01024V.xml` |
| `009` | 기타총회 | `BIP_CNTS01024V.xml` |
| `101` | 유상증자 | `BIP_CNTS01025V.xml` |
| `102` | 무상증자 | `BIP_CNTS01026V.xml` |
| `103` | 배당일정 | `BIP_CNTS01027V.xml` |
| `201` | 액면분할 | `BIP_CNTS01028V.xml` |
| `202` | 액면병합 | `BIP_CNTS01028V.xml` |
| `203` | 사무인수 | `BIP_CNTS01029V.xml` |
| `204` | 상호변경 | `BIP_CNTS01030V.xml` |
| `205` | 자본감소 | `BIP_CNTS01031V.xml` |
| `206` | 합병 | `BIP_CNTS01032V.xml` |
| `207` | 회사분할 | `BIP_CNTS01033V.xml` |
| `208` | 분할합병 | `BIP_CNTS01049V.xml` |
| `210` | 주식교환 | `BIP_CNTS01035V.xml` |
| `211` | 주식이전 | `BIP_CNTS01035V.xml` |
| `301` | 주식전환 | `BIP_CNTS01036V.xml` |
| `302` | 주식상환 | `BIP_CNTS01037V.xml` |
| `900` | 매수청구 | `BIP_CNTS01039V.xml` |

## 기준일 목록 조회

기준일 드랍다운 목록은 아래 action으로 조회한다.

```text
action: getRgtStdDtByConoList
task: ksd.safe.bip.cnts.Company.process.EntrSkedulPTask
```

핵심 파라미터는 다음 두 개다.

```xml
<ISSUCO_CUSTNO value="10"/>
<RGT_RACD value="102"/>
```

응답에는 기준일이 다음 형태로 들어온다.

```xml
<CODE value="20240101"/>
<F_STD_DT value="2024/01/01"/>
```

`CODE`가 상세 조회에 사용하는 실제 기준일 값이며, `F_STD_DT`는 화면에 표시되는 날짜다.

## 현재 구현된 무상증자 조회

현재 기본 함수는 `seibro_api.schedule_reason.get_schedule_reason_details`다.

```python
from seibro_api import get_schedule_reason_details

df = get_schedule_reason_details(
    stock_code="000100",
    reason_code="102",
    start_dt="20110101",
)
```

터미널에서는 다음처럼 실행한다.

```bash
python -m seibro_api.schedule_reason 000100 102 20110101
```

`end_dt`를 생략하면 오늘 날짜까지 조회한다.

```python
df = get_schedule_reason_details("000100", reason_code="102", start_dt="20110101", end_dt="20260506")
```

실행 중에는 다음 정보가 출력된다.

```text
드랍다운 기준일 전체 개수
설정 기간 내 기준일 개수
기간 내 기준일 목록
기준일별 상세 수집 상태
```

유한양행 `000100`, 기간 `20110101`부터 오늘까지의 실행 예시는 다음과 같다.

```text
[1/2] 드랍다운 기준일 전체 30개
      설정 기간 내 기준일 9개
      - 2024/01/01 (20240101)
      - 2023/01/01 (20230101)
      - 2022/01/01 (20220101)
      - 2021/01/01 (20210101)
      - 2020/01/01 (20200101)
      - 2019/01/01 (20190101)
      - 2018/01/01 (20180101)
      - 2017/01/01 (20170101)
      - 2011/01/01 (20110101)
```

무상증자 상세 조회는 현재 아래 네 가지 action을 실행한다.

| `DETAIL_TYPE` | action | 설명 |
|---|---|---|
| `basic` | `rissuBasicInfoViewEL1` | 무상증자 기본 정보 |
| `pre_issued_stock` | `preIssuStkDetailsList1` | 기발행 주식 내역 |
| `payment` | `payDetailsList` | 지급/단주대금 내역 |
| `issued_stock` | `issuDetailsList1` | 무상증자 발행 내역 |

결과 CSV 파일명은 다음 형식이다.

```text
schedule_reason_<종목코드>_<사유코드>_<시작일>_<종료일>.csv
```

예:

```text
schedule_reason_000100_102_20110101_20260506.csv
```

## 다른 일정사유로 확장할 때

기준일 목록 조회는 사유 코드만 바꾸면 대부분 재사용할 수 있다.

```xml
<RGT_RACD value="101"/>
```

위처럼 바꾸면 유상증자 기준일 목록을 조회하는 식이다.

다만 상세 조회는 사유별 화면 XML이 다르고, WebSquare action 이름도 다를 수 있다. 따라서 확장 순서는 다음이 좋다.

1. 해당 사유 화면을 레코더로 한 번 조작한다.
2. `web_calls.json`에서 기준일 선택 이후 실행되는 action을 찾는다.
3. action별 payload 파라미터를 확인한다.
4. 공통 기준일 순회 로직에 사유별 상세 action 목록을 추가한다.

## 구현상 주의점

- `RGT_RACD`는 일정사유 코드다.
- `ISSUCO_CUSTNO`는 종목코드가 아니며, SEIBro 내부 발행회사 고객번호다.
- 기준일 목록의 `CODE`를 상세 조회의 `RGT_STD_DT`로 사용한다.
- 무상증자 상세 일부 action에는 녹화 결과 기준 `REPM_DT=19990514`가 포함되어 있다.
- WebSquare 호출은 공식 Open API가 아니라 웹 화면 내부 호출을 재현하는 방식이다.
- 화면 개편으로 action 이름이나 XML 경로가 바뀌면 재녹화가 필요할 수 있다.
