# 파생결합증권정보 Open API 명세

[엑셀 원본](originals/Guide_DerivCombi.xlsx) · [전체 API 색인](README.md)

엑셀 가이드와 포털 미리보기에서 대조한 API 7개를 담았습니다. 요청 예시의 키는 변수명으로 표시했습니다.

## 서비스 목록

| 서비스목록 | API명 | API ID | 상세기능 |
| --- | --- | --- | --- |
| 파생결합증권정보<br>(7) | 파생결합증권 발행내역 | [`getDerivCombiIssuInfo`](#getderivcombiissuinfo) | 발행일별 발행종목 조회 |
| 파생결합증권정보<br>(7) | 기초자산별 미상환규모 | [`getBassetUnredScale`](#getbassetunredscale) | 주요 기초자산(13개)별 미상환금액 정보 |
| 파생결합증권정보<br>(7) | 파생결합증권 종목 정보 | [`getDerivCombiIsinInfo`](#getderivcombiisininfo) | 파생결합증권 종목별 상세 정보 |
| 파생결합증권정보<br>(7) | 기초자산 정보조회 | [`getAssetInfo`](#getassetinfo) | 기초자산명, 기준가격 등 기초자산 정보 |
| 파생결합증권정보<br>(7) | 기초자산 행사정보조회 | [`getAssetXrcInfo`](#getassetxrcinfo) | 행사가격, 행사비율 등 기초자산 행사정보 |
| 파생결합증권정보<br>(7) | 파생결합증권 상환조건조회 | [`getRedCondiInfo`](#getredcondiinfo) | 평가일, 상환조건 등 상환 관련 정보 |
| 파생결합증권정보<br>(7) | 파생결합증권 상환종목조회 | [`getRedIsinInfo`](#getredisininfo) | 상환일별 상환종목 정보조회 |

## 작성 이력

| 버전 | 등록일 | 주요내용 |
| --- | --- | --- |
| ver.1 | 2018-09-03 | 7개 API 등록 |
| ver.2 | 2024-05-29 | ㅇ 컬럼 목록 및 내용 현행화 |

## `getDerivCombiIssuInfo`

**파생결합증권 발행내역** · 원본 시트 `파생_파생결합증권 발행내역`

발행일별 발행종목정보

- 엑셀 URL 예시에만 표시된 파라미터 `SECN_TPCD`

포털 미리보기 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getDerivCombiIssuInfo&params=ISSU_DT:20180702,SECN_KACD:4101
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행일자 | ISSU_DT | VARCHAR2(8) | 20180702 | 종목을 발행한 일자 | 필수 |
| 2 | 종목구분코드 | SECN_KACD | CHAR(2) | 4101 | 4101:ELS<br>4102:ELB<br>4301:DLS<br>4302:DLB | 필수 |

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 종목코드 | ISIN | VARCHAR2(12) | KR6723301877 | 종목표준코드 |  |
| 2 | 한글종목명 | KOR_SECN_NM | VARCHAR2(100) | IBK투자증권2167(사모/ELS) | 종목에 부여된 한글 종목명 |  |
| 3 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 14138 | 예탁결제원이 부여한 고객번호 |  |

## `getBassetUnredScale`

**기초자산별 미상환규모** · 원본 시트 `파생_기초자산별 미상환규모`

주요 기초자산(13개)별 미상환금액 정보

원본 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getBassetUnredScale&params=STD_DT:20180731,STND_BASSET_CD:KSD020000101,SECN_TPCD:41
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 기준일자 | STD_DT | VARCHAR2(12) | 20180731 | 기준일 | 필수 |
| 2 | 기초자산코드 | STND_BASSET_CD | VARCHAR2(12) | KSD020000101 | KSD090000101 Brent<br>KSD090000201 WTI<br>KSD100000101 금<br>KSD100000201 은<br>KSD010000101 KOSPI 200<br>KSD020000101 EURO STOXX 50<br>KSD020000201 HSCEI(항셍H)<br>KSD020000301 S&amp;P 500<br>KSD020000401 FTSE 100<br>KSD020000501 NIKKEI 225<br>KSD020000601 DOW JONES<br>KSD020000901 DAX<br>KSD020001901 HSI | 필수 |
| 3 | 종목구분코드 | SECN_TPCD | CHAR(2) | 41 | [41]ELS  [43]DLS | 필수 |

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 기초자산내용 | BASSET_CONTENT | VARCHAR2(500) | EURO STOXX 50 | 기초자산 명 |  |
| 2 | 미상환종목수 | UNRED_SECNCNT | NUMBER(8) | 24504 | 미상환 종목의 수 |  |
| 3 | 미상환잔액 | UNRED_REMA | NUMBER(18,2) | 30982035962863 | 미상환 종목의 미상환잔액 합계(원화 환산) |  |

## `getDerivCombiIsinInfo`

**파생결합증권 종목 정보** · 원본 시트 `파생_파생결합증권_종목정보`

파생결합증권 종목별 상세 정보

- 목록 ID `getDerivCombiIssuInfo`

- 연속 순회 중 직전에 테스트한 `getBassetUnredScale`의 호출변수가 URL에 남아 0건이었습니다. 파생결합증권정보 메뉴를 새로고침한 뒤 이 API를 먼저 TEST하니 아래 예시의 `ISIN:KR6539335879`로 1건을 반환했습니다. 같은 종목코드의 HTTPS 응답에서도 1건과 출력 필드 20개를 확인했습니다.

원본 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getDerivCombiIsinInfo&params=ISIN:KR6539335879
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 종목번호 | ISIN | VARCHAR2(12) | KR6539335879 | 종목 표준코드 | 필수 |

### 출력 필드

포털 TEST의 XML 레코드 경로는 `vector/data/RESULT`입니다. HTTPS 응답에서는 `SeibroAPI` 안에 이 경로가 있습니다.

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 한글종목명 | KOR_SECN_NM | VARCHAR2(100) | 삼성증권19449(사모/ELS) | 한글종목명 |  |
| 2 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 1636 | 예탁결제원이 부여한 고객번호 |  |
| 3 | 종목구분명 | SECN_KANM |  | ELS | ELS<br>ELB<br>ELW<br>DLS<br>DLB<br>ETN |  |
| 4 | 발행통화코드 | ISSU_CUR_CD | CHAR(3) | KRW | 발행국가의 통화코드 |  |
| 5 | 모집방법코드 | RECU_WHCD | CHAR(2) | 21 | 11:공모  21:사모 |  |
| 6 | 최초발행수량 | FIRST_ISSU_QTY | NUMBER(18,2) | 132000000 | 파생결합증권의 최초발행수량 |  |
| 7 | 발행잔량 | ISSU_REMQ | NUMBER(18,2) | 132000000 | 파생결합증권의 발행잔량 |  |
| 8 | 납입금액비율 | PAYIN_AMT_RATIO | NUMBER(13,10) | 98.5 | 파생결합증권의 납입금액비율 |  |
| 9 | 납입금액 | PAYIN_AMT | NUMBER(18,2) | 130020000 | 파생결합증권의 납입금액 |  |
| 10 | 발행일자 | ISSU_DT | VARCHAR2(8) | 20180702 | 종목을 발행한 일자를 관리한다 |  |
| 11 | 계약일자 | CONT_DT | VARCHAR2(8) | 20180629 | 파생결합증권의 계약일자 |  |
| 12 | 만기일자 | XPIR_DT | VARCHAR2(8) | 20210702 | 종목의 만기일자(CD/어음인 경우 상환일자) |  |
| 13 | 중도상환가능여부 | MIDRED_POSS_YN | CHAR(1) | Y | Y:가능 N:불가 |  |
| 14 | 상환일자 | RED_DT | VARCHAR2(8) |  | 실제 상환일자 |  |
| 15 | 파생증권권리행사구분코드 | DERISEC_EXER_TPCD | CHAR(1) |  | 2 만기상환<br>3 조기상환<br>* 실제 상환일자(RED_DT)가 있는 경우 표기 | * 실제 상환일자(RED_DT)가 있는 경우 |
| 16 | 원금보전구분코드 | PRCP_PRSV_TPCD | CHAR(1) | 3 | [1]원금보장형(100%이상)<br>[2]부분보장형(100%미만)<br>[3]원금비보장형<br>[4]기타<br>[9]해당없음 |  |
| 17 | 원금보전율 | PRCP_PRSV_RATE | NUMBER(6,3) | 0 | 파생결합증권의 원금보전율 |  |
| 18 | 담보설정구분코드 | COLAT_SETUP_TPCD | CHAR(1) | 2 | [1]설정 [2]미설정 |  |
| 19 | 기초자산 개수 | BASSET_CNT | CHAR(1) | 3 | 포함 기초자산 개수 |  |
| 20 | 월지급여부 | MM_PAY_YN | CHAR(1) | N | 월지급여부 |  |

## `getAssetInfo`

**기초자산 정보조회** · 원본 시트 `파생_기초자산정보`

기초자산명, 기준가격 등 기초자산 정보

- 포털 TEST와 HTTPS XML에서 출력 필드 `ISIN`을 확인했습니다.

원본 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getAssetInfo&params=ISIN:KR6539335879
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 종목번호 | ISIN | VARCHAR2(12) | KR6539335879 | 종목표준코드 | 필수 |

### 출력 필드

포털 TEST의 XML 레코드 경로는 `vector/data/RESULT`입니다. HTTPS 응답에서는 `SeibroAPI` 안에 이 경로가 있습니다.

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 종목번호 | ISIN |  |  |  | 실제 응답에서 확인 |
| 2 | 자산일련번호 | ASSET_SEQ | NUMBER(4) | 1 | 파생결합증권기초자산의 일련번호 |  |
| 3 | 표준기초자산코드 | STND_BASSET_CD | VARCHAR2(12) | KSD310000306 | 기초자산 표준코드 |  |
| 4 | 표준기초자산명 | STND_BASSET_NM | VARCHAR2(200) | Hang Seng China Enterprises Index | 파생결합증권의 기초자산 내용 |  |
| 5 | 행사기준가 | XRC_STDPRC | NUMBER(26,10) | 11073 | 파생결합증권 기초자산의 기준가격 |  |
| 6 | 행사정지하한비율 | XRC_STOP_LOLMT_RATIO | NUMBER(6,3) | 55 | 파생결합증권 기초자산의 행사정지하한비율 |  |
| 7 | 행사정지하한가격 | XRC_STOP_LOLMT_PRICE | NUMBER(26,10) | 6090.15 | 파생결합증권 기초자산의 행사정지하한가격 |  |
| 8 | 행사정지상한비율 | XRC_STOP_UPLMT_RATIO | NUMBER(6,3) | 0 | 파생결합증권 기초자산의 행사정지상한비율 |  |
| 9 | 행사정지상한가격 | XRC_STOP_UPLMT_PRICE | NUMBER(26,10) | 0 | 파생결합증권 기초자산의 행사정지상한가격 |  |
| 10 | 기초자산최초평가구분코드 | BASSET_FIRST_VALAT_TPCD | CHAR(1) | 1 | 1:종가<br>2:산술평균<br>3:장중가<br>9:기타 |  |
| 11 | 기초자산최종평가구분코드 | BASSET_LAST_VALAT_TPCD | CHAR(1) | 1 | 1:종가<br>2:산술평균<br>3:장중가<br>9:기타 |  |
| 12 | 최초기준가결정시작일자 | FIRST_STDPRC_DECSN_BEGIN_DT | VARCHAR2(8) | 20180629 | 파생결합증권의 최초기준가격결정시작일자 |  |
| 13 | 최초기준가결정종료일자 | FIRST_STDPRC_DECSN_EXPRY_DT | VARCHAR2(8) | 20180629 | 파생결합증권의 최초기준가격결정종료일자 |  |
| 14 | 최종기준가결정시작일자 | LAST_STDPRC_DECSN_BEGIN_DT | VARCHAR2(8) | 20210629 | 파생결합증권의 최종기준가격결정시작일자 |  |
| 15 | 최종기준가결정종료일자 | LAST_STDPRC_DECSN_EXPRY_DT | VARCHAR2(8) | 20210629 | 파생결합증권의 최종기준가격결정종료일자 |  |
| 16 | 절상절사구분코드 | RVLT_SEVER_TPCD | CHAR(1) | 2 | [1]올림<br>[2]버림<br>[3]반올림<br>[9]해당없음 |  |

## `getAssetXrcInfo`

**기초자산 행사정보조회** · 원본 시트 `파생_기초자산행사정보`

행사가격, 행사비율 등 기초자산 행사정보

원본 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getAssetXrcInfo&params=ISIN:KR6673301885
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 종목번호 | ISIN | VARCHAR2(12) | KR6673301885 | 종목표준코드 | 필수 |

### 출력 필드

포털 TEST의 XML 레코드 경로는 `vector/data/RESULT`입니다. HTTPS 응답에서는 `SeibroAPI` 안에 이 경로가 있습니다.

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 자산일련번호 | ASSET_SEQ | NUMBER(4) | 1 | 파생결합증권기초자산의 일련번호 | getAssetInfo |
| 2 | 행사기준일련번호 | XRC_STD_SEQ | NUMBER(4) | 1 | 자산종목번호별 행사기준비율에 따라 순차적으로 부여한 번호 |  |
| 3 | 행사기준비율 | XRC_STD_RATIO | NUMBER(6,3) | 100 | 기초자산 행사기준가에 대한 행사기준비율(%) |  |
| 4 | 행사가격 | XRC_PRICE | NUMBER(26,10) | 278.83 | 파생결합증권 기초자산 행사가격 |  |

## `getRedCondiInfo`

**파생결합증권 상환조건조회** · 원본 시트 `파생_상환조건정보`

평가일, 상환조건 등 상환 관련 정보

원본 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getRedCondiInfo&params=ISIN:KR6673301885
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 종목번호 | ISIN | VARCHAR2(12) | KR6673301885 | 종목표준코드 | 필수 |

### 출력 필드

포털 TEST의 XML 레코드 경로는 `vector/data/RESULT`입니다. HTTPS 응답에서는 `SeibroAPI` 안에 이 경로가 있습니다.

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 상환조건구분코드 | RED_CONDI_TPCD | CHAR(1) | 1 | [1]중간평가<br>[2]만기상환 |  |
| 2 | 평가횟수일련번호 | VALAT_NTIMES_SEQ | NUMBER(4) | 1 | 상환조건구분 중간평가인 경우, 중간평가횟수 저장<br>상환조건구분 상환지급조건인 경우, 일련번호 저장 |  |
| 3 | 중간평가지급일자 | MID_VALAT_PAY_DT | VARCHAR2(8) | 20181206 | 파생결합증권중간평가에 대한 중간평가지급일자 |  |
| 4 | 중간평가시작일자 | MID_VALAT_BEGIN_DT | VARCHAR2(8) | 20181203 | 파생결합증권중간평가에 대한 중간평가시작일자 |  |
| 5 | 중간평가종료일자 | MID_VALAT_EXPRY_DT | VARCHAR2(8) | 20181203 | 파생결합증권중간평가에 대한 중간평가종료일자 |  |
| 6 | 상환조건내용 | RED_CONDI_CONTENT | VARCHAR2(1000) | 최초기준가격의 95%이상인 경우 | 중간평가 또는 만기상환지급 시 조건을 저장<br>(예: 기준종목 1차 중간가격 &gt; (최초기준가격 * 80%) 등..) |  |
| 7 | 상환계산식내용 | RED_FORMULA_CONTENT | VARCHAR2(1000) | 액면금액의 101.79% | 상환 시 지급 금액 계산을 위한 산출식을 저장<br>(예: 액면금액 * (100% + 10.6 * 1) 등..) |  |

## `getRedIsinInfo`

**파생결합증권 상환종목조회** · 원본 시트 `파생_상환종목정보 `

상환일별 상환종목 정보조회

- 엑셀 URL 예시에만 표시된 파라미터 `SECN_TPCD`

- 아래 호출변수로 포털 TEST와 HTTPS에서 각각 12건을 확인했습니다. 재확인 중 직전에 테스트한 `getRedCondiInfo`의 `ISIN`이 URL에 남았을 때는 0건을 반환했습니다.

포털 미리보기 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getRedIsinInfo&params=RED_DT:20180806,SECN_KACD:4101,DERISEC_EXER_TPCD:3
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 | 비고 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 상환일 | RED_DT | VARCHAR2(8) | 20180806 | 상환일자 | 필수 |  |
| 2 | 종목종류코드 | SECN_KACD | CHAR(2) | 4101 | 4101:ELS<br>4102:ELB<br>4301:DLS<br>4302:DLB | 필수 |  |
| 3 | 파생증권권리행사구분코드 | DERISEC_EXER_TPCD | CHAR(1) | 3 | 2 만기상환<br>3 조기상환 | 선택 |  |

### 출력 필드

포털 TEST의 XML 레코드 경로는 `vector/data/RESULT`입니다. HTTPS 응답에서는 `SeibroAPI` 안에 이 경로가 있습니다.

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 종목번호 | ISIN | VARCHAR2(12) | KR6552327845 | 종목표준코드 |  |
| 2 | 파생증권권리행사구분코드 | DERISEC_EXER_TPCD | CHAR(1) | 3 | 2 만기상환<br>3 조기상환 |  |
| 3 | 상환수량 | RED_QTY | NUMBER(16) | 132000000 | 상환수량 |  |
