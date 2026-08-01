from __future__ import annotations

import importlib.util
import subprocess
import sys
import textwrap
from pathlib import Path

import systemgmmkit

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "src" / "systemgmmkit"
LEGACY_ROOT_PLOT_EXPORTS = {
    "HealthMetrics",
    "InstrumentArchitecture",
    "PersistenceAnalytics",
    "PlotTheme",
    "ResultPlotAccessor",
    "SGMVizAccessor",
    "attach_plot_accessor",
    "available_styles",
    "coefficient_plot",
    "conditional_effects_plot",
    "counterfactual_scenario_plot",
    "dynamic_persistence_dashboard_v2",
    "dynamic_persistence_plot",
    "effect_surface_dashboard_v2",
    "effect_surface_plot",
    "export_postestimation_gallery",
    "export_sgm_viz_report",
    "export_sgm_viz_v2_gallery",
    "extract_health_metrics",
    "extract_instrument_architecture",
    "fixed_effects_plot",
    "hansen_ar_diagnostic_plot",
    "health_dashboard",
    "infer_persistence_phi",
    "install_result_plot_accessors",
    "instrument_architecture_dashboard_v2",
    "instrument_architecture_plot",
    "instrument_count_plot",
    "instrument_dashboard",
    "interaction_plot",
    "marginal_effects_plot",
    "margins_prediction_plot",
    "model_comparison_dashboard_v2",
    "model_health_dashboard_v2",
    "model_health_panel",
    "panel_spaghetti_plot",
    "parameter_impact_plot",
    "persistence_dashboard",
    "plot_accessor",
    "plot_all_diagnostics",
    "publication_panel_v2",
    "qq_residual_plot",
    "residual_histogram",
    "residuals_vs_fitted_plot",
    "sgm_plot_bundle",
    "sgm_viz",
    "surface_3d_plot",
}


def test_root_all_is_unique_dependency_free_and_complete() -> None:
    assert len(systemgmmkit.__all__) == 77
    assert len(systemgmmkit.__all__) == len(set(systemgmmkit.__all__))
    assert all(hasattr(systemgmmkit, name) for name in systemgmmkit.__all__)

    assert {
        "DynamicGMMWorkflowResult",
        "difference_gmm",
        "system_gmm",
    } <= set(systemgmmkit.__all__)

    assert LEGACY_ROOT_PLOT_EXPORTS.isdisjoint(systemgmmkit.__all__)


def test_root_does_not_leak_import_helpers() -> None:
    assert not hasattr(systemgmmkit, "contextlib")


def test_legacy_explicit_root_plot_imports_remain_lazy_compatible() -> None:
    from systemgmmkit import postestimation

    for name in LEGACY_ROOT_PLOT_EXPORTS:
        assert getattr(systemgmmkit, name) is getattr(postestimation, name)


def test_wildcard_import_does_not_require_matplotlib() -> None:
    script = textwrap.dedent(
        """
        import importlib.abc
        import sys

        sys.path.insert(0, sys.argv[1])

        class BlockMatplotlib(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname == "matplotlib" or fullname.startswith("matplotlib."):
                    raise ModuleNotFoundError(
                        "blocked for namespace test", name=fullname
                    )
                return None

        sys.meta_path.insert(0, BlockMatplotlib())
        namespace = {}
        exec("from systemgmmkit import *", namespace)

        assert "validate_panel" in namespace
        assert "DynamicGMMWorkflowResult" in namespace
        assert "difference_gmm" in namespace
        assert "system_gmm" in namespace
        assert "coefficient_plot" not in namespace
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", script, str(ROOT / "src")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_package_modules_are_not_shadowed_by_same_named_files() -> None:
    package_directories = {
        path.name for path in PACKAGE_ROOT.iterdir() if (path / "__init__.py").is_file()
    }
    module_files = {path.stem for path in PACKAGE_ROOT.glob("*.py")}

    assert package_directories.isdisjoint(module_files)

    for module_name in ("diagnostics", "postestimation", "reporting"):
        spec = importlib.util.find_spec(f"systemgmmkit.{module_name}")
        assert spec is not None
        assert spec.origin is not None
        assert Path(spec.origin).name == "__init__.py"
