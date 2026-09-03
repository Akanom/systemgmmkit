"""Compile the generated manuscript with the official JSS LaTeX class."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAPER_DIR = ROOT / "paper_jss"
MAIN_TEX = PAPER_DIR / "main.tex"
MAIN_PDF = PAPER_DIR / "main.pdf"


def main() -> int:
    if not MAIN_TEX.exists():
        raise FileNotFoundError("paper_jss/main.tex is missing; build tables first.")
    if not (PAPER_DIR / "jss.cls").exists() or not (PAPER_DIR / "jss.bst").exists():
        raise FileNotFoundError("Official JSS style files are missing from paper_jss/.")
    latexmk = shutil.which("latexmk")
    if latexmk is None:
        raise RuntimeError("latexmk is required to reproduce paper_jss/main.pdf.")

    for suffix in ("aux", "bbl", "blg", "fdb_latexmk", "fls", "log", "out"):
        (PAPER_DIR / f"main.{suffix}").unlink(missing_ok=True)

    completed = subprocess.run(
        [
            latexmk,
            "-g",
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "main.tex",
        ],
        cwd=PAPER_DIR,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        return completed.returncode
    if not MAIN_PDF.exists() or MAIN_PDF.stat().st_size < 10_000:
        raise RuntimeError("LaTeX completed without a usable paper_jss/main.pdf.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
