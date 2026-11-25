# SEIBRO 공식 Open API와 공공데이터포털 조회 비교

필요한 필드와 조회 범위가 SEIBRO 공식 Open API에 있으면 공식 API를 우선합니다. 공식 API에 필요한 기능이나 필드가 없으면 공공데이터포털 API를 확인합니다. 두 API에서 얻기 어려운 화면 상세는 공개 WebSquare에서 확인합니다. [데이터 소스 안내](../../data_sources.md)

## 기능이 겹치는 조회

| 조회 목적 | SEIBRO 공식 Open API | 공공데이터포털의 대응 조회 | 비교 기준 |
| --- | --- | --- | --- |
| 단축종목코드로 회사번호 또는 ISIN 확인 | `getIssucoCustnoByIsin`, `getStkStatInfo` | `getIssucoCustnoByShortIsin`, `getStkIsinByShortIsinN1` | 회사번호와 종목코드를 나눠 확인합니다. 두 포털 조회에서 삼성전자 단축코드 `005930`의 응답을 확인했습니다. [기업정보](15157348/openapi.json) · [주식정보](15157413/openapi.json) |
| 주주총회 일정과 안건 | `getGmeetInfo`, `getGmeetMeasureInfo` | `getGmeetInfo` | 포털의 총회일정은 발행회사번호 `issucoCustno`와 권리기준일 `rgtStdDt`로 조회합니다. 안건은 공식 안건 API를 사용합니다. [기업정보](15157348/openapi.json) |
| 배당 일정과 배당금 | `getDivSchedulInfo`, `getDivInfo` | `getDivInfo`, `getDiviInfo_V2` | 공식 `getDivInfo`의 기준일 범위와 예탁결제원 포털 API의 단일 `rgtStdDt`를 대조합니다. 금융위원회 배당의 조회 기준일과 배당기준일은 별도 필드입니다. [기업정보](15157348/openapi.json) · [주식배당](15043284/openapi.json) |
| 주식 상장·발행·의무보호예수 | `getStkListInfo`, `getStkIncdecDetails`, `getSafeDpDutyDepoStatus` | `getStkListInfoN1`, `getIssucoStkQtyChgList`, `getSafeDpDutyDepoStatusN1`, `getLockUpRetuInfo_V3` | 공식 상장 조회는 변경일 범위, 포털의 `getStkListInfoN1`은 ISIN을 받습니다. 의무보호예수는 예수·반환 구분과 기준일을 확인합니다. [주식정보](15157413/openapi.json) · [기업정보](15157348/openapi.json) · [주식발행](15043423/openapi.json) |
| 종목별 주식 대차 | `getSlbDealingByIsin` | `getSlbDealingByIsin`, `getStItemLendAndBorrStatu_V2` | 공식 API는 `ISIN`과 `STD_DT`를 필수로 표시합니다. 예탁결제원 포털 API는 필수 `isin`만으로 응답한 표본이 있으므로 조회일을 맞출 때 각 응답의 기준일을 확인합니다. [증권대차](15157426/openapi.json) · [주식대차](15059612/openapi.json) |
| 채권 발행·종목·조기상환 | `getBondIssuInfo`, `getBondStatInfo`, `getBondOptionXrcInfo` | `getIssurBondIssuDetailsInfo`, `getBondBasiInfo_V2`, `getBondErlyRedInfo`, `getEarlExerOpti_V2` | 발행일·발행회사·채권 ISIN이 각각 어느 요청의 검색 기준인지 확인합니다. 원리금확정 일정은 지급일 범위와 ISIN을 받는 `getPrinFixInfoSchSvc`로 확인했습니다. [채권정보](15157416/openapi.json) · [채권기본](15059592/openapi.json) · [채권권리행사](15059595/openapi.json) |
| CD·전자단기사채 종목정보 | `getCDInfo`, `getESTBInfo` | `getCdSecnInfo`, `getSTBInfo` | ISIN을 맞춘 뒤 발행·만기·잔량 등 비교에 사용할 출력 항목을 확인합니다. [단기금융증권정보](15157428/openapi.json) |
| 파생결합증권 상세·기초자산·상환조건 | `getDerivCombiIsinInfo`, `getAssetInfo`, `getAssetXrcInfo`, `getRedCondiInfo` | `getDerivCombiIsinInfoN1`, `getAssetInfoN1`, `getAssetXrcInfoN1`, `getRedCondiInfoN1` | ISIN 표기와 자료 범위를 확인합니다. 공식 API의 일부 레코드 태그는 대문자 `RESULT`이고 포털의 검증 표본은 `response/body/items/item`을 사용했습니다. [파생결합증권정보](15157429/openapi.json) |
| 외화증권 결제현황 | `getNationFrsecSetlInfo`, `getSecnFrsecSetlInfo` | `getForeSecuSettInfo_V2`, `getMarkForeSecuSettStat_V2` | 검색 조건과 집계 단위가 국가·시장·종목 중 어디에 해당하는지 확인합니다. [국제거래외화증권예탁결제](15043445/openapi.json) |

## 공공데이터포털에서 확인할 수 있는 추가 조회

| 조회 목적 | 서비스 명세 |
| --- | --- |
| 예탁수량·전자등록·결제·대차 등 월별 통계 | [한국예탁결제원 증권예탁통계](15157347/openapi.json) |
| REPO 거래·잔액·담보와 종목 금리 | [한국예탁결제원 REPO정보](15157427/openapi.json) · [금융위원회 REPO거래](15059598/openapi.json) · [금융위원회 REPO종목](15059610/openapi.json) |
| 크라우드펀딩 발행기업과 중개업자 | [크라우드펀딩정보](15059613/openapi.json) · [크라우드펀딩중개업자정보](15043360/openapi.json) |
| 금융용어 사전 | [한국예탁결제원 금융용어](15158905/openapi.json) |

[SEIBRO 공식 Open API 색인](../README.md) · [공공데이터포털 서비스 색인](README.md) · [대표 요청과 응답](verification.md)
