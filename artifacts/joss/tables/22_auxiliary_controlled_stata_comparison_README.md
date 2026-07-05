# Artifact 22: Controlled Stata Comparison

## Status

- Difference GMM: PASS_TOLERANT_AUXILIARY
- System GMM: PASS_NUMERIC

## Sample alignment

The clean Stata rerun uses the same effective samples as systemgmmkit:

- Difference GMM: 840 observations, 120 groups, 5 instruments
- System GMM: 960 observations, 120 groups, 8 instruments

## Final clean comparison

Difference GMM:
- maximum absolute coefficient gap: 0.021803
- maximum absolute standard-error gap: 0.046186

System GMM:
- maximum absolute coefficient gap: 2.49e-08
- maximum absolute standard-error gap: 5.72e-07

## Interpretation

The Artifact 22 controlled panel data is valid and clean. Earlier mismatches were caused by stale Stata exports and sample mismatch. After rerunning Stata on aligned effective samples, System GMM matches systemgmmkit at numerical tolerance.

Difference GMM is not strict numerical parity in this ad hoc comparison, but it falls within the predefined tolerant auxiliary agreement band.

Formal parity claims are based on Artifact 24, the maintained xtabond2 / xtdpdgmm parity certificate from the systemgmmkit repository.
