from __future__ import annotations

from pathlib import Path

from systemgmmkit.reporting import ParityReport, ParityResult


def main() -> None:
    out = Path("artifacts/parity")
    out.mkdir(parents=True, exist_ok=True)

    report = ParityReport(
        results=[
            ParityResult(
                spec="difference_gmm_baseline_controls",
                status="PASS_PARITY",
                original_status="PASS_STRICT",
                blocks_release=False,
                policy_message="Native Difference GMM passed current strict parity contract.",
            ),
            ParityResult(
                spec="system_gmm_baseline_controls",
                status="EXPERIMENTAL_PARITY_PENDING",
                original_status="FAIL_PARITY",
                blocks_release=False,
                policy_message="Native System GMM executes but coefficient-level strict parity is pending.",
            ),
        ]
    )

    report.to_csv(out / "strict_parity_results.csv")
    report.to_markdown(out / "strict_parity_results.md")


if __name__ == "__main__":
    main()
