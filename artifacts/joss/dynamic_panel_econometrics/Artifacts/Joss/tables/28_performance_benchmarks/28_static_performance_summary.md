# Artifact 28A: Static, Panel, and IV Performance Benchmarks

## Runtime and Memory Summary

| benchmark      | size_label   |   n_entities |   n_periods |   n_rows_raw |   repetitions |   mean_seconds |   median_seconds |   min_seconds |   max_seconds |   mean_peak_memory_mb |   max_peak_memory_mb |
|:---------------|:-------------|-------------:|------------:|-------------:|--------------:|---------------:|-----------------:|--------------:|--------------:|----------------------:|---------------------:|
| 2SLS           | small        |          120 |          10 |         1200 |             3 |      0.032703  |        0.0323116 |     0.02906   |     0.0367375 |              7.29143  |             7.29155  |
| 2SLS           | medium       |          300 |          12 |         3600 |             3 |      0.0892193 |        0.0807829 |     0.0797898 |     0.107085  |             69.4227   |            69.4228   |
| 2SLS           | large        |          600 |          15 |         9000 |             3 |      0.402018  |        0.400277  |     0.366515  |     0.439262  |            466.102    |           466.102    |
| Fixed Effects  | small        |          120 |          10 |         1200 |             3 |      0.61419   |        0.620122  |     0.593823  |     0.628626  |              3.12756  |             3.13351  |
| Fixed Effects  | medium       |          300 |          12 |         3600 |             3 |     26.8164    |       27.5294    |    23.3705    |    29.5493    |             23.061    |            23.0674   |
| Fixed Effects  | large        |          600 |          15 |         9000 |             3 |    369.698     |      380.401     |   347.455     |   381.24      |            116.219    |           116.235    |
| OLS            | small        |          120 |          10 |         1200 |             3 |      0.0288797 |        0.0330093 |     0.0177817 |     0.0358481 |              0.17867  |             0.181208 |
| OLS            | medium       |          300 |          12 |         3600 |             3 |      0.0215451 |        0.0212717 |     0.0195411 |     0.0238225 |              0.464969 |             0.465357 |
| OLS            | large        |          600 |          15 |         9000 |             3 |      0.0205366 |        0.0214295 |     0.0170396 |     0.0231407 |              1.12633  |             1.12661  |
| Pooled OLS     | small        |          120 |          10 |         1200 |             3 |      0.0226991 |        0.020297  |     0.0171989 |     0.0306013 |              0.178371 |             0.17889  |
| Pooled OLS     | medium       |          300 |          12 |         3600 |             3 |      0.0228158 |        0.0227165 |     0.0194589 |     0.0262721 |              0.46625  |             0.466777 |
| Pooled OLS     | large        |          600 |          15 |         9000 |             3 |      0.0292449 |        0.029417  |     0.0200035 |     0.0383142 |              1.12763  |             1.12808  |
| Random Effects | small        |          120 |          10 |         1200 |             3 |      0.0453362 |        0.0519638 |     0.0311806 |     0.0528643 |              0.380547 |             0.389922 |
| Random Effects | medium       |          300 |          12 |         3600 |             3 |      0.0380867 |        0.0382429 |     0.0307295 |     0.0452878 |              1.05762  |             1.05802  |
| Random Effects | large        |          600 |          15 |         9000 |             3 |      0.0353256 |        0.0277658 |     0.0243206 |     0.0538903 |              2.53081  |             2.53115  |

## Interpretation

This artifact reports runtime and traced Python peak memory for systemgmmkit static, panel, and IV workflows. It covers OLS, pooled OLS, fixed effects, random effects, and 2SLS across increasing synthetic panel sizes. These are reproducibility-oriented benchmarks, not hardware-independent speed claims. Dynamic-GMM performance is intentionally benchmarked separately because GMM instrument construction can dominate runtime and should not block the static performance artifact.
