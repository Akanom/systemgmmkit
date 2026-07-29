# Kaggle and Google Colab usage

`systemgmmkit` examples may be run in Kaggle or Google Colab notebooks when the
notebook validates `systemgmmkit` panel-data or dynamic-GMM workflows only.
Cloud notebooks are reproducibility aids; they are not a repository-wide package
comparison workflow.

## Package boundary

- Use `systemgmmkit` notebooks for panel-data, IV/2SLS, Difference GMM, System
  GMM, diagnostics, post-estimation, forecasting, visualization, and
  package-scoped validation examples.
- Do not host `limiteddepkit`, causal-inference, R-learner, DiD, or unrelated
  package evidence inside a `systemgmmkit` notebook.
- If a notebook compares against Stata, R, or Python references, the comparison
  must be tied to an aligned `systemgmmkit` estimator, fixture, instrument
  design, covariance target, sample construction, and tolerance.

## Credentials and data

- Never commit `kaggle.json`, Google credentials, API tokens, cookies, or local
  notebook secrets.
- Store Kaggle credentials in the runtime secret manager or in
  `~/.kaggle/kaggle.json` on the machine running the notebook.
- Keep downloaded third-party datasets and generated validation work directories
  out of Git unless their license and provenance permit redistribution.
- Record dataset source URLs, hashes, package versions, random seeds, Stata/R
  reference versions where used, and the exact `systemgmmkit` commit or release.

## Minimal cloud setup

```python
!python -m pip install systemgmmkit

import systemgmmkit as sgk

print(sgk.__version__)
```

For development checkouts, install from the repository URL or upload a built
wheel. Pin the package version for any notebook intended as validation evidence.

## Evidence rule

Cloud notebook output can support examples and adoption notes, but formal
validation claims remain the package-scoped Stata/R/Python harnesses documented
in the validation and artifact guides.
