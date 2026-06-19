import re
from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

fod_pattern = re.compile(
    r"def _fod_at\(series: pd\.Series, pos: int\) -> float \| None:\n"
    r".*?\n"
    r"(?=def _transform_at\(series: pd\.Series, pos: int, transformation: str\) -> float \| None:)",
    re.DOTALL,
)

fod_new = '''def _fod_at(series: pd.Series, pos: int) -> float | None:
    """Forward orthogonal deviation at positional index ``pos``.

    Diagnostic scaling modes are controlled by SYSTEMGMMKIT_FOD_SCALE_MODE:

        canonical: sqrt(m / (m + 1)) * deviation
        unscaled:  deviation
        inverse:   sqrt((m + 1) / m) * deviation
        negative:  -canonical

    where m is the number of usable future observations.
    """

    import math
    import os

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

    deviation = float(now) - (sum(future_values) / float(m))

    mode = (
        os.getenv("SYSTEMGMMKIT_FOD_SCALE_MODE", "canonical")
        .strip()
        .lower()
    )

    if mode in {"canonical", "default", ""}:
        scale = math.sqrt(float(m) / float(m + 1))
    elif mode in {"unscaled", "none", "raw"}:
        scale = 1.0
    elif mode in {"inverse", "reverse"}:
        scale = math.sqrt(float(m + 1) / float(m))
    elif mode in {"negative", "neg"}:
        scale = -math.sqrt(float(m) / float(m + 1))
    else:
        raise ValueError(
            "Unsupported SYSTEMGMMKIT_FOD_SCALE_MODE="
            f"{mode!r}. Use canonical, unscaled, inverse, or negative."
        )

    return scale * deviation


'''

text, n_fod = fod_pattern.subn(fod_new, text, count=1)
if n_fod != 1:
    raise RuntimeError(f"Expected to replace exactly one _fod_at block; replaced {n_fod}.")

err_pattern = re.compile(
    r"def _transformed_error_terms\(\n"
    r".*?\n"
    r"(?=def _build_native_matrices\()",
    re.DOTALL,
)

err_new = '''def _transformed_error_terms(
    index: pd.Index,
    pos: int,
    transformation: str,
) -> dict[object, float]:
    """Return underlying level-error weights for a transformed equation row.

    Uses the same FOD scaling mode as _fod_at so first-step weighting remains
    internally consistent during diagnostics.
    """

    import math
    import os

    transformation_normalized = str(transformation).strip().lower()
    n = len(index)

    if transformation_normalized in {"fd", "first_difference", "difference"}:
        if pos <= 0 or pos >= n:
            return {}
        return {
            index[pos]: 1.0,
            index[pos - 1]: -1.0,
        }

    if transformation_normalized in {
        "fod",
        "orthogonal",
        "orthogonal_deviations",
        "forward_orthogonal_deviations",
    }:
        if pos < 0 or pos >= n - 1:
            return {}

        future_positions = list(range(pos + 1, n))
        m = len(future_positions)
        if m <= 0:
            return {}

        mode = (
            os.getenv("SYSTEMGMMKIT_FOD_SCALE_MODE", "canonical")
            .strip()
            .lower()
        )

        if mode in {"canonical", "default", ""}:
            scale = math.sqrt(float(m) / float(m + 1))
        elif mode in {"unscaled", "none", "raw"}:
            scale = 1.0
        elif mode in {"inverse", "reverse"}:
            scale = math.sqrt(float(m + 1) / float(m))
        elif mode in {"negative", "neg"}:
            scale = -math.sqrt(float(m) / float(m + 1))
        else:
            raise ValueError(
                "Unsupported SYSTEMGMMKIT_FOD_SCALE_MODE="
                f"{mode!r}. Use canonical, unscaled, inverse, or negative."
            )

        future_weight = -scale / float(m)

        weights: dict[object, float] = {index[pos]: scale}
        for j in future_positions:
            weights[index[j]] = weights.get(index[j], 0.0) + future_weight

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

print("Patched FOD diagnostic scaling modes.")
