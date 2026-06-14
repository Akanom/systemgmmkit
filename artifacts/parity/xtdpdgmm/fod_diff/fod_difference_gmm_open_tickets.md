# FOD Difference GMM Open Tickets

## Closed in current milestone

- FOD transformed-row construction corrected.
- FOD IV-style transformed-equation instruments aligned with `xtdpdgmm model(fodev)` using current level values.
- Coefficient parity certified for endogenous-x and predetermined-x one-step and two-step FOD Difference GMM.
- FOD Difference GMM Windmeijer standard errors brought to near parity with maximum absolute SE gap below `1e-2` on the maintained oracle set.

## Follow-up tickets

### 1. Exact Windmeijer SE parity

Current status: near parity.

Target: investigate whether the remaining endogenous-x two-step SE gap can be reduced below `1e-3` without overfitting to the maintained oracle set.

Priority: P2.

### 2. FOD diagnostic parity

Current status: not certified.

Target: align and certify overidentification diagnostics, Hansen/J reporting, and serial-correlation diagnostics against `xtdpdgmm model(fodev)`.

Priority: P2.

### 3. Broader FOD oracle expansion

Current status: maintained oracle covers endogenous-x and predetermined-x collapsed FOD Difference GMM.

Target: add additional FOD specifications covering alternative lag windows, additional IV blocks, unbalanced panels, and optional time dummies.

Priority: P2.
