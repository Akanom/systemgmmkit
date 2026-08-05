# Artifact 24: Frozen Legacy Dynamic-GMM Snapshot

## Status

FROZEN_LEGACY_SNAPSHOT

## Source

Copied from the maintained systemgmmkit repository after commit:

01d0625 Update System GMM xtabond2 parity certificate

## Interpretation

This directory is a frozen single-spec snapshot copied from an earlier commit. Its
historical exclusion of the constant is not the current certification contract.
It is retained for submission provenance only and is not an independent authority.

The current authority is the six-spec registry and unified certificate under
`artifacts/parity/xtabond2/`. That certificate requires the complete expected
parameter set, including the constant where specified, and reports diagnostic
agreement separately from instrument validity.

Artifact 22 is retained only as an auxiliary controlled Stata comparison:
- Difference GMM: PASS_TOLERANT_AUXILIARY
- System GMM: PASS_NUMERIC
