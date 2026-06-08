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

특징: 코드값 20여 종을 한글로 자동 디코딩(`CODE_TABLES`, `CREDIT_GRADE_MAP`), 전환가능주식수 자동 계산.

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
SEIBRO 웹 WebSquare (key X)   → 회사검색 · 권리기준일 · 무상증자 상세 · 배당내역상세
DART (별도 기관, key O)       → 사채 발행공시 이력 · 정기보고서 사채 테이블
```

## 참고: 알려진 제약

- **배당내역상세(BIP_CNTS01043V)**: 서버 task(`EntrFnafInfoPTask`)가 **최신 4개 결산연도**를
  하드코딩 반환한다. `STD_YEAR`/`SETACC_YYMM` 등 연도 파라미터를 넣어도 무시되므로,
  이 API로는 5년 이전 과거 데이터를 조회할 수 없다. (과거치는 기간 입력을 받는 다른
  배당 페이지가 필요.)
- `resources/`의 Colab 노트북(`seibro_mandatory`=의무보유, `seibro_shmeeting`=주주총회 등)은
  아직 패키지 함수로 승격되지 않은 영역의 연구 프로토타입이다.
