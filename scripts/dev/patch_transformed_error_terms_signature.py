import re
from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

pattern = re.compile(
    r"def _transformed_error_terms\(\n"
    r".*?\n"
    r"(?=def _build_native_matrices\()",
    re.DOTALL,
)

replacement = '''def _transformed_error_terms(
    index: pd.Index,
    pos: int,
    transformation: str,
) -> dict[object, float]:
    """Return underlying level-error weights for a transformed equation row.

    Backward-compatible call signature used by _build_native_matrices:

        _transformed_error_terms(group.index, pos, spec.transformation)

    FD:
        Δe_t = e_t - e_{t-1}

    FOD:
        sqrt(m/(m+1)) * (e_t - mean(e_{t+1}, ..., e_T))

    Here ``index`` supplies the row keys used inside row_meta. The values do not
    need to be calendar times; they only need to identify the underlying level
    error rows consistently within an entity.
    """

    import math

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

        scale = math.sqrt(float(m) / float(m + 1))
        future_weight = -scale / float(m)

        weights: dict[object, float] = {index[pos]: scale}
        for j in future_positions:
            weights[index[j]] = weights.get(index[j], 0.0) + future_weight

        return weights

    raise ValueError(
        "transformation must be one of 'fd', 'difference', 'fod', or 'orthogonal'."
    )


'''

text, n = pattern.subn(replacement, text, count=1)

if n != 1:
    raise RuntimeError(f"Expected to replace one _transformed_error_terms block; replaced {n}.")

path.write_text(text, encoding="utf-8")
print("Patched _transformed_error_terms with backward-compatible signature.")
