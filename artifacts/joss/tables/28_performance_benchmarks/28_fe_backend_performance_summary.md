# Artifact 28A Addendum: Fixed-Effects Backend Performance

## Runtime and Memory Summary

| benchmark     | backend      | size_label   |   n_entities |   n_periods |   n_rows_raw |   repetitions |   mean_seconds |   median_seconds |   min_seconds |   max_seconds |   mean_peak_memory_mb |   max_peak_memory_mb |
|:--------------|:-------------|:-------------|-------------:|------------:|-------------:|--------------:|---------------:|-----------------:|--------------:|--------------:|----------------------:|---------------------:|
| Fixed Effects | linearmodels | small        |          120 |          10 |         1200 |             3 |      0.572437  |        0.154072  |     0.105462  |     1.45778   |               4.88166 |             13.4721  |
| Fixed Effects | linearmodels | medium       |          300 |          12 |         3600 |             3 |      0.084478  |        0.0836433 |     0.0788437 |     0.0909471 |               1.52964 |              1.53075 |
| Fixed Effects | linearmodels | large        |          600 |          15 |         9000 |             3 |      0.0885693 |        0.088793  |     0.0850077 |     0.0919072 |               3.69601 |              3.69923 |
| Fixed Effects | native       | small        |          120 |          10 |         1200 |             3 |      0.629094  |        0.593171  |     0.581805  |     0.712304  |               3.13193 |              3.13927 |
| Fixed Effects | native       | medium       |          300 |          12 |         3600 |             3 |     28.2407    |       27.0218    |    25.1747    |    32.5258    |              23.0636  |             23.0696  |
| Fixed Effects | native       | large        |          600 |          15 |         9000 |             3 |    373.399     |      392.288     |   326.533     |   401.377     |             116.222   |            116.237   |

## Interpretation

This addendum compares the native and linearmodels fixed-effects backends. The main static benchmark identified fixed effects as the dominant runtime bottleneck. This backend comparison determines whether the linearmodels backend should be recommended for larger fixed-effects panels.
