# SEIBRO 저장소 안내

- SEIBRO 조회 요청은 [사용 가이드](skills/seibro/SKILL.md)에서 데이터 출처와 공개 함수를 먼저 찾습니다.
- 재사용 로직은 `seibro_api/`에 둡니다. API·웹 호출은 각각 `seibro_api/openapi/`와 `seibro_api/web/`에 이미 구현된 전송 경로를 이용합니다.
- 시나리오를 추가하거나 고칠 때는 `scenarios/_src/<openapi|web|combined>/`의 Python 원본을 수정하고 같은 분류로 빌드합니다. 시나리오의 설명과 노트북은 [색인](scenarios/README.md)에서 연결합니다.
- 키를 명령 인자·로그·노트북에 넣지 않습니다. 로컬 조회는 환경변수나 `.env`, Colab은 Secrets를 사용합니다.
- 변경 후 `python -m pytest -q`와 수정한 시나리오 빌드로 확인합니다.
