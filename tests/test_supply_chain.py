from __future__ import annotations

import zipfile
from pathlib import Path

from scripts.inspect_dist import inspect
from scripts.verify_dependencies import dependency_errors

ROOT = Path(__file__).resolve().parents[1]


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


def test_publish_workflow_audits_and_smokes_the_exact_artifacts() -> None:
    workflow = (ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
    upload_position = workflow.index("actions/upload-artifact@")

    required_before_upload = (
        "pip_audit --strict --require-hashes -r requirements/release.txt",
        "pip_audit --strict --format cyclonedx-json --output sbom.cdx.json .",
        "Smoke-test the exact built wheel",
        "--only-binary=:all:",
        "sys.path.insert(0, '${wheels[0]}')",
        "from systemgmmkit.estimators import first_difference",
        "Smoke-test the exact built sdist",
        "-I scripts/release_smoke.py --expected-version",
    )
    for marker in required_before_upload:
        assert marker in workflow
        assert workflow.index(marker) < upload_position
    dependency_install = workflow.index('"$smoke_python" -m pip install')
    archive_import = workflow.index('"$smoke_python" -I -c')
    assert dependency_install < archive_import
    assert "'.whl/' in systemgmmkit.__file__" in workflow
    assert workflow.count("-I scripts/release_smoke.py --expected-version") == 2
    assert workflow.count('"$smoke_python" -m pip check') == 2
    assert "sbom.cdx.json" in workflow[upload_position:]


def test_release_smoke_output_does_not_disclose_an_install_path() -> None:
    smoke_source = (ROOT / "scripts" / "release_smoke.py").read_text(encoding="utf-8")

    assert "systemgmmkit.__file__" not in smoke_source
    assert '"module"' not in smoke_source
    assert '"distribution_version"' in smoke_source
