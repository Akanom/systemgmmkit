from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

import pandas as pd

from .metrics import regression_metrics
from .prediction import predict
from .split import panel_train_test_split


@dataclass(frozen=True)
class GMMSearchResult:
    results: pd.DataFrame
    best_result: Any | None
    best_spec: dict[str, Any] | None


class GMMGridSearch:
    """
    Lightweight GMM specification search.

    This does NOT implement new GMM estimation. It repeatedly calls the existing
    validated estimator builder/runner supplied by the user.
    """

    def __init__(
        self,
        *,
        build_spec: Callable[..., Any],
        run_model: Callable[..., Any],
        param_grid: Iterable[dict[str, Any]],
        y: str,
        entity: str,
        time: str,
        selection_metric: str = "rmse",
        minimize: bool = True,
        test_size: float | int = 0.2,
        diagnostic_rules: dict[str, tuple[str, float]] | None = None,
    ) -> None:
        self.build_spec = build_spec
        self.run_model = run_model
        self.param_grid = list(param_grid)
        self.y = y
        self.entity = entity
        self.time = time
        self.selection_metric = selection_metric
        self.minimize = minimize
        self.test_size = test_size
        self.diagnostic_rules = diagnostic_rules or {}

    def _passes_diagnostics(self, diagnostics: dict[str, Any]) -> bool:
        for key, (op, threshold) in self.diagnostic_rules.items():
            if key not in diagnostics:
                return False

            value = float(diagnostics[key])

            if op == ">" and not value > threshold:
                return False
            if op == ">=" and not value >= threshold:
                return False
            if op == "<" and not value < threshold:
                return False
            if op == "<=" and not value <= threshold:
                return False
            if op == "==" and not value == threshold:
                return False

        return True

    def fit(self, data: pd.DataFrame) -> GMMSearchResult:
        train, test = panel_train_test_split(
            data,
            time=self.time,
            test_size=self.test_size,
        )

        rows: list[dict[str, Any]] = []
        stored: list[tuple[dict[str, Any], Any]] = []

        for i, params in enumerate(self.param_grid, start=1):
            row: dict[str, Any] = {"spec_id": i, **params}

            try:
                spec = self.build_spec(**params)
                result = self.run_model(
                    spec,
                    train,
                    entity=self.entity,
                    time=self.time,
                )

                y_pred = predict(result, test, strict=False)
                row.update(regression_metrics(test[self.y], y_pred))

                diagnostics = getattr(result, "diagnostics", {})
                diagnostics = diagnostics() if callable(diagnostics) else diagnostics
                diagnostics = dict(diagnostics or {})

                for k, v in diagnostics.items():
                    if isinstance(v, (int, float)):
                        row[f"diag_{k}"] = float(v)

                row["passes_diagnostics"] = self._passes_diagnostics(diagnostics)
                row["error"] = ""
                stored.append((params, result))

            except Exception as exc:
                row["passes_diagnostics"] = False
                row["error"] = f"{type(exc).__name__}: {exc}"

            rows.append(row)

        table = pd.DataFrame(rows)

        candidates = table.loc[
            (table["error"].fillna("") == "") &
            (table["passes_diagnostics"].astype(bool))
        ].copy()

        if candidates.empty or self.selection_metric not in candidates.columns:
            return GMMSearchResult(
                results=table,
                best_result=None,
                best_spec=None,
            )

        candidates = candidates.sort_values(
            self.selection_metric,
            ascending=self.minimize,
        )

        best_id = int(candidates.iloc[0]["spec_id"])
        best_spec, best_result = stored[best_id - 1]

        return GMMSearchResult(
            results=table,
            best_result=best_result,
            best_spec=best_spec,
        )
