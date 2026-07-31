from __future__ import annotations

from pathlib import Path


def test_native_system_gmm_warning_language_reflects_certification_boundary():
    text = Path("src/systemgmmkit/dynamic_panel.py").read_text(encoding="utf-8")

    assert "coefficient, Windmeijer-SE" in text
    assert "Hansen/Sargan" in text
    assert "signed AR diagnostic parity" in text
    assert "four maintained xtabond2" in text
    assert "does not imply universal Stata identity" in text
