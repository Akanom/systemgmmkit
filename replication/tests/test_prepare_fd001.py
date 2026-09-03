from __future__ import annotations

import importlib.util
import io
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "processing" / "01_prepare_fd001.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("prepare_fd001", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load replication script: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_extracts_fd001_from_current_nested_nasa_archive_layout(tmp_path: Path) -> None:
    module = _load_script()
    expected = b"1 1 0.0\n"

    nested_buffer = io.BytesIO()
    with zipfile.ZipFile(nested_buffer, "w") as nested:
        nested.writestr("CMaps/train_FD001.txt", expected)

    outer_path = tmp_path / "nasa.zip"
    nested_member = "6. Turbofan Engine Degradation Simulation Data Set/CMAPSSData.zip"
    with zipfile.ZipFile(outer_path, "w") as outer:
        outer.writestr(nested_member, nested_buffer.getvalue())

    payload, member = module._extract_fd001_bytes(outer_path)

    assert payload == expected
    assert member == f"{nested_member}!/CMaps/train_FD001.txt"
