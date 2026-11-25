# SEIBRO 데이터 조회 도구

한국예탁결제원의 공식 Open API와 공개 WebSquare 화면에서 주식·채권·권리일정 데이터를 조회하는 Python 패키지입니다. 주식관련사채 분석에는 DART 공시, 희석주식수 분석에는 KRX 상장주식수도 씁니다.

조회 항목은 **SEIBRO 공식 Open API → 공공데이터포털 API → 공개 WebSquare** 순으로 찾습니다. 공공데이터포털은 공식 API에 없는 항목을 조회할 때 사용하고, WebSquare는 두 API에서 얻기 어려운 화면 상세를 조회할 때 사용합니다. [데이터 소스 안내](docs/data_sources.md)

## 에이전트와 처음 쓰는 사람

1. Claude Code나 Codex에 이 저장소를 열고 요청을 전달하세요. [SEIBRO 사용 가이드](skills/seibro/SKILL.md)에서 질문별 데이터 출처, 공개 함수, 해석 기준을 찾을 수 있습니다.
2. 레포 루트에서 `python -m pip install -e .`를 실행합니다. 키가 필요한 조회에만 [`.env.example`](.env.example)의 해당 항목을 로컬 `.env`에 설정합니다.
3. 가이드에서 고른 Python 함수를 실행합니다. 실행 결과가 들어 있는 실습은 [시나리오 목록](scenarios/README.md)에서 Colab으로 열 수 있습니다.

```python
from seibro_api import get_company_schedules

schedules = get_company_schedules(
    "005930", "20260101", "20260630", use_openapi=False, save_csv=False,
)
print(schedules.head().to_string(index=False))
```

## 자료 위치

| 위치 | 내용 |
|---|---|
| [SEIBRO 사용 가이드](skills/seibro/SKILL.md) | 질문에서 함수로 연결하는 에이전트 진입점 |
| [소스별 데이터 안내](docs/data_sources.md) | SEIBRO 데이터 조회 경로와 보조 데이터 소스 |
| [SEIBRO 공식 Open API 명세](docs/reference/README.md) | API 37개 색인, 요청·응답 필드와 한국예탁결제원 엑셀 원본 |
| [공공데이터포털 API 명세](docs/reference/data-go-kr/README.md) | 한국예탁결제원·금융위원회 서비스 30개의 명세, 원본 가이드, 대표 호출 결과 |
| [Python API 레퍼런스](docs/python_reference.md) | 함수 입력·출력, 호출 예시와 기준일 차이 |
| [`seibro_api/`](seibro_api/) | 재사용할 Python 함수. 공식 클라이언트는 `openapi/`, 공개 화면 호출은 `web/` |
| [`scenarios/`](scenarios/README.md) | 공식 API·웹·혼합 실습. 각 시나리오는 Python 원본, 설명, 실행된 Colab 노트북으로 구성 |
| [`recorder/`](recorder/README.md) | 공개 WebSquare 화면을 조사할 때 쓰는 개발 도구 |

패키지는 Python으로 수정합니다. 시나리오는 `scenarios/_src/`의 Python 원본을 고치고 `python scenarios/_tools/build.py <분류>/<번호>`로 노트북을 생성합니다.
