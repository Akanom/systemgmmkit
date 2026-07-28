# Dependency review

Review date: 2026-07-28

Owner: Maintainer

Reassessment: every dependency change and at least quarterly

## Dependency boundaries

| Package | Purpose | Installed scope |
|---|---|---|
| NumPy | Numerical arrays and linear algebra | Mandatory runtime; `>=1.23,<3` |
| pandas | Panel-data indexing and labelled results | Mandatory runtime; `>=1.5,<4` |
| SciPy | Optimization, distributions, and matrix routines | Mandatory runtime; `>=1.9,<2` |
| pydynpd | External GMM backend and parity comparator | Optional `pydynpd`/`all` and test only |
| linearmodels | FE/RE/IV backend and comparator | Optional `fe`/`all` and test only |
| Matplotlib | Post-estimation graphics | Optional `plots`/`all` and test only |
| Ruff and mypy | Static development checks | Development/test only |
| build | PEP 517 distribution construction | Release only |

The core import has no network or shell requirement. Optional backends are
bounded, independently installable, and excluded from core dependencies.

## Scanner findings reviewed

The scanner screenshots identify capabilities, not exploitability in this
package. The dashboard did not expose its downloaded-artifact SHA-256, so no
version-level suppression is authorized. The following hashes are the official
PyPI metadata values and must be matched to the scanner artifact before any
finding can be closed as artifact-identical.

| Finding | Exact artifact | Official SHA-256 | Disposition and containment |
|---|---|---|---|
| Opaque/obfuscated archive | `numpy-2.5.1.tar.gz` | `a48a113e6afea91f5608793bafa7ef2ad481fefbda87ec5069f483de61cb9fa3` | `MONITOR`. Nested archives are Meson test fixtures; do not suppress until the scanner hash matches. Prefer official wheels. |
| Potential `f2py` `eval` path | `numpy-2.5.1-cp312-cp312-macosx_10_13_x86_64.whl` | `2c889b56fe48b1018f764b0eec8df59ab654e9148aa91faa12596043500de277` | `REVIEWED`. F2PY is a NumPy build/interface subsystem and is not called by systemgmmkit. Treat attacker-writable F2PY configuration as untrusted and do not execute it. |
| Shell access | `build-1.5.0-py3-none-any.whl` | `13f3eecb844759ab66efec90ca17639bbf14dc06cb2fdf37a9010322d9c50a6f` | `EXPECTED, RELEASE-ONLY`. A build frontend must invoke isolated build backends. It is absent from runtime requirements and runs only in the protected release workflow. |
| Low-popularity package | `pydynpd-0.2.2-py3-none-any.whl` | `b3aef5847ea86d7d9b2d1b8e62df0925a119ad81d52d760d8ed154ca92e8bcb8` | `REVIEWED, OPTIONAL`. Popularity is not a vulnerability signal. The package remains bounded and isolated to opt-in backend/parity use; native GMM remains available. |
| Native code | `linearmodels-7.0-cp310-cp310-macosx_10_9_x86_64.whl` | `ca7a338c7108d6ddf880396e3c391207fa189f639e508282c05926cd5c67c963` | `EXPECTED, OPTIONAL`. The compiled panel utility is part of the declared FE/IV backend, not the core import. Use only official hashed artifacts. |
| Install scripts | `ruff-0.16.0.tar.gz` | `e460aafd5495ec89efaa6ced2e4a9a581116451e1c88b9d37ef497e0f8e93982` | `EXPECTED, DEVELOPMENT-ONLY`. Ruff is a Rust application; the flagged `build.rs` files and formatter fixture are source-build content. Prefer the official platform wheel and never install it at runtime. |
| AI-detected pickle/daemon risk | `mypy-2.3.0-cp310-cp310-macosx_10_9_x86_64.whl` | `1fa8d916ac3b705af733c4c1e6c9ebe38fd0d52beb15b105c3e8355b55e6ecdc` | `MONITOR, DEVELOPMENT-ONLY`. The flagged path belongs to local `dmypy` daemon startup. CI does not invoke `dmypy`; untrusted `--options-data` must never be accepted. Ordinary package runtime does not import mypy. |
| Network access | `matplotlib-3.11.1-cp311-cp311-macosx_10_12_x86_64.whl` | `b7cf158e7add54a8d51ac9b5a84abd6d4e13ed4951b4f25f1c5139f41c2addb2` | `EXPECTED, OPTIONAL`. Matplotlib is a plotting extra. systemgmmkit plotting does not fetch remote data; validation data downloads remain separate, hash-verified scripts. |

The permissive development bounds can resolve newer versions than the currently
committed hash-locked requirement graphs (for example NumPy 2.5.1 versus the
current 2.4.6 lock). CI and releases install the repository's hashed requirement
files; a dependency update must regenerate and review those files separately.

## Controls

- Reusable governance workflows run dependency audit, secret scan, distribution
  inspection, and hashed-lock verification.
- Release tooling is separated from runtime dependencies and protected by the
  release environment.
- Source distributions and native wheels must match official PyPI hashes; prefer
  wheels where a source build is unnecessary.
- No scanner control is disabled and no finding is recorded as an accepted risk.
- Package import and estimator execution require neither shell nor network access.
