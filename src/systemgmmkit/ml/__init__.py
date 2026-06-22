"""
ML-style workflow tools for systemgmmkit.

This layer is intentionally additive:
- no estimator internals are changed
- accepted econometric models are reused
- tools operate through duck-typed result adapters
"""

from .adapter import ResultAdapter, adapt_result
from .metrics import regression_metrics
from .prediction import predict, fitted_values, residuals
from .split import panel_train_test_split, PanelTimeSeriesSplit
from .validation import cross_validate_panel
from .gmm_search import GMMGridSearch, GMMSearchResult

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
    "GMMGridSearch",
    "GMMSearchResult",
]
