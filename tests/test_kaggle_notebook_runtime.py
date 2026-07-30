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
    assert "f4e830808afcf8938386b5f89d708d8fad0bb0f5" in source
    assert '"universal-output-hub>=0.2.2,<1"' in source
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


def test_reporting_cells_use_outputhub_for_static_and_gmm_results():
    reporting_source = _code_cell_source(13)
    gmm_source = _code_cell_source(15)

    assert "from universal_output_hub import OutputHub" in reporting_source
    assert "sgk.add_to_outputhub" in reporting_source
    assert "assert len(hub.models) == 3" in reporting_source
    assert "include_diagnostics=True" in gmm_source
    assert 'metadata["estimator"] == "difference_gmm"' in gmm_source
    assert "assert len(hub.models) == 4" in gmm_source
    assert "assert len(hub.tables) == 1" in gmm_source
