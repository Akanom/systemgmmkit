from __future__ import annotations

import zipfile
from pathlib import Path

from scripts.inspect_dist import inspect
from scripts.verify_dependencies import dependency_errors


def test_dependency_metadata_satisfies_policy() -> None:
    assert dependency_errors(Path(__file__).parents[1]) == []


def test_artifact_inspector_rejects_path_traversal(tmp_path: Path) -> None:
    wheel = tmp_path / "unsafe-1-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("../outside.py", "")
    report = inspect(wheel, set(), 250_000_000, 20_000)
    assert any("unsafe archive path" in error for error in report["errors"])


def test_artifact_inspector_rejects_private_key(tmp_path: Path) -> None:
    wheel = tmp_path / "unsafe-1-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        marker = "-----BEGIN " + "PRIVATE KEY-----\n"
        archive.writestr("package/key.txt", marker)
    report = inspect(wheel, set(), 250_000_000, 20_000)
    assert any("private key" in error for error in report["errors"])


def test_artifact_inspector_rejects_backup_snapshot(tmp_path: Path) -> None:
    wheel = tmp_path / "unsafe-1-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("package/model.before_patch.py", "")
    report = inspect(wheel, set(), 250_000_000, 20_000)
    assert any("sensitive file name" in error for error in report["errors"])
