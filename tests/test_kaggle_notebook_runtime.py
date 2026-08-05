import json
import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.9/3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "kaggle" / "systemgmmkit_quickstart.ipynb"
KERNEL_METADATA = ROOT / "notebooks" / "kaggle" / "kernel-metadata.json"


def _code_cell_source(index: int) -> str:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cell = notebook["cells"][index]
    assert cell["cell_type"] == "code"
    return "".join(cell["source"])


def _project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return str(tomllib.load(handle)["project"]["version"])


def test_install_cell_uses_exact_pypi_release_and_evicts_stale_modules():
    source = _code_cell_source(2)
    project_version = _project_version()

    assert "--no-deps" in source
    assert f'"systemgmmkit=={project_version}"' in source
    assert "git+" not in source
    assert '"universal-output-hub==0.2.4"' in source
    assert "tuple(sys.modules)" in source
    assert 'name == "systemgmmkit"' in source
    assert 'name.startswith("systemgmmkit.")' in source
    assert "sys.modules.pop(module_name, None)" in source
    assert "importlib.invalidate_caches()" in source


def test_kernel_metadata_matches_documented_public_notebook():
    metadata = json.loads(KERNEL_METADATA.read_text(encoding="utf-8"))
    cloud_docs = (ROOT / "docs" / "CLOUD_NOTEBOOKS.md").read_text(encoding="utf-8")

    assert metadata["id"] == "akanom/systemgmmkit-quickstart"
    assert metadata["id"] in cloud_docs


def test_notebook_has_no_saved_outputs_or_machine_paths():
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cell_ids = [cell.get("id") for cell in notebook["cells"]]

    assert notebook["nbformat"] == 4
    assert notebook["nbformat_minor"] >= 5
    assert all(
        isinstance(cell_id, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", cell_id)
        for cell_id in cell_ids
    )
    assert len(cell_ids) == len(set(cell_ids))
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            assert cell["execution_count"] is None
            assert cell["outputs"] == []
    source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    assert "sgk.__file__" not in source
    assert 'print("native_gmm path:"' not in source
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "/systemgmmkit_notebook_outputs/" in gitignore


def test_verification_cell_detects_multiline_groupby_apply():
    source = _code_cell_source(3)

    assert f'assert sgk.__version__ == "{_project_version()}"' in source
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


def test_postestimation_tables_use_compact_inference_formatting():
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])

    assert "sgk.format_inference_frame(post.linear_combinations" in source
    assert "sgk.format_inference_frame(post.wald_tests" in source
