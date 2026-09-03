| Estimator      | Comparators                       |   Max coef. diff |   Max SE diff |
|:---------------|:----------------------------------|-----------------:|--------------:|
| OLS            | R lm, Stata, statsmodels          |         2.16e-08 |      4.01e-10 |
| Pooled OLS     | R plm, Stata, linearmodels        |         2.16e-08 |      4.01e-10 |
| Fixed Effects  | R plm, Stata, linearmodels        |         1.6e-08  |      1.14e-09 |
| Random Effects | R plm, Stata, linearmodels        |         2.16e-08 |      0.000658 |
| 2SLS           | R AER::ivreg, Stata, linearmodels |         6.35e-08 |      0.00038  |