## systemgmmkit 0.5.1

This release updates the public PyPI package after native System GMM parity certification.

### Highlights

- Certifies native System GMM baseline as `PASS_STRICT_XTABOND2_SYSTEM_GMM_BASELINE`.
- Adds verified parity against Stata `xtabond2` for:
  - sample size;
  - instrument count;
  - coefficient estimates;
  - Windmeijer-corrected two-step standard errors;
  - Hansen p-values;
  - signed AR(1)/AR(2) diagnostics and p-values.
- Adds multi-spec AR diagnostic parity validation for:
  - baseline controls;
  - no-controls;
  - three-way interaction;
  - decomposition controls.
- Updates reviewer-facing parity artifacts and README documentation.

### Scope note

This is a benchmark-specific parity certification, not a universal claim of Stata identity across every possible `xtabond2` configuration.

## Installation

    python -m pip install systemgmmkit==0.5.0
    