# systemgmmkit Conformance Roadmap

## Existing benchmark spec names

The conformance suite keeps the existing benchmark names:

- difference_gmm_baseline_controls
- system_gmm_baseline_controls
- system_gmm_three_way_controls
- system_gmm_three_way_no_controls
- system_gmm_decomposition_controls

## Current certification language

| Spec | Status |
|---|---|
| difference_gmm_baseline_controls | PASS_PARITY / PASS_STRICT |
| system_gmm_baseline_controls | EXPERIMENTAL_PARITY_PENDING |
| system_gmm_three_way_controls | EXPERIMENTAL_PARITY_PENDING |
| system_gmm_three_way_no_controls | EXPERIMENTAL_PARITY_PENDING |
| system_gmm_decomposition_controls | EXPERIMENTAL_PARITY_PENDING |

## Required next work

1. pooled OLS parity
2. fixed-effects parity
3. two-way fixed-effects parity
4. random-effects parity
5. first-difference estimator
6. first-difference parity
7. panel IV / 2SLS parity
8. robust and clustered SE parity
9. Difference GMM expanded parity
10. System GMM strict parity
11. instrument-count parity
12. instrument-matrix parity
13. AR(1), AR(2), Hansen, Sargan, Diff-Hansen parity
14. missing-data and e(sample)-style parity
15. balanced/unbalanced panel parity
16. automated parity report generator
17. graphical parity report through universal-output-hub
