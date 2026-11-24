from types import SimpleNamespace

import nbformat
import pytest
from nbclient.exceptions import CellExecutionError

from scenarios._tools import build


@pytest.fixture
def example(tmp_path, monkeypatch):
    source_root = tmp_path / "_src"
    source_root.mkdir()
    scenario = source_root / "example.py"
    scenario.write_text("# %% [markdown]\n# Example\n# %%\npass\n", encoding="utf-8")
    destination = tmp_path / "example.ipynb"
    destination.write_text("previous notebook", encoding="utf-8")
    monkeypatch.setattr(build, "SRC", source_root)
    monkeypatch.setattr(build, "SCEN", tmp_path)
    return scenario, destination


@pytest.mark.parametrize("output", [
    "https://example.invalid/?ServiceKey=synthetic-test-value",
    '<vector vectorkey="synthetic-test-value"/>',
    "escaped " + "synthetic%2Ftest%2Bvalue",
])
def test_leaked_credentials_never_replace_notebook(example, monkeypatch, capsys, output):
    source, destination = example
    monkeypatch.setenv("SEIBRO_API_KEY", "synthetic/test+value")

    def execute(notebook):
        notebook.cells[-1].outputs = [nbformat.v4.new_output("stream", name="stdout", text=output)]

    monkeypatch.setattr(build, "NotebookClient", lambda notebook, **kwargs: SimpleNamespace(
        execute=lambda: execute(notebook)
    ))
    assert build.build(source) is False
    assert destination.read_text(encoding="utf-8") == "previous notebook"
    assert output not in capsys.readouterr().out


def test_failed_cell_traceback_is_not_published(example, monkeypatch, capsys):
    source, destination = example

    def fail():
        raise CellExecutionError("synthetic-test-value", "RuntimeError", "synthetic-test-value")

    monkeypatch.setattr(build, "NotebookClient", lambda *args, **kwargs: SimpleNamespace(execute=fail))
    assert build.build(source) is False
    assert destination.read_text(encoding="utf-8") == "previous notebook"
    assert "synthetic-test-value" not in capsys.readouterr().out
