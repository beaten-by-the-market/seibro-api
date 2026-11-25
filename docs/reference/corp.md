# 기업정보 Open API 명세

[엑셀 원본](originals/Guide_Corp.xlsx) · [전체 API 색인](README.md)

엑셀 가이드와 포털 미리보기에서 대조한 API 9개를 담았습니다. 요청 예시의 키는 변수명으로 표시했습니다.

## 서비스 목록

| 서비스목록 | API명 | API ID | 상세기능 |
| --- | --- | --- | --- |
| 기업정보<br>(9) | 발행종목으로 발행회사번호 조회 | [`getIssucoCustnoByIsin`](#getissucocustnobyisin) | 종목코드로 발행회사번호, 발행회사명 조회 |
| 기업정보<br>(9) | 기준일 정보 | [`getStddtInfo`](#getstddtinfo) | 발행회사별 기준일 정보 조회(최근 3년치) |
| 기업정보<br>(9) | 총회일정 정보 | [`getGmeetInfo`](#getgmeetinfo) | 기업의 총회(정기,임시,종류,기타) 일정 조회 |
| 기업정보<br>(9) | 총회안건 정보 | [`getGmeetMeasureInfo`](#getgmeetmeasureinfo) | 기업의 총회(정기,임시,종류,기타) 안건 조회 |
| 기업정보<br>(9) | 상호변경 정보 | [`getFmnmAltInfo`](#getfmnmaltinfo) | 상호변경 일정, 변경 전후 상호 등 상호변경 관련 정보 |
| 기업정보<br>(9) | 대금지급일정 정보 | [`getCostPaySchedul`](#getcostpayschedul) | 배당금, 단주대금 지급일정 정보 |
| 기업정보<br>(9) | 배당일정 정보 | [`getDivSchedulInfo`](#getdivschedulinfo) | 현금/주식/동시/무배당 일정 조회 |
| 기업정보<br>(9) | 배당분배금내역 정보 | [`getDivInfo`](#getdivinfo) | 배당 분배금 배정비율, 금액 등 배당내역 |
| 기업정보<br>(9) | 단주대금 정보 | [`getOddLotInfo`](#getoddlotinfo) | 단주대금 사유, 기준일 등 단주대금 관련 정보 |

## 작성 이력

| 버전 | 등록일 | 주요내용 |
| --- | --- | --- |
| ver.1 | 2018-09-03 | ㅇ 9개 API 등록 |
| ver.2 | 2018-12-28 | ㅇ 기준일 정보 호출파라미터 수정(기준일 from/to 추가)<br>ㅇ 총회일정/총회안건 정보 호출파라미터 수정(발행체 번호 추가)<br>ㅇ 총회일정 정보 전자투표 적용여부 추가<br>ㅇ 배당일정 정보 호출파라미터 수정(기준일 from/to 추가, 발행회사번호 필수에서 선택변수로 변경) |
| ver.3 | 2024-05-29 | ㅇ 전자증권여부, 권리사유코드 추가<br>ㅇ 배당일정 정보 칼럼 순서 수정<br>(권리기준일자-권리사유세부유형코드 =&gt; 권리사유세부유형코드-권리기준일자 |

## `getIssucoCustnoByIsin`

**발행종목으로 발행회사번호 조회** · 원본 시트 `기업_발행종목으로 발행회사번호 조회`

종목코드로 발행회사번호, 발행회사명 조회

원본 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getIssucoCustnoByIsin&params=ISIN:KR7005930003,SHOTN_ISIN:005930
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 종목코드 | ISIN | VARCHAR2(12) | KR7005930003 | 표준종목코드 | 필수선택 |
| 2 | 단축종목코드 | SHOTN_ISIN | VARCHAR2(12) | 005930 | 단축종목코드 | 필수선택 |

> * <필수선택> 파라미터는 하나 이상 입력

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 593 | 예탁결제원이 부여한 고객번호 |  |
| 2 | 대표종목명 | REP_SECN_NM | VARCHAR2(100) | 삼성전자 | 대표주식 종목명 |  |

## `getStddtInfo`

**기준일 정보** · 원본 시트 `기업_기준일정보`

발행회사별 기준일 정보 조회(최근 3년치)

포털 미리보기 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getStddtInfo&params=ISSUCO_CUSTNO:593,BEGIN_STD_DT:20161231,EXPRY_STD_DT:20181231,RGT_RACD:001
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 593 | 예탁결제원이 부여한 고객번호 | 필수 |
| 2 | 시작기준일자 | BEGIN_STD_DT | NUMBER(8) | 20161231 | 기준일 조회시작일 | 필수 |
| 3 | 종료기준일자 | EXPRY_STD_DT | NUMBER(8) | 20181231 | *  종료기준일자 미입력 시 시작기준일자로 자동설정 <br>** 시작기준일자로부터 3년까지 입력가능 | 선택 |
| 4 | 권리사유코드 | RGT_RACD | CHAR(3) | 001 | [001]정기총회<br>[002]임시총회<br>[003]종류총회<br>[009]기타<br>[101]유상증자<br>[102]무상증자<br>[103]배당/분배<br>[201]액면분할<br>[202]액면병합<br>[203]통일교체<br>[204]상호변경<br>[205]자본감소<br>[206]합병<br>[207]회사분할<br>[208]분할합병<br>[906]무상소각<br>[907]이익소각 | 선택 |

> <선택> 파라미터는 필요한 경우에만 입력

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 593 | 예탁결제원이 부여한 고객번호 |  |
| 2 | 대표종목명 | REP_SECN_NM | VARCHAR2(100) | 삼성전자 | 대표종목명 |  |
| 3 | 권리기준일자 | RGT_STD_DT | VARCHAR2(8) | 20180630 | 권리가 발생하는 기준일자 |  |
| 4 | 권리사유코드 | RGT_RACD | CHAR(3) | 103 | 권리사유명(RGT_RACD_NM)참조 |  |
| 5 | 권리사유명 | RGT_RACD_NM | VARCHAR2(100) | 배당/분배 | 주주총회,배당, 상호변경 등 권리사유 |  |
| 6 | 권리사유<br>세부유형코드 | RGT_RSN_DTAIL_SORT_CD | CHAR(2) | 02 | 01 주식배당<br>02 현금배당<br>03 동시배당<br>04 무배당<br>11 이익분배<br>12 청산분배<br>21 흡수합병<br>22 신설합병<br>31 무상감자<br>32 유상감자<br>41 소규모합병<br>42 상장<br>43 주식매수청구<br>90 미정<br>99 기타 |  |

## `getGmeetInfo`

**총회일정 정보** · 원본 시트 `기업_총회일정정보`

기업의 총회(정기,임시,종류,기타) 안건 조회

포털 미리보기 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getGmeetInfo&params=ISSUCO_CUSTNO:593,ISSUIN_NO:00593,RGT_STD_DT:20171231
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 593 | 예탁결제원이 부여한 고객번호 | 필수선택 |
| 2 | 발행회사발행체번호 | ISSUIN_NO | VARCHAR2(6) | 00593 | 발행체번호(표준코드 내 5자리) | 필수선택 |
| 3 | 권리기준일자 | RGT_STD_DT | VARCHAR2(8) | 20171231 | 권리가 발생하는 기준일자 | 필수 |

> * <필수선택> 파라미터는 하나 이상 입력

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 593 | 예탁결제원이 부여한 고객번호 |  |
| 2 | 발행회사발행체번호 | ISSUIN_NO | VARCHAR2(6) | 00593 | 종목표준코드 내 5자리 |  |
| 3 | 총회종류코드 | GMET_KACD | CHAR(3) | 001 | [001]정기총회<br>[002]임시총회<br>[003]종류총회<br>[009]기타 |  |
| 4 | 권리사유<br>세부유형코드 | RGT_RSN_DTAIL_SORT_CD | CHAR(2) | 99 | [01]주식배당<br>[02]현금배당<br>[03]동시배당<br>[04]무배당<br>[11]이익분배<br>[12]청산분배<br>[21]흡수합병<br>[22]신설합병<br>[31]무상감자<br>[32]유상감자<br>[41]소규모합병<br>[42]상장<br>[43]주식매수청구<br>[44]소규모주식이전/교환<br>[90]미정<br>[99]기타 |  |
| 5 | 명부폐쇄시작일자 | ROST_CLOSE_BEGIN_DT | VARCHAR2(8) | 20180101 | 명부폐쇄 시작일 |  |
| 6 | 명부폐쇄종료일자 | ROST_CLOSE_EXPRY_DT | VARCHAR2(8) | 20180131 | 명부폐쇄 종료일 |  |
| 7 | 총회개최여부 | GMET_OMEET_YN | CHAR(1) | Y | 주주 총회에 대한 개최여부 |  |
| 8 | 총회장소구분코드 | GMET_PLACE_TPCD | CHAR(1) | 1 | [1]서울<br>[2]지방<br>[3]해당없음 |  |
| 9 | 이사회결의공시일자 | COUNCL_DTERMIN_PUBN_DT | VARCHAR2(8) |  | 총회일정의 이사회결의공시일자 |  |
| 10 | 총회장소 | GMET_PLACE | VARCHAR2(100) | 서울특별시~ | 주주 총회 장소 |  |
| 11 | 주식매수청구관련여부 | STK_BUYREQ_RL_YN | CHAR(1) | N | 주식매수청구관련여부를 관리함 Y/N |  |
| 12 | 권리기준일자 | RGT_STD_DT | VARCHAR2(8) | 20171231 | 권리가 발생하는 기준일자 |  |
| 13 | 총회일자 | GMET_DT | VARCHAR2(8) | 20180323 | 총회가 개최되는 일자 |  |
| 14 | 총회시각 | GMET_TTM | VARCHAR2(6) | 0900 | 총회가 개최되는 시각 |  |
| 15 | 통지시한일자 | NOTC_DLINE_DT | VARCHAR2(8) | 20180308 | 총회일정사유의 통지시한일자 |  |
| 16 | 연기여부 | DFER_YN | CHAR(1) | N | (특히 펀드)최초 총회개최일자에 성립되지않고<br> 다른 일자로 연기되었는지 여부 |  |
| 17 | 전자투표 적용여부 | EVOTE_YN | CHAR(1) | Y | 해당 주총일에 전자투표 적용여부 |  |
| 18 | 전자증권 여부 | ELTSC_YN | CHAR(1) | N | [Y]전자증권<br>[N]예탁증권 |  |

## `getGmeetMeasureInfo`

**총회안건 정보** · 원본 시트 `기업_총회안건정보`

기업의 총회(정기,임시,종류,기타) 안건 조회

포털 미리보기 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getGmeetMeasureInfo&params=ISSUCO_CUSTNO:593,ISSUIN_NO:00593,RGT_STD_DT:20171231
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 593 | 예탁결제원이 부여한 고객번호 | 필수선택 |
| 2 | 발행회사발행체번호 | ISSUIN_NO | VARCHAR2(6) | 00593 | 종목표준코드 내 5자리 | 필수선택 |
| 3 | 권리기준일자 | RGT_STD_DT | VARCHAR2(8) | 20171231 | 권리가 발생하는 기준일자 | 필수 |

> * <필수선택> 파라미터는 하나 이상 입력

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 593 | 예탁결제원이 부여한 고객번호 |  |
| 2 | 발행회사발행체번호 | ISSUIN_NO | VARCHAR2(6) | 00593 | 종목표준코드 내 5자리 |  |
| 3 | 권리기준일자 | RGT_STD_DT | VARCHAR2(8) | 20171231 | 권리가 발생하는 기준일자 |  |
| 4 | 총회일자 | GMET_DT | VARCHAR2(8) | 20180323 | 총회가 개최되는 일자 |  |
| 5 | 총회종류코드 | GMET_KACD | CHAR(3) | 001 | [001]정기총회<br>[002]임시총회<br>[003]종류총회<br>[009]기타 |  |
| 6 | 안건일련번호 | AGENDA_SEQ | NUMBER(10) | 1 | 총회일정안건을 구분할 수 있는 일련번호 |  |
| 7 | 안건표시번호 | AGENDA_XPRES_NO | VARCHAR2(12) | 1 | 총회일정의 안건에 대한 표시번호 |  |
| 8 | 안건조회순서 | AGENDA_SCH_SEQO | CHAR(6) | 1 | 안건의 순서를 관리 |  |
| 9 | 안건번호 | AGENDA_NO | VARCHAR2(12) | 001 | 안건명에 해당하는 안건코드 |  |
| 10 | 세부안건번호 | DTAIL_AGENDA_NO | VARCHAR2(12) |  | 안건에 따르는 세부안건코드 |  |
| 11 | 안건명 | AGENDA_NM | VARCHAR2(500) | 재무제표승인 | 총회일정에서 선택된 안건명 |  |
| 12 | 영문안건명 | ENG_AGENDA_NM | VARCHAR2(500) | APPROVAL OF FINANCIAL STATEMENTS | 총회일정에서 선택된 영문 안건명 |  |
| 13 | 세부안건명 | DTAIL_AGENDA_NM | VARCHAR2(200) |  | 총회일정에서 선택된 세부안건명 |  |
| 14 | 세부영문안건명 | DTAIL_ENG_AGENDA_NM | VARCHAR2(200) |  | 총회일정에서 선택된 세부영문안건명 |  |
| 15 | 투표방식구분코드 | VOTE_MANN_TPCD | CHAR(1) | 9 | [1]집중투표<br>[4]최다득표자선임방식<br>[9]해당없음 |  |
| 16 | 총회결과구분코드 | GMET_RESULT_TPCD | CHAR(1) | 1 | [1]승인(선임)<br>[2]부결(미선임)<br>[3]수정승인<br>[4]부분승인<br>[5]철회 |  |

## `getFmnmAltInfo`

**상호변경 정보** · 원본 시트 `기업_상호변경`

상호변경 일정, 변경전후 상호명 등

원본 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getFmnmAltInfo&params=ISSUCO_CUSTNO:3572,RGT_STD_DT:20151001
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 3572 | 예탁결제원이 부여한 고객번호 | 필수선택 |
| 2 | 권리기준일자 | RGT_STD_DT | VARCHAR2(8) | 20151001 | 권리가 발생하는 기준일자 | 필수선택 |

> * <필수선택> 파라미터는 하나 이상 입력

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 3572 | 예탁결제원이 부여한 고객번호 |  |
| 2 | 권리기준일자 | RGT_STD_DT | VARCHAR2(8) | 20151001 | 권리가 발생하는 기준일자 |  |
| 3 | 변경전상호(국문) | FMNM_BFALT_KOR_NM | VARCHAR2(200) | ㈜다음카카오 | 상호변경신청 이전의 상호한글명칭 |  |
| 4 | 변경전상호(영문) | FMNM_BFALT_ENG_NM | VARCHAR2(200) | Daum kakao | 상호변경신청 이전의 상호영문명칭 |  |
| 5 | 변경후상호(국문) | FMNM_ALT_KOR_NM | VARCHAR2(100) | ㈜카카오 | 상호변경사유의 변경후 상호 |  |
| 6 | 변경후상호(영문) | FMNM_ALT_ENG_NM | VARCHAR2(100) | Kakao Corp. | 상호변경사유의 변경후 영문상호 |  |
| 7 | 혼용유통시작일자 | MIXUS_CIRCL_BEGIN_DT | VARCHAR2(8) | 20151012 | 상호변경사유의 혼용유통시작일자 |  |
| 8 | 혼용유통종료일자 | MIXUS_CIRCL_EXPRY_DT | VARCHAR2(8) | 20151019 | 상호변경사유의 혼용유통종료일자 |  |
| 9 | 단일유통일자 | UNI_CIRCL_DT | VARCHAR2(8) | 20151020 | 상호변경사유의 단일유통일자 |  |

## `getCostPaySchedul`

**대금지급일정 정보** · 원본 시트 `기업_대금지급일정`

배당금, 단주대금 지급일정 정보

- 포털 TEST의 XML에서 출력 필드 `RGT_RACD_NM`을 확인했습니다.

원본 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getCostPaySchedul&params=TH1_PAY_TERM_BEGIN_DT:20180720,PAY_COST_TPCD:3
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 대금지급일 | TH1_PAY_TERM_BEGIN_DT | VARCHAR2(8) | 20180720 | 권리 지급에 대한 1차지급기간시작일자 | 필수 |
| 2 | 지급대금구분코드 | PAY_COST_TPCD | CHAR(1) | 3 | 1:배당금 <br>3:단주대금 | 필수 |

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 4631 | 예탁결제원이 부여한 고객번호 |  |
| 2 | 종목번호 | ISIN | VARCHAR2(12) | KR7046310009 | 종목표준코드 |  |
| 3 | 한글종목명 | KOR_SECN_NM | VARCHAR2(100) | 백금티앤에이 | 종목에 부여된 한글 종목명 |  |
| 4 | 종목종류코드 | SECN_KACD | CHAR(4) | 101 | 101:보통주, 201:우선주 |  |
| 5 | 권리기준일자 | RGT_STD_DT | VARCHAR2(8) | 20180612 | 권리가 발생하는 기준일자 |  |
| 6 | 권리사유명 | RGT_RACD_NM |  |  |  | 실제 응답에서 확인 |
| 7 | 권리사유세부유형코드 | RGT_RSN_DTAIL_SORT_CD | CHAR(2) | 99 | 01 주식배당<br>02 현금배당<br>03 동시배당<br>04 무배당<br>11 이익분배<br>12 청산분배<br>21 흡수합병<br>22 신설합병<br>31 무상감자<br>32 유상감자<br>41 소규모합병<br>42 상장<br>43 주식매수청구<br>90 미정<br>99 기타 |  |

## `getDivSchedulInfo`

**배당일정 정보** · 원본 시트 `기업_배당일정`

현금/주식/동시/무배당 일정 조회

포털 미리보기 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getDivSchedulInfo&params=ISSUCO_CUSTNO:593,BEGIN_STD_DT:20161231,EXPRY_STD_DT:20181231,RGT_RSN_DTAIL_SORT_CD:02
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 593 | 예탁결제원이 부여한 고객번호 | 선택 |
| 2 | 시작기준일자 | BEGIN_STD_DT | VARCHAR2(8) | 20161231 | 권리가 발생하는 기준일자 | 필수 |
| 3 | 종료기준일자 | EXPRY_STD_DT | VARCHAR2(8) | 20181231 | *  고객번호가 없거나 종료기준일자 미입력 시작기준일자로 자동설정 <br>** 고객번호가 있는 경우, 시작기준일자로부터 3년까지 입력가능 | 선택 |
| 4 | 권리사유세부유형코드 | RGT_RSN_DTAIL_SORT_CD | CHAR(2) | 02 | 01 주식배당<br>02 현금배당<br>03 동시배당<br>04 무배당 | 선택 |

> <선택> 파라미터는 필요한 경우에만 입력

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 593 | 예탁결제원이 부여한 고객번호 |  |
| 2 | 대표종목명 | REP_SECN_NM | VARCHAR2(100) | 삼성전자 | 대표종목명 |  |
| 3 | 권리사유코드 | RGT_RACD |  | 103 | 103: 배당/분배 |  |
| 4 | 권리사유세부유형코드 | RGT_RSN_DTAIL_SORT_CD | CHAR(2) | 02 | 01 주식배당<br>02 현금배당<br>03 동시배당<br>04 무배당 |  |
| 5 | 권리기준일자 | RGT_STD_DT | VARCHAR2(8) | 20171231 | 권리가 발생하는 기준일자 |  |
| 6 | 배정방법코드 | ALOC_WHCD | CHAR(1) | 2 | [1]정율<br>[2]정액<br>[3]정율+정액 |  |
| 7 | 결산구분코드 | SETACC_TPCD | CHAR(1) | 1 | 1:결산, 2:반기, 3:분기 |  |
| 8 | 확정구분코드 | FIX_TPCD | CHAR(1) | 1 | 1:확정, 2:예고, 3:미정 |  |
| 9 | 명부폐쇄시작일자 | ROST_CLOSE_BEGIN_DT | VARCHAR2(8) | 20180101 | 명부폐쇄 시작일 |  |
| 10 | 명부폐쇄종료일자 | ROST_CLOSE_EXPRY_DT | VARCHAR2(8) | 20180131 | 명부폐쇄 종료일 |  |
| 11 | 권리락일자 | XRGT_DT | VARCHAR2(8) | 20171227 | 권리락이 이루어진 날짜 |  |
| 12 | 전자증권여부 | ELTSC_YN | CHAR(1) | N | [Y]전자증권<br>[N]예탁증권 |  |

## `getDivInfo`

**배당분배금내역 정보** · 원본 시트 `기업_배당분배금내역`

배당 분배금 배정비율, 금액 등 배당내역

포털 미리보기 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getDivInfo&params=ISSUCO_CUSTNO:593,BEGIN_STD_DT:20161231,EXPRY_STD_DT:20181231
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 593 | 예탁결제원이 부여한 고객번호 | 필수 |
| 2 | 시작기준일자 | BEGIN_STD_DT | VARCHAR2(8) | 20161231 | 권리가 발생하는 기준일자(FROM) | 필수 |
| 3 | 종료기준일자 | EXPRY_STD_DT | VARCHAR2(8) | 20181231 | *  종료기준일자 미입력 시 시작기준일자로 자동설정 <br>** 시작기준일자로부터 3년까지 입력가능 | 선택 |

> <선택> 파라미터는 필요한 경우에만 입력

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 종목표준코드 | 테이블 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 종목번호 | ISIN | VARCHAR2(12) | KR7005930003 | 종목표준코드 |  |
| 2 | 한글종목명 | KOR_SECN_NM | VARCHAR2(100) | 삼성전자 | 종목에 부여된 한글 종목명 |  |
| 3 | 종목종류 | SECN_KACD_NM | VARCHAR2(10) | 보통주 | 보통주,우선주,2우선주 ~ |  |
| 4 | 권리기준일자 | RGT_STD_DT | VARCHAR2(8) | 20171231 | 권리가 발생하는 기준일자 |  |
| 5 | 액면가 | PVAL | NUMBER(15,4) | 5000 | 주권에 표시되어 있는 가격 |  |
| 6 | 주식배정비율 | STK_ALOC_RATIO | NUMBER(23,18) | 0 | 권리발행의 주식배정비율 |  |
| 7 | 현금배정비율 | CASH_ALOC_RATIO | NUMBER(23,18) | 430 | 권리발행의 현금배정비율 |  |
| 8 | 현금배정금액 | CASH_ALOC_AMT | NUMBER(30,20) | 21500 | 1주당 현금배정금액(원화) |  |
| 9 | 시가배당율 | MARTP_DIV_RATE | NUMBER(23,18) | 0.9 | 권리발행의 시가배당율 |  |
| 10 | 배당지급일(현금) | TH1_PAY_TERM_BEGIN_DT | VARCHAR2(8) | 20180423 | 권리 지급에 대한 1차지급기간시작일자 |  |
| 11 | 교부일자(주식) | DELI_DT | VARCHAR2(8) |  | 해당 권리일정에 대한 회차별 교부일자 |  |
| 12 | 대주주기타차등배정여부 | MAJSHR_ETC_DIFF_ALOC_YN | CHAR(1) | N | 배당정책상 대주주가 소액주주보다 낮은 배당률을 받는 지여부 |  |
| 13 | 자사주무배정여부 | TSTK_NOAGN_YN | CHAR(1) | Y | 자사주 무배당여부 |  |
| 14 | 현금차등배당금액 | CASH_DIFF_DIVIAMT_VAL | NUMBER(30,20) |  | 차등배당이 있는 경우, 현금차등배당금액 |  |
| 15 | 현금차등배당율 | CASH_DIFF_DIVI_RATE | NUMBER(23,18) |  | 차등배당이 있는 경우, 현금차등배당율 |  |
| 16 | 주식차등배당율 | STK_DIFF_DIVI_RATE | NUMBER(23,18) |  | 차등배당이 있는 경우, 주식차등배당율 |  |
| 17 | 시가차등배당율 | MARTP_DIFF_DIVI_RATE | NUMBER(23,18) |  | 차등배당이 있는 경우, 시가차등배당율 |  |

## `getOddLotInfo`

**단주대금 정보** · 원본 시트 `기업_단주대금`

단주대금 사유, 기준일 등 관련정보

- 포털은 두 변수를 `필수선택`으로 표시합니다. 두 변수를 함께 넣은 기본 TEST는 1건을 반환했고, HTTPS로 각 변수만 넣은 두 요청은 각각 0건을 반환했습니다.

원본 호출 예시

```text
http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp?key={SEIBRO_API_KEY}&apiId=getOddLotInfo&params=ISSUCO_CUSTNO:10364,TH1_PAY_TERM_BEGIN_DT:20180709
```

### 요청 파라미터

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 필수여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 발행회사고객번호 | ISSUCO_CUSTNO | NUMBER(10) | 10364 | 예탁결제원이 부여한 고객번호 | 필수선택 |
| 2 | 대금지급일 | TH1_PAY_TERM_BEGIN_DT | VARCHAR2(8) | 20180709 | 권리 지급에 대한 1차지급기간시작일자 | 필수선택 |

### 출력 필드

| No. | 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 권리기준일자 | RGT_STD_DT | VARCHAR2(8) | 20180611 | 권리가 발생하는 기준일자 |  |
| 2 | 권리사유코드 | RGT_RACD | CHAR(3) | 102 | 권리사유명(RGT_RACD_NM) 참조 |  |
| 3 | 권리사유명 | RGT_RACD_NM | VARCHAR2(200) | 무상증자 | 권리사유코드(RGT_RACD)에 대한 설명 |  |
| 3 | 권리사유세부유형코드 | RGT_RSN_DTAIL_SORT_CD | CHAR(2) | 99 | 01 주식배당<br>02 현금배당<br>03 동시배당<br>04 무배당<br>11 이익분배<br>12 청산분배<br>21 흡수합병<br>22 신설합병<br>31 무상감자<br>32 유상감자<br>41 소규모합병<br>42 상장<br>43 주식매수청구<br>90 미정<br>99 기타 |  |
| 4 | 산정기준구분코드 | ESTM_STD_TPCD | CHAR(2) | 04 | [04]상장일종가<br>[10]액면가<br>[05]상장일전일종가<br>[99]기타<br>[90]해당없음<br>[06]상장일익일종가<br>[01]기준일종가<br>[02]기준일전일종가<br>[03]기준일익일종가<br>[07]주총일종가<br>[08]주총일전일종가<br>[09]주총일익일종가 |  |
| 5 | 산정기준일자 | ESTM_STD_DT | VARCHAR2(8) | 20180702 | 대금산정의 산정기준일자 |  |
| 6 | 산정기준가 | ESTM_STDPRC | NUMBER(9) | 3175 | 단주대금기준가 등 산정기준가 |  |
| 7 | 명부폐쇄시작일자 | ROST_CLOSE_BEGIN_DT | VARCHAR2(8) |  | 명부폐쇄 시작일 |  |
| 8 | 명부폐쇄종료일자 | ROST_CLOSE_EXPRY_DT | VARCHAR2(8) |  | 명부폐쇄 종료일 |  |
| 9 | 권리락일자 | XRGT_DT | VARCHAR2(8) | 20180608 | 권리락이 이루어진 날짜 |  |
