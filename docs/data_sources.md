# 데이터 소스 정리

`seibro_api` 패키지가 데이터를 끌어오는 경로를 **소스별로 구분**한 문서.
크게 세 갈래다.

1. **SEIBRO 공식 Open API** — 인증키(`SEIBRO_API_KEY`) 필요
2. **SEIBRO 웹 (WebSquare)** — 비공식, 인증키 불필요
3. **DART** — 별도 기관(전자공시), 인증키(`DART_API_KEY`) 필요

---

## 1. SEIBRO 공식 Open API (key O)

- 엔드포인트: `http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp`
- 인증: `.env`의 `SEIBRO_API_KEY`
- 구현: [`client.py`](../seibro_api/client.py) `SeibroClient._call_api()` (XML→DataFrame, 3회 재시도)

| apiId | 용도 | 호출 함수 |
|-------|------|----------|
| `getShotnByMart` | 시장별 전체 상장종목 명부(종목코드·종목명·고객번호) | `get_stock_registry()` |
| `getStkIncdceDetails` | 발행회사별 주식수량 변동내역(액면분할·무상증자 등) | `get_stock_issue_details()` |
| `getStkStatInfo` | 종목 기본정보(단축코드→ISIN·고객번호) | 내부 조회 |
| `getXrcStkStatInfo` | 종목에 연결된 주식관련사채(CB/BW/EB) 목록 | `get_stock_bonds()` |
| `getBondStatInfo` | 사채별 상세(미상환잔액·전환가·신용등급·옵션 등 31개 칼럼) | `get_stock_bonds()` |
| `getIssucoCustnoByIsin` | 종목코드 → 발행회사고객번호·대표종목명 | `SeibroClient.get_issuco_custno()` |
| `getDivSchedulInfo` | 배당일정(권리기준일·권리락일·명부폐쇄·확정구분), 금액 없음 | `SeibroClient.get_dividend_schedules()` |
| `getDivInfo` | 배당분배금내역(주당배당금·시가배당률·지급일·차등배당) | `SeibroClient.get_dividend_payouts()` |

특징: 코드값 20여 종을 한글로 자동 디코딩(`CODE_TABLES`, `CREDIT_GRADE_MAP`), 전환가능주식수 자동 계산.

배당 3종을 묶은 고수준 함수는 [`dividend_history.py`](../seibro_api/dividend_history.py)
`get_dividend_history()` / `get_market_dividend_schedules()`. 서버 제약(3년 상한)을
구간 분할로 우회한다. 상세는 아래 "알려진 제약" 참고.

---

## 2. SEIBRO 웹 — WebSquare 호출 (key X)

- 엔드포인트: `https://seibro.or.kr/websquare/engine/proworks/callServletService.jsp`
- 방식: XML POST(`<reqParam action=… task=…>`) + 브라우저 헤더(Referer/submissionid)
- 구현: [`schedule_reason.py`](../seibro_api/schedule_reason.py) `SeibroWebSquareClient`,
  [`dividend.py`](../seibro_api/dividend.py)

| action | 페이지(w2xPath) | 용도 | 호출 함수 |
|--------|-----------------|------|----------|
| `searchCompanyContentList` | BIP_CMUC01024P | 회사 검색(키 없이 종목→고객번호 해결) | 내부 조회 |
| `getRgtStdDtByConoList` | (사유별) | 사유별 권리기준일 드롭다운 목록 | `get_schedule_reason_details()` |
| `rissuBasicInfoViewEL1` 외 3종 | BIP_CNTS01026V | 무상증자(102) 기준일별 상세 | `get_bonus_issue_details()` |
| `entrDivResultsList` / `entrDivResultsList2` | BIP_CNTS01043V | 배당내역상세(보통주/우선주) | `get_dividend_details()` |
| `chgDetailsListEL1` | BIP_CNTS01012V | 발행주식수증감내역(개별) — 기간 조회 지원 | `get_issued_share_changes()` |

일정사유 19종(정기/임시총회·유무상증자·배당·액면분할·합병·분할·주식교환·매수청구 등)은
`SCHEDULE_REASONS`에 정의돼 있으나, **상세 조회가 구현된 것은 무상증자(102)뿐**이고
나머지는 기준일 목록만 반환한다.

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

## 2b. KSD KOFR 공시 — kofr.kr WebSquare (key X)

- 엔드포인트: `https://www.kofr.kr/websquare/engine/proworks/callServletService.jsp`
- 방식: 섹션 2와 동일한 WebSquare XML POST. 호스트만 다르다(`www.kofr.kr`, KSD의 KOFR 공시 사이트).
- 구현: [`kofr.py`](../seibro_api/kofr.py) `get_kofr_rates()` — 페이지네이션(`CURR_PAGE`) 자동 처리.

| action | task | 용도 | 호출 함수 |
|--------|------|------|----------|
| `getGridRateList` | `ksd.rfr.user.rate.process.RatePTask` | 기간별 KOFR 일별공시(금리·지수·30/90/180일 복리평균) | `get_kofr_rates()` |

KOFR = Korea Overnight Financing Repo rate. 국채·통안증권 담보 익일물 RP 거래에서 산출하는
무위험지표금리(RFR, LIBOR 대체 한국판)로 KSD가 산출·공시한다. 응답 필드: `RFR_PUBN_DT`(공시일자),
`RFR_PUBN_MR`(KOFR), `RFR_INDEX`(지수), `D30/D90/D180_AVG_MR`(복리평균).

---

## 3. DART (별도 기관)

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
SEIBRO 웹 WebSquare (key X)   → 회사검색 · 권리기준일 · 무상증자 상세 · 배당내역상세 · 발행주식수증감내역
KSD KOFR kofr.kr (key X)      → KOFR 무위험지표금리 일별공시(금리·지수·복리평균)
DART (별도 기관, key O)       → 사채 발행공시 이력 · 정기보고서 사채 테이블
```

## 참고: 알려진 제약

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
- `resources/`의 Colab 노트북(`seibro_mandatory`=의무보유, `seibro_shmeeting`=주주총회 등)은
  아직 패키지 함수로 승격되지 않은 영역의 연구 프로토타입이다.
