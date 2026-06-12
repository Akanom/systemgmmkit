from __future__ import annotations

import re
from pathlib import Path

README = Path("README.md")
text = README.read_text(encoding="utf-8")

backup = Path("artifacts/parity/xtabond2/README_before_system_gmm_parity_update.md")
backup.parent.mkdir(parents=True, exist_ok=True)
backup.write_text(text, encoding="utf-8")


def block(lines: list[str]) -> str:
    return "\n".join(lines).strip() + "\n"


def replace_section(source: str, heading: str, lines: list[str]) -> str:
    pattern = re.compile(
        rf"(?ms)^## {re.escape(heading)}\n.*?(?=^---\n\n## |\Z)"
    )

    replacement = f"## {heading}\n\n{block(lines)}\n"

    source2, count = pattern.subn(replacement, source, count=1)

    if count != 1:
        raise RuntimeError(f"Could not replace section: {heading}")

    return source2


def replace_if_present(source: str, old: str, new: str) -> str:
    if old in source:
        return source.replace(old, new)
    print(f"WARNING: text not found for replacement: {old[:90]!r}")
    return source


text = replace_if_present(
    text,
    "* experimental native System GMM estimation;",
    "* native System GMM estimation with verified `xtabond2` baseline parity checks;",
)

text = replace_section(
    text,
    "Current validation status",
    [
        "| Estimator                       | Current status                                      | Interpretation |",
        "| ------------------------------- | --------------------------------------------------- | -------------- |",
        "| Static panel estimators         | Active development                                  | Pooled OLS, Fixed Effects, Random Effects, and Panel IV / 2SLS are available for applied workflow use and should be validated against reference packages for critical work. |",
        "| Native Difference GMM           | Strict parity passed on current benchmark           | Native Difference GMM matches the current validation backend and Stata oracle within numerical tolerance on the tested benchmark. |",
        "| Native System GMM               | `xtabond2` baseline parity passed                   | Native System GMM matches `xtabond2` on the current collapsed two-step System GMM benchmark for coefficients, raw residual moments (`Z'u`), group-scaled two-step weighting matrix (`A2 / n_groups`), and Hansen J. |",
        "| System GMM via `backend=\"auto\"` | Stable public workflow route                        | `backend=\"auto\"` remains the recommended public workflow route unless the user needs explicit native/adapter comparison. Users who need exact replication should report the selected backend and validation benchmark. |",
        "",
        "The current validation harness confirms strict parity for native Difference GMM on the benchmark specification.",
        "",
        "Native System GMM now passes a dedicated `xtabond2` baseline parity benchmark. The verified benchmark covers coefficient estimates, raw residual moments (`Z'u`), the group-scaled two-step weighting matrix (`A2 / n_groups`), and the Hansen J statistic.",
        "",
        "This should be interpreted as a strong baseline parity result, not as a universal claim of Stata identity across every possible dataset, lag window, missing-data pattern, instrument classification, covariance assumption, or finite-sample correction. Broader specification coverage and Windmeijer-corrected two-step standard-error parity remain on the validation roadmap.",
    ],
)

text = replace_section(
    text,
    "Dynamic GMM backend policy",
    [
        "`systemgmmkit` is the user-facing package for dynamic-panel GMM workflows.",
        "",
        "Users should call the public API:",
        "",
        "```python",
        "from systemgmmkit import run_system_gmm, run_difference_gmm",
        "```",
        "",
        "The package then routes estimation through the selected backend.",
        "",
        "| User option           | Difference GMM behavior                                       | System GMM behavior |",
        "| --------------------- | ------------------------------------------------------------- | ------------------- |",
        "| `backend=\"auto\"`      | Uses the validated native `systemgmmkit` Difference GMM path. | Uses the package's configured stable System GMM route. This is the recommended default workflow unless the user needs a specific backend. |",
        "| `backend=\"validated\"` | Uses the validated native `systemgmmkit` Difference GMM path. | Routes through the validated backend adapter where available. |",
        "| `backend=\"native\"`    | Uses the native `systemgmmkit` engine.                        | Uses the native `systemgmmkit` engine. The current baseline `xtabond2` parity benchmark is passed for collapsed two-step System GMM coefficients, moments, group-scaled A2, and Hansen J. |",
        "| `backend=\"pydynpd\"`   | Explicitly routes through the backend adapter.                | Explicitly routes through the backend adapter. |",
        "",
        "This design keeps `systemgmmkit` as the stable public interface while allowing explicit backend selection for replication, benchmarking, and sensitivity analysis.",
        "",
        "For empirical System GMM work, a typical public workflow is:",
        "",
        "```python",
        "result = run_system_gmm(",
        "    spec,",
        "    data,",
        "    entity=\"id\",",
        "    time=\"time\",",
        "    backend=\"auto\",",
        ")",
        "```",
        "",
        "For strict native replication of the current `xtabond2` parity benchmark, use `backend=\"native\"` and match the sample, lag windows, collapsed-instrument setting, IV treatment, time-dummy treatment, transformation, covariance assumptions, and estimation options.",
    ],
)

text = replace_if_present(
    text,
    "Native System GMM is currently experimental. Use `backend=\"auto\"` for empirical System GMM workflows requiring stronger external validation through the package’s validated backend route.",
    "Native System GMM now passes a dedicated `xtabond2` baseline parity benchmark for collapsed two-step System GMM coefficients, residual moments, group-scaled two-step weighting matrix, and Hansen J. Broader specification coverage and Windmeijer-corrected two-step standard-error parity remain under validation, so users should report the backend, model specification, instrument count, and validation context for critical empirical work.",
)

text = replace_if_present(
    text,
    "This is a construction-architecture milestone, not a final claim of universal System GMM coefficient parity.",
    "This construction architecture now supports the current native System GMM `xtabond2` baseline parity result. It should still be interpreted conservatively: the benchmark verifies a specific collapsed two-step System GMM specification, not universal equivalence across all possible panel designs and covariance corrections.",
)

text = replace_if_present(
    text,
    "* experimental System GMM;",
    "* System GMM with verified `xtabond2` baseline parity for the current collapsed two-step benchmark;",
)

native_extra = [
    "The native System GMM parity benchmark currently verifies:",
    "",
    "* coefficient estimates against `xtabond2`;",
    "* raw residual moments (`Z'u`) after instrument-order mapping;",
    "* two-step weighting matrix alignment after group scaling (`A2 / n_groups`);",
    "* Hansen J statistic alignment;",
    "* automated pytest regression guarding for the benchmark.",
    "",
    "The remaining high-priority validation gap is Windmeijer-corrected two-step standard-error parity, followed by broader tests across alternative datasets, lag windows, missing-data structures, and instrument classifications.",
]

if "The native System GMM parity benchmark currently verifies:" not in text:
    text = replace_if_present(
        text,
        "The native backend is intended to provide a transparent Python implementation that can be inspected, tested, and extended without relying only on an external backend.",
        "The native backend is intended to provide a transparent Python implementation that can be inspected, tested, and extended without relying only on an external backend.\n\n" + block(native_extra).strip(),
    )

text = replace_section(
    text,
    "Validation roadmap",
    [
        "Before claiming broader production certification across panel designs, the package should continue to be tested on:",
        "",
        "* balanced panels;",
        "* unbalanced panels;",
        "* short-`T` panels;",
        "* longer-`T` panels;",
        "* high-`N`, low-`T` panels;",
        "* panels with missing observations;",
        "* different lag windows;",
        "* models with no controls;",
        "* models with many controls;",
        "* interaction-heavy specifications;",
        "* decomposition specifications;",
        "* alternative instrument classifications;",
        "* Stata `xtabond2` replication benchmarks.",
        "",
        "High-priority remaining validation items:",
        "",
        "* Windmeijer-corrected two-step standard-error parity;",
        "* broader System GMM parity across multiple specifications;",
        "* robustness of AR(1), AR(2), Sargan, and Hansen diagnostics across panel structures;",
        "* documentation of exact Stata-compatible options and known non-equivalence cases.",
        "",
        "This roadmap protects the package from overclaiming and supports academically defensible validation.",
    ],
)

README.write_text(text, encoding="utf-8")

print("Updated README.md with native System GMM xtabond2 baseline parity status.")
print(f"Backup written to: {backup}")
