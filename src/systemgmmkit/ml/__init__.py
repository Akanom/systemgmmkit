"""
ML-style workflow tools for systemgmmkit.

This layer is intentionally additive:
- no estimator internals are changed
- accepted econometric models are reused
- tools operate through duck-typed result adapters
"""

from .adapter import ResultAdapter, adapt_result
from .backtest import backtest_forecast
from .compare import compare_models
from .easy import (
    ForecastSummary,
    MLWorkflowSummary,
    PostEstimationSummary,
    quick_forecast,
    quick_ml,
    quick_postestimation,
)
from .forecast import forecast
from .gmm_search import (
    DynamicGMMHybridSearch,
    GMMGridSearch,
    GMMRankingWeights,
    GMMSearchResult,
    GMMValidityRules,
    auto_dynamic_gmm,
    dynamic_gmm_candidate_grid,
)
from .metrics import regression_metrics
from .prediction import fitted_values, predict, residuals
from .split import PanelTimeSeriesSplit, panel_train_test_split
from .validation import cross_validate_panel

__all__ = [
    "ResultAdapter",
    "adapt_result",
    "regression_metrics",
    "predict",
    "fitted_values",
    "residuals",
    "panel_train_test_split",
    "PanelTimeSeriesSplit",
    "cross_validate_panel",
    "PostEstimationSummary",
    "ForecastSummary",
    "MLWorkflowSummary",
    "quick_postestimation",
    "quick_forecast",
    "quick_ml",
    "GMMGridSearch",
    "GMMSearchResult",
    "GMMValidityRules",
    "GMMRankingWeights",
    "DynamicGMMHybridSearch",
    "auto_dynamic_gmm",
    "dynamic_gmm_candidate_grid",
    "compare_models",
    "forecast",
    "backtest_forecast",
]
