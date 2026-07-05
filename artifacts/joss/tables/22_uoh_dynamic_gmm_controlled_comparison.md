| term                      | Difference GMM                                                     | System GMM   |
|:--------------------------|:-------------------------------------------------------------------|:-------------|
| Predetermined regressor   | 0.265653                                                           | 0.055877     |
|                           | (0.223165)                                                         | (0.137907)   |
| Exogenous regressor       | 0.251000***                                                        | 0.242354***  |
|                           | (0.044706)                                                         | (0.019691)   |
| Lagged dependent variable | 0.711380***                                                        | 0.929211***  |
|                           | (0.264949)                                                         | (0.042293)   |
| Constant                  |                                                                    | 0.129496***  |
|                           |                                                                    | (0.035087)   |
|                           |                                                                    |              |
| Significance              | * p≤0.1, ** p≤0.05, *** p≤0.01                                     |              |
|                           |                                                                    |              |
| Notes                     | Controlled synthetic panel.                                        |              |
|                           | Lagged dependent variable treated as endogenous with GMM lags 2:3. |              |
|                           | x_pred treated as predetermined with GMM lags 2:3.                 |              |
|                           | x_exog treated as exogenous IV-style.                              |              |
|                           | Collapsed instruments; two-step estimation.                        |              |
|                           | Stata xtabond2 reference commands are exported separately.         |              |
