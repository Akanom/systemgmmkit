from pathlib import Path

import pandas as pd

OUT = Path("Artifacts/Joss/tables/28_performance_benchmarks")

static = pd.read_csv(OUT / "28_static_performance_summary.csv")
fe = pd.read_csv(OUT / "28_fe_backend_performance_summary.csv")
dynamic = pd.read_csv(OUT / "28_dynamic_gmm_performance_summary.csv")
dynamic_diag = pd.read_csv(OUT / "28_dynamic_gmm_performance_diagnostics.csv")
dynamic_errors = pd.read_csv(OUT / "28_dynamic_gmm_performance_errors.csv")

md = "# Artifact 28: Performance and Scalability Benchmarks\n\n"

md += "## 28A: Static, Panel, and IV Performance\n\n"
md += static.to_markdown(index=False)

md += "\n\n## 28A Addendum: Fixed-Effects Backend Performance\n\n"
md += fe.to_markdown(index=False)

md += "\n\n## 28B: Dynamic-GMM Performance\n\n"
md += dynamic.to_markdown(index=False)

md += "\n\n## Dynamic-GMM Diagnostics Snapshot\n\n"
md += dynamic_diag.to_markdown(index=False)

if not dynamic_errors.empty:
    md += "\n\n## Dynamic-GMM Errors\n\n"
    md += dynamic_errors.to_markdown(index=False)

md += "\n\n## Interpretation\n\n"
md += (
    "Artifact 28 reports performance evidence for systemgmmkit across static, panel, IV, "
    "and dynamic-panel GMM workflows. OLS, pooled OLS, random effects, and 2SLS complete "
    "quickly on synthetic panels up to 9,000 rows. The main performance bottleneck is the "
    "native fixed-effects backend, which is correct but scales poorly on larger fixed-effects "
    "panels. The linearmodels fixed-effects backend is substantially faster and should be "
    "preferred for larger fixed-effects workloads. Difference GMM and System GMM both complete "
    "successfully on controlled dynamic-panel benchmarks using the validated native backend. "
    "These benchmarks are reproducibility-oriented and hardware-dependent; they should not be "
    "interpreted as absolute hardware-independent speed claims.\n"
)

md += "\n\n## Paper-Safe Summary\n\n"
md += (
    "The performance benchmark confirms that the package is practical for small and moderate "
    "validation workloads used in the paper. Static and IV estimators are fast at the tested "
    "sizes. Dynamic-GMM benchmarks complete successfully on controlled panels, with System GMM "
    "taking longer than Difference GMM as expected. Fixed-effects performance depends strongly "
    "on backend choice; the linearmodels backend is recommended for larger fixed-effects panels.\n"
)

path = OUT / "28_performance_summary_final.md"
path.write_text(md, encoding="utf-8")

print("[DONE] Wrote", path)
print(md)
