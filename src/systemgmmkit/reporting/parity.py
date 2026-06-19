from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_PARITY_COLUMNS = [
    "spec",
    "native_nobs",
    "native_n_instruments",
    "pydynpd_nobs",
    "pydynpd_n_groups",
    "pydynpd_n_instruments",
    "hansen_p",
    "ar1_p",
    "ar2_p",
    "status",
    "original_status",
    "blocks_release",
    "policy_message",
    "same_instrument_count",
    "max_abs_coef_diff",
    "mean_abs_coef_diff",
    "sign_match_rate",
]


@dataclass(frozen=True)
class ParityResult:
    spec: str
    native_nobs: int | None = None
    native_n_instruments: int | None = None
    pydynpd_nobs: int | None = None
    pydynpd_n_groups: int | None = None
    pydynpd_n_instruments: int | None = None
    hansen_p: float | None = None
    ar1_p: float | None = None
    ar2_p: float | None = None
    status: str = "UNKNOWN"
    original_status: str = "UNKNOWN"
    blocks_release: bool = True
    policy_message: str = ""
    same_instrument_count: bool | None = None
    max_abs_coef_diff: float | None = None
    mean_abs_coef_diff: float | None = None
    sign_match_rate: float | None = None


@dataclass
class ParityReport:
    package: str = "systemgmmkit"
    suite: str = "Panel Econometrics Conformance Suite"
    results: list[ParityResult | dict[str, Any]] = field(default_factory=list)

    def to_dataframe(self) -> pd.DataFrame:
        rows = []

        for result in self.results:
            if isinstance(result, ParityResult):
                rows.append(asdict(result))
            else:
                rows.append(dict(result))

        df = pd.DataFrame(rows)

        for col in REQUIRED_PARITY_COLUMNS:
            if col not in df.columns:
                df[col] = None

        return df[REQUIRED_PARITY_COLUMNS]

    def to_csv(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.to_dataframe().to_csv(path, index=False)
        return path

    def to_markdown(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        df = self.to_dataframe()
        text = f"# {self.suite}\n\n"
        text += f"Package: `{self.package}`\n\n"
        text += df.to_markdown(index=False)

        path.write_text(text, encoding="utf-8")
        return path


def classify_parity_result(
    spec: str,
    native_nobs: int | None,
    pydynpd_nobs: int | None,
    native_n_instruments: int | None,
    pydynpd_n_instruments: int | None,
    max_abs_coef_diff: float | None,
    tolerance: float = 1e-5,
    system_gmm_native: bool = False,
) -> ParityResult:
    same_nobs = native_nobs == pydynpd_nobs
    same_instr = native_n_instruments == pydynpd_n_instruments

    if (
        same_nobs
        and same_instr
        and max_abs_coef_diff is not None
        and max_abs_coef_diff <= tolerance
    ):
        status = "PASS_PARITY"
        original_status = "PASS_STRICT"
        blocks_release = False
        message = "Native estimator passed strict parity."
    elif system_gmm_native:
        status = "EXPERIMENTAL_PARITY_PENDING"
        original_status = "FAIL_PARITY"
        blocks_release = False
        message = (
            "Native System GMM executed but strict coefficient-level parity is not certified yet."
        )
    else:
        status = "FAIL_PARITY"
        original_status = "FAIL_PARITY"
        blocks_release = True
        message = "Estimator failed strict parity requirements."

    return ParityResult(
        spec=spec,
        native_nobs=native_nobs,
        native_n_instruments=native_n_instruments,
        pydynpd_nobs=pydynpd_nobs,
        pydynpd_n_instruments=pydynpd_n_instruments,
        status=status,
        original_status=original_status,
        blocks_release=blocks_release,
        policy_message=message,
        same_instrument_count=same_instr,
        max_abs_coef_diff=max_abs_coef_diff,
    )
