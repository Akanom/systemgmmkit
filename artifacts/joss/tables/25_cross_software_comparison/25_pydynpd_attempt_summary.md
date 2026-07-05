# Artifact 25: pydynpd Numerical Benchmark

## Status

COMPLETED_IN_COMPATIBILITY_ENVIRONMENT

## Environment

The pydynpd benchmark completed successfully after running it in a pinned compatibility environment rather than the active Python 3.14 environment.

Compatibility environment:

- Python: compatibility venv `.venv-pydynpd`
- NumPy: 1.26.4
- SciPy: 1.11.4
- pandas: 2.1.4
- pydynpd: 0.2.2

## Results

pydynpd completed both benchmark runs:

- Difference GMM: OK
- System GMM: OK

The results are included in:

- `25_python_pydynpd_difference_gmm_results.csv`
- `25_python_pydynpd_system_gmm_results.csv`
- `25_python_pydynpd_run_log.json`

## Interpretation

The pydynpd numerical results are retained as cross-software ecosystem comparison outputs.

They are not treated as failed parity tests. The comparison status is REVIEW because pydynpd differs from systemgmmkit beyond the predefined auxiliary tolerance band. This is expected unless instrument construction, sample trimming, equation scope, finite-sample correction, and covariance scaling are exactly aligned across packages.

Formal parity evidence in the paper relies on:

- Artifact 24: maintained dynamic-GMM parity certificate
- Artifact 22: controlled Stata/systemgmmkit comparison
