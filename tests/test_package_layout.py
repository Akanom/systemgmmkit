from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "systemgmmkit"


def test_internal_python_subpackages_are_explicit() -> None:
    missing = sorted(
        str(directory.relative_to(PACKAGE))
        for directory in PACKAGE.rglob("*")
        if directory.is_dir()
        and any(directory.glob("*.py"))
        and not (directory / "__init__.py").is_file()
    )

    assert missing == []


def test_package_imports_from_a_python_archive(tmp_path: Path) -> None:
    archive = tmp_path / "systemgmmkit-source.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for source in sorted(PACKAGE.rglob("*.py")):
            bundle.write(source, source.relative_to(PACKAGE.parent))

    command = (
        "import sys; "
        f"sys.path.insert(0, {str(archive)!r}); "
        "import systemgmmkit; "
        "from systemgmmkit.estimators import FirstDifferenceResult, first_difference; "
        "assert systemgmmkit.__version__; "
        "assert FirstDifferenceResult is not None; "
        "assert callable(first_difference)"
    )
    completed = subprocess.run(
        [sys.executable, "-I", "-c", command],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
