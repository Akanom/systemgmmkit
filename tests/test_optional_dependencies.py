from __future__ import annotations

import subprocess
import sys
import textwrap


def test_core_import_does_not_require_matplotlib() -> None:
    script = textwrap.dedent(
        """
        import importlib.abc
        import sys

        class BlockMatplotlib(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname == "matplotlib" or fullname.startswith("matplotlib."):
                    raise ModuleNotFoundError(
                        "blocked for optional-dependency test", name=fullname
                    )
                return None

        sys.meta_path.insert(0, BlockMatplotlib())
        import systemgmmkit
        from systemgmmkit import validate_panel

        assert callable(validate_panel)
        try:
            systemgmmkit.coefficient_plot
        except ImportError as exc:
            assert "systemgmmkit[plots]" in str(exc)
        else:
            raise AssertionError("plotting import should require the plots extra")
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
