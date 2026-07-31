from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH_PATTERNS = (
    re.compile(r"(?i)\b[A-Z]:[\\/]+Users[\\/]+(?!(?:<|\$|\{|%))[^\\/\s\"']+"),
    re.compile(r"/(?:Users|home)/(?!(?:<|\$|\{|%))[^/\s\"']+"),
)


def _tracked_files() -> list[Path]:
    if not (REPO_ROOT / ".git").exists():
        pytest.skip("repository path-hygiene check requires a Git checkout")

    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    return [REPO_ROOT / entry.decode("utf-8") for entry in completed.stdout.split(b"\0") if entry]


def test_tracked_text_files_do_not_disclose_local_profile_paths() -> None:
    violations: list[str] = []

    for path in _tracked_files():
        if not path.is_file():
            continue
        content = path.read_bytes()
        if b"\0" in content:
            continue
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            continue

        for pattern in PROFILE_PATH_PATTERNS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                violations.append(f"{path.relative_to(REPO_ROOT)}:{line}")

    assert not violations, (
        "tracked files disclose machine-specific user-profile paths; replace them "
        "with repository-relative paths, parameters, or environment variables:\n"
        + "\n".join(violations)
    )
