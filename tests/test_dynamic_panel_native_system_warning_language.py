from __future__ import annotations

import ast
from pathlib import Path


def test_native_system_gmm_warning_language_reflects_certification_boundary():
    source = Path("src/systemgmmkit/dynamic_panel.py").read_text(encoding="utf-8")
    text = "\n".join(
        node.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    )

    assert "coefficient, Windmeijer-SE" in text
    assert "Hansen/Sargan" in text
    assert "signed AR diagnostic parity" in text
    assert "six maintained xtabond2" in text
    assert "exact sample-key parity" in text
    assert "does not imply universal Stata identity" in text
