from pathlib import Path

paper = Path("paper/paper.md")

if not paper.exists():
    raise FileNotFoundError("paper/paper.md not found. Create paper/paper.md first.")

text = paper.read_text(encoding="utf-8")

validation_table = r"""
<!-- VALIDATION_SUMMARY_TABLE_START -->

| Artifact | Scope | Reference software | Result |
|---|---|---|---|
| 22 | Controlled dynamic-GMM comparison | Stata `xtabond2` | System GMM `PASS_NUMERIC`; Difference GMM `PASS_TOLERANT_AUXILIARY` |
| 24 | Maintained System GMM parity certificate | Stata `xtabond2` | `PASS_XTABOND2_PARITY` |
| 25 | Dynamic-GMM ecosystem comparison | Stata, R, Python | Ecosystem comparison; strict parity limited to aligned Stata benchmarks |
| 26 | Static and post-estimation validation | `statsmodels`, `linearmodels` | OLS/Pooled/FE `PASS_NUMERIC`; RE/2SLS `PASS_COEFFICIENTS` |
| 27 | Static cross-software validation | Python, R, Stata | OLS, pooled OLS, FE, RE, and 2SLS pass under aligned specifications |

<!-- VALIDATION_SUMMARY_TABLE_END -->
"""

workflow_table = r"""
<!-- POSTESTIMATION_ML_TABLE_START -->

| Layer | Capabilities checked | Result |
|---|---|---|
| Post-estimation | `vcov`, `confint`, `predict`, fitted values, residuals | OK |
| Stata-style post-estimation | `lincom`, Wald tests, marginal effects, margins | OK |
| ML-style workflow | result adaptation, prediction, residuals, regression metrics, panel split | OK |
| Extended ML interfaces | model comparison, forecasting, backtesting, dynamic-GMM search | API discovered |

<!-- POSTESTIMATION_ML_TABLE_END -->
"""

performance_table = r"""
<!-- PERFORMANCE_SUMMARY_TABLE_START -->

| Workflow | Tested scale | Result |
|---|---|---|
| OLS / pooled OLS / random effects | Up to 9,000 rows | Fast in tested environment |
| 2SLS | Up to 9,000 rows | Completed successfully; memory rises with size |
| Fixed effects, native backend | Up to 9,000 rows | Compact `native-within` runtime; avoids full FE dummy matrix |
| Fixed effects, `linearmodels` backend | Up to 9,000 rows | Optional upstream `PanelOLS` result object and backend-specific features |
| Difference GMM | 300--600 rows | Approximately 0.46--0.78 seconds |
| System GMM | 300--600 rows | Approximately 0.70--1.52 seconds |

<!-- PERFORMANCE_SUMMARY_TABLE_END -->
"""


def replace_or_insert(text, start_marker, end_marker, heading, block):
    if start_marker in text and end_marker in text:
        before = text.split(start_marker)[0]
        after = text.split(end_marker, 1)[1]
        return before + block.strip() + after

    if heading not in text:
        raise ValueError(f"Heading not found: {heading}")

    return text.replace(heading, heading + "\n" + block, 1)


text = replace_or_insert(
    text,
    "<!-- VALIDATION_SUMMARY_TABLE_START -->",
    "<!-- VALIDATION_SUMMARY_TABLE_END -->",
    "# Validation and Cross-Software Comparison",
    validation_table,
)

text = replace_or_insert(
    text,
    "<!-- POSTESTIMATION_ML_TABLE_START -->",
    "<!-- POSTESTIMATION_ML_TABLE_END -->",
    "# Post-Estimation and ML Workflow Layer",
    workflow_table,
)

text = replace_or_insert(
    text,
    "<!-- PERFORMANCE_SUMMARY_TABLE_START -->",
    "<!-- PERFORMANCE_SUMMARY_TABLE_END -->",
    "# Performance Benchmarks",
    performance_table,
)

paper.write_text(text, encoding="utf-8")

print("[DONE] Updated", paper)
