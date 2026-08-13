from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RANDOM_SEED = 20260724
random.seed(RANDOM_SEED)


def _find_repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in (current, *current.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("Could not locate repository root from this script location.")


ROOT = _find_repo_root()
ARTIFACT_JSS = ROOT / "artifacts" / "jss"
MANIFEST_PATH = ROOT / "replication" / "manifest.csv"
EXPECTED_PATH = ROOT / "replication" / "expected_outputs.yml"
RUN_LOG_DIR = ARTIFACT_JSS / "logs"
REPRO_DIR = ARTIFACT_JSS / "reproducibility"
CHECK_SUM_FILE = ROOT / "replication" / "checksums.sha256"


@dataclass
class Step:
    name: str
    command: list[str]
    required: bool = True


@dataclass
class OutputExpectation:
    path: Path
    minimum_rows: int | None = None
    minimum_size_bytes: int | None = None
    required_columns: list[str] | None = None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run_command(step: Step, log_file: Path) -> int:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    command_str = " ".join(str(c) for c in step.command)

    log_lines = [
        f"RUN_START_UTC: {started}",
        f"STEP: {step.name}",
        f"COMMAND: {command_str}",
    ]

    with log_file.open("w", encoding="utf-8") as f:
        for line in log_lines:
            f.write(line + "\n")
        f.write("-" * 80 + "\n")
        f.flush()
        try:
            result = subprocess.run(
                step.command,
                cwd=ROOT,
                check=False,
                text=True,
                stdout=f,
                stderr=subprocess.STDOUT,
            )
            return_code = result.returncode
        except FileNotFoundError as exc:
            return_code = 127
            f.write(f"ERROR: command not found ({exc})\n")
        except Exception as exc:  # pragma: no cover - defensive runtime
            return_code = 1
            f.write(f"ERROR: unexpected execution failure ({exc})\n")

        finished = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        f.write("-" * 80 + "\n")
        f.write(f"RUN_END_UTC: {finished}\n")
        f.write(f"RETURN_CODE: {return_code}\n")

    return return_code


def _load_expectations(path: Path) -> list[OutputExpectation]:
    if not path.exists():
        return []

    expectations: list[OutputExpectation] = []
    current: OutputExpectation | None = None
    in_columns = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- path:"):
            if current is not None:
                expectations.append(current)
            value = stripped.split(":", 1)[1].strip().strip('"')
            current = OutputExpectation(path=(ROOT / value))
            in_columns = False
            continue

        if current is None:
            continue

        if stripped.startswith("minimum_rows:"):
            try:
                current.minimum_rows = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                current.minimum_rows = None
            in_columns = False
            continue

        if stripped.startswith("minimum_size_bytes:"):
            try:
                current.minimum_size_bytes = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                current.minimum_size_bytes = None
            in_columns = False
            continue

        if stripped.startswith("required_columns:"):
            current.required_columns = []
            in_columns = True
            continue

        if in_columns and stripped.startswith("-"):
            if current.required_columns is not None:
                current.required_columns.append(stripped[1:].strip())
            continue

        if line.startswith("  - ") and in_columns and current.required_columns is not None:
            current.required_columns.append(line.strip()[2:].strip())

        if stripped and not stripped.startswith("-") and not stripped.startswith("#"):
            in_columns = False

    if current is not None:
        expectations.append(current)

    return expectations


def _row_count(path: Path) -> int | None:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".txt"}:
        try:
            import pandas as pd

            return int(len(pd.read_csv(path)))
        except Exception:
            return None
    if suffix in {".json", ".parquet"}:
        try:
            import pandas as pd

            return (
                int(len(pd.read_json(path)))
                if suffix == ".json"
                else int(len(pd.read_parquet(path)))
            )
        except Exception:
            return None
    try:
        return int(path.stat().st_size > 0)
    except OSError:
        return None


def _verify_output(expect: OutputExpectation) -> tuple[bool, str, int | None]:
    path = expect.path
    if not path.exists():
        return False, "missing_output", None

    try:
        if (
            expect.minimum_size_bytes is not None
            and path.stat().st_size < expect.minimum_size_bytes
        ):
            return False, "insufficient_size", None
    except OSError:
        return False, "stat_failed", None

    rows = _row_count(path)
    if expect.minimum_rows is not None and (rows is None or rows < expect.minimum_rows):
        return False, f"insufficient_rows:{rows}", rows

    if expect.required_columns:
        suffix = path.suffix.lower()
        if suffix in {".csv", ".txt"}:
            try:
                import pandas as pd

                df = pd.read_csv(path, nrows=0)
            except Exception:
                return False, "column_check_read_failed", rows
            missing = [col for col in expect.required_columns if col not in set(df.columns)]
            if missing:
                return False, f"missing_columns:{','.join(missing)}", rows

    return True, "ok", rows


def _collect_verification_status(
    expectations: list[OutputExpectation],
) -> list[tuple[Path, bool, str, int | None]]:
    results = []
    for expect in expectations:
        ok, note, rows = _verify_output(expect)
        results.append((expect.path, ok, note, rows))
    return results


def _build_checksums(paths: list[Path], checksum_file: Path) -> None:
    rows = []
    for path in sorted(set(p for p in paths if p.exists()), key=str):
        try:
            rows.append({"path": str(path.relative_to(ROOT)), "sha256": _sha256(path)})
        except ValueError:
            rows.append({"path": str(path), "sha256": _sha256(path)})
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    with checksum_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "sha256"])
        writer.writeheader()
        writer.writerows(rows)


def _manifest_inputs_for_output(output: str) -> list[str]:
    if output.startswith("paper_jss/tables") or output.startswith("artifacts/jss/tables"):
        return ["artifacts/joss/tables/*.csv/.tex"]
    if output.startswith("paper_jss/main.tex"):
        return [
            "paper_jss/tables/*.tex",
            "artifacts/joss/tables/*.csv",
            "v0.5.14 release certificates",
        ]
    if output.startswith("artifacts/jss/reproducibility"):
        return ["system_info.txt", "python_environment.txt", "software_versions.csv"]
    if output.startswith("artifacts/jss/figures"):
        return ["results/*/*.csv", "artifacts/joss/tables/*.csv"]
    if output.startswith("results/"):
        return ["data/processed/*.csv", "artifacts/joss/tables/*.csv"]
    return ["artifacts/joss/*", "results/*"]


def _generation_script_for_output(output: str) -> str:
    if output.startswith("artifacts/jss/tables"):
        return "replication/scripts/tables/01_build_tables.py"
    if output.startswith("artifacts/jss/figures"):
        return "replication/scripts/figures/01_build_figures.py"
    if output.startswith("artifacts/jss/reproducibility"):
        return "replication/scripts/python/00_session_info.py"
    if output.startswith("results/"):
        return "replication/scripts/python/*.py"
    if output == "paper_jss/main.pdf":
        return "replication/scripts/manuscript/01_compile_jss.py"
    if output.startswith("paper_jss/figures"):
        return "replication/scripts/figures/01_build_figures.py"
    if output.startswith("paper_jss/tables") or output in {
        "paper_jss/main.tex",
        "paper_jss/publication_manifest.json",
    }:
        return "replication/scripts/tables/01_build_tables.py"
    if output.startswith("paper_jss/jss"):
        return "official JSS template asset; see paper_jss/JSS_STYLE_SOURCE.md"
    return "replication/run_all.py"


def _build_manifest(
    mode: str,
    step_records: list[tuple[str, int, bool]],
    checks: list[tuple[Path, bool, str, int | None]],
) -> None:
    with MANIFEST_PATH.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "result_id",
            "mode",
            "manuscript_section",
            "manuscript_object",
            "input_files",
            "generation_script",
            "output_files",
            "expected_rows",
            "checksum",
            "required",
            "status",
            "status_note",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for idx, (path, ok, note, rows) in enumerate(checks, start=1):
            rel = str(path.relative_to(ROOT))
            writer.writerow(
                {
                    "result_id": f"R{idx:03d}",
                    "mode": mode,
                    "manuscript_section": "JSS/TAB+FIG",
                    "manuscript_object": rel,
                    "input_files": " | ".join(_manifest_inputs_for_output(rel)),
                    "generation_script": _generation_script_for_output(rel),
                    "output_files": rel,
                    "expected_rows": str(rows or ""),
                    "checksum": _sha256(path) if path.exists() else "",
                    "required": "yes",
                    "status": "PASS" if ok else "FAIL",
                    "status_note": note,
                }
            )

        for idx, (name, code, required) in enumerate(step_records, start=len(checks) + 1):
            writer.writerow(
                {
                    "result_id": f"S{idx:03d}",
                    "mode": mode,
                    "manuscript_section": "pipeline_step",
                    "manuscript_object": name,
                    "input_files": "",
                    "generation_script": "replication/run_all.py",
                    "output_files": "multiple",
                    "expected_rows": "",
                    "checksum": "",
                    "required": "yes" if required else "no",
                    "status": "PASS" if code == 0 else f"FAIL_{code}",
                    "status_note": "",
                }
            )


def _clean_generated(remove: list[Path]) -> None:
    def clear_contents(directory: Path) -> None:
        """Clear generated children while tolerating OneDrive-protected root folders."""
        for child in directory.iterdir():
            if child.is_file() or child.is_symlink():
                child.unlink(missing_ok=True)
                continue
            try:
                shutil.rmtree(child, ignore_errors=False)
            except PermissionError:
                clear_contents(child)

    for target in remove:
        resolved = target.resolve()
        if resolved != ROOT and ROOT not in resolved.parents:
            raise RuntimeError(f"Refusing to clean outside repository root: {resolved}")
        if not target.exists():
            continue
        if target.is_file():
            target.unlink(missing_ok=True)
        else:
            try:
                shutil.rmtree(target, ignore_errors=False)
            except PermissionError as exc:
                clear_contents(target)
                remaining_files = [path for path in target.rglob("*") if path.is_file()]
                if remaining_files:
                    raise RuntimeError(
                        f"Generated files remain after OneDrive-safe clean: {remaining_files}"
                    ) from exc


def _pipeline_for_mode(mode: str) -> list[Step]:
    base = [
        Step(
            name="Record environment and software versions",
            command=[sys.executable, "replication/scripts/python/00_session_info.py"],
        ),
        Step(
            name="Prepare FD001 processing report",
            command=[sys.executable, "replication/scripts/processing/01_prepare_fd001.py"],
        ),
        Step(
            name="Run leakage-controlled N-CMAPSS application",
            command=[sys.executable, "replication/scripts/python/09_ncmapss_application.py"],
        ),
        Step(
            name="Run controlled Difference and System GMM",
            command=[sys.executable, "replication/scripts/python/10_controlled_dynamic_gmm.py"],
        ),
        Step(
            name="Run diagnostic-first automatic GMM search",
            command=[sys.executable, "replication/scripts/python/11_auto_gmm_search.py"],
        ),
        Step(
            name="Run external Python ML comparison",
            command=[sys.executable, "replication/scripts/python/12_ml_comparator.py"],
        ),
        Step(
            name="Static validation snapshot",
            command=[sys.executable, "replication/scripts/python/01_static_validation.py"],
        ),
        Step(
            name="System GMM validation snapshot",
            command=[sys.executable, "replication/scripts/python/02_system_gmm_validation.py"],
        ),
        Step(
            name="Difference GMM validation snapshot",
            command=[sys.executable, "replication/scripts/python/03_difference_gmm_validation.py"],
        ),
        Step(
            name="Windmeijer and diagnostics snapshot",
            command=[sys.executable, "replication/scripts/python/04_windmeijer_validation.py"],
        ),
        Step(
            name="Post-estimation validation snapshot",
            command=[sys.executable, "replication/scripts/python/05_postestimation_validation.py"],
        ),
        Step(
            name="Panel validation snapshot",
            command=[sys.executable, "replication/scripts/python/06_panel_validation.py"],
        ),
        Step(
            name="Forecast backtesting snapshot",
            command=[sys.executable, "replication/scripts/python/07_forecast_backtesting.py"],
        ),
        Step(
            name="FD001 application snapshot",
            command=[sys.executable, "replication/scripts/python/08_fd001_application.py"],
        ),
        Step(
            name="Build manuscript tables",
            command=[sys.executable, "replication/scripts/tables/01_build_tables.py"],
        ),
        Step(
            name="Build manuscript figures",
            command=[sys.executable, "replication/scripts/figures/01_build_figures.py"],
        ),
        Step(
            name="Compile JSS manuscript",
            command=[sys.executable, "replication/scripts/manuscript/01_compile_jss.py"],
        ),
    ]

    if mode == "full":
        stata_ps1 = ROOT / "scripts" / "stata" / "run_stata_references.ps1"
        if stata_ps1.exists():
            base.append(
                Step(
                    name="Stata-enabled comparison pipeline",
                    command=[
                        "powershell",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(stata_ps1),
                    ],
                    required=False,
                )
            )
        else:
            base.append(
                Step(
                    name="Stata-enabled comparison pipeline (missing reference script)",
                    command=[
                        sys.executable,
                        "-c",
                        "print('Stata reference script not present in repository.')",
                    ],
                    required=False,
                )
            )

    return base


def _run(mode: str, run_verify_only: bool = False) -> int:
    os.environ["RANDOM_SEED"] = str(RANDOM_SEED)
    os.environ["PYTHONHASHSEED"] = str(RANDOM_SEED)
    os.environ["SYSTEMGMMKIT_REPLICATION_MODE"] = mode

    REPRO_DIR.mkdir(parents=True, exist_ok=True)
    RUN_LOG_DIR.mkdir(parents=True, exist_ok=True)

    expectations = _load_expectations(EXPECTED_PATH)
    step_records: list[tuple[str, int, bool]] = []

    if run_verify_only:
        step_records.append(("verify_only", 0, True))
    else:
        for idx, step in enumerate(_pipeline_for_mode(mode), start=1):
            log_file = RUN_LOG_DIR / f"{idx:02d}_{step.name.lower().replace(' ', '_')}.log"
            code = _run_command(step, log_file)
            step_records.append((step.name, code, step.required))
            print(f"[{'PASS' if code == 0 else 'FAIL'}] {step.name} (exit {code})")
            if code != 0 and step.required:
                checks = _collect_verification_status(expectations)
                _build_manifest(mode, step_records, checks)
                return code

    preverify_checks = _collect_verification_status(expectations)
    _build_manifest(mode, step_records, preverify_checks)
    _build_checksums(
        [path for path, _, _, _ in preverify_checks if path.exists()],
        CHECK_SUM_FILE,
    )

    verify_step = Step(
        name="Verify outputs",
        command=[sys.executable, "replication/scripts/validation/99_verify_outputs.py"],
        required=True,
    )
    verify_code = _run_command(
        verify_step,
        RUN_LOG_DIR / "99_output_verification.log",
    )
    print(f"[{'PASS' if verify_code == 0 else 'FAIL'}] Verify outputs (exit {verify_code})")
    step_records.append((verify_step.name, verify_code, verify_step.required))

    checks = _collect_verification_status(expectations)
    _build_manifest(mode, step_records, checks)

    if verify_code != 0:
        return verify_code

    failed_outputs = [
        path for path, ok, note, _ in checks if not ok and path.name != "checksums.sha256"
    ]
    if failed_outputs:
        with MANIFEST_PATH.open("a", encoding="utf-8") as f:
            f.write(f"# failed_required_outputs={len(failed_outputs)}\n")
        return 1

    _build_checksums([path for path, _, _, _ in checks if path.exists()], CHECK_SUM_FILE)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=("Run the JSS manuscript replication pipeline."))
    parser.add_argument(
        "--mode",
        choices=("smoke", "open", "full"),
        default="open",
        help="smoke: core checks only; open: python + archived cross-software references; full: includes Stata reruns where available.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete pipeline-owned generated outputs before rerunning.",
    )
    parser.add_argument(
        "--run-verify-only",
        action="store_true",
        help="Run only output verification against expected outputs.",
    )
    args = parser.parse_args()

    run_stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    run_marker = {
        "mode": args.mode,
        "seed": RANDOM_SEED,
        "run_at_utc": run_stamp,
        "repo_root": ".",
    }
    if args.clean:
        _clean_generated(
            [
                ROOT / "data" / "processed",
                ROOT / "data" / "synthetic",
                ROOT / "results" / "normalized",
                ROOT / "results" / "comparisons",
                ROOT / "results" / "raw" / "systemgmmkit",
                ARTIFACT_JSS / "tables",
                ARTIFACT_JSS / "figures",
                RUN_LOG_DIR,
                REPRO_DIR,
                ROOT / "paper_jss" / "tables",
                ROOT / "paper_jss" / "figures",
                ROOT / "paper_jss" / "main.tex",
                ROOT / "paper_jss" / "main.pdf",
                ROOT / "paper_jss" / "main.aux",
                ROOT / "paper_jss" / "main.bbl",
                ROOT / "paper_jss" / "main.blg",
                ROOT / "paper_jss" / "main.fdb_latexmk",
                ROOT / "paper_jss" / "main.fls",
                ROOT / "paper_jss" / "main.log",
                ROOT / "paper_jss" / "main.out",
                MANIFEST_PATH,
                CHECK_SUM_FILE,
            ]
        )

    _write_json(REPRO_DIR / "replication_run.json", run_marker)
    return _run(args.mode, run_verify_only=args.run_verify_only)


if __name__ == "__main__":
    raise SystemExit(main())
