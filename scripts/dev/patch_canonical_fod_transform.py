import re
from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

# ---------------------------------------------------------------------
# Replace _fod_at block.
# ---------------------------------------------------------------------

fod_pattern = re.compile(
    r"def _fod_at\(series: pd\.Series, pos: int\) -> float \| None:\n"
    r".*?\n"
    r"(?=def _transform_at\(series: pd\.Series, pos: int, transformation: str\) -> float \| None:)",
    re.DOTALL,
)

fod_new = '''def _fod_at(series: pd.Series, pos: int) -> float | None:
    """Forward orthogonal deviation at positional index ``pos``.

    For observation t, with m usable future observations, the canonical
    Arellano-Bover forward-orthogonal transformation is:

        sqrt(m / (m + 1)) * (v_t - mean(v_{t+1}, ..., v_T))

    The final observation has no future observations and is therefore unusable.
    """

    import math

    n = len(series)
    if pos < 0 or pos >= n - 1:
        return None

    now = _safe_get(series, pos)
    if now is None:
        return None

    future_values: list[float] = []
    for j in range(pos + 1, n):
        val = _safe_get(series, j)
        if val is not None:
            future_values.append(float(val))

    m = len(future_values)
    if m <= 0:
        return None

    future_mean = sum(future_values) / float(m)
    scale = math.sqrt(float(m) / float(m + 1))

    return scale * (float(now) - future_mean)


'''

text, n_fod = fod_pattern.subn(fod_new, text, count=1)
if n_fod != 1:
    raise RuntimeError(f"Expected to replace exactly one _fod_at block; replaced {n_fod}.")

# ---------------------------------------------------------------------
# Replace _transformed_error_terms block.
# ---------------------------------------------------------------------

err_pattern = re.compile(
    r"def _transformed_error_terms\(\n"
    r".*?\n"
    r"(?=def _build_native_matrices\()",
    re.DOTALL,
)

err_new = '''def _transformed_error_terms(
    *,
    group: pd.DataFrame,
    pos: int,
    time: str,
    transformation: str,
) -> dict[object, float]:
    """Return underlying level-error weights for a transformed equation row.

    FD:
        Δe_t = e_t - e_{t-1}

    FOD:
        sqrt(m/(m+1)) * (e_t - mean(e_{t+1}, ..., e_T))

    where m is the number of usable future observations.
    """

    import math

    transformation_normalized = str(transformation).strip().lower()
    current_time = group[time].iloc[pos]

    if transformation_normalized in {"fd", "first_difference", "difference"}:
        if pos <= 0:
            return {}
        previous_time = group[time].iloc[pos - 1]
        return {
            current_time: 1.0,
            previous_time: -1.0,
        }

    if transformation_normalized in {"fod", "orthogonal", "orthogonal_deviations", "forward_orthogonal_deviations"}:
        n = len(group)
        if pos < 0 or pos >= n - 1:
            return {}

        future_times = [group[time].iloc[j] for j in range(pos + 1, n)]
        m = len(future_times)
        if m <= 0:
            return {}

        scale = math.sqrt(float(m) / float(m + 1))
        future_weight = -scale / float(m)

        weights: dict[object, float] = {current_time: scale}
        for t_future in future_times:
            weights[t_future] = weights.get(t_future, 0.0) + future_weight

        return weights

    raise ValueError(
        "transformation must be one of 'fd', 'difference', 'fod', or 'orthogonal'."
    )


'''

text, n_err = err_pattern.subn(err_new, text, count=1)
if n_err != 1:
    raise RuntimeError(
        f"Expected to replace exactly one _transformed_error_terms block; replaced {n_err}."
    )

path.write_text(text, encoding="utf-8")

print("Patched canonical FOD transformation and transformed-error metadata.")
