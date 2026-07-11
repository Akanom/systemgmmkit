# Native dynamic-panel GMM result: difference_gmm_native

- Backend: `native-gmm`
- Observations: `810`
- Instruments: `5`
- Covariance: `robust-clustered-two-step-uncorrected`
- Notes:
  - Native dynamic-panel GMM engine.
  - Native System GMM parity with xtabond2 is verified for coefficients, N, groups, instruments, and close Hansen diagnostics on the maintained collapsed benchmark; Sargan and AR diagnostics are certified against xtabond2 for the maintained collapsed two-step System GMM benchmark within declared numerical tolerance.
  - Windmeijer-corrected two-step standard errors are available via windmeijer=True but are not the default.

|         |    coef |   std_err |        z |   p_value |
|:--------|--------:|----------:|---------:|----------:|
| L1.y    |  0.5265 |    0.0293 |  17.9883 |         0 |
| x1      |  0.536  |    0.012  |  44.7856 |         0 |
| x2      | -0.3423 |    0.0121 | -28.2197 |         0 |
| control |  0.2299 |    0.0046 |  50.445  |         0 |