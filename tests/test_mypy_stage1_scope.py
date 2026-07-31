from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.9/3.10 compatibility
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_STAGE1_FILES = [
    "src/systemgmmkit/spec.py",
    "src/systemgmmkit/validation.py",
    "src/systemgmmkit/tables.py",
    "src/systemgmmkit/linear.py",
    "src/systemgmmkit/fixed_effects.py",
    "src/systemgmmkit/panel_iv.py",
    "src/systemgmmkit/random_effects.py",
    "src/systemgmmkit/estimators/first_difference.py",
    "src/systemgmmkit/suite.py",
]


def test_mypy_stage1_scope_is_explicit_and_fail_closed() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["mypy"]

    assert config["files"] == EXPECTED_STAGE1_FILES
    assert config["follow_imports"] == "silent"
    assert config["disallow_untyped_defs"] is True
    assert config["disallow_incomplete_defs"] is True
    assert config["warn_unused_ignores"] is True
    assert config.get("ignore_missing_imports") is not True
    assert "disable_error_code" not in config
    assert all((ROOT / relative_path).is_file() for relative_path in config["files"])
