from __future__ import annotations

import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.9/3.10
    import tomli as tomllib

import systemgmmkit

ROOT = Path(__file__).resolve().parents[1]


def test_release_version_metadata_is_consistent() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project_version = tomllib.load(handle)["project"]["version"]

    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    release_notes = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    citation_match = re.search(r'^version: "([^"]+)"$', citation, flags=re.MULTILINE)
    citation_date_match = re.search(r'^date-released: "([^"]+)"$', citation, flags=re.MULTILINE)

    assert citation_match is not None
    assert citation_date_match is not None
    assert systemgmmkit.__version__ == project_version == citation_match.group(1)
    assert f"# systemgmmkit {project_version} Release Notes" in release_notes
    assert f"## {project_version} - {citation_date_match.group(1)}" in changelog
    assert f"Version {project_version}" in citation


def test_outputhub_dependency_preserves_python_39_core_support() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        optional = tomllib.load(handle)["project"]["optional-dependencies"]

    requirement = "universal-output-hub>=0.2.2,<1; python_version >= '3.10'"
    assert optional["outputhub"] == [requirement]
    assert requirement in optional["dev"]
    assert requirement in optional["all"]


def test_v1_metadata_declares_stable_api_policy() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]

    classifiers = set(project["classifiers"])
    policy = (ROOT / "docs" / "API_STABILITY.md").read_text(encoding="utf-8")

    assert project["version"] == "1.0.4"
    assert "Development Status :: 5 - Production/Stable" in classifiers
    assert "Development Status :: 3 - Alpha" not in classifiers
    assert "semantic versioning" in policy
    assert "Econometric claim boundary" in policy


def test_release_requirements_cover_windows_build_dependency() -> None:
    release_input = (ROOT / "requirements" / "release.in").read_text(encoding="utf-8")
    release_requirements = (ROOT / "requirements" / "release.txt").read_text(encoding="utf-8")

    assert 'colorama==0.4.6; sys_platform == "win32"' in release_input
    assert 'colorama==0.4.6 ; sys_platform == "win32"' in release_requirements
    assert "sha256:08695f5cb7ed6e0531a20572697297273c47b8cae5a63ffc6d6ed5c201be6e44" in (
        release_requirements
    )
    assert "sha256:4f1d9991f5acc0ca119f9d443620b77f9d6b33703e51011c16baf57afb285fc6" in (
        release_requirements
    )
    assert 'pywin32-ctypes==0.2.3; sys_platform == "win32"' in release_input
    assert 'pywin32-ctypes==0.2.3 ; sys_platform == "win32"' in release_requirements
    assert "sha256:8a1513379d709975552d202d942d9837758905c8d01eb82b8bcc30918929e7b8" in (
        release_requirements
    )
    assert "sha256:d162dc04946d704503b2edc4d55f3dba5c1d539ead017afa00142c38b9885755" in (
        release_requirements
    )
