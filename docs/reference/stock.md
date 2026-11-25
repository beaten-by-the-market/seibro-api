# 주식정보 Open API 명세

[엑셀 원본](originals/Guide_Stock.xlsx) · [전체 API 색인](README.md)

엑셀 가이드와 포털 미리보기에서 대조한 API 9개를 담았습니다. 요청 예시의 키는 변수명으로 표시했습니다.

## 서비스 목록

| 서비스목록 | API명 | API ID | 상세기능 |
| --- | --- | --- | --- |
| 주식정보<br>(9) | 주식 종목 정보 | [`getStkStatInfo`](#getstkstatinfo) | 주식 종목별 상세 정보 |
| 주식정보<br>(9) | 비상장유통추정 정보 | [`getUnlistCirclInfo`](#getunlistcirclinfo) | 비상장주식의 예탁, 계좌대체, 반환수량 |
| 주식정보<br>(9) | 종목별 대차거래 현황 | [`getSlbDealingByIsin`](#getslbdealingbyisin) | 종목별 대차거래내역, 내외국인 참여 현황 |
| 주식정보<br>(9) | 시장별 단축코드 조회 | [`getShotnByMart`](#getshotnbymart) | 시장별 발행종목 단축코드 조회 |
| 주식정보<br>(9) | 주식 상장 정보 | [`getStkListInfo`](#getstklistinfo) | 예탁지정 및 시장 상장 관련 정보 |
| 주식정보<br>(9) | 주식관련사채 행사대상 주식정보 | [`getXrcStkStatInfo`](#getxrcstkstatinfo) | CB/BW/EB 행사대상 주식 정보 |
| 주식정보<br>(9) | 주식관련사채 행사내역 | [`getXrcStkOptionXrcInfo`](#getxrcstkoptionxrcinfo) | CB/BW/EB 권리행사 정보 |
| 주식정보<br>(9) | 주식증감내역 | [`getStkIncdecDetails`](#getstkincdecdetails) | 발행횟수별 주식수량 변동내역 |
| 주식정보<br>(9) | 의무보호예수/반환정보 | [`getSafeDpDutyDepoStatus`](#getsafedpdutydepostatus) | 의무보호예수 및 반환정보 조회 |

## 작성 이력

| 버전 | 등록일 | 주요내용 |
| --- | --- | --- |
| ver.1 | 2018-09-03 | ㅇ 7개 API 등록 |
| ver.2 | 2018-10-02 | ㅇ 주식증감내역 API 추가<br>ㅇ 주식종목정보 호출파라미터 추가(총발행주식수 기준일) |
| ver.3 | 2018-12-28 | ㅇ 주식상장정보 호출파라미터 변경(변경시작일/종료일)<br>ㅇ 주식상장정보에 변경전/후 유통시장 정보 추가<br>ㅇ 시장별 단축코드 조회에 발행회사 고객번호 추가 |
| ver.4 | 2020-09-28 | ㅇ 컬럼 목록 및 내용 현행화 |
| ver.5 | 2021-08-04 | ㅇ 상장구분코드 신규코드 적용 |
| ver.6 | 2024-05-29 | ㅇ 컬럼 목록 및 내용 현행화 |

## `getStkStatInfo`

**주식 종목 정보** · 원본 시트 `주식_주식종목정보`

주식 종목별 상세 정보

포털 미리보기 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getStkStatInfo&params=SHOTN_ISIN:005930,ISIN:KR7005930003,ISSUCO_CUSTNO:593,STD_DT:20180921
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 단축코드 | SHOTN_ISIN | VARCHAR2(12) | 005930 | 종목단축코드 | 필수선택 |
| 2 | 종목코드 | ISIN | VARCHAR2(12) | KR7005930003 | 표준종목코드 | 필수선택 |
| 3 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 593 | 예탁결제원이 부여한 고객번호 | 필수선택 |
| 4 | 기준일 | STD_DT | VARCHAR2(8) | 20180921 | 총발행주식수 산정 기준일<br>(#8.주식증감내역&gt; 발행일자(ISSU_DT)) | 선택 |

> * <필수선택> 파라미터는 하나 이상 입력, <선택> 파라미터는 원하는 경우에만 입력

> * 발행회사고객번호(ISSUCO_CUSTNO)는 주식정보>시장별 단축코드 조회에서 일괄호출 가능

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 593 | 예탁결제원이 부여한 고객번호 |  |
| 2 | 상장시장명 | LIST_NM | CHAR(2) | 유가증권시장 | 상장시장명 |  |
| 3 | 한글종목명 | KOR_SECN_NM | VARCHAR2(100) | 삼성전자 | 종목에 부여된 한글 종목명 |  |
| 4 | 영문종목명 | ENG_SECN_NM | VARCHAR2(200) | SAMSUNG ELECTRONICS | 종목에 부여된 영문 종목명 |  |
| 5 | 종목코드 | ISIN | VARCHAR2(12) | KR7005930003 | 표준종목코드 |  |
| 6 | 단축코드 | SHOTN_ISIN | VARCHAR2(12) | 005930 | 주식단축코드 |  |
| 7 | 통화코드 | ISSU_CUR_CD | CHAR(3) | KRW | 발행국가 통화코드 |  |
| 8 | 액면가 | PVAL | NUMBER(15,4) | 100 | 액면가 |  |
| 9 | 종목종류코드 | SECN_KACD | CHAR(4) | 101 | [0101]보통주<br>[0201]우선주<br>[0301]후배주<br>[0401]혼합주 |  |
| 10 | 신구주구분코드 | NNOSTK_TPCD | CHAR(1) | 1 | [1]구주<br>[2]1신<br>[3]2신<br>[4]3신<br>[5]4신<br>[6]5신<br>[7]6신<br>[8]7신<br>[9]8신 |  |
| 11 | 발행국가코드 | ISSU_NATION_CD | CHAR(2) | KR | 발행한 국가의 ISO코드(KR:KOREA) |  |
| 12 | 1주당 의결권수 | VOTRNO | NUMBER(5,2) | 1 | 1주에 대한 의결권수 |  |
| 13 | 총발행주식수 | TOTAL_STK_CNT | NUMBER(15,4) | 6419324700 | 총발행주식수 | 총발행주식수 기준일에 따라 상이<br>(기준일 조건 미입력시, 최근값 호출) |
| 14 | 전자증권 여부 | ELTSC_YN | CHAR(1) | N | [Y]전자증권<br>[N]예탁증권 |  |

## `getUnlistCirclInfo`

**비상장유통추정 정보** · 원본 시트 `주식_비상장유통추정정보`

비상장주식의 예탁,계좌대체, 반환수량

- 종목종류 필드의 엑셀 표기는 `SECN_KACA_NM`입니다. 포털 출력 표와 TEST XML에서 `SECN_KACD_NM`을 확인했습니다.

원본 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getUnlistCirclInfo&params=STD_DT:20180807,ISSUCO_CUSTNO:4131,ISIN:KR7064400005,SHOTN_ISIN:064400
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 기준일자 | STD_DT | VARCHAR2(8) | 20180807 | 기준일자 | 필수 |
| 2 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 4131 | 예탁결제원이 부여한 고객번호 | 선택 |
| 2 | 종목코드 | ISIN | VARCHAR2(12) | KR7064400005 | 표준종목코드 | 선택 |
| 3 | 단축코드 | SHOTN_ISIN | VARCHAR2(12) | 064400 | 종목단축코드 | 선택 |

> * <필수> 파라미터는 반드시 입력, <선택> 파라미터는 원하는 경우에만 입력

> * 발행회사고객번호(ISSUCO_CUSTNO)는 주식정보>시장별 단축코드 조회에서 일괄호출 가능

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 종목번호 | ISIN | VARCHAR2(12) | KR7064400005 | 종목표준코드 |  |
| 2 | 단축코드 | SHOTN_ISIN | VARCHAR2(12) | 064400 | 종목단축코드 |  |
| 3 | 대표종목명 | REP_SECN_NM | VARCHAR2(100) | 엘지씨엔에스 | 한글 종목명 |  |
| 4 | 종목종류 | SECN_KACD_NM | VARCHAR2(100) | 보통주 | 보통주, 우선주 |  |
| 5 | 예탁수량 | GEN_DEPO_QTY | NUMBER(16) | 0 | 일반예탁주식수 |  |
| 6 | 반환수량 | RTHING_RETURN_STKQTY | NUMBER(16) | 0 | 실물반환주식수 |  |
| 7 | 계좌대체수량 | ACNTTR_QTY | NUMBER(16) | 1400 | 계좌대체주식수 |  |
| 8 | 전자증권 여부 | ELTSC_YN | CHAR(1) | N | [Y]전자증권<br>[N]예탁증권 |  |

## `getSlbDealingByIsin`

**종목별 대차거래 현황** · 원본 시트 `주식_종목별 대차거래 현황`

종목별 대차거래내역, 내외국인 참여 현황

| 항목 | 내용 |
| --- | --- |
| 참고사항 | 한국예탁결제원 중개거래에 한하여 정보 제공 |

원본 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getSlbDealingByIsin&params=ISIN:KR7068270008,STD_DT:20180822
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 종목코드 | ISIN | VARCHAR2(12) | KR7068270008 | 표준종목코드 | 필수 |
| 2 | 기준일 | STD_DT | VARCHAR2(8) | 20180822 | 조회기준일 | 필수 |

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 총발행주식수 | TOT_ISSU_STKQTY | NUMBER(16) | 87399845 | 해당 종목의 총발행주식수 |  |
| 2 | 일일거래량 | TR_QTY | NUMBER(16) |  | 일일거래량 |  |
| 3 | 대차체결량 | MATC_QTY | NUMBER(16) | 300210 | 대차체결량 |  |
| 4 | 대차상환량 | RED_QTY | NUMBER(16) | 39829 | 대차상환량 |  |
| 5 | 대차잔고주수 | SLB_TR_REM_QTY | NUMBER(16) | 21976319 | 기준일 현재 잔고 주수 |  |
| 6 | 외국인 대여잔고금액 | FRINER_LEND_REM_AMT | NUMBER(16) | 4179731923300 | 외국인 대여잔고금액 |  |
| 7 | 외국인 대여잔고비율 | FRINER_LEND_REM_RATIO | NUMBER(5,2) | 71.08 | 외국인 대여잔고비율 |  |
| 8 | 내국인 대여잔고금액 | NATIVE_LEND_REM_AMT | NUMBER(16) | 1700699489400 | 내국인 대여잔고금액 |  |
| 9 | 내국인 대여잔고비율 | NATIVE_LEND_REM_RATIO | NUMBER(5,2) | 28.92 | 내국인 대여잔고비율 |  |
| 10 | 외국인 차입잔고금액 | FRINER_BRW_REM_AMT | NUMBER(16) | 4881975749000 | 외국인 차입잔고금액 |  |
| 11 | 외국인 차입잔고비율 | FRINER_BRW_REM_RATIO | NUMBER(5,2) | 83.02 | 외국인 차입잔고비율 |  |
| 12 | 내국인 차입잔고금액 | NATIVE_BRW_REM_AMT | NUMBER(16) | 998455663700 | 내국인 차입잔고금액 |  |
| 13 | 내국인 차입잔고비율 | NATIVE_BRW_REM_RATIO | NUMBER(5,2) | 16.98 | 내국인 차입잔고비율 |  |

## `getShotnByMart`

**시장별 단축코드 조회** · 원본 시트 `주식_시장별 단축코드 조회`

시장별 발행종목 단축코드 조회

원본 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getShotnByMart&params=MART_TPCD:13
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 시장구분 | MART_TPCD | CHAR(2) | 13 | [11]유가증권시장<br>[12]코스닥시장<br>[13]K-OTC시장<br>[14]코넥스시장<br>[50]기타시장 | 필수 |

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 단축코드 | SHOTN_ISIN | VARCHAR2(12) | 005900 | 종목단축코드 |  |
| 2 | 종목명 | KOR_SECN_NM | VARCHAR2(100) | 동양건설산업 | 한글종목명 |  |
| 3 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 593 | 예탁결제원이 부여한 고객번호 |  |

## `getStkListInfo`

**주식 상장 정보** · 원본 시트 `주식_상장정보 `

예탁지정 및 시장 상장 관련 정보

원본 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getStkListInfo&params=ALT_BEGIN_DT:20181201,ALT_EXPRY_DT:20181231
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 변경시작일 | ALT_BEGIN_DT | VARCHAR2(8) | 20181201 | 유통시장 변경기준일 조회 시작일(FROM) | 필수 |
| 2 | 변경종료일 | ALT_EXPRY_DT | VARCHAR2(8) | 20181231 | 유통시장 변경기준일 조회 종료일(TO) <br>* 변경시작일로부터 1개월까지 설정 가능 | 필수 |

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 13381 | 예탁결제원이 부여한 고객번호 |  |
| 2 | 종목코드 | ISIN | VARCHAR2(12) | KR7117930008 | 종목표준코드 |  |
| 3 | 단축코드 | SHOTN_ISIN | VARCHAR2(12) | 117930 | 종목단축코드 |  |
| 4 | 종목명 | KOR_SECN_NM | VARCHAR2(100) | 한진해운 | 한글종목명 |  |
| 5 | 변경전 유통형태 | BFALT_CIRCL_FORM | CHAR(2) | 211 | [110] 유가증권시장<br>[120] 코스닥시장<br>[130] K-OTC시장<br>[140] 코넥스시장<br>[211] 예탁지정<br>[212] 등록지정<br>[221] 예탁지정취소<br>[222] 등록지정취소<br>[230] 보호예수<br>[241] 권리<br>[242] 등록적격<br>[250] KSM<br>[910] 소멸/폐지<br>[990] 기타 |  |
| 6 | 변경후 유통형태 | AFALT_CIRCL_FORM | CHAR(2) | 221 | [110] 유가증권시장<br>[120] 코스닥시장<br>[130] K-OTC시장<br>[140] 코넥스시장<br>[211] 예탁지정<br>[212] 등록지정<br>[221] 예탁지정취소<br>[222] 등록지정취소<br>[230] 보호예수<br>[241] 권리<br>[242] 등록적격<br>[250] KSM<br>[910] 소멸/폐지<br>[990] 기타 |  |
| 7 | 변경일자(적용일자) | APLI_DT | VARCHAR2(8) | 20181217 | 종목상장(예탁지정 포함) 적용일자 |  |

## `getXrcStkStatInfo`

**주식관련사채 행사대상 주식 정보** · 원본 시트 `주식_주식관련사채 행사대상 주식 정보 `

CB/BW/EB 행사대상 주식 정보

포털 미리보기 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getXrcStkStatInfo&params=BOND_ISIN:KR6474171G56,XRC_STK_ISIN:KR7474170008
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 채권 종목번호 | BOND_ISIN | VARCHAR2(12) | KR6474171G56 | EB BW CB 채권 종목코드 | 필수선택 |
| 2 | 행사주식종목번호 | XRC_STK_ISIN | VARCHAR2(12) | KR7474170008 | 행사주식 종목코드 | 필수선택 |

> * <필수선택> 파라미터는 하나 이상 입력

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 채권 종목번호 | BOND_ISIN | VARCHAR2(12) | KR6002221887 | EB BW CB 채권 종목코드 |  |
| 2 | 채권 종목명 | BOND_SECN_NM | VARCHAR2(100) | 한일철강2(사모/전/풋) | EB BW CB 채권명 |  |
| 3 | 채권종류코드 | BOND_KIND_NM | VARCHAR2(10) | CB | EB CB 분리형BW 비분리형BW |  |
| 4 | 행사주식종목번호 | XRC_STK_ISIN | VARCHAR2(12) | KR7002220002 | 행사주식 종목코드 |  |
| 5 | 주식 종목명 | STK_SECN_NM | VARCHAR2(100) | 한일철강 | 행사주식 종목명 |  |
| 6 | 신주인수권증권종목번호 | WRTB_ISIN | VARCHAR2(12) |  | 신주인수권증권이 발행된 경우 종목코드 |  |
| 7 | 신주인수권증권명 | WRTB_SECN_NM | VARCHAR2(100) |  | 신주인수권증권 이름 |  |
| 8 | 행사비율 | XRC_RATIO | NUMBER(20,10) | 100 | 행사대상종목의 행사비율<br>기본값 0.0 |  |
| 9 | 행사가격 | XRC_PRICE | NUMBER(17,7) | 23800 | 행사대상종목의 행사가격<br>기본값 0 |  |
| 10 | 결산기말제한일수 | SETACC_ENDTERM_LIMIT_DAYS | NUMBER(3) | 0 | 주식관련사채 행사 결산기말 제한 일 수 |  |
| 11 | 신주배정일전제한일수 | NEWSTK_ALOC_DD_BF_LIMIT_DAYS | NUMBER(3) | 0 | 행사대상종목의 신주배정일전 제한일수 |  |
| 12 | 청구제한사유내용 | DMAN_LIMIT_RSN_CONTENT | VARCHAR2(500) |  | 텍스트로 입력한 청구제한사유 |  |

## `getXrcStkOptionXrcInfo`

**주식관련사채 행사내역** · 원본 시트 `주식_주식관련사채 행사내역 `

CB/BW/EB 권리행사 정보

포털 미리보기 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getXrcStkOptionXrcInfo&params=RGT_STD_DT:20260901,BOND_ISIN:KR6067171G17,XRC_POSS_BEGIN_DT:20260212
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 권리행사일 | RGT_STD_DT | VARCHAR2(12) | 20260901 | 권리행사일자 | 필수선택 |
| 2 | 채권 종목코드 | BOND_ISIN | VARCHAR2(12) | KR6067171G17 | EB BW CB 채권 종목코드 | 필수선택 |
| 3 | 행사가능시작일자 | XRC_POSS_BEGIN_DT | VARCHAR2(8) | 20260212 | 주식관련사채 행사조건의 행사가능시작일자 | 필수선택 |

> * <필수선택> 파라미터는 하나 이상 입력, <선택> 파라미터는 원하는 경우에만 입력

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 채권 종목코드 | BOND_ISIN | VARCHAR2(12) | KR6079161C75 | EB BW CB 채권 종목코드 |  |
| 2 | 한글종목명 | BOND_KOR_SECN_NM | VARCHAR2(100) | 씨제이 씨지브이 35CB(신종)(전환/콜/후) | EB BW CB 채권명 |  |
| 3 | 채권종류코드 | BOND_KIND_NM | VARCHAR2(10) | CB | EB CB 분리형BW 비분리형BW |  |
| 4 | 행사주식 종목코드 | XRC_STK_ISIN | VARCHAR2(12) | KR7079160008 | 행사주식 종목코드 |  |
| 5 | 행사주식명 | STK_KOR_SECN_NM | VARCHAR2(100) | 씨제이씨지브이 | 행사주식 종목명 |  |
| 6 | 권리행사일 | RGT_STD_DT | VARCHAR2(12) | 20231129 | 주식전환 행사일 |  |
| 7 | 행사시작일 | XRC_POSS_BEGIN_DT | VARCHAR2(8) | 20220821 | 주식관련사채 행사조건의 행사가능시작일자 |  |
| 8 | 행사종료일 | XRC_POSS_EXPRY_DT | VARCHAR2(8) | 20520621 | 주식관련사채 행사조건의 행사가능종료일자 |  |
| 9 | 행사금액 | XRC_AMT | NUMBER(17,7) | 124215 | 행사금액 |  |
| 10 | 행사주수 | XRC_QTY | NUMBER(17,7) | 7 | 행사주수 |  |
| 11 | 행사가격 | XRC_PRICE | NUMBER(17,7) | 17745 | 행사가격 |  |
| 12 | 주식상장일 | LIST_DT | VARCHAR2(8) | 20231215 | 상장일 |  |

## `getStkIncdecDetails`

**주식증감내역** · 원본 시트 `주식_주식증감내역`

발행횟수별 주식수량 변동내역

포털 미리보기 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getStkIncdecDetails&params=SHOTN_ISIN:005930,ISIN:KR7005930003,ISSUCO_CUSTNO:593,ISSU_YEAR:2018
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 단축코드 | SHOTN_ISIN | VARCHAR2(12) | 005930 | 종목단축코드 | 필수선택 |
| 2 | 종목코드 | ISIN | VARCHAR2(12) | KR7005930003 | 표준종목코드 | 필수선택 |
| 3 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 593 | 예탁결제원이 부여한 고객번호 | 필수선택 |
| 4 | 발행연도 | ISSU_YEAR | NUMBER(4) | 2018 | 발행연도 | 선택 |

> * <필수선택> 파라미터는 하나 이상 입력, <선택> 파라미터는 원하는 경우에만 입력

> * 발행회사고객번호(ISSUCO_CUSTNO)는 주식정보>시장별 단축코드 조회에서 일괄호출 가능

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 593 | 고객을 시스템적으로 식별하기 위해서 부여하는 일련번호 |  |
| 2 | 종목번호 | ISIN | VARCHAR2(12) | KR7005930003 | 종목표준코드 |  |
| 3 | 종목종류코드 | SECN_KACD | CHAR(4) | 0101 | [0101]보통주<br>[0201]우선주<br>[0301]후배주<br>[0401]혼합주 |  |
| 4 | 종목발행횟수 | SECN_ISSU_NTIMES | NUMBER(5) | 75 | 회사가 주식을 발행하는 과정에서 발행 이력을 관리하기 위하여 발행시 마다 부여하는 순서 |  |
| 5 | 발행일자 | ISSU_DT | VARCHAR2(8) | 20180503 | 유가증권 등을 발행한 날로서 주권의 경우 그 효력이 발생하는 일자 |  |
| 6 | 발행가 | ISSUPRC | NUMBER(15) | 100 | 1주당 발행가 |  |
| 7 | 발행수량 | ISSU_QTY | NUMBER(16) | 6419324700 | 주권에 대해 해당 횟수에 발행한 수량 |  |
| 8 | 종목발행사유코드 | SECN_ISSU_RACD | CHAR(3) | 201 | 종목이 발행된 권리사유 코드 | 8.종목발행사유명(SECN_ISSU_NM) 참조 |
| 9 | 종목발행사유명 | SECN_ISSU_NM | VARCHAR2(100) | 액면분할 | 종목이 발행된 권리사유명 |  |
| 10 | 상장일자 | LIST_DT | VARCHAR2(8) | 20180504 | 종목상장 적용일자 |  |

## `getSafeDpDutyDepoStatus`

**의무보호예수/반환정보** · 원본 시트 `주식_의무보호예수반환정보`

의무보호예수 및 반환정보 조회

- 엑셀 URL 예시의 `apiId`가 비어 있습니다.

- 포털은 `EXPRY_DT`와 `BIZ_TPCD`를 필수로 표시합니다. 아래 네 변수를 넣은 TEST에서 1건을 확인했습니다.

포털 미리보기 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getSafeDpDutyDepoStatus&params=BEGIN_DT:20190221,EXPRY_DT:20190227,MART_TPCD:11,BIZ_TPCD:1
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) |  | 예탁결제원이 부여한 고객번호 | 선택 |
| 2 | 조회기준일(FROM) | BEGIN_DT | VARCHAR2(8) | 20190221 | 예수 또는 반환 일정 조회 기준일(FROM) | 필수 |
| 3 | 조회기준일 (TO) | EXPRY_DT | VARCHAR2(8) | 20190227 | *  고객번호가 없거나 미입력 시 기준일(FROM)로 자동설정 <br>** 고객번호가 있는 경우, 기준일(FROM)으로부터 3년까지 가능 | 필수 |
| 4 | 시장구분 | MART_TPCD | CHAR(2) | 11 | [11]유가증권시장<br>[12]코스닥시장<br>[13]K-OTC시장<br>[14]코넥스시장<br>[50]기타시장 | 선택 |
| 5 | 업무구분 | BIZ_TPCD | CHAR(1) | 1 | [1] 예수 [2] 반환 | 필수 |

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 162 | 예탁결제원이 부여한 고객번호 |  |
| 2 | 한글종목명 | KOR_SECN_NM | VARCHAR2(100) | 케이비아이동국실업 | 한글종목명 |  |
| 3 | 종목종류코드 | SECN_KACD | CHAR(4) | 보통주 | 보통주<br>우선주<br>후배주<br>혼합주 |  |
| 4 | 단축코드 | SHOTN_ISIN | VARCHAR2(12) | 1620 | 종목단축코드 |  |
| 5 | 시장구분 | MART_TPCD | CHAR(2) | 11 | [11]유가증권시장<br>[12]코스닥시장<br>[13]K-OTC시장<br>[14]코넥스시장<br>[50]기타시장 |  |
| 6 | 업무구분 | OCCR_SEQ | CHAR(1) | 1 | [1] 예수 [2] 반환 |  |
| 7 | 예수일 | SAFEDP_DT | VARCHAR2(8) | 20190225 | 의무보호예수일 |  |
| 8 | 예수주식수 | SAFEDP_QTY | NUMBER(16) | 12730000 | 의무보호예수 주식수 |  |
| 9 | 보호예수사유코드 | DUTY_SAFEDP_RACD | CHAR(2) | 02 | 00 해당없음<br>01 일반<br>02 모집(전매제한)<br>03 최대주주(상장)<br>04 최대주주(코스닥)<br>43 최대주주(기술성장기업)<br>05 투자회사(상장)<br>06 초과유상증자<br>07 지정취소<br>08 질권담보<br>09 등록주선인<br>10 외국인양수(변동제한)<br>11 벤처금융<br>12 기관투자가<br>13 합병(상장)<br>14 합병(코스닥)<br>15 부동산(상장)<br>16 부동산(코스닥)<br>17 법원M&amp;A<br>18 주식교환(코스닥)<br>19 벤처금융(주식교환)<br>20 벤처금융(합병)<br>21 기관투자가(합병)<br>44 기관투자가(코넥스)<br>22 기관투자가(주식교환)<br>23 제3자배정최대주주(코스닥)<br>24 선박(상장)<br>25 채권기관협의회<br>26 주식교환(상장)<br>27 영업자산양도&amp;제3자배정(상장)<br>28 영업자산양도&amp;제3자배정(코스닥)<br>29 제3자배정유상증자(상장)<br>30 제3자배정유상증자(코스닥)<br>31 최대주주(제3자배정)<br>32 SPAC(상장)<br>33 SPAC(코스닥)<br>34 SPAC 합병(상장)<br>35 SPAC 합병(코스닥)<br>36 명목회사(상장)<br>37 명목회사(코스닥)<br>38 자발적보호예수<br>39 우회상장<br>40 상장주선인(국내기업)<br>48 상장주선인(외국기업)<br>41 전매제한<br>42 기타(특정금전신탁편입 등)<br>45 크라우드펀딩<br>46 크라우드펀딩(최대주주)<br>49 모집(전매제한)-크라우드펀딩전문투자자<br>47 주관회사(금투협)<br>50 상장주선인(50%미만)<br>51 상장주선인(50%이상)<br>52 최대주주변경(법인 또는 조합)<br>90 기타의무예수<br>99 기타<br>53 상장적격성 실질심사<br>54 기타 보호예수 필요 주주<br>55 주식매수선택권 |  |
| 10 | 반환일 | RETURN_DT | VARCHAR2(8) |  | 반환일자 |  |
| 11 | 반환주식수 | RETURN_QTY | NUMBER(16) |  | 반환 주식수 |  |
| 12 | 총발행주식수 | TOTAL_STK_CNT | NUMBER(16) | 111293031 | 총발행주식수 |  |
