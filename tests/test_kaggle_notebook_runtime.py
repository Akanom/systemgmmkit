import json
from pathlib import Path

NOTEBOOK = (
    Path(__file__).resolve().parents[1] / "notebooks" / "kaggle" / "systemgmmkit_quickstart.ipynb"
)


def _code_cell_source(index: int) -> str:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cell = notebook["cells"][index]
    assert cell["cell_type"] == "code"
    return "".join(cell["source"])


def test_install_cell_evicts_stale_systemgmmkit_modules():
    source = _code_cell_source(2)

    assert "--no-deps" in source
    assert "50583c7e5520a3a343d6fbeba3713a63b14a4b44" in source
    assert "6638a2f87c68cde44ace2d2661a9361afffb0595" not in source
    assert "tuple(sys.modules)" in source
    assert 'name == "systemgmmkit"' in source
    assert 'name.startswith("systemgmmkit.")' in source
    assert "sys.modules.pop(module_name, None)" in source
    assert "importlib.invalidate_caches()" in source


def test_verification_cell_detects_multiline_groupby_apply():
    source = _code_cell_source(3)

    assert 'lag_start = native_source.index("def _lag_test")' in source
    assert 'assert ".apply(" not in lag_test_source' in source
    assert 'assert "_resid_lag_product" in lag_test_source' in source
