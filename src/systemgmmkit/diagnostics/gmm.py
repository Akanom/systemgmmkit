from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GmmDiagnostics:
    ar1_pvalue: float | None = None
    ar2_pvalue: float | None = None
    hansen_pvalue: float | None = None
    sargan_pvalue: float | None = None
    diff_hansen_pvalue: float | None = None
    n_instruments: int | None = None
    n_groups: int | None = None

    @property
    def instrument_pressure_ratio(self) -> float | None:
        if self.n_instruments is None or self.n_groups in (None, 0):
            return None
        return self.n_instruments / self.n_groups

    @property
    def passes_basic_gmm_diagnostics(self) -> bool:
        if self.ar2_pvalue is not None and self.ar2_pvalue < 0.05:
            return False
        if self.hansen_pvalue is not None and self.hansen_pvalue < 0.05:
            return False
        if self.instrument_pressure_ratio is not None and self.instrument_pressure_ratio >= 1.0:
            return False
        return True
