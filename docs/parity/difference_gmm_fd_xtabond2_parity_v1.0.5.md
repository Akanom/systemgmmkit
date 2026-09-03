# First-difference Difference GMM parity in 1.0.5

## Scope

SystemGMMKit 1.0.5 corrects the native, collapsed, first-difference,
two-step Difference-GMM path used by the following maintained Stata command:

```stata
xtabond2 y L.y x w, ///
    gmm(L.y x, lag(2 3) collapse equation(diff)) ///
    iv(w, equation(diff)) noleveleq twostep robust small
```

The fixed reference is Stata 17 IC with `xtabond2` 3.7.2. The reference
bundle contains balanced, unbalanced, and variable-missing panels. It is
identified by the source-CSV SHA-256 digests in
`artifacts/parity/xtabond2/difference_gmm_fd/xtabond2_reference_v1.json`.
Tracked input-fixture digests are computed after canonicalizing text newlines
to LF, so the same Git content has one identity on Windows and POSIX checkouts.
Submitted Stata-export digests remain byte-exact and are not canonicalized.
The Stata-reported clock date is retained verbatim in that artifact, but is not
treated as the actual execution date because the source host used a deliberately
non-current Stata clock.

## Corrected estimator algebra

For entity-specific transformed-error covariance matrix \(H_i\), the first-step
weight is now

\[
A_1 = \left(\sum_i Z_i' H_i Z_i\right)^{-1},
\]

instead of the homoskedastic 2SLS weight \((Z'Z)^{-1}\). The row metadata
constructs \(H_i\) directly, so gaps and variable-specific missingness do not
assume a rectangular panel.

With first-step residual moments \(g_{1i}=Z_i'e_{1i}\),

\[
A_2 = \left(\sum_i g_{1i}g_{1i}'\right)^{-1}
\]

is the second-step criterion weight. The Hansen statistic is therefore

\[
J_H=(Z'e_2)'A_2(Z'e_2),
\]

without re-estimating a third weight from the final residuals.

The Windmeijer correction follows the construction in `xtabond2.mata`. Let
\(V_2=(X'ZA_2Z'X)^{-1}\), \(a=A_2Z'e_2\), and
\(ZX_i=Z_i'X_i\). Define

\[
R=\sum_i\left[(g_{1i}'a)ZX_i+(g_{1i}a')ZX_i\right]
\]

and

\[
D_W=V_2X'ZA_2R.
\]

Then the unscaled corrected covariance is

\[
V_{2c}=V_2+D_WV_{1r}D_W'+D_WV_2+V_2D_W',
\]

followed by the registered `small` finite-sample scalar. The Sargan statistic
uses first-step residual moments and
\(\widehat\sigma_1^2=e_1'e_1/(2N_{\text{obs}})\). The signed AR diagnostics use
the same robust/two-step denominator construction as `xtabond2`, with the raw
Difference-GMM \(A_2\) weight.

## Maintained numerical gates

The three fixtures require exact parameter names, semantic moment identities,
instrument and sample counts, and entity-time estimation-sample keys. Numeric
outputs use prospective absolute tolerances that accommodate the different
matrix inversion and accumulation implementations in Mata and NumPy:

| Surface | Absolute tolerance |
| --- | ---: |
| Coefficients | `2e-7` |
| Windmeijer covariance | `5e-8` |
| Second-step criterion weight, A2 | `2e-9` |
| Summed residual moments, Z'e2 | `2e-5` |
| Hansen J / p-value | `1e-6` / `2e-7` |
| Sargan J / p-value | `2e-6` / `3e-7` |
| Signed AR z / p-value | `2e-6` / `2e-7` |

The largest observed differences across the maintained fixtures were
`7.63e-8` for coefficients, `2.28e-8` for covariance, `1.43e-9` for A2,
`6.83e-6` for Z'e2, `7.89e-7` for Hansen J, `1.24e-7` for Hansen p,
`9.46e-7` for Sargan J, `1.75e-7` for Sargan p, `8.72e-7` for signed AR z,
and `1.32e-7` for AR p. All exact identity gates passed.

These results are strict numerical agreement, not bit identity. They certify
only the registered estimator, instrument, transformation, step, covariance,
and fixture surface. They do not establish instrument validity, identify a
causal model, endorse a specification, or imply universal Stata parity.

## Reproduction

Run the source-bound comparator against the unchanged Stata bundle:

```powershell
python scripts/parity/compare_fd_difference_gmm_to_xtabond2.py `
  --stata-root <path-to-unchanged-stata-matrix-export-root>
```

Run the maintained regression test:

```powershell
python -m pytest -q tests/test_fd_difference_gmm_xtabond2_parity.py
```

The comparator verifies the source CSV hashes before fitting. It fails closed
if invoked from a different checkout, if a fixture or Stata export changes, if
any numerical gate fails, or if an exact identity differs.
