# Controlled performance benchmarks

Performance work must preserve the validated econometric execution path. The
reference implementation remains the default; acceleration is explicit and is
accepted only when coefficients, covariance-derived standard errors, residuals,
instrument counts, and diagnostics are exactly equal on the maintained cases.

## Stage 1 scope

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

## Boundaries

- `reference` remains the default and rollback path.
- The accelerator does not weaken numerical tolerances or suppress diagnostics.
- The uncollapsed-request case records current native behaviour but does not
  expand the maintained collapsed parity claim or alter instrument rules.
- Benchmark JSON and profiler output are generated evidence and should not be
  committed unless a review explicitly requests a stable artifact.
