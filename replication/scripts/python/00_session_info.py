"""Record reproducibility information for the JSS replication package."""

from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
REPRO_ROOT = ROOT / "artifacts" / "jss" / "reproducibility"
REPRO_ROOT.mkdir(parents=True, exist_ok=True)


def _module_version(package: str) -> str:
    try:
        return importlib.metadata.version(package)
    except Exception:
        return "unavailable"


def _tag_commit(tag: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", f"{tag}^{{commit}}"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unavailable"


def _run_capture(command: list[str]) -> str:
    try:
        return subprocess.check_output(
            command,
            cwd=ROOT,
            text=True,
            stderr=subprocess.STDOUT,
            timeout=120,
        ).strip()
    except FileNotFoundError:
        return "command_not_found"
    except Exception as exc:
        return f"command_failed: {exc}"


def main() -> int:
    seed = os.environ.get("RANDOM_SEED", "20260724")
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    rows = [
        {"module": "python", "version": sys.version.split()[0], "source": "runtime"},
        {"module": "systemgmmkit", "version": _module_version("systemgmmkit"), "source": "runtime"},
        {"module": "pandas", "version": _module_version("pandas"), "source": "runtime"},
        {"module": "numpy", "version": _module_version("numpy"), "source": "runtime"},
        {"module": "scipy", "version": _module_version("scipy"), "source": "runtime"},
        {"module": "statsmodels", "version": _module_version("statsmodels"), "source": "runtime"},
        {"module": "scikit-learn", "version": _module_version("scikit-learn"), "source": "runtime"},
        {"module": "matplotlib", "version": _module_version("matplotlib"), "source": "runtime"},
        {
            "module": "universal-output-hub",
            "version": _module_version("universal-output-hub"),
            "source": "runtime",
        },
    ]
    pd.DataFrame(rows).to_csv(REPRO_ROOT / "software_versions.csv", index=False, encoding="utf-8")

    system_info = [
        f"replication_run_utc={timestamp}",
        f"random_seed={seed}",
        f"python_executable={Path(sys.executable).name}",
        f"platform={platform.platform()}",
        f"machine={platform.machine()}",
        f"processor={platform.processor()}",
        f"systemgmmkit_version={_module_version('systemgmmkit')}",
        f"universal_output_hub_version={_module_version('universal-output-hub')}",
        "systemgmmkit_release_tag=v1.0.0",
        f"systemgmmkit_release_commit={_tag_commit('v1.0.0')}",
    ]
    (REPRO_ROOT / "system_info.txt").write_text("\n".join(system_info) + "\n", encoding="utf-8")

    try:
        env_txt = subprocess.check_output(
            [sys.executable, "-m", "pip", "freeze"],
            text=True,
            cwd=ROOT,
            timeout=180,
        )
    except Exception as exc:
        env_txt = f"pip_freeze_failed: {exc}"
    (REPRO_ROOT / "python_environment.txt").write_text(env_txt, encoding="utf-8")

    (REPRO_ROOT / "r_session_info.txt").write_text(
        _run_capture(["Rscript", "-e", 'cat(paste0("R/", R.version$string, "\\n"))']),
        encoding="utf-8",
    )
    (REPRO_ROOT / "stata_version.txt").write_text(
        "\n".join(
            [
                f"stata: {_run_capture(['stata', '--version'])}",
                f"stata-mp: {_run_capture(['stata-mp', '--version'])}",
                f"stata-se: {_run_capture(['stata-se', '--version'])}",
            ]
        ),
        encoding="utf-8",
    )

    status = {
        "status": "ok",
        "mode": os.environ.get("SYSTEMGMMKIT_REPLICATION_MODE", "open"),
        "seed": int(seed),
        "timestamp_utc": timestamp,
        "systemgmmkit_release_tag": "v1.0.0",
        "systemgmmkit_release_commit": _tag_commit("v1.0.0"),
        "python": sys.version.split()[0],
        "system": platform.platform(),
    }
    (REPRO_ROOT / "replication_session_status.json").write_text(
        json.dumps(status, indent=2),
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
