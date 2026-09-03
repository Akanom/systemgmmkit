# JSS replication package

This directory is the single-entry replication package for the JSS manuscript.
It regenerates the data products, econometric results, validation summaries,
automatic GMM search, all nine manuscript tables, the manuscript figure, and the
compiled JSS PDF. Exact output paths, generating scripts, checksums, and pass/fail
status are recorded in `manifest.csv` and `checksums.sha256`.

The JOSS submission is separate and remains Markdown-only at `paper/paper.md`.
The JSS manuscript uses the official `jss` LaTeX class in `paper_jss/`.

## Requirements

- Python 3.9 or newer (the recorded run uses Python 3.12.3 on Windows 11).
- A LaTeX installation providing `latexmk`, `pdflatex`, and BibTeX.
- Internet access on the first open/full run to download NASA C-MAPSS FD001.
- About 250 MB of free working space; no GPU is required.
- Optional: licensed Stata with `xtabond2` for an independent proprietary rerun.

Install the pinned publication dependencies from the repository root:

```powershell
python -m pip install -r replication/requirements.txt
```

The workflow refuses to build manuscript tables unless the installed versions
are exactly `systemgmmkit==1.0.0` and `universal-output-hub==0.2.4`.

## One-command runs

The open, reviewer-facing replication is:

```powershell
python replication/run_all.py --mode open --clean
```

On the recorded Windows 11 reference machine, the complete open run finished in
190.247 seconds on 2026-08-09. Runtime will vary by CPU, LaTeX installation, and
whether the NASA archive must be downloaded.

Use the deterministic smoke mode for a quick pipeline check. Only this mode may
substitute a documented synthetic FD001 panel when the NASA input is absent:

```powershell
python replication/run_all.py --mode smoke --clean
```

The full mode adds the optional Stata hook when its wrapper is present:

```powershell
python replication/run_all.py --mode full --clean
```

To recheck existing artifacts without rerunning estimators:

```powershell
python replication/run_all.py --mode open --run-verify-only
```

## Executed workflow

1. Record the OS, Git state, Python environment, and software versions.
2. Acquire and process NASA C-MAPSS FD001, recording source hashes.
3. Run the leakage-controlled N-CMAPSS application.
4. Generate and estimate the controlled Difference/System GMM panel.
5. Execute the four-candidate diagnostic-first automatic GMM search.
6. Normalize static, GMM, Windmeijer, post-estimation, panel-validation,
   forecasting, and application checks.
7. Export every manuscript table through Universal Output Hub 0.2.4.
8. Generate the manuscript figure from the normalized automatic-search CSV.
9. Compile `paper_jss/main.tex` with the official JSS class and `jss.bst`.
10. Apply structural and semantic output gates, then write the manifest,
    verification report, per-step logs, and SHA-256 file list.

The main model/application scripts are `09_ncmapss_application.py`,
`10_controlled_dynamic_gmm.py`, and `11_auto_gmm_search.py`. The table, figure,
manuscript, and validation stages live under their matching subdirectories in
`replication/scripts/`.

## Data provenance

The compact N-CMAPSS application panel is a fixed, checked input at
`data/external/ncmapss/ncmapss_ds01_dev_unit_cycle_compact.csv`; its README
records its derivation and SHA-256 value. The open/full pipeline downloads the
official NASA C-MAPSS archive only when `data/raw/fd001/train_FD001.txt` is
absent. The URL, archive hash, extracted-file hash, dimensions, and missingness
are written to `artifacts/jss/reproducibility/fd001_preprocessing_report.json`.

## Primary outputs

- `paper_jss/main.pdf`: compiled JSS manuscript.
- `paper_jss/tables/*.{tex,csv,md}`: nine Universal Output Hub exports.
- `paper_jss/publication_manifest.json`: exact table inputs and exclusions.
- `results/comparisons/auto_gmm_search_results.csv`: executed model-search rows.
- `results/comparisons/ml_external_python_comparison.csv`: same-split
  predictive comparison with statsmodels and scikit-learn. This is not GMM
  estimator parity.
- `artifacts/jss/figures/`: manuscript figure in PDF and PNG.
- `artifacts/jss/logs/`: one log per pipeline stage.
- `artifacts/jss/reproducibility/verification_report.json`: semantic gate report.
- `replication/manifest.csv`: output-to-script traceability table.
- `replication/checksums.sha256`: SHA-256 list for expected outputs.

## Cross-software boundary

The open run reads the six-specification Stata certificate from the signed
`v0.5.14` evidence tag and fails if the installed package version differs from
`1.0.0`. This makes
the reported certificate reproducible without proprietary software. It does not
claim to rerun Stata. A full independent Stata execution remains an optional
platform-specific verification and must be identified as such in any submission
log.

The portable manual do-file is
`replication/scripts/stata/jss_dynamic_gmm_manual.do`. From the repository root,
run:

```stata
do replication/scripts/stata/jss_dynamic_gmm_manual.do
```

If Stata starts in another directory, pass the repository root explicitly:

```stata
do "C:/path/to/systemgmmkit/replication/scripts/stata/jss_dynamic_gmm_manual.do" ///
   "C:/path/to/systemgmmkit"
```

The script exports coefficients, standard errors, Hansen and AR diagnostics,
observation/group counts, and instrument counts to `artifacts/jss/stata_manual/`.
Its printed execution date is provenance only and is never used as a numerical
parity condition.

Where Stata has no analogue for the ML/search orchestration, run the executable
Python comparison:

```powershell
python replication/scripts/python/12_ml_comparator.py
```

It compares the registered temporal holdout against statsmodels OLS and a
scikit-learn random forest. The output labels these as predictive baselines,
not substitutes for the Stata Dynamic GMM certificate.
