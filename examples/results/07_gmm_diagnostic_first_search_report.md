# Dynamic GMM specification search report

- Candidates evaluated: 2
- Passed diagnostics: 1
- Rejected by diagnostics: 1
- Failed during estimation/evaluation: 0
- Selection metric: `rmse`

## Recommended specification

- Candidate: `2`
- Model: `custom`
- Rank score: `1.4`
- rmse: `0.7956`

## Candidate table

| spec_id | steps | collapse | transformation | rank_score | rmse | diag_hansen_p | diag_ar2_p | diag_n_instruments | diag_n_groups | diagnostic_policy | missing_required_diagnostics | passes_diagnostics | rejection_reason | error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | twostep | True | fd | 1.4 | 0.7956 | 0.5007 | 0.4079 | 5 | 70 | strict |  | True |  |  |
| 1 | twostep | True | fd |  | 1.013 |  | 0.4083 | 4 | 70 | strict | hansen_p | False | missing_hansen_p |  |