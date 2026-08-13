# JSS manuscript

This directory contains the Journal of Statistical Software manuscript. The
generated `main.tex` uses the official `jss` class (version 3.6, dated
2026-04-28); `JSS_STYLE_SOURCE.md` records the upstream download URL and hashes.
All nine table bodies are exported through Universal Output Hub 0.2.4 and all
printed sources appear below their corresponding table as part of the caption.
The publication generator also writes the manuscript's numbered econometric,
predictive, controlled-DGP, and diagnostic-search equations; the replication
verifier requires their labels so they cannot disappear silently on rebuild.

Regenerate the complete manuscript, including model results, table/figure
artifacts, PDF, logs, manifest, checksums, and verification report, from the
repository root:

```powershell
python replication/run_all.py --mode open --clean
```

For a manuscript-only rebuild after upstream artifacts already exist:

```powershell
python replication/scripts/tables/01_build_tables.py
python replication/scripts/figures/01_build_figures.py
python replication/scripts/manuscript/01_compile_jss.py
```

The separate JOSS submission remains Markdown-only at `paper/paper.md`. No JSS
LaTeX or generated PDF is written into `paper/`.
