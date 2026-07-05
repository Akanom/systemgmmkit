# Artifact 28B: Dynamic-GMM Performance Benchmark

## Sample Audit

| size_label   |   rows |   entities |   periods |   missing_L1_y | systemgmmkit_version   | backend   |   timeout_seconds |
|:-------------|-------:|-----------:|----------:|---------------:|:-----------------------|:----------|------------------:|
| tiny         |    300 |         30 |        10 |             30 | 0.5.11                 | native    |               180 |
| small        |    600 |         60 |        10 |             60 | 0.5.11                 | native    |               180 |

## Runtime and Memory Summary

| benchmark      | backend   | size_label   |   n_rows |   n_entities |   n_periods |   repetitions |   mean_seconds |   median_seconds |   min_seconds |   max_seconds |   mean_peak_memory_mb |   max_peak_memory_mb | status   |
|:---------------|:----------|:-------------|---------:|-------------:|------------:|--------------:|---------------:|-----------------:|--------------:|--------------:|----------------------:|---------------------:|:---------|
| Difference GMM | native    | small        |      600 |           60 |          10 |             1 |       0.775118 |         0.775118 |      0.775118 |      0.775118 |              0.751925 |             0.751925 | OK       |
| Difference GMM | native    | tiny         |      300 |           30 |          10 |             1 |       0.457724 |         0.457724 |      0.457724 |      0.457724 |              0.425929 |             0.425929 | OK       |
| System GMM     | native    | small        |      600 |           60 |          10 |             1 |       1.51854  |         1.51854  |      1.51854  |      1.51854  |              1.53016  |             1.53016  | OK       |
| System GMM     | native    | tiny         |      300 |           30 |          10 |             1 |       0.698656 |         0.698656 |      0.698656 |      0.698656 |              0.817631 |             0.817631 | OK       |

## Diagnostics Snapshot

|   nobs |   n_groups |   n_instruments | covariance_type                       |   hansen_p |   sargan_p |         ar1_p |       ar2_p | benchmark      | backend   | size_label   |   rep | status   |
|-------:|-----------:|----------------:|:--------------------------------------|-----------:|-----------:|--------------:|------------:|:---------------|:----------|:-------------|------:|:---------|
|    210 |         30 |               5 | robust-clustered-two-step-uncorrected |   0.18071  |   0.594091 |   2.41739e-06 |   0.473271  | Difference GMM | native    | tiny         |     1 | OK       |
|    240 |         30 |               8 | robust-clustered-two-step-windmeijer  |   0.310645 |   0.429167 | nan           | nan         | System GMM     | native    | tiny         |     1 | OK       |
|    420 |         60 |               5 | robust-clustered-two-step-uncorrected |   0.744914 |   0.877675 |   6.77373e-13 |   0.0395453 | Difference GMM | native    | small        |     1 | OK       |
|    480 |         60 |               8 | robust-clustered-two-step-windmeijer  |   0.549899 |   0.548038 | nan           | nan         | System GMM     | native    | small        |     1 | OK       |

## Interpretation

Artifact 28B reports controlled dynamic-GMM performance using the validated native backend. Difference GMM and System GMM are benchmarked separately from static/panel/IV workflows because instrument construction, weighting matrices, and two-step covariance correction can dominate runtime. Runs that exceed the timeout or raise process-level exits are reported transparently rather than blocking artifact generation. These benchmarks are reproducibility-oriented and hardware-dependent; they are not absolute speed claims.
