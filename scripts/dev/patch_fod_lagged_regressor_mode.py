import re
from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

pattern = re.compile(
    r"def _transformed_regressor_at\(\n"
    r".*?\n"
    r"(?=def _lagged_level_instrument_at)",
    re.DOTALL,
)

replacement = '''def _transformed_regressor_at(
    group: pd.DataFrame,
    regressor: str,
    pos: int,
    transformation: str,
) -> float | None:
    """Return the transformed-equation value for a structural regressor.

    Diagnostic FOD lagged-regressor modes are controlled by:

        SYSTEMGMMKIT_FOD_LAGGED_REGRESSOR_MODE=transform_lagged
            Current/default: A(L^k y)

        SYSTEMGMMKIT_FOD_LAGGED_REGRESSOR_MODE=lag_transformed
            Alternative: L^k(Ay)

    FD is left unchanged.
    """

    import os

    transformation_normalized = str(transformation).strip().lower()
    parsed = _parse_lagged_regressor(regressor)

    if parsed is None:
        return _transform_at(group[regressor], pos, transformation)

    lag, base = parsed
    base_series = group[base]

    if transformation_normalized in {
        "fod",
        "orthogonal",
        "orthogonal_deviations",
        "forward_orthogonal_deviations",
    }:
        mode = (
            os.getenv("SYSTEMGMMKIT_FOD_LAGGED_REGRESSOR_MODE", "transform_lagged")
            .strip()
            .lower()
        )

        if mode in {"transform_lagged", "current", "default", ""}:
            lagged = _lagged_series(base_series, lag)
            return _transform_at(lagged, pos, transformation)

        if mode in {"lag_transformed", "lag_of_transformed", "alternative"}:
            transformed_base_values = []
            for j in range(len(base_series)):
                transformed_base_values.append(_transform_at(base_series, j, transformation))
            transformed_base = pd.Series(transformed_base_values, index=base_series.index)
            return _safe_get(transformed_base, pos - lag)

        raise ValueError(
            "Unsupported SYSTEMGMMKIT_FOD_LAGGED_REGRESSOR_MODE="
            f"{mode!r}. Use transform_lagged or lag_transformed."
        )

    lagged = _lagged_series(base_series, lag)
    return _transform_at(lagged, pos, transformation)


'''

text, n = pattern.subn(replacement, text, count=1)

if n != 1:
    raise RuntimeError(f"Expected to replace one _transformed_regressor_at block; replaced {n}.")

path.write_text(text, encoding="utf-8")
print("Patched FOD lagged-regressor diagnostic mode.")
