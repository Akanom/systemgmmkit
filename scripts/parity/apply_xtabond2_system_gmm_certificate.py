from __future__ import annotations

from pathlib import Path

import pandas as pd

if __package__:
    from .system_gmm_certification_registry import REPOSITORY_ROOT, load_certification_registry
else:
    from system_gmm_certification_registry import REPOSITORY_ROOT, load_certification_registry

XTABOND2_ROOT = Path("artifacts/parity/xtabond2")
UNIFIED_CERTIFICATE = XTABOND2_ROOT / "diagnostic_parity_certificate.csv"
LEGACY_CERTIFICATE_CSV = XTABOND2_ROOT / "xtabond2_system_gmm_parity_certificate.csv"
LEGACY_CERTIFICATE_MD = XTABOND2_ROOT / "xtabond2_system_gmm_parity_certificate.md"
LEGACY_BASELINE_SPEC = "system_gmm_baseline_controls"


def build_legacy_projection() -> pd.DataFrame:
    registry = load_certification_registry()
    if LEGACY_BASELINE_SPEC not in registry.specifications:
        raise ValueError(
            f"Legacy baseline is absent from the certification registry: {LEGACY_BASELINE_SPEC}"
        )

    source_path = REPOSITORY_ROOT / UNIFIED_CERTIFICATE
    source = pd.read_csv(source_path)
    projection = source.loc[source["spec"].eq(LEGACY_BASELINE_SPEC)].copy()
    if len(projection) != 1:
        raise ValueError(
            f"Expected one {LEGACY_BASELINE_SPEC!r} row in {source_path}, found {len(projection)}"
        )
    projection.insert(0, "compatibility_source", UNIFIED_CERTIFICATE.as_posix())
    return projection


def main() -> None:
    projection = build_legacy_projection()
    csv_path = REPOSITORY_ROOT / LEGACY_CERTIFICATE_CSV
    md_path = REPOSITORY_ROOT / LEGACY_CERTIFICATE_MD
    projection.to_csv(csv_path, index=False)
    md_path.write_text(
        "# xtabond2 System GMM Legacy Compatibility Projection\n\n"
        "This file has no independent certification decision logic. Its single baseline row is "
        "projected verbatim from the unified certificate named in `compatibility_source`; the "
        "central registry defines the maintained specification and gates.\n\n"
        + projection.to_markdown(index=False)
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
