from pathlib import Path

import pandas as pd

OUT = Path("Artifacts/Joss/tables/28_performance_benchmarks")

static = pd.read_csv(OUT / "28_static_performance_summary.csv")
fe = pd.read_csv(OUT / "28_fe_backend_performance_summary.csv")

md = "# Artifact 28A: Static, Panel, IV, and Fixed-Effects Backend Performance\n\n"

md += "## Static, Panel, and IV Runtime Summary\n\n"
md += static.to_markdown(index=False)

md += "\n\n## Fixed-Effects Backend Runtime Summary\n\n"
md += fe.to_markdown(index=False)

md += "\n\n## Interpretation\n\n"
md += (
    "Artifact 28A reports runtime and traced Python peak memory for systemgmmkit static, "
    "panel, and IV workflows. OLS, pooled OLS, random effects, and 2SLS complete quickly "
    "on synthetic panels up to 9,000 rows. The main performance bottleneck is native fixed "
    "effects: the native backend is correct but scales poorly on medium and large panels. "
    "The linearmodels fixed-effects backend is substantially faster and should be preferred "
    "for larger fixed-effects workloads. Median runtime is the preferred performance statistic "
    "because first-run warm-up and import/cache effects can distort means, especially for backend "
    "comparisons. These benchmarks are reproducibility-oriented and hardware-dependent; they are "
    "not absolute speed claims.\n"
)

md += "\n\n## Practical Recommendation\n\n"
md += (
    "For small fixed-effects models, either backend is usable. For medium and large fixed-effects "
    "models, users should prefer `prefer_backend=\"linearmodels\"`. Future optimization work should "
    "focus on the native fixed-effects backend.\n"
)

path = OUT / "28_static_fe_backend_performance_summary_final.md"
path.write_text(md, encoding="utf-8")

print("[DONE] Wrote", path)
print(md)
