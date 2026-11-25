# 채권정보 Open API 명세

[엑셀 원본](originals/Guide_Bond.xlsx) · [전체 API 색인](README.md)

엑셀 가이드와 포털 미리보기에서 대조한 API 8개를 담았습니다. 요청 예시의 키는 변수명으로 표시했습니다.

## 서비스 목록

| 서비스목록 | API 명 | API ID | 상세기능 |
| --- | --- | --- | --- |
| 채권정보<br>(8) | 채권 발행내역 | [`getBondIssuInfo`](#getbondissuinfo) | 발행일별 또는 발행회사별 발행종목 조회 |
| 채권정보<br>(8) | 채권 종목 정보 | [`getBondStatInfo`](#getbondstatinfo) | 채권 종목별 상세 정보 |
| 채권정보<br>(8) | 이자지급 정보 | [`getIntPayInfo`](#getintpayinfo) | 채권 종목별 이자지급 정보 |
| 채권정보<br>(8) | 조기상환 정보 | [`getBondOptionXrcInfo`](#getbondoptionxrcinfo) | Call/Put 옵션 행사에 따른 조기상환 정보 |
| 채권정보<br>(8) | 단기금융증권 발행내역 | [`getShortmIssuInfo`](#getshortmissuinfo) | 발행일별 발행종목 조회 |
| 채권정보<br>(8) | CD 종목 정보 | [`getCDInfo`](#getcdinfo) | CD 종목별 상세 정보 |
| 채권정보<br>(8) | CP 종목 정보 | [`getCPInfo`](#getcpinfo) | CP 종목별 상세 정보 |
| 채권정보<br>(8) | 전자단기사채 종목 정보 | [`getESTBInfo`](#getestbinfo) | 전자단기사채 종목별 상세 정보 |

## 작성 이력

| 버전 | 등록일 | 주요내용 |
| --- | --- | --- |
| ver.1 | 2018-09-03 | 9개 API 등록 |
| ver.2 | 2018-10-26 | ㅇ 신용등급 정보제공 방식 변경 <br>  - 종목별 신용등급 정보(getBondCreditRtInfo) API를 삭제하고, <br>채권/CP/전단채 종목 정보 내에 신용평가사별 신용등급(본평가) 컬럼을 추가 |
| ver.3 | 2024-05-29 | ㅇ 채권종목정보<br> - 전자증권여부, 권리행사주체, 이자산정방식 추가<br>ㅇ CD정보<br> - 전자증권여부 추가 |

## `getBondIssuInfo`

**채권 발행내역** · 원본 시트 `1_채권_채권발행내역`

발행일별/발행회사별 발행종목 조회

| 항목 | 내용 |
| --- | --- |
| 참고사항 | 회사채, 주식관련사채 정보 제공 |

- 상세 시트 ID `getBondIssuinfo`

원본 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getBondIssuInfo&params=ISSU_DT:20180803,ISSUCO_CUSTNO:29998
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행일자 | ISSU_DT | VARCHAR2(8) | 20180803 | 종목을 발행한 일자 | 필수선택 |
| 2 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 29998 | 예탁결제원이 부여한 고객번호 | 필수선택 |

> * 필수선택 값은 하나 이상 입력

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행일자 | ISSU_DT | VARCHAR2(8) | 20180803 | 종목을 발행한 일자 |  |
| 2 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 29998 | 예탁결제원이 부여한 고객번호 |  |
| 3 | 발행회사 명칭 | ISSUCO_CUST_NM | VARCHAR2(100) | 에스케이해운 | 발행회사 명칭 |  |
| 4 | 종목코드 | ISIN | VARCHAR2(12) | KR6268761881 | 종목표준코드 |  |
| 5 | 한글종목명 | KOR_SECN_NM | VARCHAR2(100) | SK해운61 | 종목에 부여된 한글 종목명 |  |

## `getBondStatInfo`

**채권 종목 정보** · 원본 시트 `2_채권_채권종목정보`

채권 종목별 상세 정보

| 항목 | 내용 |
| --- | --- |
| 참고사항 | 회사채, 주식관련사채 정보 제공 |

원본 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getBondStatInfo&params=ISIN:KR6268761881
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 종목코드 | ISIN | VARCHAR2(12) | KR6268761881 | 표준종목코드 | 필수 |

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 |  | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행사 번호 | ISSUCO_CUSTNO | NUMBER(10) | 29998 | 예탁결제원이 부여한 고객번호 |  |
| 2 | 한글종목명 | KOR_SECN_NM | VARCHAR2(100) | SK해운 61 | 종목에 부여된 한글 종목명 |  |
| 3 | 종목종류코드 | SECN_KACD | CHAR(4) | 1108 | [1108]일반회사채 |  |
| 4 | 발행일자 | ISSU_DT | VARCHAR2(8) | 20180803 | 종목을 발행한 일자 |  |
| 5 | 만기일자 | XPIR_DT | VARCHAR2(8) | 20200203 | 종목 만기 일자 |  |
| 6 | 발행통화코드 | ISSU_CUR_CD | CHAR(3) | KRW | 발행국가의 통화코드 |  |
| 7 | 발행금액 | FIRST_ISSU_AMT | NUMBER(20,4) | 126000000000 | 채권에 대한 최초발행금액 |  |
| 8 | 발행잔액 | ISSU_REMA | NUMBER(18,2) | 126000000000 | 채권 발행잔량 |  |
| 9 | 납입금액 | PAYIN_AMT | NUMBER(18,2) | 126000000000 | 채권에 대한 납입금액 |  |
| 10 | 표면이자율 | COUPON_RATE | NUMBER(13,10) | 4.485 | 채권에 대한 표면이율 |  |
| 11 | 만기상환율 | XPIRED_RATE | NUMBER(14,10) | 100 | 채권에 대한 만기 상환비율 |  |
| 12 | 모집방법코드 | RECU_WHCD | CHAR(2) | 11 | 11:공모<br>12:사모<br>13:일반(국채,지방채,특수채)<br>14:CBO기초사모<br>21:매출 |  |
| 13 | 발행방법코드 | ISSU_WHCD | CHAR(1) | 2 | [1]실물발행<br>[2]전액등록<br>[3]부분등록<br>[4]청약증거금영수증발행<br>[5]전액불소지<br>[6]부분불소지 |  |
| 14 | 특이채권종류구분코드 | PARTICUL_BOND_KIND_TPCD | CHAR(1) | 9 | 1:전환<br>2:교환<br>3:신주인수권<br>4:분리형신주인수권<br>6:이익참가<br>9:해당없음 |  |
| 15 | 옵션구분코드 | OPTION_TPCD | CHAR(4) | 0 | [9401]CALL<br>[9402]PUT<br>[9403]CALL+PUT<br>[9404]NOTE<br>[0000]옵션해당없음 |  |
| 16 | 강제조기상환여부 | FORC_ERLY_RED_YN | CHAR(1) | N | Y:YES<br>N:NO |  |
| 17 | 금리변동구분코드 | MR_CHG_TPCD | CHAR(1) | 1 | [1]고정<br>[2]변동<br>[3]고정+변동 |  |
| 18 | 등록기관구분코드 | REGI_ORG_TPCD | CHAR(2) | 1 | 1:KSD |  |
| 19 | 보증구분코드 | GRTY_TPCD | CHAR(1) | 2 | [1]보증<br>[2]무보증<br>[3]담보부<br>[4]일반 |  |
| 20 | 기명구분코드 | SIGNA_TPCD | CHAR(1) | 2 | [1]기명<br>[2]무기명<br>[3]기명+무기명 |  |
| 21 | 순위구분코드 | RANK_TPCD | CHAR(1) | 1 | [1]선순위<br>[2]후순위<br>[3]중순위<br>[9]해당없음 |  |
| 22 | 이자지급방법구분코드 | INT_PAY_WAY_TPCD | CHAR(1) | 1 | 1:이표<br>2:할인<br>3:복리<br>4:단리 |  |
| 23 | 단리복리구분코드 | SINT_CINT_TPCD | CHAR(1) | 1 | 1:단리<br>2:복리<br>3:단리+복리 |  |
| 24 | 이자율변동구분코드 | IRATE_CHG_TPCD | CHAR(1) | 1 | [1]이율동일<br>[2]이율상이<br>[3]비정형 |  |
| 25 | 만기보장수익율 | XPIR_GUAR_PRATE | NUMBER(13,10) | 0 | 채권에 대한 만기보장수익율 |  |
| 26 | 만기보장수익율구분코드 | XPIR_GUAR_PRATE_TPCD | CHAR(2) | 99 | [01]연복리<br>[02]3개월복리<br>[03]6개월복리<br>[04]연단리<br>[05]1개월복리<br>[99]해당없음 |  |
| 27 | 원금상환방법코드 | PRCP_RED_WHCD | CHAR(2) | 11 | 11:만기상환<br>21:중도상환<br>31:조기상환<br>41:이익분배<br>51:자동상환<br>14:수시상환<br>12:균등분할상환<br>13:불균등분할상환 |  |
| 28 | 상장일 | APLI_DT | VARCHAR2(8) |  | 종목상장 적용일자(상장일) |  |
| 29 | 상장폐지일자 | DLIST_DT | VARCHAR2(8) |  | 종목상장의 폐지일자 |  |
| 30 | KIS평가등급코드 | KIS_VALAT_GRD_CD | CHAR(3) | 133 | [110]AAA<br>[111]AAA+<br>[112]AAA0(A1)<br>[113]AAA-<br>[120]AA<br>[121]AA+(A2+)<br>[122]AA0(A2)<br>[123]AA-(A2-)<br>[130]A<br>[131]A+(A3+)<br>[132]A0(A3)<br>[133]A-(A3-)<br>[210]BBB<br>[211]BBB+<br>[212]BBB0<br>[213]BBB-<br>[220]BB<br>[221]BB+<br>[222]BB0<br>[223]BB-<br>[230]B<br>[231]B+<br>[232]B0(B)<br>[233]B-<br>[310]CCC<br>[311]CCC+<br>[312]CCC0<br>[313]CCC-<br>[320]CC<br>[321]CC+<br>[322]CC0<br>[323]CC-<br>[330]C<br>[331]C+<br>[332]C0<br>[333]C-<br>[440]D<br>[900]유보<br>[999]취소 | 발행당시 <br>신용등급 |
| 31 | NICE평가등급코드 | NICE_VALAT_GRD_CD | CHAR(3) |  |  |  |
| 32 | 서울신용평가등급코드 | SCI_VALAT_GRD_CD | CHAR(3) |  |  |  |
| 33 | 한국기업평가등급코드 | KR_VALAT_GRD_CD | CHAR(3) | 133 |  |  |
| 34 | 전자증권여부 | ELTSC_YN | CHAR(1) | N | [Y]전자증권<br>[N]예탁증권 |  |
| 35 | 권리행사주체 | EXER_MBODY_TPCD | CHAR(1) | 1 | 1:KSD<br>2:자체 |  |
| 36 | 이자산정방식 | INT_ESTM_MANN_TPCD | CHAR(1) | 1 | 1:정형<br>2:비정형<br>3:해당없음 |  |

## `getIntPayInfo`

**이자지급 정보** · 원본 시트 `3_채권_이자지급정보 `

채권 종목별 이자지급 정보

| 항목 | 내용 |
| --- | --- |
| 참고사항 | 회사채, 주식관련사채 정보 제공 |

포털 미리보기 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getIntPayInfo&params=ISIN:KR6017812G82
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 종목코드 | ISIN | VARCHAR2(12) | KR6017812G82 | 표준종목코드 | 필수 |

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 표면이자율 | COUPON_RATE | NUMBER(13,10) | 0 | 채권에 대한 표면이율 |  |
| 2 | 이자지급방법구분코드 | INT_PAY_WAY_TPCD | CHAR(1) | 1 | 1:이표<br>2:할인<br>3:복리<br>4:단리 |  |
| 3 | 이자지급주기기간수 | INT_PAY_CYCLE_TERMS | NUMBER(6) | 3 | 채권에 대한 이자지급주기 |  |
| 4 | 이자지급주기구분코드 | INT_PAY_CYCLE_TPCD | CHAR(2) | 23 | [23]개월<br>[24]분기<br>[25]반기<br>[26]년<br>[99]기타 |  |
| 5 | 절상절사구분코드 | RVLT_SEVER_TPCD | CHAR(1) | 2 | [1]올림<br>[2]버림<br>[3]반올림<br>[9]해당없음 |  |
| 6 | 경과이자지급여부 | ACRINT_PAY_YN | CHAR(1) | N | Y:지급 N:미지급 |  |
| 7 | 은행휴무일이자지급일구분코드 | BANK_HOLIDAY_INT_PAYDD_TPCD | CHAR(1) | 2 | 1:직전영업일<br>2:직후영업일<br>3:해당일 |  |
| 8 | 이자지급시기구분코드 | INT_PAY_TIMS_TPCD | CHAR(2) | 01 | [01]후급<br>[02]선급<br>[03]상환시<br>[04]발행시 |  |
| 9 | 직전이표일 | BEFORE_DATE | VARCHAR2(8) |  | 직전 이자지급일 |  |
| 10 | 차기이표일 | AFTER_DATE | VARCHAR2(8) | 20181110 | 차기 이자지급일 |  |

## `getBondOptionXrcInfo`

**조기상환 정보** · 원본 시트 `4_채권_조기상환정보`

콜/풋 옵션 행사에 따른 조기상환 내역

| 항목 | 내용 |
| --- | --- |
| 참고사항 | 회사채, 주식관련사채 정보 제공 |

원본 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getBondOptionXrcInfo&params=ISIN:KR6225693573,ERLY_RED_DT:20180824
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 종목코드 | ISIN | VARCHAR2(12) | KR6225693573 | 표준종목코드 | 필수선택 |
| 2 | 조기상환일 | ERLY_RED_DT | VARCHAR2(8) | 20180824 | 조기상환일 | 필수선택 |

> * 필수선택 값은 하나 이상 입력

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 종목코드 | ISIN | VARCHAR2(12) | KR6225693573 | 표준종목코드 |  |
| 2 | 한글종목명 | KOR_SECN_NM | VARCHAR2(100) | 제이티캐피탈제일차유동화전문 | 종목에 부여된 한글 종목명 |  |
| 3 | 행사시작일 | XRC_BEGIN_DT | VARCHAR2(8) |  | 조기상환 행사 시작일자 |  |
| 4 | 행사종료일 | XRC_EXPRY_DT | VARCHAR2(8) |  | 조기상환 행사 종료일자 |  |
| 5 | 조기상환일 | ERLY_RED_DT | VARCHAR2(8) | 20180824 | 조기상환일 |  |
| 6 | 옵션구분코드 | OPTION_TPCD | CHAR(2) | 9401 | 9401: CALL / 9402: PUT<br>9403: CALL+PUT |  |
| 7 | 적용이자율 | APLI_IRATE | NUMBER(13,10) | 3.75 | 적용이자율 |  |
| 8 | 조기상환금액 | ERLY_REDAMT_VAL | NUMBER(18,2) | 2000000000 | 조기상환금액 |  |
| 9 | 이자지급금액 | INT_PAY_AMT | NUMBER(18,2) | 117842465 | 이자지급금액 |  |
| 10 | 최근발행잔액 | ISSU_REMA | NUMBER(18,2) | 35000000000 | 채권 발행잔량 |  |
| 11 | 행사비율 | XRC_RATIO | NUMBER(13,10) | 3.08 | 행사비율 |  |

## `getShortmIssuInfo`

**단기금융증권 발행내역** · 원본 시트 `5_채권_단기금융증권발행내역`

발행일별 발행종목 조회

| 항목 | 내용 |
| --- | --- |
| 참고사항 | CD/CP/전자단기사채 정보 제공 |

원본 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getShortmIssuInfo&params=ISSU_DT:20180801,SECN_TPCD:12
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행일자 | ISSU_DT | VARCHAR2(8) | 20180801 | 종목을 발행한 일자 | 필수 |
| 2 | 종목구분코드 | SECN_TPCD | CHAR(2) | 12 | [12]어음<br>[13]CD<br>[14]전자단기사채 | 필수 |

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 종목코드 | ISIN | VARCHAR2(12) | KRZF01270188 | 종목표준코드 |  |
| 2 | 한글종목명 | KOR_SECN_NM | VARCHAR2(100) | 리드코프 20180801-364-1 | 종목에 부여된 한글 종목명 |  |
| 3 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 1270 | 예탁결제원이 부여한 고객번호 |  |
| 4 | 발행회사 명칭 | ISSUCO_CUST_NM | VARCHAR2(100) | 리드코프 | 발행회사 명칭 |  |

## `getCDInfo`

**CD 종목 정보** · 원본 시트 `6_채권_CD정보`

CD 종목별 상세 정보

- 목록 ID `getCDinfo`

포털 미리보기 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getCDInfo&params=ISIN:KRZE03901G8S
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 종목코드 | ISIN | VARCHAR2(12) | KRZE03901G8S | 종목코드 | 필수 |

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행사 번호 | ISSUCO_CUSTNO | NUMBER(10) | 29210 | 예탁결제원이 부여한 고객번호 |  |
| 2 | 한글종목명 | KOR_SECN_NM | VARCHAR2(100) | 수협은행 여의도종합금융본부 20240328-183-1 | 종목에 부여된 한글 종목명 |  |
| 3 | 발행통화코드 | ISSU_CUR_CD | CHAR(3) | KRW | 발행국가의 통화코드 |  |
| 4 | 발행금액 | FIRST_ISSU_AMT | NUMBER(20,4) | 200000000000 | CD에 대한 최초발행금액 |  |
| 5 | 발행방법코드 | ISSU_WHCD | CHAR(1) | 2 | [1]실물발행<br>[2]전액등록<br>[3]부분등록<br>[4]청약증거금영수증발행<br>[5]전액불소지<br>[6]부분불소지 |  |
| 6 | 액면금액 | FACE_AMT | NUMBER(16) | 10000000000 | CD에 해당하는 액면가 |  |
| 7 | 매출금액 | SALE_AMT | NUMBER(18,2) | 9822214247 | CD에 해당하는 매출액 |  |
| 8 | 할인율 | DISCN_RATE |  | 3.546 | CD에 해당하는 할인율 |  |
| 9 | 이자지급방식구분코드 | INT_PAY_MANN_TPCD | CHAR(1) | 1 | [1]할인식<br>[2]부리식 |  |
| 10 | 발행일자 | ISSU_DT | VARCHAR2(8) | 20240328 | 종목을 발행한 일자 |  |
| 11 | 만기일자 | XPIR_DT | VARCHAR2(8) | 20240927 | 종목의 만기일자(CD의 상환일자) |  |
| 12 | 전자증권 여부 | ELTSC_YN | CHAR(1) | Y | [Y]전자증권<br>[N]예탁증권 |  |

## `getCPInfo`

**CP 종목 정보** · 원본 시트 `7_채권_CP정보`

CP 종목별 상세 정보

- 목록 ID `getCPinfo`

- 연속 순회 중 직전에 테스트한 CD 종목코드 `KRZE03901G8S`가 URL에 남아 0건이었습니다. 채권정보 메뉴를 새로고침한 뒤 이 API를 먼저 TEST하니 아래 예시의 `ISIN:KRZF30300A87`로 1건을 반환했습니다. 같은 종목코드의 HTTPS 응답에서도 1건과 출력 필드 20개를 확인했습니다.

원본 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getCPInfo&params=ISIN:KRZF30300A87
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 종목코드 | ISIN | VARCHAR2(12) | KRZF30300A87 | 종목코드 | 필수 |

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행사 번호 | ISSUCO_CUSTNO | NUMBER(10) | 33427 | 예탁결제원이 부여한 고객번호 |  |
| 2 | 한글종목명 | KOR_SECN_NM | VARCHAR2(100) | 윈케이제구차 20180702-364-10 | 종목에 부여된 한글 종목명 |  |
| 3 | 발행통화코드 | ISSU_CUR_CD | CHAR(3) | KRW | 발행국가의 통화코드 |  |
| 4 | 발행금액 | ISSU_AMT | NUMBER(20,4) | 5000000000 | CP에 대한 최초발행금액 |  |
| 5 | 종목종류코드 | SECN_KACD | CHAR(4) | 1204 | [1201]일반기업어음<br>[1202]유동화회사ABCP<br>[1203]Standalone유한ABCP<br>[1204]Conduit주식ABCP |  |
| 6 | 어음분류코드 | BILL_CACD | CHAR(1) | 1 | [1]기업어음<br>[2]상업어음<br>[3]무역어음<br>[4]표지어음<br>[5]자발어음 |  |
| 7 | 발행방법코드 | ISSU_WHCD | CHAR(1) | 1 | [1]실물발행<br>[2]전액등록<br>[3]부분등록<br>[4]청약증거금영수증발행<br>[5]전액불소지<br>[6]부분불소지 |  |
| 8 | 매출일자 | SALE_DT | VARCHAR2(8) | 20180702 | 어음에 대한 매출일자 |  |
| 9 | 이자지급방식구분코드 | INT_PAY_MANN_TPCD | CHAR(1) | 1 | [1]할인식<br>[2]부리식 |  |
| 10 | 발행일자 | ISSU_DT | VARCHAR2(8) | 20180702 | 종목을 발행한 일자 |  |
| 11 | 만기일자 | XPIR_DT | VARCHAR2(8) | 20190701 | 종목의 만기일자 |  |
| 12 | 할인기관고객번호 | DISCN_ORG_CUSTNO | NUMBER(10) | 3061 | 할인기관의 고객번호 |  |
| 13 | 할인기관명 | DISCN_ORD_NM | VARCHAR2(100) | 교보증권 | 할인기관명 |  |
| 14 | 지급은행지점번호 | PAY_BANK_BRONO | NUMBER(5) | 311 | 지급은행지점번호 |  |
| 15 | 지급은행명 | BANK_NM | VARCHAR2(100) | 농협은행(NH금융PLUS여의도) | 지급은행명 |  |
| 16 | 원천징수구분코드 | WHOLD_TPCD | CHAR(1) | 1 | 1: 상환시 / 2: 매출시 / 3: 미확정 |  |
| 17 | KIS평가등급코드 | KIS_VALAT_GRD_CD | CHAR(3) | 112 | [110]AAA<br>[111]AAA+<br>[112]AAA0(A1)<br>[113]AAA-<br>[120]AA<br>[121]AA+(A2+)<br>[122]AA0(A2)<br>[123]AA-(A2-)<br>[130]A<br>[131]A+(A3+)<br>[132]A0(A3)<br>[133]A-(A3-)<br>[210]BBB<br>[211]BBB+<br>[212]BBB0<br>[213]BBB-<br>[220]BB<br>[221]BB+<br>[222]BB0<br>[223]BB-<br>[230]B<br>[231]B+<br>[232]B0(B)<br>[233]B-<br>[310]CCC<br>[311]CCC+<br>[312]CCC0<br>[313]CCC-<br>[320]CC<br>[321]CC+<br>[322]CC0<br>[323]CC-<br>[330]C<br>[331]C+<br>[332]C0<br>[333]C-<br>[440]D<br>[900]유보<br>[999]취소 | 발행당시 <br>신용등급 |
| 18 | NICE평가등급코드 | NICE_VALAT_GRD_CD | CHAR(3) | 112 |  |  |
| 19 | 서울신용평가등급코드 | SCI_VALAT_GRD_CD | CHAR(3) |  |  |  |
| 20 | 한국기업평가등급코드 | KR_VALAT_GRD_CD | CHAR(3) |  |  |  |

## `getESTBInfo`

**전자단기사채 종목 정보** · 원본 시트 `8_채권_전자단기사채정보`

전자단기사채 종목별 상세 정보

- 목록 ID `getESTBinfo`

원본 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getESTBInfo&params=ISIN:KRZS24449010
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 종목코드 | ISIN | VARCHAR2(12) | KRZS24449010 | 종목코드 | 필수 |

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사 고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 27597 | 예탁결제원이 부여한 고객번호 |  |
| 2 | 전자단기사채종류코드 | ESTB_KACD | CHAR(1) | 3 | [1]일반<br>[2]AB<br>[3]PF AB<br>[4]특수 |  |
| 3 | 한글종목명 | KOR_SECN_NM | VARCHAR2(100) | 디에스평택진위제일차<br>20180802-92-1E | 종목에 부여된 한글 종목명 |  |
| 4 | 발행통화코드 | ISSU_CUR_CD | CHAR(3) | KRW | 발행국가의 통화코드 |  |
| 5 | 발행금액 | ISSU_AMT | NUMBER(18,2) | 5000000000 | 발행금액 |  |
| 6 | 모집방법코드 | RECU_WHCD | CHAR(2) | 99 | [11]공모<br>[21]사모<br>[22]CBO기초사모<br>[23]전문투자형 사모<br>[26]경영참여형 사모<br>[99]면제 |  |
| 7 | 발행일자 | ISSU_DT | VARCHAR2(8) | 20180802 | 종목을 발행한 일자를 관리한다 |  |
| 8 | 만기일자 | XPIR_DT | VARCHAR2(8) | 20181102 | 종목의 만기일자 |  |
| 9 | 일물 | DAYOBJ | VARCHAR2(8) | 92 | 만기일-발행일 |  |
| 10 | 원천징수여부 | WHOLD_YN | CHAR(1) | Y | Y:징수 N:면제 |  |
| 11 | 보증여부 | GRORG_YN | CHAR(1) | N |  |  |
| 12 | KIS평가등급코드 | KIS_VALAT_GRD_CD | CHAR(3) |  | [110]AAA<br>[111]AAA+<br>[112]AAA0(A1)<br>[113]AAA-<br>[120]AA<br>[121]AA+(A2+)<br>[122]AA0(A2)<br>[123]AA-(A2-)<br>[130]A<br>[131]A+(A3+)<br>[132]A0(A3)<br>[133]A-(A3-)<br>[210]BBB<br>[211]BBB+<br>[212]BBB0<br>[213]BBB-<br>[220]BB<br>[221]BB+<br>[222]BB0<br>[223]BB-<br>[230]B<br>[231]B+<br>[232]B0(B)<br>[233]B-<br>[310]CCC<br>[311]CCC+<br>[312]CCC0<br>[313]CCC-<br>[320]CC<br>[321]CC+<br>[322]CC0<br>[323]CC-<br>[330]C<br>[331]C+<br>[332]C0<br>[333]C-<br>[440]D<br>[900]유보<br>[999]취소 | 발행당시 <br>신용등급 |
| 13 | NICE평가등급코드 | NICE_VALAT_GRD_CD | CHAR(3) | 112 |  |  |
| 14 | 서울신용평가등급코드 | SCI_VALAT_GRD_CD | CHAR(3) |  |  |  |
| 15 | 한국기업평가등급코드 | KR_VALAT_GRD_CD | CHAR(3) | 112 |  |  |
