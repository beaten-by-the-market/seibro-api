# 시나리오 노트북

`seibro_api` 패키지로 예탁결제원(SEIBRO) 데이터를 실제 분석 질문에 쓰는 예시입니다. 노트북마다 Colab에서 바로 열 수 있고, 실행 결과가 저장돼 있어 열기만 해도 결과를 볼 수 있습니다.

| 번호 | 노트북 | 질문 예시 | 쓰는 데이터 | 필요한 키 |
|---|---|---|---|---|
| 1-01 | [희석주식수 분석](1_stock/01_dilution.md) | "CB·BW가 다 전환되면 주식수가 얼마나 늘어?", "보호예수 물량은?" | KRX 상장주식수, SEIBRO 주식관련사채·행사 내역·의무보유·주식 증감 | `SEIBRO_API_KEY`, `KRX_ID`/`KRX_PW` |
| 1-02 | [종목별 주총 일정과 안건](1_stock/02_shareholder_meetings.md) | "삼성전자 주총은 언제 열렸고 어떤 안건이 나왔어?" | SEIBRO Open API | `SEIBRO_API_KEY` |
| 2-01 | [일자별 발행 채권](2_bond/01_issued_bonds_by_date.md) | "11월 23일에 발행된 회사채 보여줘", "이번 달 CB 발행 회사는?" | SEIBRO 채권 발행 목록·상세 | `SEIBRO_API_KEY` |
| 2-02 | [미상환 CB·BW 잔액 대조](2_bond/02_outstanding_bond_reconciliation.md) | "정기보고서 잔액과 지금 잔액이 얼마나 달라?" | DART 정기보고서, SEIBRO 공식 API와 웹 상세 | `DART_API_KEY`, `SEIBRO_API_KEY` |

## Colab에서 쓰기
1. 표의 노트북을 열고 상단 "Open in Colab" 배지를 누릅니다.
2. 왼쪽 🔑(Secrets)에 필요한 키를 넣고 "노트북 액세스"를 켭니다.
   - `SEIBRO_API_KEY`: [SEIBRO OpenPlatform](https://seibro.or.kr/OpenPlatform/)에서 신청
   - `DART_API_KEY`: [OpenDART](https://opendart.fss.or.kr/)에서 신청
   - `KRX_ID` / `KRX_PW`: KRX 정보데이터시스템 계정 ([krx-data-api](https://github.com/beaten-by-the-market/krx-data-api) 참고)
3. 위에서부터 실행합니다. 첫 셀이 `seibro-api`(필요하면 `krx-data-api`도)를 GitHub에서 설치합니다.

## 로컬에서 고치고 다시 만들기
노트북(`.ipynb`)은 직접 고치지 않습니다. 원본을 고친 뒤 빌더로 다시 만듭니다.

```bash
pip install -e .                     # 이 레포 (krx-data-api 도 필요하면 같은 방식으로)
pip install nbformat nbclient ipykernel
python scenarios/_tools/build.py              # 전체 다시 실행·저장
python scenarios/_tools/build.py 1_stock/01   # 하나만
python scenarios/_tools/show.py scenarios/1_stock/01_dilution.ipynb   # 출력 확인
```

```
scenarios/
├── _src/<유형>/<번호>_<이름>.py   # 원본 (# %% [markdown] / # %% 셀 구분). 여기를 고친다
├── _tools/
│   ├── build.py            # 원본 → 실행된 .ipynb (Colab 배지·설치 셀·공통 셀 삽입, 키 누출 검사)
│   ├── seibro_helper.py    # 모든 노트북의 공통 셀 (Secrets → 환경변수, 표시 옵션, 한글 폰트)
│   └── show.py             # 실행된 노트북의 출력을 터미널에서 확인
└── <유형>/<번호>_<이름>.ipynb + .md   # 실행 결과 포함 노트북 + 짧은 설명
```

- 로컬 실행 폴더는 레포 루트라서 `.env`의 `SEIBRO_API_KEY`를 씁니다. KRX 계정은 `krx-data-api`를 편집 설치(`pip install -e`)했다면 그 레포의 `.env`를 패키지가 직접 읽습니다.
- SEIBRO Open API는 키를 URL 쿼리에 넣고, 응답 XML에도 키가 `vectorkey` 속성으로 되돌아옵니다. 원시 URL과 응답 출력은 피하세요. `build.py`는 저장 전에 코드와 출력을 검사합니다. 실행 오류나 자격증명 탐지가 발생하면 이전 파일을 보존합니다.
- `seibro_helper.py`를 고치면 모든 노트북을 다시 빌드하세요.
