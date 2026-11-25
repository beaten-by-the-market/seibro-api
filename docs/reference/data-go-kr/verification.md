# 공공데이터포털 Open API 호출 검증

2026-11-25 승인된 개발계정으로 서비스 30개의 대표 GET 요청을 실행했습니다. 아래 URL의 인증키는 자리표시자입니다.

대표 조회 30개 모두 HTTP `200`과 서비스 코드 `00`, 응답 레코드를 확인했습니다. 한국예탁결제원 서비스는 XML, 금융위원회 서비스는 `resultType=json`을 지정해 JSON으로 확인했습니다. 두 형식 모두 검증한 레코드의 경로는 `response/body/items/item`입니다.

Swagger의 `host`에는 `apis.data.go.kr`과 서비스 경로가 함께 기재돼 있습니다. 아래 예시 URL은 `https://`와 서비스 경로, 조회 기능을 결합했습니다. 직접 브라우저에서 확인할 때는 서비스 상세의 **활용정보 → OpenAPI 실행 준비 → OpenAPI 호출** 순으로 진행합니다.

## 명세와 실측에서 확인한 차이

- 금융위원회 국제거래외화증권예탁결제의 `getForeSecuSettInfo_V2`는 Swagger에 `dataSqno`가 정의돼 있습니다. 동일 조건의 JSON 두 페이지와 XML 첫 페이지의 표본에서는 이 필드를 확인하지 못했습니다. [실측 결과](#api-15043445)
- 한국예탁결제원 일부 API는 데이터가 없을 때 HTTP `200`과 서비스 코드 `3`(`NODATA_ERROR`)을 반환합니다. 일부 금융위원회 조회에서는 HTTP `200`, 서비스 코드 `00`, 빈 `items`가 함께 반환됐습니다. [채권정보](#api-15157416) · [주식배당](#api-15043284)
- 원리금확정 정보의 지급일 범위와 ISIN을 포털 Swagger 화면에 입력해 HTTP `200`, 코드 `00`, XML 1건을 확인했습니다. [원리금확정 정보](#채권-원리금확정-정보-포털-화면-검증)

## 서비스별 대표 호출

### API 15157413

한국예탁결제원_주식정보서비스_GW · [getStkIsinByShortIsinN1 공식 명세](https://www.data.go.kr/data/15157413/openapi.do)

```http
GET https://apis.data.go.kr/B552481/StockSvc/getStkIsinByShortIsinN1?serviceKey={SERVICE_KEY}&pageNo=1&numOfRows=1&shortIsin=005930
```

- HTTP `200`, 서비스 코드 `00`, XML. 레코드 1건 반환, 응답의 전체 건수 1건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `isin`, `issucoCustno`, `korSecnNm`, `engSecnNm`, `shotnIsin`, `issuDt`, `secnKacdNm`, `eltscYn`.

### API 15157348

한국예탁결제원_기업정보서비스_GW · [getIssucoCustnoByShortIsin 공식 명세](https://www.data.go.kr/data/15157348/openapi.do)

```http
GET https://apis.data.go.kr/B552481/CorpSvc/getIssucoCustnoByShortIsin?serviceKey={SERVICE_KEY}&shortIsin=005930
```

- HTTP `200`, 서비스 코드 `00`, XML. 레코드 1건 반환, 응답의 전체 건수 1건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `issucoCustno`, `issucoNm`, `listNm`.

### API 15157347

한국예탁결제원_증권예탁통계서비스_GW · [getSecDepoStat 공식 명세](https://www.data.go.kr/data/15157347/openapi.do)

```http
GET https://apis.data.go.kr/B552481/SecDepoStat/getSecDepoStat?serviceKey={SERVICE_KEY}&sch_std_yymm=202512
```

- HTTP `200`, 서비스 코드 `00`, XML. 레코드 1건 반환, 응답의 전체 건수 1건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `vctfListDepoStkqty`, `unlsDepoStkqty`, `listBondDepoAmt`, `unlsBondDepoAmt`.

### API 15157426

한국예탁결제원_증권대차서비스_GW · [getSlbDealingByIsin 공식 명세](https://www.data.go.kr/data/15157426/openapi.do)

```http
GET https://apis.data.go.kr/B552481/SlbSvc/getSlbDealingByIsin?serviceKey={SERVICE_KEY}&isin=KR7005930003
```

- HTTP `200`, 서비스 코드 `00`, XML. 레코드 5건 반환, 응답의 전체 건수 5건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `stdDt`, `slbTrRemQty`, `matcQty`, `redQty`.

### API 15157429

한국예탁결제원_파생결합증권정보서비스_GW · [getMonthlyIssuRedStatusN1 공식 명세](https://www.data.go.kr/data/15157429/openapi.do)

```http
GET https://apis.data.go.kr/B552481/DerivesSvc/getMonthlyIssuRedStatusN1?serviceKey={SERVICE_KEY}&pageNo=1&numOfRows=1&yyyymm=202512
```

- HTTP `200`, 서비스 코드 `00`, XML. 레코드 1건 반환, 응답의 전체 건수 1건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `yyyymm`, `elsIssuSecncnt`, `elsIssuAmt`, `elsEarlyredSecncnt`, `elsEarlyredAmt`, `elsRedSecncnt`, `elsRedAmt`, `dlsIssuKrwSecncnt`, `dlsIssuKrwAmt`, `dlsEarlyredKrwSecncnt`, `dlsEarlyredKrwAmt`, `dlsRedKrwSecncnt`, `dlsRedKrwAmt`, `dlsIssuNkrwSecncnt`, `dlsIssuNkrwAmt`, `dlsEarlyredNkrwSecncnt`, `dlsEarlyredNkrwAmt`, `dlsRedNkrwSecncnt`, `dlsRedNkrwAmt`, `elwIssuSecncnt`, `elwIssuAmt`, `elwEarlyredSecncnt`, `elwEarlyredAmt`, `elwRedSecncnt`, `elwRedAmt`.
- 앞선 표본 `/getDerivCombiIsinInfoN1`의 `isin=KR6539335879`에서 HTTP `200`, 서비스 코드 `3`, 레코드 0건를 확인했습니다.

### API 15157427

한국예탁결제원_REPO정보서비스_GW · [getCurRepoRem 공식 명세](https://www.data.go.kr/data/15157427/openapi.do)

```http
GET https://apis.data.go.kr/B552481/RepoSvc/getCurRepoRem?serviceKey={SERVICE_KEY}&std_dt=20251230&cur_cd=KRW
```

- HTTP `200`, 서비스 코드 `00`, XML. 레코드 1건 반환, 응답의 전체 건수 1건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `repoRema`.

### API 15157416

한국예탁결제원_채권정보서비스_GW · [getRgtXrcInfo 공식 명세](https://www.data.go.kr/data/15157416/openapi.do)

```http
GET https://apis.data.go.kr/B552481/BondSvc/getRgtXrcInfo?serviceKey={SERVICE_KEY}&schStdYy=2025
```

- HTTP `200`, 서비스 코드 `00`, XML. 레코드 1건 반환, 응답의 전체 건수 1건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `exerCost`, `texerCount`.
- 지급일 범위와 ISIN을 함께 받는 [원리금확정 정보 조회](#채권-원리금확정-정보-포털-화면-검증)도 확인했습니다.
- 앞선 표본 `/getIssurBondIssuDetailsInfo`의 `issucoCustno=593`에서 HTTP `200`, 서비스 코드 `3`, 레코드 0건를 확인했습니다.

### API 15157414

한국예탁결제원_국제거래정보서비스_GW · [getNationCdSch 공식 명세](https://www.data.go.kr/data/15157414/openapi.do)

```http
GET https://apis.data.go.kr/B552481/OverseaSvc/getNationCdSch?serviceKey={SERVICE_KEY}&pageNo=1&numOfRows=1
```

- HTTP `200`, 서비스 코드 `00`, XML. 레코드 1건 반환, 응답의 전체 건수 295건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `nationCd`, `nationNm`, `nationEngNm`.

### API 15157428

한국예탁결제원_단기금융증권정보서비스_GW · [getCdSecnInfo 공식 명세](https://www.data.go.kr/data/15157428/openapi.do)

```http
GET https://apis.data.go.kr/B552481/ShortmSvc/getCdSecnInfo?serviceKey={SERVICE_KEY}&isin=KRZE03901G8S
```

- HTTP `200`, 서비스 코드 `00`, XML. 레코드 2건 반환, 응답의 전체 건수 2건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `korSecnNm`, `issuAmt`, `issuDt`, `xpirDt`.

### API 15158905

한국예탁결제원_금융용어조회서비스_GW · [getFinancialTermMeaning 공식 명세](https://www.data.go.kr/data/15158905/openapi.do)

```http
GET https://apis.data.go.kr/B552481/FnTermSvc/getFinancialTermMeaning?serviceKey={SERVICE_KEY}&pageNo=1&numOfRows=1&term=%EA%B3%B5%EB%A7%A4%EB%8F%84
```

- HTTP `200`, 서비스 코드 `00`, XML. 레코드 1건 반환, 응답의 전체 건수 1건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `fnceDictNm`, `ksdFnceDictDescContent`.
- 앞선 표본 `/getFinancialTermMeaning`의 `term=대량주식 보유상황 공시제도`에서 HTTP `200`, 서비스 코드 `3`, 레코드 0건를 확인했습니다.

### API 15043284

금융위원회_주식배당정보 · [getDiviInfo_V2 공식 명세](https://www.data.go.kr/data/15043284/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetStocDiviInfoService_V2/getDiviInfo_V2?serviceKey={SERVICE_KEY}&pageNo=1&numOfRows=1&resultType=json
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 71664건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `basDt`, `crno`, `isinCd`, `stckIssuCmpyNm`, `isinCdNm`, `scrsItmsKcd`, `scrsItmsKcdNm`, `stckParPrc`, `trsnmDptyDcd`, `trsnmDptyDcdNm`, `stckStacMd`, `dvdnBasDt`, `cashDvdnPayDt`, `stckHndvDt`, `stckDvdnRcd`, `stckDvdnRcdNm`, `stckGenrDvdnAmt`, `stckGrdnDvdnAmt`, `stckGenrCashDvdnRt`, `stckGenrDvdnRt`, `cashGrdnDvdnRt`, `stckGrdnDvdnRt`.
- 앞선 표본 `/getDiviInfo_V2`의 `basDt=20260708`, `crno=1101110013287`, `stckIssuCmpyNm=경방`에서 HTTP `200`, 서비스 코드 `00`, 레코드 0건를 확인했습니다.

### API 15043423

금융위원회_주식발행정보 · [getItemBasiInfo_V3 공식 명세](https://www.data.go.kr/data/15043423/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetStocIssuInfoService_V3/getItemBasiInfo_V3?serviceKey={SERVICE_KEY}&pageNo=1&numOfRows=1&resultType=json&basDt=20260705&crno=0000001253404&stckIssuCmpyNm=%EC%99%84%EB%A6%AC%EC%9D%B8%ED%84%B0%EB%82%B4%EC%85%94%EB%84%90%ED%99%80%EB%94%A9%EC%8A%A4
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 1건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `basDt`, `crno`, `isinCd`, `stckIssuCmpyNm`, `isinCdNm`, `scrsItmsKcd`, `scrsItmsKcdNm`, `stckParPrc`, `issuStckCnt`, `lstgDt`, `lstgAbolDt`, `dpsgRegDt`, `dpsgCanDt`, `issuFrmtClsfNm`, `itmsShrtnCd`.
- 앞선 표본 `/getStocIssuInfo_V3`의 `basDt=20260704`, `crno=1101110002959`, `stckIssuCmpyNm=한화`에서 HTTP `200`, 서비스 코드 `00`, 레코드 0건를 확인했습니다.
- 앞선 표본 `/getStocIssuInfo_V3`의 `basDt=20260704`에서 HTTP `200`, 서비스 코드 `00`, 레코드 0건를 확인했습니다.

### API 15059582

금융위원회_국제거래종목정보 · [getDepoReceItem_V2 공식 명세](https://www.data.go.kr/data/15059582/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetDrTradItemInfoService_V2/getDepoReceItem_V2?serviceKey={SERVICE_KEY}&numOfRows=1&pageNo=1&resultType=json&basDt=20260713&crno=1101110000086
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 1건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `basDt`, `crno`, `isinCd`, `isinCdNm`, `drIssuCmpyNm`, `stckKcd`, `stckKcdNm`, `orshIsinCdNm`, `orshIsinCd`, `itmsShrtnCd`, `itmsShrtnCdNm`, `orshDrRto`, `drDcd`, `drDcdNm`, `drCnvrPsblLmtTsumCnt`, `drCnvrPsblStckCnt`, `drCnvrOrshCnt`, `drXchgDcd`, `drXchgDcdNm`, `drDpsgInstNm`.

### API 15059609

금융위원회_주식권리일정정보 · [getRighExerReasSche_V2 공식 명세](https://www.data.go.kr/data/15059609/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetStocRighScheService_V2/getRighExerReasSche_V2?serviceKey={SERVICE_KEY}&numOfRows=1&pageNo=1&resultType=json&basDt=20260901&issuCmpyKsdCustNo=8472&stckIssuCmpyNm=%ED%95%9C%EC%A0%84KPS
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 5건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `basDt`, `issuCmpyKsdCustNo`, `crno`, `stckIssuCmpyNm`, `stckParPrc`, `stckIssuRcd`, `stckIssuRcdNm`, `rgtExertRcdNm`, `rgtExertSttgDt`, `rgtExertEdDt`, `trsnmDptyDcd`, `trsnmDptyDcdNm`, `stckStacMd`, `nmlsLckSttgDt`, `nmlsLckEdDt`, `scrsIssuMnbdCd`, `scrsIssuMnbdCdNm`, `rgtExertRcd`.

### API 15043445

금융위원회_국제거래외화증권예탁결제정보 · [getForeSecuSettInfo_V2 공식 명세](https://www.data.go.kr/data/15043445/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetDrForeSecuSettInfoService_V2/getForeSecuSettInfo_V2?serviceKey={SERVICE_KEY}&pageNo=1&numOfRows=1&resultType=json&frcrScrtDpsgStlDt=20200305
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 43건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `frcrScrtDpsgStlDt`, `scrsDcd`, `scrsDcdNm`, `scrsMrktNtnlDcd`, `scrsMrktNtnlDcdNm`, `dpsgScrtSlngCcnt`, `buynCcnt`.
- Swagger 정의 중 이 호출 표본에서 확인되지 않은 필드 `dataSqno`.
- 같은 조회 조건의 `pageNo=2&resultType=json` 및 `pageNo=1&resultType=xml` 응답에서도 `dataSqno`가 관찰되지 않았습니다.

### API 15059612

금융위원회_주식대차정보 · [getStLendAndBorrItemRank_V2 공식 명세](https://www.data.go.kr/data/15059612/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetStocLendBorrInfoService_V2/getStLendAndBorrItemRank_V2?serviceKey={SERVICE_KEY}&numOfRows=1&pageNo=1&resultType=json&basDt=20260825
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 2774건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `basDt`, `isinCd`, `lnbScrtDcd`, `lnbScrtDcdNm`, `isinCdNm`, `lnbCclStckCnt`, `rcalRdptStckCnt`, `rdptStckCnt`, `lnbRmanStckCnt`, `lnbBal`.

### API 15059607

금융위원회_주식등록예탁가능정보 · [getDepoAvaiWhet_V2 공식 명세](https://www.data.go.kr/data/15059607/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetStocDepoInfoService_V2/getDepoAvaiWhet_V2?serviceKey={SERVICE_KEY}&numOfRows=1&pageNo=1&resultType=json&basDt=20261006&crno=0000000000000&stckIssuCmpyNm=%ED%97%9D%EC%85%A9%EA%B7%B8%EB%A3%B9
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 1건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `basDt`, `crno`, `isinCd`, `stckIssuCmpyNm`, `isinCdNm`, `scrsItmsKcd`, `scrsItmsKcdNm`, `lstgDt`, `lstgAbolDt`, `dpsgRegDt`, `lstgDcd`, `lstgDcdNm`, `stckIssuFrmtNm`, `dpsgRegCanDt`, `rbfLstgDcd`, `rbfLstgDcdNm`, `stckNcirRcd`, `stckNcirRcdNm`, `afrpItmsNm`, `itmsShrtnCd`.

### API 15043421

금융위원회_채권발행정보 · [getIssuIssuItemStat_V2 공식 명세](https://www.data.go.kr/data/15043421/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetBondTradInfoService_V2/getIssuIssuItemStat_V2?serviceKey={SERVICE_KEY}&pageNo=1&numOfRows=1&resultType=json
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 88544건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `basDt`, `crno`, `scrsItmsKcd`, `isinCd`, `scrsItmsKcdNm`, `bondIsurNm`, `isinCdNm`, `bondIssuDt`, `bondIssuFrmtNm`, `bondIssuAmt`, `bondIssuCurCd`, `bondIssuCurCdNm`, `bondExprDt`, `bondPymtAmt`, `irtChngDcd`, `irtChngDcdNm`, `bondSrfcInrt`, `bondIntTcd`, `bondIntTcdNm`.
- 앞선 표본 `/getIssuIssuItemStat_V2`의 `basDt=20260729`, `crno=2850110404511`, `bondIsurNm=45스페이스`에서 HTTP `200`, 서비스 코드 `00`, 레코드 0건를 확인했습니다.

### API 15059592

금융위원회_채권기본정보 · [getBondBasiInfo_V2 공식 명세](https://www.data.go.kr/data/15059592/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetBondIssuInfoService_V2/getBondBasiInfo_V2?serviceKey={SERVICE_KEY}&numOfRows=1&pageNo=1&resultType=json&basDt=20260708&crno=1111710007324&bondIsurNm=%EC%84%9C%EC%9A%B8%EC%A3%BC%ED%83%9D%EB%8F%84%EC%8B%9C%EA%B0%9C%EB%B0%9C%EA%B3%B5%EC%82%AC
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 56건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `basDt`, `crno`, `scrsItmsKcd`, `isinCd`, `scrsItmsKcdNm`, `bondIsurNm`, `isinCdNm`, `bondIssuDt`, `bondIssuAmt`, `bondIssuCurCd`, `optnTcd`, `optnTcdNm`, `bondIssuCurCdNm`, `sicNm`, `bondExprDt`, `intCmpuMcd`, `intCmpuMcdNm`, `bondPymtAmt`, `irtChngDcd`, `irtChngDcdNm`, `bondSrfcInrt`, `bondBal`, `grnDcd`, `bondIntTcd`, `bondIntTcdNm`, `grnDcdNm`, `bondRnknDcd`, `bondRnknDcdNm`, `pclrBondKcd`, `pclrBondKcdNm`, `lstgDt`, `bondOffrMcd`, `bondOffrMcdNm`, `txtnDcd`, `txtnDcdNm`, `pamtRdptMcd`, `pamtRdptMcdNm`, `stripsPsblYn`, `stripsNm`, `prisLnkgBondYn`, `piamPayInstNm`, `piamPayBrofNm`, `cptUsgeDcd`, `cptUsgeDcdNm`, `bondRegInstDcd`, `bondRegInstDcdNm`, `issuDptyNm`, `bondUndtInstNm`, `bondGrnInstNm`, `cpbdMngCmpyNm`, `crfndYn`, `prmncBondYn`, `qibTrgtScrtYn`, `prmncBondTmnDt`, `rgtExertMnbdDcd`, `rgtExertMnbdDcdNm`, `qibTmnDt`, `intPayCyclCtt`, `nxtmCopnDt`, `rbfCopnDt`, `bnkHldyIntPydyDcd`, `bnkHldyIntPydyDcdNm`, `sttrHldyIntPydyDcd`, `sttrHldyIntPydyDcdNm`, `intPayMmntDcd`, `intPayMmntDcdNm`, `elpsIntPayYn`, `kisScrsItmsKcd`, `kisScrsItmsKcdNm`, `kbpScrsItmsKcd`, `kbpScrsItmsKcdNm`, `niceScrsItmsKcd`, `niceScrsItmsKcdNm`, `fnScrsItmsKcd`, `fnScrsItmsKcdNm`.

### API 15059591

금융위원회_단기금융증권발행정보 · [getCdIssuBasiInfo_V2 공식 명세](https://www.data.go.kr/data/15059591/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetShorTermSecuIssuInfoService_V2/getCdIssuBasiInfo_V2?serviceKey={SERVICE_KEY}&numOfRows=1&pageNo=1&resultType=json&basDt=20260902
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 293건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `basDt`, `isinCd`, `scrsDcd`, `scrsDcdNm`, `codpIssuHdofNo`, `codpIssuBnkNm`, `isinCdNm`, `codpIssuDt`, `codpExprDt`, `codpParPrc`, `codpSaleAmt`, `codpIssuAmt`, `codpDcRat`, `codpIssuFrmtNm`, `codpRdptDt`, `codpIssuCurCd`, `codpIssuCurCdNm`, `codpPayBnkNm`, `codpPayBnkBrofCd`, `codpRegDt`.

### API 15059610

금융위원회_REPO종목정보 · [getInteRateInfo_V2 공식 명세](https://www.data.go.kr/data/15059610/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetRepoItemInfoService_V2/getInteRateInfo_V2?serviceKey={SERVICE_KEY}&pageNo=1&numOfRows=1&resultType=json&basDt=20200304
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 3569건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `basDt`, `rpSqno`, `rpBuyScrtKcd`, `rpBuyScrtKcdNm`, `rpBuyAplCurCd`, `rpBuyAplCurCdNm`, `rdptTermCcd`, `rdptTermCcdNm`, `rpRmngExprDcd`, `rpRmngExprDcdNm`, `purcBzcTcd`, `purcBzcTcdNm`, `slrBzcTcd`, `slrBzcTcdNm`, `rpInrt`.

### API 15043462

금융위원회_채권대차정보 · [getBondLendAndBorrRank_V2 공식 명세](https://www.data.go.kr/data/15043462/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetBondLendBorrInfoService_V2/getBondLendAndBorrRank_V2?serviceKey={SERVICE_KEY}&pageNo=1&numOfRows=1&resultType=json&basDt=20200228&lnbScrtDcdNm=%EC%B1%84%EA%B6%8C
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 104건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `basDt`, `isinCd`, `lnbScrtDcd`, `lnbScrtDcdNm`, `isinCdNm`, `lnbBal`, `lnbCclAmt`, `lnbRdptAmt`.

### API 15059613

금융위원회_크라우드펀딩정보 · [getFundIssuCompInfo_V2 공식 명세](https://www.data.go.kr/data/15059613/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetFundInfoService_V2/getFundIssuCompInfo_V2?serviceKey={SERVICE_KEY}&numOfRows=1&pageNo=1&resultType=json&basDt=20200317&fundIssuCmpyNm=%EB%A7%88%EC%9D%B4%EB%B9%84
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 1건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `basDt`, `fundIssuCmpyNm`, `fundTofrAmt`, `fundOffrSttgDt`, `fundOffrEdDt`, `fundSbscAmt`, `fundSbscRt`, `fundInvsCnt`, `fundIssuCmpyRprsBzcNm`.

### API 15059611

금융위원회_채권권리일정정보 · [getBondRighExerSche_V2 공식 명세](https://www.data.go.kr/data/15059611/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetBondRighScheInfoService_V2/getBondRighExerSche_V2?serviceKey={SERVICE_KEY}&numOfRows=1&pageNo=1&resultType=json&basDt=20220925&crno=1101710029402&bondIsurNm=%ED%95%9C%EA%B5%AD%EC%A3%BC%ED%83%9D%EA%B8%88%EC%9C%B5%EA%B3%B5%EC%82%AC
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 44건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `basDt`, `crno`, `scrsItmsKcd`, `isinCd`, `scrsItmsKcdNm`, `bondIsurNm`, `isinCdNm`, `bondIssuDt`, `bondIssuFrmtNm`, `bondIssuAmt`, `scrsScedDcd`, `bondExprDt`, `scrsScedDcdNm`, `irtChngDcd`, `irtChngDcdNm`, `bondIntTcd`, `bondIntTcdNm`.

### API 15043446

금융위원회_단기금융증권거래정보 · [getCaseBuyAndSellInfo_V2 공식 명세](https://www.data.go.kr/data/15043446/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetShorTermSecuTradInfoService_V2/getCaseBuyAndSellInfo_V2?serviceKey={SERVICE_KEY}&pageNo=1&numOfRows=1&resultType=json&basDt=20200228
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 2450건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `basDt`, `shtrFinPrdDcd`, `isinCd`, `stlSqno`, `slngShtrFinBzcDcd`, `shtrFinPrdDcdNm`, `curCd`, `slngShtrFinBzcDcdNm`, `curCdNm`, `buynShtrFinBzcDcd`, `buynShtrFinBzcDcdNm`, `isinCdNm`, `shtrPrdRmngExprDcd`, `shtrPrdRmngExprDcdNm`, `shtrFinPrdTrdAmt`, `shtrFinPrdIrt`, `shtrFinPrdIssuDt`, `shtrFinPrdExprDt`.

### API 15043461

금융위원회_신주인수권증권발행정보 · [getPreeRighSecuBasiInfo_V2 공식 명세](https://www.data.go.kr/data/15043461/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetPreeRighSecuIssuInfoService_V2/getPreeRighSecuBasiInfo_V2?serviceKey={SERVICE_KEY}&pageNo=1&numOfRows=1&resultType=json
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 90737건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `basDt`, `crno`, `isinCd`, `isinCdNm`, `itmsShrtnCd`, `prmrIsurNm`, `lstgDcd`, `lstgDcdNm`, `prmrExertPrc`, `prmrIssuDt`, `prmrExertPsblSttgDt`, `prmrExertPsblEdDt`.
- 앞선 표본 `/getPreeRighSecuBasiInfo_V2`의 `crno=1101110004286`, `prmrIsurNm=팬오션`에서 HTTP `200`, 서비스 코드 `00`, 레코드 0건를 확인했습니다.

### API 15059598

금융위원회_REPO거래정보 · [getCaseForTrad_V2 공식 명세](https://www.data.go.kr/data/15059598/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetRepoTradInfoService_V2/getCaseForTrad_V2?serviceKey={SERVICE_KEY}&numOfRows=1&pageNo=1&resultType=json&basDt=20260917
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 19937건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `basDt`, `rpSqno`, `rpBuyAplCurCd`, `rpBuyAplCurCdNm`, `rdptTermCcd`, `rdptTermCcdNm`, `rpRmngExprDcd`, `rpRmngExprDcdNm`, `rpInrt`, `slngShtrFinBzcDcd`, `slngShtrFinBzcDcdNm`, `buynShtrFinBzcDcd`, `buynShtrFinBzcDcdNm`, `rpOpngDt`, `rpBuyAmt`, `rpMrgamRto`, `scrsItmsKcd`, `scrsItmsKcdNm`, `isinCd`, `isinCdNm`, `buyScrtCnt`, `buyScrtBuyAmt`, `buyScrtEvlAmt`.

### API 15043360

금융위원회_크라우드펀딩중개업자정보 · [getFundBrokInfo_V2 공식 명세](https://www.data.go.kr/data/15043360/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetFundBrokInfoService_V2/getFundBrokInfo_V2?serviceKey={SERVICE_KEY}&pageNo=1&numOfRows=1&resultType=json&basDt=20220926&fundBrkrNm=%ED%8E%80%EB%8D%94%ED%92%80
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 1건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `basDt`, `fundBrkrSqno`, `fundBrkrNm`, `scrsDcd`, `scrsDcdNm`, `fundIssuAmt`.

### API 15043364

금융위원회_주식분포및사고주권정보 · [getIrreRigforSecu_V2 공식 명세](https://www.data.go.kr/data/15043364/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetStocTradInfoService_V2/getIrreRigforSecu_V2?serviceKey={SERVICE_KEY}&pageNo=1&numOfRows=1&resultType=json&basDt=20260728&crno=1101110150138&stckIssuCmpyNm=%EB%8C%80%EC%9A%B0
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 973건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `basDt`, `crno`, `isinCd`, `stckIssuCmpyNm`, `isinCdNm`, `scrsDcd`, `scrsDcdNm`, `stckAcdnDcd`, `stckAcdnDcdNm`, `stckIssuSqno`, `acdnScrtNoClsfNm`, `acdnScrtNo`, `acdnRgscKindCnt`.

### API 15059595

금융위원회_채권권리행사정보 · [getEarlExerOpti_V2 공식 명세](https://www.data.go.kr/data/15059595/openapi.do)

```http
GET https://apis.data.go.kr/1160100/GetBondRedeInfoService_V2/getEarlExerOpti_V2?serviceKey={SERVICE_KEY}&numOfRows=1&pageNo=1&resultType=json
```

- HTTP `200`, 서비스 코드 `00`, JSON. 레코드 1건 반환, 응답의 전체 건수 24776건.
- 레코드 경로 `response/body/items/item`. 확인한 필드 `basDt`, `crno`, `isinCd`, `bondIsurNm`, `isinCdNm`, `optnTcd`, `optnTcdNm`, `optnExertSttgDt`, `optnExertRto`, `optnExertEdDt`, `clrdDt`, `optnExertAmt`.
- 앞선 표본 `/getEarlExerOpti_V2`의 `crno=1748110007503`에서 연결 오류를 확인했습니다.

## 채권 원리금확정 정보 포털 화면 검증

공공데이터포털 채권정보서비스에서 OpenAPI 실행 준비를 누른 후 지급일 범위와 종목코드를 입력하고 OpenAPI 호출을 실행했습니다. 포털 화면과 HTTPS 직접 호출에서 같은 XML 필드와 레코드 1건을 확인했습니다. [한국예탁결제원 채권정보서비스](https://www.data.go.kr/data/15157416/openapi.do)

```http
GET https://apis.data.go.kr/B552481/BondSvc/getPrinFixInfoSchSvc?serviceKey={SERVICE_KEY}&pageNo=1&numOfRows=1&schBeginDt=20261120&schExpryDt=20261205&isin=KR6017812G82
```

- HTTP `200`, 서비스 코드 `00`, XML 1건.
- 확인한 필드 `payDt`, `rgtDmanTpcd`, `isin`, `krwYn`, `orgnPayDt`, `prinTpcd`, `depoLimitSchdDt`, `payDtFixYn`, `intPayNtimesTpcd`, `sintCintTpcd`, `discintSortTpcd`, `xtraintSortTpcd`.

[공공데이터포털 서비스 색인](README.md) · [SEIBRO 공식 Open API와 비교](overlap.md)
