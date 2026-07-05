# Artifact 24: Maintained Dynamic-GMM Parity Evidence

## Status

PASS_XTABOND2_PARITY

## Source

Copied from the maintained systemgmmkit repository after commit:

01d0625 Update System GMM xtabond2 parity certificate

## Interpretation

The maintained System GMM benchmark passes xtabond2 parity for compared structural coefficients and Windmeijer-corrected standard errors within numerical tolerance. Native-only constant terms are reported separately where applicable.

This is the authoritative parity evidence for the JOSS submission.

Artifact 22 is retained only as an auxiliary controlled Stata comparison:
- Difference GMM: PASS_TOLERANT_AUXILIARY
- System GMM: PASS_NUMERIC
