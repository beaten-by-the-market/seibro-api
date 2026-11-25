# 데이터 소스 정리

SEIBRO 관련 데이터는 아래 순서로 조회 경로를 선택합니다.

1. **SEIBRO 공식 Open API**에서 필요한 조회 기능과 필드를 먼저 찾습니다. 인증에는 `SEIBRO_API_KEY`를 사용합니다.
2. 공식 API에 필요한 항목이 없으면 **공공데이터포털 API**를 확인합니다. 서비스별 활용신청과 공공데이터포털 인증키가 필요합니다.
3. 두 API에서 얻기 어려운 화면 상세는 **SEIBRO 공개 WebSquare**에서 확인합니다. 공개 화면에는 API 인증키가 필요 없습니다.

KOFR와 DART는 각각 금리 공시와 기업 공시를 보완하는 출처입니다.

---

## 1. SEIBRO 공식 Open API (key O)

- 엔드포인트: `https://seibro.or.kr/OpenPlatform/callOpenAPI.jsp`
- 인증: `.env`의 `SEIBRO_API_KEY`
- 구현: [`openapi/client.py`](../seibro_api/openapi/client.py) `SeibroClient._call_api()` (XML→DataFrame, 인증서 검증)
- 원천 명세: [공식 Open API 색인](reference/README.md)에서 5개 분야의 요청·응답 필드와 엑셀 원본을 확인합니다.

| apiId | 용도 | 호출 함수 |
|-------|------|----------|
| `getShotnByMart` | 시장별 전체 상장종목 명부(종목코드·종목명·고객번호) | `get_stock_registry()` |
| `getStkIncdecDetails` | 발행회사별 주식수량 변동내역(액면분할·무상증자 등) | `get_stock_issue_details()` |
| `getStkStatInfo` | 종목 기본정보(단축코드→ISIN·고객번호·발행주식총수) | `SeibroClient.get_stock_info()` |
| `getXrcStkStatInfo` | 종목에 연결된 주식관련사채(CB/BW/EB) 목록 | `get_stock_bonds()`, `SeibroClient.get_stock_linked_bonds()` |
| `getBondStatInfo` | 사채별 상세(미상환잔액·금리·신용등급·옵션 등) | `get_stock_bonds()`, `SeibroClient.get_bond_detail()` |
| `getBondOptionXrcInfo` | 채권 표준코드별 상환 옵션 행사 | `SeibroClient.get_bond_redemptions()` |
| `getXrcStkOptionXrcInfo` | 주식관련사채 권리행사 내역(행사일·행사금액·행사주식수·당시 행사가) | `SeibroClient.get_bond_exercises()`, `get_stock_linked_bond_status()` |
| `getBondIssuInfo` | 발행일(하루) 또는 발행회사별 채권 발행 목록 | `SeibroClient.get_bond_issues()`, `get_issued_bonds()` |
| `getSafeDpDutyDepoStatus` | 의무보호예수 예수(BIZ_TPCD=1)·반환(2) 내역, 조회기간 1년 이하 | `SeibroClient.get_lockup_status()`, `get_lockup_records()` |
| `getIssucoCustnoByIsin` | 종목코드 → 발행회사고객번호·대표종목명 | `SeibroClient.get_issuco_custno()` |
| `getDivSchedulInfo` | 배당일정(권리기준일·권리락일·명부폐쇄·확정구분), 금액 없음 | `SeibroClient.get_dividend_schedules()` |
| `getDivInfo` | 배당분배금내역(주당배당금·시가배당률·지급일·차등배당) | `SeibroClient.get_dividend_payouts()` |
| `getStddtInfo`, `getGmeetInfo`, `getGmeetMeasureInfo` | 주총 권리기준일·개최 정보·안건 | `get_shareholder_meetings()` |

특징: 코드값 20여 종을 한글로 자동 디코딩(`CODE_TABLES`, `CREDIT_GRADE_MAP`), 전환가능주식수 자동 계산.

배당 3종을 묶은 고수준 함수는 [`dividend_history.py`](../seibro_api/dividend_history.py)
`get_dividend_history()` / `get_market_dividend_schedules()`. 서버 제약(3년 상한)을
구간 분할로 우회한다. 상세는 아래 "알려진 제약" 참고.

---

## 2. 공공데이터포털 Open API

한국예탁결제원 서비스 10개와 금융위원회 서비스 20개를 조사했습니다. 호출은 `https://apis.data.go.kr`에서 수행하며, 서비스별 경로와 파라미터는 공개 Swagger 명세를 따릅니다. 대표 조회에서는 한국예탁결제원 서비스의 XML과 금융위원회 서비스의 JSON 응답을 확인했습니다.

주총·배당·채권 발행·상환 등은 SEIBRO 공식 Open API와 겹치는 영역입니다. 기준일 의미, 검색 단위, 응답 필드가 맞는지 확인한 뒤 비교합니다. 증권예탁 통계, REPO, 크라우드펀딩, 금융용어처럼 공식 API 37개에서 찾기 어려운 항목도 이 경로에서 확인할 수 있습니다. [공공데이터포털 서비스 색인](reference/data-go-kr/README.md) · [겹치는 조회 비교](reference/data-go-kr/overlap.md)

활용정보의 **OpenAPI 실행 준비 → OpenAPI 호출**로 요청 변수와 응답을 확인할 수 있습니다. 개인 인증키는 실행할 때만 사용하고 공유하는 예시에는 자리표시자를 사용합니다. [대표 호출 및 응답 검증](reference/data-go-kr/verification.md)

---

## 3. SEIBRO 웹 — WebSquare 호출 (key X)

- 엔드포인트: `https://seibro.or.kr/websquare/engine/proworks/callServletService.jsp`
- 방식: XML POST(`<reqParam action=… task=…>`) + 브라우저 헤더(Referer/submissionid)
- 공통 전송·파싱: [`web/client.py`](../seibro_api/web/client.py). 화면별 조회와 두 경로를 함께 쓰는 함수는 도메인 모듈에서 제공합니다.

| action | 페이지(w2xPath) | 용도 | 호출 함수 |
|--------|-----------------|------|----------|
| `searchCompanyContentList` | BIP_CMUC01024P | 회사 검색(키 없이 종목→고객번호 해결) | 내부 조회 |
| `getRgtStdDtByConoList` | (사유별) | 사유별 권리기준일 드롭다운 목록 | `get_schedule_reason_details()` |
| `rissuBasicInfoViewEL1` 외 3종 | BIP_CNTS01026V | 무상증자(102) 기준일별 상세 | `get_bonus_issue_details()` |
| `entrDivResultsList` / `entrDivResultsList2` | BIP_CNTS01043V | 배당내역상세(보통주/우선주) | `get_dividend_details()` |
| `chgDetailsListEL1` | BIP_CNTS01012V | 발행주식수증감내역(개별) — 기간 조회 지원 | `get_issued_share_changes()` |
| `issuInfoViewEL1` / `exerInfoView` | BIP_CNTS03004V | 채권 종목상세 기본정보 / 행사정보(현재 행사가·BW 신주대금 납입방법) | `get_bond_web_info()` |

일정사유별 상세 조회는 무상증자(102), 배당(103), 액면분할(201), 액면병합(202), 자본감소(205)를 지원합니다. 그 외 사유는 기준일 목록을 반환합니다. `get_company_schedules()`와 `get_dividend_details()`에는 `use_openapi=False`를 지정해 회사 검색도 WebSquare로 실행할 수 있습니다.

### 메뉴 링크 → API 만드는 워크플로

웹 메뉴 URL(`…?w2xPath=/IPORTAL/…/{PAGE}.xml&menuNo=NN`)만 있으면 다음이 가능하다.

1. `https://seibro.or.kr{w2xPath}` 의 정의 XML을 직접 fetch
2. JS에서 `callTask('<action>', '<task>')` → action·task 추출
3. `setInstanceValue('request/reqParam/<PARAM>/@value', …)` → 필수 파라미터 추출
4. submission_id = `submission_` + action
5. `SeibroWebSquareClient` 패턴으로 POST 재현

**한계**: 다단계 연쇄 호출(예: 기준일을 먼저 받아 다음 호출에 주입), 날짜범위·페이징이
위젯 이벤트로만 세팅되는 경우, JS가 너무 동적인 경우 → 이럴 땐 recorder로 fallback.

### recorder — 웹 호출 발굴 도구

[`recorder/seibro_recorder.py`](../recorder/seibro_recorder.py): Selenium + Chrome DevTools
Protocol로 SEIBRO를 수동 조작하며 WebSquare XML POST를 녹화 → `web_calls.json`,
`replay_candidates.py` 생성. 위 action들을 발굴해 패키지로 승격하는 경로.

---

## 3b. KSD KOFR 공시 — kofr.kr WebSquare (key X)

- 엔드포인트: `https://www.kofr.kr/websquare/engine/proworks/callServletService.jsp`
- 방식: SEIBRO 공개 화면과 같은 WebSquare XML POST를 `www.kofr.kr`에서 사용합니다.
- 구현: [`kofr.py`](../seibro_api/kofr.py) `get_kofr_rates()` — 페이지네이션(`CURR_PAGE`) 자동 처리.

| action | task | 용도 | 호출 함수 |
|--------|------|------|----------|
| `getGridRateList` | `ksd.rfr.user.rate.process.RatePTask` | 기간별 KOFR 일별공시(금리·지수·30/90/180일 복리평균) | `get_kofr_rates()` |

KOFR = Korea Overnight Financing Repo rate. 국채·통안증권 담보 익일물 RP 거래에서 산출하는
무위험지표금리(RFR, LIBOR 대체 한국판)로 KSD가 산출·공시한다. 응답 필드: `RFR_PUBN_DT`(공시일자),
`RFR_PUBN_MR`(KOFR), `RFR_INDEX`(지수), `D30/D90/D180_AVG_MR`(복리평균).

---

## 4. DART (별도 기관)

| 소스 | 용도 | 호출 함수 |
|------|------|----------|
| DART Open API (`OpenDartReader`) | CB/BW/EB 발행결정 공시 이력, 자금조달 목적·공시URL | `get_dart_cb_events()` |
| DART 정기보고서 XML | 사업/반기보고서의 CB·BW·EB·채무증권 발행실적 테이블 | `get_bonds_from_report()` |

통합 표출: `display_bond_summary()` — Seibro API + DART API + 보고서 XML을 한 번에 조회.

---

## 소스별 한눈 요약

```
SEIBRO 공식 Open API (key O)  → 종목명부 · 주식수량변동 · 주식관련사채(CB/BW/EB) 현황
                              · 배당일정/배당분배금내역(1987년~, 3년씩 분할조회)
공공데이터포털 API (key O)   → 공식 API 조회 범위 보완 · 증권예탁 통계 · REPO · 크라우드펀딩
SEIBRO 웹 WebSquare (key X)   → 회사검색 · 권리기준일 · 무상증자 상세 · 배당내역상세 · 발행주식수증감내역
KSD KOFR kofr.kr (key X)      → KOFR 무위험지표금리 일별공시(금리·지수·복리평균)
DART (별도 기관, key O)       → 사채 발행공시 이력 · 정기보고서 사채 테이블
```

## 참고: 알려진 제약

### Open API 공통 (실측 2026-11)
- 키가 URL 쿼리에 들어가고, **응답 XML에도 `vectorkey` 속성으로 키가 되돌아온다.** 원시 URL·응답을
  출력하지 말 것. `_call_api`는 예외·출력 메시지에서 키를 `***`로 가린다.
- 약 8% 확률로 `<header><error><code value="003"/>…서비스 호출 중 오류…</error></header>`가 온다.
  같은 요청을 다시 부르면 정상. `_call_api`가 재시도한다.
- 필수 파라미터 누락·기간 초과는 `<RES><validErrorMsg value="…"/></RES>`로 온다
  (예: "조회기간은 1년을 초과 할 수 없습니다."). `SeibroAPIError("… 서버 오류: …")`로 올린다.
- 주식수량 변동내역 apiId는 `getStkIncdecDetails`다. 예전 표기 `getStkIncdceDetails`는 vector 없는 응답만 준다.

### 의무보호예수 (getSafeDpDutyDepoStatus)
- 조회기간은 양 끝 포함 365일 이하. `get_lockup_records()`가 365일 구간으로 나눠 부른다.
- 감자·액면분할·액면병합 뒤 예탁원은 기존 예수 기록을 반환 처리하지 않고 바뀐 수량으로 새로
  예수한다. 미반환 잔량을 그냥 더하면 같은 주식을 여러 번 센다. [희석 분석](../scenarios/combined/01_dilution.md)
- `TOTAL_STK_CNT`는 조회 시점의 발행주식총수다(예수 당시 값이 아님).

### 주식관련사채 행사가
- `getXrcStkStatInfo`와 웹 `exerInfoView`의 `XRC_PRICE`는 현재 행사가다. 감자·분할 뒤 행사 실적이 없는
  사채는 조정이 반영됐는지 이 데이터만으로 확인할 수 없다(예: 한울앤제주 12CB 18,540원).
- `stock_bond.get_stock_bonds()`의 `전환가능_주식수`(= 미상환잔액 ÷ 행사가)는 CB에만 맞다. BW는
  `get_stock_linked_bond_status()`의 `발행금액 − 누적행사금액`을 쓸 것. EB는 주식수를 늘리지 않는다.


- **배당내역상세(BIP_CNTS01043V)**: 서버 task(`EntrFnafInfoPTask`)가 **최신 4개 결산연도**를
  하드코딩 반환한다. `STD_YEAR`/`SETACC_YYMM` 등 연도 파라미터를 넣어도 무시되므로,
  이 API로는 5년 이전 과거 데이터를 조회할 수 없다. (과거치는 기간 입력을 받는 다른
  배당 페이지가 필요.)
- **배당 Open API(`getDivSchedulInfo`, `getDivInfo`) — 실측 확인된 서버 동작**
  - **3년 상한, 조용한 절단**: `BEGIN_STD_DT` 기준 3년까지만 반환하고 더 긴 구간을
    요청해도 에러 없이 잘린다. (예: 2015-01-01~2025-12-31 요청 → 2017-12-31까지만
    16건. 3년씩 쪼개 호출하면 80건.) `get_dividend_history()`가 자동 분할한다.
  - **전체 조회는 하루치만**: `getDivSchedulInfo`에서 `ISSUCO_CUSTNO`를 빼면
    기간이 무시되고 `BEGIN_STD_DT` 하루치만 나온다(2024-12-31 → 1,084건).
    시장 전체 스캔은 기준일 루프가 필요하다. `getDivInfo`는 고객번호가 필수라
    전체 조회 자체가 불가능하다.
  - **금액은 2003-06-30 기준일부터**: 그 이전은 `CASH_ALOC_AMT`(주당배당금)와
    `MARTP_DIV_RATE`(시가배당률)가 0이고 `CASH_ALOC_RATIO`(당시 액면 대비 %)만 있다.
    데이터 자체는 1987년까지 소급된다(삼성전자 기준).
  - **`PVAL`은 현재 액면가**: 과거 기준일 행에도 현재 액면가가 실린다(삼성전자
    2016년 행의 PVAL=100). `PVAL × CASH_ALOC_RATIO`로 배당금을 역산하면 액면분할
    이전 구간에서 틀린다. 주당배당금은 `CASH_ALOC_AMT`를 쓴다.
  - **`getDivInfo` 출력에 고객번호가 없다**: 일정과 조인하려면 요청에 쓴
    `ISSUCO_CUSTNO`를 직접 붙여야 한다.
  - **`getIssucoCustnoByIsin`은 없는 코드에 엉뚱한 회사를 돌려준다**: "000000" →
    에어로시스템·서울창업투자 2건. 유효 코드는 항상 1건이므로 1건이 아니면 실패
    처리한다(`get_issuco_custno()`가 검증).
  - **필수 파라미터 누락 시 `<vector>` 없는 응답**: `<SeibroAPI><RES/></SeibroAPI>`만
    온다. `SeibroAPIError`로 즉시 올리고 재시도하지 않는다.

## 이전 연구 자료

- 의무보유, 주총, 채권 발행·상환 조회는 위 공식 API 함수와 [시나리오](../scenarios/README.md)로 이어집니다.
- 공유자원포털의 `StockSvc/getSafeDpDutyDepoStatusN1`은 별도 서비스키를 쓰던 연구 예제입니다. 현재 패키지의 보호예수는 OpenPlatform의 `getSafeDpDutyDepoStatus`를 호출합니다.
- 예전 연구 노트북은 `2f96200` 시점의 Git 이력에서 확인할 수 있습니다. 기업정보 관련 원본 자료는 [가이드 엑셀](../resources/Guide_Corp%20%281%29.xlsx)에 있습니다.
