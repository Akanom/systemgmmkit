# API stability policy

`systemgmmkit` 1.0.0 marks the documented public API as stable.

## Compatibility commitment

- Public names documented in the README or exported through `systemgmmkit.__all__`
  follow semantic versioning.
- Result attributes and table columns documented as public will not be removed or
  incompatibly redefined in a minor or patch release.
- Where practical, a deprecated interface remains available for at least one
  minor release and emits actionable migration guidance before removal in a
  subsequent major release.
- Bug fixes may change numerically incorrect behavior in patch releases. Such
  changes require regression tests, release-note disclosure, and updated parity
  evidence when a certified path is affected.
- Private names, explicitly experimental interfaces, and generated artifact
  internals are outside this compatibility guarantee.

## Econometric claim boundary

Stable API status is not a claim that every user specification is identified,
diagnostically valid, or identical to another package. Cross-software claims
remain limited to the registered fixtures, comparator versions, tolerances, and
artifacts recorded by the certification workflow.

## Supported Python versions

The release metadata and CI matrix define supported Python versions. Dropping a
supported Python version is announced in advance and occurs only in a minor or
major release.
