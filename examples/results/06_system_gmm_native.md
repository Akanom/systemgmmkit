# Native dynamic-panel GMM result: system_gmm_native

- Backend: `native-gmm`
- Observations: `900`
- Instruments: `9`
- Covariance: `robust-clustered-two-step-windmeijer`
- Notes:
  - Native dynamic-panel GMM engine.
  - Native System GMM parity with xtabond2 is verified for coefficients, N, groups, instruments, and close Hansen diagnostics on the maintained collapsed benchmark; Sargan and AR diagnostics are certified against xtabond2 for the maintained collapsed two-step System GMM benchmark within declared numerical tolerance.
  - Windmeijer-corrected two-step standard errors are enabled via windmeijer=True using the pydynpd 0.2.2 formula path; xtabond2 e(V) parity must still be checked.
  - Native System GMM coefficient, Windmeijer-SE, Hansen/Sargan, and signed AR diagnostic parity are certified on the maintained xtabond2 benchmark suite.

|         |    coef |   std_err |       z |   p_value |
|:--------|--------:|----------:|--------:|----------:|
| L1.y    |  0.7743 |    0.0317 | 24.4353 |    0      |
| x1      |  0.3159 |    0.0665 |  4.7466 |    0      |
| x2      | -0.1417 |    0.0792 | -1.7887 |    0.0737 |
| control |  0.2122 |    0.0265 |  8      |    0      |
| _con    | -0.1261 |    0.0481 | -2.6231 |    0.0087 |