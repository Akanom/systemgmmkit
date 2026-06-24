from __future__ import annotations

from pathlib import Path


def test_native_system_gmm_warning_language_reflects_certified_diagnostics():
    text = Path("src/systemgmmkit/dynamic_panel.py").read_text(encoding="utf-8")

    assert "Sargan/AR diagnostic parity remains uncertified" not in text
    assert "uncertified" not in text
    assert "Hansen/Sargan" in text
    assert "signed AR diagnostic parity" in text
