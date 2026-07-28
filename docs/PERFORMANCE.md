# Controlled performance benchmarks

Performance work must preserve the validated econometric execution path. The
reference implementation remains the default; acceleration is explicit and is
accepted only when coefficients, covariance-derived standard errors, residuals,
instrument counts, and diagnostics are exactly equal on the maintained cases.

## Native GMM preparation

Profiling on the maintained 1,344-row, 96-entity System-GMM artifact showed that
matrix preparation, not the estimator algebra, dominated wall time. In a profiled
reference run, `_build_native_matrices` consumed 4.819 of 4.971 seconds. Repeated
pandas extraction in `_safe_get`, `_lagged_series`, and `_style_source_series` was
the principal cost.

The opt-in `preparation_engine="accelerated"` path caches immutable, per-fit source
and transformed Series. It preserves the existing row construction, sorting,
missing-data rules, instrument ordering, matrix operations, estimator algebra, and
diagnostics. It introduces no JIT compiler and no runtime dependency.

On Windows with CPython 3.13.7, NumPy 2.5.1, pandas 3.0.5, and SciPy 1.18.0, the
controlled System-GMM artifact produced these warm-fit medians:

| Engine | Median | Relative speed | Reduction |
|---|---:|---:|---:|
| `reference` | 1.3019 s | 1.00x | - |
| `accelerated` | 0.3895 s | 3.34x | 70.1% |

These measurements are machine- and environment-specific. They are evidence for
the optimization, not a universal performance guarantee.

The committed harness's 240-row one-step Difference-GMM smoke case recorded a
343,590-byte reference versus 332,144-byte accelerated `tracemalloc` peak, a
3.3% reduction. This is Python-managed allocation evidence, not total process
resident memory.

## Reproduce

From an isolated development environment at the repository root:

```powershell
python benchmarks/benchmark_native_gmm.py --suite quick --repetitions 3
python benchmarks/benchmark_native_gmm.py --suite full --repetitions 5 --output benchmark-results/native-gmm.json
python benchmarks/benchmark_native_gmm.py --suite full --profile-case instrument_heavy_system_fd --profile-limit 40
```

The harness uses deterministic synthetic panels and includes balanced,
unbalanced, unsorted, internally gapped, one-step, two-step, Windmeijer,
collapsed, currently requested uncollapsed, FD, FOD, Difference-GMM,
System-GMM, large-N, large-T, wider-lag, and related-specification cases. It
reports the first fit, repeated warm fits, environment
metadata, dimensions, instrument counts, diagnostics, exact reference/accelerated
parity, and a separately measured `tracemalloc` Python-allocation peak. The latter
is not total process resident memory.

The quick smoke command used by maintainers is:

```powershell
python benchmarks/benchmark_native_gmm.py --case small_difference_fd_onestep --engine accelerated --repetitions 1
```

## Static estimators

The static-estimator harness profiles full OLS, pooled OLS, fixed-effects,
random-effects, and panel-IV fits. It confirmed that NumPy/BLAS already handles
the ordinary OLS algebra efficiently, while wide LSDV designs spent most of their
time repeatedly applying SVD-based rank checks to every design prefix.

The opt-in static `preparation_engine="accelerated"` performs one full-design
rank check. When the design is full rank, it safely bypasses the repeated prefix
checks. When the design is rank deficient, it falls back to the unchanged
sequential reference algorithm, including its tolerance and column order. The
estimator, projection, covariance, fitted-value, and diagnostic algebra is shared
unchanged.

On Windows with CPython 3.14.6, NumPy 2.4.6, pandas 3.0.3, SciPy 1.17.1, and
OpenBLAS 0.3.31, the deterministic quick suite produced these warm medians:

| Workload | Reference | Accelerated | Relative speed | Reduction |
|---|---:|---:|---:|---:|
| OLS robust, 16,000 rows | 0.0135 s | not needed | - | - |
| Pooled OLS clustered, 12,000 rows | 0.1055 s | not needed | - | - |
| Two-way LSDV fixed effects, 800 rows | 0.4756 s | 0.0646 s | 7.37x | 86.4% |
| Random effects, 15,028 rows | 0.0244 s | not shipped | - | - |
| Panel IV without effects, 2,000 rows | 0.0515 s | 0.0431 s | 1.20x | 16.3% |
| Panel IV with two-way LSDV effects, 640 rows | 0.5335 s | 0.1075 s | 4.96x | 79.8% |

Every accelerated case reported exact reference identity for coefficients,
standard errors, residuals, fitted values, and prepared design ordering. Python
allocation peaks were also slightly lower for the two material LSDV cases. The
random-effects candidate reduced runtime by only about 6%; it was not retained
because the improvement did not justify another public execution path.

Reproduce the static benchmark from the repository root:

```powershell
python benchmarks/benchmark_static_estimators.py --suite quick --repetitions 5
python benchmarks/benchmark_static_estimators.py --suite full --repetitions 5 --output benchmark-results/static-estimators.json
python benchmarks/benchmark_static_estimators.py --case panel_iv_lsdv --profile-case panel_iv_lsdv --profile-limit 40
```

## Boundaries

- `reference` remains the default and rollback path.
- The accelerator does not weaken numerical tolerances or suppress diagnostics.
- Static acceleration does not regroup panel-IV matrix multiplication or change
  rank-deficient column selection; both remain on the validated reference path.
- The uncollapsed-request case records current native behaviour but does not
  expand the maintained collapsed parity claim or alter instrument rules.
- Benchmark JSON and profiler output are generated evidence and should not be
  committed unless a review explicitly requests a stable artifact.
