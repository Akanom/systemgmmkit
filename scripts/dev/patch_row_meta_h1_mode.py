from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

old = '''def _native_h1_from_row_meta(
    row_meta_i: list[dict[str, object]],
) -> np.ndarray:
    """Build entity-specific first-step H1 from stacked error metadata.

    Each row stores the underlying error composition:

        diff row:  error_terms = {t: +1, t-1: -1}
        level row: error_terms = {t: +1}

    Assuming serially uncorrelated level errors with unit variance,
    Cov(row_a, row_b) is the dot product of their error-term coefficient maps.

    This is general for balanced and unbalanced panels and does not assume a
    fixed D/L block width.
    """
    n = len(row_meta_i)
    h = np.zeros((n, n), dtype=float)

    maps: list[dict[object, float]] = []
    for meta in row_meta_i:
        raw_terms = meta.get("error_terms", {})
        if not isinstance(raw_terms, dict):
            raw_terms = {}
        maps.append({k: float(v) for k, v in raw_terms.items()})

    for i in range(n):
        terms_i = maps[i]
        for j in range(i, n):
            terms_j = maps[j]

            if len(terms_i) <= len(terms_j):
                val = sum(coef * terms_j.get(t, 0.0) for t, coef in terms_i.items())
            else:
                val = sum(coef * terms_i.get(t, 0.0) for t, coef in terms_j.items())

            h[i, j] = val
            h[j, i] = val

    return h
'''

new = '''def _native_h1_from_row_meta(
    row_meta_i: list[dict[str, object]],
) -> np.ndarray:
    """Build entity-specific first-step H1 from stacked error metadata.

    Diagnostic modes:
        SYSTEMGMMKIT_ROW_META_H1_MODE=dot_product  -> current metadata covariance
        SYSTEMGMMKIT_ROW_META_H1_MODE=identity     -> identity covariance

    The identity mode is used to test FOD / orthogonal System-GMM parity, where
    properly scaled transformed errors should have identity covariance.
    """
    import os as _row_meta_h1_os

    n = len(row_meta_i)

    mode = (
        _row_meta_h1_os.getenv("SYSTEMGMMKIT_ROW_META_H1_MODE", "dot_product")
        .strip()
        .lower()
    )

    if mode in {"identity", "eye"}:
        return np.eye(n, dtype=float)

    if mode not in {"dot_product", "metadata", "default", ""}:
        raise ValueError(
            "Unsupported SYSTEMGMMKIT_ROW_META_H1_MODE="
            f"{mode!r}. Use dot_product or identity."
        )

    h = np.zeros((n, n), dtype=float)

    maps: list[dict[object, float]] = []
    for meta in row_meta_i:
        raw_terms = meta.get("error_terms", {})
        if not isinstance(raw_terms, dict):
            raw_terms = {}
        maps.append({k: float(v) for k, v in raw_terms.items()})

    for i in range(n):
        terms_i = maps[i]
        for j in range(i, n):
            terms_j = maps[j]

            if len(terms_i) <= len(terms_j):
                val = sum(coef * terms_j.get(t, 0.0) for t, coef in terms_i.items())
            else:
                val = sum(coef * terms_i.get(t, 0.0) for t, coef in terms_j.items())

            h[i, j] = val
            h[j, i] = val

    return h
'''

if old not in text:
    raise RuntimeError("Could not find _native_h1_from_row_meta block.")

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")

print("Patched row-meta H1 diagnostic mode.")
