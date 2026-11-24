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
3. 저장한 노트북에 SEIBRO 키 값이 들어 있으면 실패로 표시한다(Open API 는 키를 URL 에 넣음).

사용
    python scenarios/_tools/build.py                 # 전체
    python scenarios/_tools/build.py 1_stock/01      # 경로에 이 문자열이 든 원본만
    python scenarios/_tools/build.py --no-exec …
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from urllib.parse import quote

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

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


def _secret_values() -> list[str]:
    """누출 검사용: 환경변수·레포 .env 의 키·비밀번호 값(출력하지 않음)."""
    vals = [os.environ.get(n, "") for n in ("SEIBRO_API_KEY", "DART_API_KEY", "KRX_PW")]
    env = REPO / ".env"
    if env.is_file():
        for line in env.read_text(encoding="utf-8-sig").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                if k.strip() in ("SEIBRO_API_KEY", "DART_API_KEY"):
                    vals.append(v.strip().strip('"').strip("'"))
    return [v for v in vals if len(v) >= 8]


def build(src_path: Path, execute: bool = True) -> bool:
    rel = src_path.relative_to(SRC).with_suffix(".ipynb")
    out = SCEN / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    text = src_path.read_text(encoding="utf-8")
    cells = parse(text)
    if not cells or cells[0][0] != "markdown":
        raise SystemExit(f"{src_path}: 첫 셀은 제목 markdown 이어야 합니다")

    needs_krx = "krx_data_api" in text
    secrets = ["SEIBRO_API_KEY"] + (["KRX_ID", "KRX_PW"] if needs_krx else [])
    url = f"https://colab.research.google.com/github/{GITHUB}/blob/{BRANCH}/scenarios/{quote(rel.as_posix())}"
    badge = f"[![Colab에서 열기](https://colab.research.google.com/assets/colab-badge.svg)]({url})"
    helper = f"SECRETS = {secrets!r}\n" + (HERE / "seibro_helper.py").read_text(encoding="utf-8").strip()
    names = ", ".join(f"`{s}`" for s in secrets)
    setup_md = ("## 0. 준비\n"
                f"Colab 왼쪽 🔑(Secrets)에 {names}를 등록하고 이 노트북의 액세스를 켠 뒤 아래 두 셀을 실행하세요. "
                "첫 셀은 패키지를 설치하고, 두 번째 셀은 모든 시나리오에 공통인 준비 코드입니다(접어 두어도 됩니다). "
                "SEIBRO Open API 키는 [SEIBRO OpenPlatform](https://seibro.or.kr/OpenPlatform/)에서 신청합니다.")

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

    ok = True
    if execute:
        client = NotebookClient(nb, timeout=900, kernel_name="python3",
                                resources={"metadata": {"path": str(REPO)}})
        try:
            client.execute()
        except CellExecutionError as e:
            ok = False
            print(f"✗ {rel.as_posix()} — 실행 오류 (오류까지 저장함)\n{str(e)[-1500:]}")
    nbformat.write(nb, out)

    saved = out.read_text(encoding="utf-8")
    leaked = [v for v in _secret_values() if v in saved]
    if leaked:
        ok = False
        print(f"✗ {rel.as_posix()} — 노트북에 API 키 값이 들어 있습니다. 출력을 지우고 원인을 고치세요.")
    if ok:
        print(f"✓ {rel.as_posix()}")
    return ok


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
