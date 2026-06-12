# GMM Weight Scaling Candidate Test

Native J-stat: `147.83846658036637`
xtabond2 Hansen statistic: `6.5773711`
Native W norm: `0.7835812218923436`
xtabond2 A2 norm: `0.0106323168364126`

| scale_name                  |       scale |    scaled_j |   target_xtabond2_hansen |   abs_diff |
|:----------------------------|------------:|------------:|-------------------------:|-----------:|
| match_target_J              | 0.0444903   |   6.57737   |                  6.57737 |    0       |
| match_A2_norm               | 0.0135689   |   2.006     |                  6.57737 |    4.57137 |
| divide_by_groups_96         | 0.0104167   |   1.53998   |                  6.57737 |    5.03739 |
| divide_by_nobs_1248         | 0.000801282 |   0.11846   |                  6.57737 |    6.45891 |
| divide_by_stacked_rows_2400 | 0.000416667 |   0.0615994 |                  6.57737 |    6.51577 |
| none                        | 1           | 147.838     |                  6.57737 |  141.261   |

## Interpretation

- This tests scalar normalization only.
- If `match_A2_norm` is close to `match_target_J`, the problem is mostly scalar normalization.
- If not, the problem is matrix construction, residual moment aggregation, or equation stacking.