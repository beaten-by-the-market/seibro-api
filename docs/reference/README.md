# SEIBRO 공식 Open API 명세

한국예탁결제원 엑셀 가이드 5종의 API 37개를 정리했습니다. API ID나 영문 필드명을 검색한 뒤 상세 페이지에서 자료형, 샘플, 필수여부, 코드표를 확인할 수 있습니다.

공식 API에 필요한 조회가 없으면 [공공데이터포털 API 명세](data-go-kr/README.md)에서 서비스와 대표 호출을 확인합니다.

2026-11-25 포털의 5개 메뉴에서 각 API의 호출변수와 TEST URL·XML 응답을 대조했습니다. 첫 순회에서 35개 API가 레코드를 반환했습니다. 0건이었던 두 API는 메뉴를 새로고침하고 다시 TEST해 각각 1건을 확인했습니다. [API 활용신청 포털](https://openplatform.seibro.or.kr/websquare/startup_control.jsp?w2xPath=/startup/api/BIP_SUAW3001.xml)

## 가이드

| 분야별 명세 | 엑셀 원본 | API 수 |
| --- | --- | --- |
| [기업정보](corp.md) | [`Guide_Corp.xlsx`](originals/Guide_Corp.xlsx) | 9 |
| [주식정보](stock.md) | [`Guide_Stock.xlsx`](originals/Guide_Stock.xlsx) | 9 |
| [채권정보](bond.md) | [`Guide_Bond.xlsx`](originals/Guide_Bond.xlsx) | 8 |
| [파생결합증권정보](derivcombi.md) | [`Guide_DerivCombi.xlsx`](originals/Guide_DerivCombi.xlsx) | 7 |
| [외화증권정보](oversea.md) | [`Guide_Oversea.xlsx`](originals/Guide_Oversea.xlsx) | 4 |

[외화증권 국가코드표](oversea.md#외화증권-국가코드)는 엑셀의 참고 시트를 옮겼습니다.

## API 색인

| API ID | 분야 | API 명 | 요청 파라미터 | 출력 필드 수 | 첫 순회 TEST 응답 건수 |
| --- | --- | --- | --- | --- | --- |
| [`getIssucoCustnoByIsin`](corp.md#getissucocustnobyisin) | 기업정보 | 발행종목으로 발행회사번호 조회 | `ISIN`, `SHOTN_ISIN` | 2 | 1 |
| [`getStddtInfo`](corp.md#getstddtinfo) | 기업정보 | 기준일 정보 | `ISSUCO_CUSTNO`, `BEGIN_STD_DT`, `EXPRY_STD_DT`, `RGT_RACD` | 6 | 3 |
| [`getGmeetInfo`](corp.md#getgmeetinfo) | 기업정보 | 총회일정 정보 | `ISSUCO_CUSTNO`, `ISSUIN_NO`, `RGT_STD_DT` | 18 | 1 |
| [`getGmeetMeasureInfo`](corp.md#getgmeetmeasureinfo) | 기업정보 | 총회안건 정보 | `ISSUCO_CUSTNO`, `ISSUIN_NO`, `RGT_STD_DT` | 16 | 11 |
| [`getFmnmAltInfo`](corp.md#getfmnmaltinfo) | 기업정보 | 상호변경 정보 | `ISSUCO_CUSTNO`, `RGT_STD_DT` | 9 | 1 |
| [`getCostPaySchedul`](corp.md#getcostpayschedul) | 기업정보 | 대금지급일정 정보 | `TH1_PAY_TERM_BEGIN_DT`, `PAY_COST_TPCD` | 7 | 124 |
| [`getDivSchedulInfo`](corp.md#getdivschedulinfo) | 기업정보 | 배당일정 정보 | `ISSUCO_CUSTNO`, `BEGIN_STD_DT`, `EXPRY_STD_DT`, `RGT_RSN_DTAIL_SORT_CD` | 12 | 9 |
| [`getDivInfo`](corp.md#getdivinfo) | 기업정보 | 배당분배금내역 정보 | `ISSUCO_CUSTNO`, `BEGIN_STD_DT`, `EXPRY_STD_DT` | 17 | 18 |
| [`getOddLotInfo`](corp.md#getoddlotinfo) | 기업정보 | 단주대금 정보 | `ISSUCO_CUSTNO`, `TH1_PAY_TERM_BEGIN_DT` | 10 | 1 |
| [`getStkStatInfo`](stock.md#getstkstatinfo) | 주식정보 | 주식 종목 정보 | `SHOTN_ISIN`, `ISIN`, `ISSUCO_CUSTNO`, `STD_DT` | 14 | 1 |
| [`getUnlistCirclInfo`](stock.md#getunlistcirclinfo) | 주식정보 | 비상장유통추정 정보 | `STD_DT`, `ISSUCO_CUSTNO`, `ISIN`, `SHOTN_ISIN` | 8 | 1 |
| [`getSlbDealingByIsin`](stock.md#getslbdealingbyisin) | 주식정보 | 종목별 대차거래 현황 | `ISIN`, `STD_DT` | 13 | 1 |
| [`getShotnByMart`](stock.md#getshotnbymart) | 주식정보 | 시장별 단축코드 조회 | `MART_TPCD` | 3 | 130 |
| [`getStkListInfo`](stock.md#getstklistinfo) | 주식정보 | 주식 상장 정보 | `ALT_BEGIN_DT`, `ALT_EXPRY_DT` | 7 | 252 |
| [`getXrcStkStatInfo`](stock.md#getxrcstkstatinfo) | 주식정보 | 주식관련사채 행사대상 주식 정보 | `BOND_ISIN`, `XRC_STK_ISIN` | 12 | 1 |
| [`getXrcStkOptionXrcInfo`](stock.md#getxrcstkoptionxrcinfo) | 주식정보 | 주식관련사채 행사내역 | `RGT_STD_DT`, `BOND_ISIN`, `XRC_POSS_BEGIN_DT` | 12 | 1 |
| [`getStkIncdecDetails`](stock.md#getstkincdecdetails) | 주식정보 | 주식증감내역 | `SHOTN_ISIN`, `ISIN`, `ISSUCO_CUSTNO`, `ISSU_YEAR` | 10 | 3 |
| [`getSafeDpDutyDepoStatus`](stock.md#getsafedpdutydepostatus) | 주식정보 | 의무보호예수/반환정보 | `ISSUCO_CUSTNO`, `BEGIN_DT`, `EXPRY_DT`, `MART_TPCD`, `BIZ_TPCD` | 12 | 1 |
| [`getBondIssuInfo`](bond.md#getbondissuinfo) | 채권정보 | 채권 발행내역 | `ISSU_DT`, `ISSUCO_CUSTNO` | 5 | 1 |
| [`getBondStatInfo`](bond.md#getbondstatinfo) | 채권정보 | 채권 종목 정보 | `ISIN` | 36 | 1 |
| [`getIntPayInfo`](bond.md#getintpayinfo) | 채권정보 | 이자지급 정보 | `ISIN` | 10 | 1 |
| [`getBondOptionXrcInfo`](bond.md#getbondoptionxrcinfo) | 채권정보 | 조기상환 정보 | `ISIN`, `ERLY_RED_DT` | 11 | 1 |
| [`getShortmIssuInfo`](bond.md#getshortmissuinfo) | 채권정보 | 단기금융증권 발행내역 | `ISSU_DT`, `SECN_TPCD` | 4 | 290 |
| [`getCDInfo`](bond.md#getcdinfo) | 채권정보 | CD 종목 정보 | `ISIN` | 12 | 1 |
| [`getCPInfo`](bond.md#getcpinfo) | 채권정보 | CP 종목 정보 | `ISIN` | 20 | 0 |
| [`getESTBInfo`](bond.md#getestbinfo) | 채권정보 | 전자단기사채 종목 정보 | `ISIN` | 15 | 1 |
| [`getDerivCombiIssuInfo`](derivcombi.md#getderivcombiissuinfo) | 파생결합증권정보 | 파생결합증권 발행내역 | `ISSU_DT`, `SECN_KACD` | 3 | 54 |
| [`getBassetUnredScale`](derivcombi.md#getbassetunredscale) | 파생결합증권정보 | 기초자산별 미상환규모 | `STD_DT`, `STND_BASSET_CD`, `SECN_TPCD` | 3 | 1 |
| [`getDerivCombiIsinInfo`](derivcombi.md#getderivcombiisininfo) | 파생결합증권정보 | 파생결합증권 종목 정보 | `ISIN` | 20 | 0 |
| [`getAssetInfo`](derivcombi.md#getassetinfo) | 파생결합증권정보 | 기초자산 정보조회 | `ISIN` | 16 | 3 |
| [`getAssetXrcInfo`](derivcombi.md#getassetxrcinfo) | 파생결합증권정보 | 기초자산 행사정보조회 | `ISIN` | 4 | 8 |
| [`getRedCondiInfo`](derivcombi.md#getredcondiinfo) | 파생결합증권정보 | 파생결합증권 상환조건조회 | `ISIN` | 7 | 10 |
| [`getRedIsinInfo`](derivcombi.md#getredisininfo) | 파생결합증권정보 | 파생결합증권 상환종목조회 | `RED_DT`, `SECN_KACD`, `DERISEC_EXER_TPCD` | 3 | 12 |
| [`getNationFrsecCusInfo`](oversea.md#getnationfrseccusinfo) | 외화증권정보 | 국가별 외화증권 보관현황 | `STD_DT`, `NATION_CD` | 2 | 4 |
| [`getNationFrsecSetlInfo`](oversea.md#getnationfrsecsetlinfo) | 외화증권정보 | 국가별 외화증권 결제현황 | `SETL_DT`, `NATION_CD` | 4 | 7 |
| [`getSecnFrsecCusInfo`](oversea.md#getsecnfrseccusinfo) | 외화증권정보 | 종목별 외화증권 보관현황 | `STD_DT`, `ISIN` | 4 | 2 |
| [`getSecnFrsecSetlInfo`](oversea.md#getsecnfrsecsetlinfo) | 외화증권정보 | 종목별 외화증권 결제현황 | `PROC_DT`, `ISIN` | 5 | 2 |

## 원본 표기 차이

엑셀의 목록, 상세 시트, 호출 예시가 서로 다른 곳입니다. 색인에는 포털에서 확인한 API ID를 사용했습니다.

| API ID | 차이 |
| --- | --- |
| [`getSafeDpDutyDepoStatus`](stock.md#getsafedpdutydepostatus) | 엑셀 URL 예시의 `apiId`가 비어 있습니다. |
| [`getBondIssuInfo`](bond.md#getbondissuinfo) | 상세 시트 ID `getBondIssuinfo` |
| [`getCDInfo`](bond.md#getcdinfo) | 목록 ID `getCDinfo` |
| [`getCPInfo`](bond.md#getcpinfo) | 목록 ID `getCPinfo` |
| [`getESTBInfo`](bond.md#getestbinfo) | 목록 ID `getESTBinfo` |
| [`getDerivCombiIssuInfo`](derivcombi.md#getderivcombiissuinfo) | 엑셀 URL 예시에만 표시된 파라미터 `SECN_TPCD` |
| [`getDerivCombiIsinInfo`](derivcombi.md#getderivcombiisininfo) | 목록 ID `getDerivCombiIssuInfo` |
| [`getRedIsinInfo`](derivcombi.md#getredisininfo) | 엑셀 URL 예시에만 표시된 파라미터 `SECN_TPCD` |

## 읽는 법

- `필수선택`의 입력 조건은 각 API의 요청 표와 주석을 함께 확인합니다. 자료형·코드표는 엑셀 가이드를 따릅니다.
- 포털 미리보기 호출 예시는 화면에 표시된 URL입니다. HTTPS 전송과 키 처리는 [Python 클라이언트](../../seibro_api/openapi/client.py)에서 맡습니다. 구현된 공개 함수는 [Python API 레퍼런스](../python_reference.md), 실측한 제약은 [데이터 소스](../data_sources.md)에 있습니다.
- 파생결합증권 일부 API는 대문자 `RESULT`를 반환합니다. 현재 Python 클라이언트는 소문자 `result`를 찾으므로 해당 응답에서 파싱 오류가 납니다.
- 문서는 엑셀 가이드와 [포털 확인 기록](portal_preview.json)에서 생성합니다. 자료를 갱신한 뒤 레포 루트에서 `python docs/reference/build_openapi_reference.py`를 실행합니다. `--check`는 저장 없이 생성 문서의 일치 여부를 검사합니다.
