"""실행된 노트북의 출력 확인: python scenarios/_tools/show.py scenarios/combined/01_dilution.ipynb"""
import sys
import nbformat

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

for path in sys.argv[1:]:
    nb = nbformat.read(path, as_version=4)
    print(f"#### {path}")
    for i, c in enumerate(nb.cells):
        if c.cell_type != "code" or "SEIBRO 공통 셀" in c.source:
            continue
        print(f"--- [{i}] {c.source.splitlines()[0][:90] if c.source else ''}")
        for o in c.get("outputs", []):
            if o.output_type == "stream":
                print(o.text[:3000])
            elif o.output_type in ("execute_result", "display_data"):
                d = o.get("data", {})
                if "text/plain" in d and "image/png" not in d:
                    print(d["text/plain"][:3000])
                if "image/png" in d:
                    print("[그림]")
            elif o.output_type == "error":
                print("ERROR:", o.ename, o.evalue[:500])
