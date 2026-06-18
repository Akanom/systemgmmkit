from __future__ import annotations

from pathlib import Path

path = Path("src/systemgmmkit/presets.py")
text = path.read_text(encoding="utf-8")

old = '''    global_lag_value = kwargs.pop("gmm_lags", kwargs.get("default_lag", (2, 2)))
    global_lag = _validate_gmm_lag_window("gmm_lags", global_lag_value)
'''

new = '''    has_explicit_global_lag = "gmm_lags" in kwargs or "default_lag" in kwargs
    global_lag_value = kwargs.pop("gmm_lags", kwargs.get("default_lag", (2, 2)))
    global_lag = _validate_gmm_lag_window("gmm_lags", global_lag_value)
'''

if old not in text:
    raise RuntimeError("Could not find global lag block to patch.")

text = text.replace(old, new, 1)

old = '''        elif "dependent_lag_limits" not in kwargs:
            kwargs["dependent_lag_limits"] = global_lag
'''

new = '''        elif has_explicit_global_lag and "dependent_lag_limits" not in kwargs:
            kwargs["dependent_lag_limits"] = global_lag
'''

if old not in text:
    raise RuntimeError("Could not find dependent lag fallback block to patch.")

text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
print("Patched dependent lag backward compatibility.")
