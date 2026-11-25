"""시나리오 노트북 빌더: scenarios/_src/<유형>/<이름>.py → scenarios/<유형>/<이름>.ipynb (실행 결과 포함).

원본 형식 (셀 구분 주석)
    # %% [markdown]
    # # 제목
    # 설명 …
    # %%
    파이썬 코드 …

빌더가 하는 일
1. 첫 markdown 셀 아래에 "Colab에서 열기" 배지와 준비 셀 2개를 넣는다.
   - Colab일 때만 패키지 설치: seibro-api (git), 원본이 krx_data_api 를 쓰면 krx-data-api (git) 도
   - 공통 셀(_tools/seibro_helper.py 내용 + 맨 위에 필요한 Secrets 목록)
2. 노트북을 실제로 실행해 출력까지 저장한다(--no-exec 이면 실행 안 함).
   실행 폴더는 레포 루트라서 로컬에서는 레포 .env 의 SEIBRO_API_KEY 를 쓴다.
   KRX 계정은 krx-data-api 를 편집 설치한 경우 그 레포의 .env 를 패키지가 직접 읽는다.
3. 저장 전에 노트북의 코드와 출력에 자격증명 값이 들어 있는지 검사한다.

사용
    python scenarios/_tools/build.py                 # 전체
    python scenarios/_tools/build.py openapi/01      # 경로에 이 문자열이 든 원본만
    python scenarios/_tools/build.py --no-exec …
"""
from __future__ import annotations

import os
import json
import re
import sys
from importlib.util import find_spec
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import quote, quote_plus

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError
from dotenv import dotenv_values

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.platform.startswith("win"):
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

HERE = Path(__file__).resolve().parent
SCEN = HERE.parent
REPO = SCEN.parent
SRC = SCEN / "_src"
GITHUB = "beaten-by-the-market/seibro-api"
BRANCH = "main"
SEIBRO_PKG = f"git+https://github.com/{GITHUB}.git"
KRX_PKG = "git+https://github.com/beaten-by-the-market/krx-data-api.git"
SECRET_NAMES = ("SEIBRO_API_KEY", "SEIBRO_SHARE_API_KEY", "DART_API_KEY", "KRX_ID", "KRX_PW")
QUERY_SECRET = re.compile(
    r"""(?i)(?:[?&](?:key|servicekey|crtfc_key)=|vectorkey\s*=\s*['"])[A-Za-z0-9%+/_=-]{8,}"""
)


def install_cell(needs_krx: bool) -> str:
    pkgs = [f'"{SEIBRO_PKG}"'] + ([f'"{KRX_PKG}"'] if needs_krx else []) + ["koreanize-matplotlib"]
    return ("# Colab에서만: 패키지 설치 (로컬은 이 레포를 pip install -e . 로 설치해 두면 됨)\n"
            "import sys\n"
            'if "google.colab" in sys.modules:\n'
            f"    !pip -q install {' '.join(pkgs)}")


def parse(src: str) -> list[tuple[str, str]]:
    cells, kind, buf = [], None, []

    def flush():
        if kind is None:
            return
        text = "\n".join(buf).strip("\n")
        if kind == "markdown":
            text = "\n".join(re.sub(r"^# ?", "", ln) for ln in text.splitlines())
        if text.strip():
            cells.append((kind, text))

    for line in src.splitlines():
        if line.startswith("# %%"):
            flush()
            kind, buf = ("markdown" if "[markdown]" in line else "code"), []
        else:
            buf.append(line)
    flush()
    return cells


def _secret_values() -> set[str]:
    """프로세스와 패키지가 읽을 수 있는 .env의 자격증명을 모은다."""
    configs = [os.environ, dotenv_values(REPO / ".env", encoding="utf-8-sig")]
    krx = find_spec("krx_data_api")
    if krx and krx.origin:
        configs.append(dotenv_values(Path(krx.origin).resolve().parents[1] / ".env", encoding="utf-8-sig"))
    return {
        value
        for config in configs
        for name, value in config.items()
        if value and len(value) >= 4 and (name in SECRET_NAMES or re.fullmatch(r"DART_API_KEY_\d+", name))
    }


def _contains_secret(notebook: str) -> bool:
    # JSON 안의 이스케이프를 먼저 해제해 원문과 URL 인코딩을 모두 검사한다.
    decoded = json.dumps(json.loads(notebook), ensure_ascii=False)
    if QUERY_SECRET.search(notebook.replace(r'\"', '"')):
        return True
    for value in _secret_values():
        for variant in {value, quote(value, safe=""), quote_plus(value)}:
            if json.dumps(variant, ensure_ascii=False)[1:-1] in decoded:
                return True
    return False


def build(src_path: Path, execute: bool = True) -> bool:
    rel = src_path.relative_to(SRC).with_suffix(".ipynb")
    out = SCEN / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    text = src_path.read_text(encoding="utf-8")
    cells = parse(text)
    if not cells or cells[0][0] != "markdown":
        raise SystemExit(f"{src_path}: 첫 셀은 제목 markdown 이어야 합니다")

    needs_krx = "krx_data_api" in text
    needs_dart = "DART_API_KEY" in text
    secrets = [] if rel.parts[0] == "web" else ["SEIBRO_API_KEY"]
    if needs_dart:
        secrets.append("DART_API_KEY")
    if needs_krx:
        secrets.extend(["KRX_ID", "KRX_PW"])
    url = f"https://colab.research.google.com/github/{GITHUB}/blob/{BRANCH}/scenarios/{quote(rel.as_posix())}"
    badge = f"[![Colab에서 열기](https://colab.research.google.com/assets/colab-badge.svg)]({url})"
    helper = f"SECRETS = {secrets!r}\n" + (HERE / "seibro_helper.py").read_text(encoding="utf-8").strip()
    if secrets:
        names = ", ".join(f"`{name}`" for name in secrets)
        credentials = f"Colab 왼쪽 🔑(Secrets)에 {names}를 등록하고 이 노트북의 액세스를 켭니다. "
        if "SEIBRO_API_KEY" in secrets:
            credentials += "SEIBRO Open API 키는 [SEIBRO OpenPlatform](https://seibro.or.kr/OpenPlatform/)에서 신청합니다. "
    else:
        credentials = "이 시나리오는 WebSquare 공개 화면을 조회하며 API 키가 필요 없습니다. "
    setup_md = "## 0. 준비\n" + credentials + "아래 두 셀을 실행해 패키지를 설치하고 실행 환경을 준비하세요."

    nb = nbformat.v4.new_notebook()
    nb.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                   "language_info": {"name": "python"},
                   "colab": {"provenance": [], "toc_visible": True}}
    nb.cells.append(nbformat.v4.new_markdown_cell(cells[0][1] + "\n\n" + badge))
    nb.cells.append(nbformat.v4.new_markdown_cell(setup_md))
    nb.cells.append(nbformat.v4.new_code_cell(install_cell(needs_krx)))
    nb.cells.append(nbformat.v4.new_code_cell(helper, metadata={"cellView": "form", "jupyter": {"source_hidden": True}}))
    for kind, body in cells[1:]:
        nb.cells.append(nbformat.v4.new_markdown_cell(body) if kind == "markdown" else nbformat.v4.new_code_cell(body))

    if execute:
        client = NotebookClient(nb, timeout=900, kernel_name="python3",
                                resources={"metadata": {"path": str(REPO)}})
        try:
            client.execute()
        except CellExecutionError:
            failed_cell = next(
                (i for i, cell in enumerate(nb.cells, 1)
                 if any(output.output_type == "error" for output in cell.get("outputs", []))),
                None,
            )
            print(f"✗ {rel.as_posix()} — 셀 실행 실패 (셀 번호: {failed_cell or '알 수 없음'})")
            return False

    serialized = nbformat.writes(nb)
    if _contains_secret(serialized):
        print(f"✗ {rel.as_posix()} — 자격증명으로 보이는 값이 있어 저장을 중단했습니다.")
        return False

    with NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                            dir=out.parent, suffix=".tmp", delete=False) as tmp:
        temp_path = Path(tmp.name)
        tmp.write(serialized + "\n")
    try:
        temp_path.replace(out)
    finally:
        temp_path.unlink(missing_ok=True)
    print(f"✓ {rel.as_posix()}")
    return True


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    execute = "--no-exec" not in sys.argv
    srcs = sorted(p for p in SRC.rglob("*.py"))
    if args:
        srcs = [p for p in srcs if any(a in p.relative_to(SRC).as_posix() for a in args)]
    if not srcs:
        raise SystemExit("빌드할 원본이 없습니다")
    results = [build(p, execute) for p in srcs]
    if not all(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
