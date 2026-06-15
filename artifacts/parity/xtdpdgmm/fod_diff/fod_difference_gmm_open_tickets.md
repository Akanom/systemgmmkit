# FOD Difference GMM Open Tickets

## Closed in current milestone

- FOD transformed-row construction corrected.
- FOD IV-style transformed-equation instruments aligned with `xtdpdgmm model(fodev)` using current level values.
- Coefficient parity certified for endogenous-x and predetermined-x one-step and two-step FOD Difference GMM.
- FOD Difference GMM Windmeijer standard errors brought to near parity with maximum absolute SE gap below `1e-2` on the maintained oracle set.

## Priority follow-up tickets

### 1. FOD diagnostic parity against `xtdpdgmm`

Current status: open.

Priority: P1.

Target:
- Align and certify overidentification diagnostics where available.
- Confirm whether `xtdpdgmm model(fodev)` reports Hansen/J, Sargan/J, or related overidentification statistics for each maintained FOD Difference GMM specification.
- Align native AR(1) and AR(2) serial-correlation diagnostics with the `xtdpdgmm` oracle or document any convention differences.
- Export diagnostic comparison tables alongside the coefficient and standard-error parity artifacts.

Reason:
Diagnostics are part of reviewer-facing GMM credibility. Coefficient and Windmeijer-SE parity are strong, but GMM results are not fully reviewer-proof until the diagnostic reporting path is explicitly validated.

### 2. Broader FOD oracle expansion

Current status: open.

Priority: P1.

Target:
- Add additional FOD Difference GMM oracle specifications covering:
  - alternative lag windows;
  - additional IV-style blocks;
  - time dummies;
  - unbalanced panels;
  - larger instrument sets;
  - additional endogenous and predetermined timing combinations.
- Confirm that coefficient parity and near Windmeijer-SE parity remain stable beyond the maintained collapsed benchmark.

Reason:
The current oracle is strong but narrow. Broader oracle coverage reduces the risk that parity is benchmark-specific.

## Lower-priority refinement

### 3. Exact Windmeijer SE parity below `1e-3`

Current status: open.

Priority: P2.

Target:
Investigate whether the remaining endogenous-x two-step SE gap can be reduced below `1e-3` without overfitting to the maintained oracle set.

Reason:
Current near-parity is already below `1e-2`, which is release-quality for the maintained oracle. Further tightening is useful but not release-blocking.
