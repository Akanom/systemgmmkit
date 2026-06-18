from pathlib import Path
import re

path = Path("scripts/dev/compare_realdata_notime_lag_window_native_vs_stata.py")
text = path.read_text(encoding="utf-8")

old = r'''def as_dict(value):
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return {}

def extract_params(result):
    params = as_dict(getattr(result, "params", None) or getattr(result, "coefficients", None) or getattr(result, "coef", None))
    ses = as_dict(getattr(result, "std_errors", None) or getattr(result, "standard_errors", None) or getattr(result, "bse", None))

    if not params:
        raise RuntimeError(f"Could not extract params from {type(result)}")

    return pd.DataFrame([
        {
            "param": str(k),
            "native_coef": v,
            "native_std_err": ses.get(k, math.nan),
        }
        for k, v in params.items()
    ])
'''

new = r'''def first_attr(obj, names):
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return None

def as_dict(value):
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return {}

def extract_params(result):
    params = as_dict(first_attr(result, ["params", "coefficients", "coef"]))
    ses = as_dict(first_attr(result, ["std_errors", "standard_errors", "stderr", "bse"]))

    if not params:
        raise RuntimeError(f"Could not extract params from {type(result)}")

    rows = []
    for k, v in params.items():
        rows.append(
            {
                "param": str(k),
                "native_coef": v,
                "native_std_err": ses.get(k, math.nan),
            }
        )

    return pd.DataFrame(rows)
'''

if old not in text:
    raise RuntimeError("Could not find old extractor block to replace.")

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")

print("Patched pandas-safe native result extractor.")
