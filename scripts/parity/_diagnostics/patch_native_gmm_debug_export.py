from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

if "SYSTEMGMMKIT_EXPORT_GMM_DEBUG" in text and "native_Z.csv" in text:
    print("Debug export block already exists. No patch needed.")
    raise SystemExit(0)

needle = """    _u_col = residual_vec.reshape(-1, 1)
    _ztu = Z.T @ _u_col
    _j_stat = float((_ztu.T @ W @ _ztu).squeeze())
    _ztu_norm = float(np.linalg.norm(_ztu))
    _w_norm = float(np.linalg.norm(W))

    return NativeGMMResult(
"""

insert = """    _u_col = residual_vec.reshape(-1, 1)
    _ztu = Z.T @ _u_col
    _j_stat = float((_ztu.T @ W @ _ztu).squeeze())
    _ztu_norm = float(np.linalg.norm(_ztu))
    _w_norm = float(np.linalg.norm(W))

    # Optional parity/debug export for xtabond2 internals.
    # Enable with:
    #   $env:SYSTEMGMMKIT_EXPORT_GMM_DEBUG = "1"
    #   $env:SYSTEMGMMKIT_GMM_DEBUG_DIR = "artifacts/parity/xtabond2"
    if __import__("os").environ.get("SYSTEMGMMKIT_EXPORT_GMM_DEBUG") == "1":
        from pathlib import Path as _GmmDebugPath

        debug_dir = _GmmDebugPath(
            __import__("os").environ.get(
                "SYSTEMGMMKIT_GMM_DEBUG_DIR",
                "artifacts/parity/xtabond2",
            )
        )
        debug_dir.mkdir(parents=True, exist_ok=True)

        pd.DataFrame(_ztu, columns=["native_Ze"]).to_csv(
            debug_dir / "native_Ze.csv",
            index=False,
        )

        pd.DataFrame(Z).to_csv(
            debug_dir / "native_Z.csv",
            index=False,
        )

        pd.DataFrame(_u_col, columns=["native_u_stack"]).to_csv(
            debug_dir / "native_u_stack.csv",
            index=False,
        )

        pd.DataFrame(W).to_csv(
            debug_dir / "native_A2.csv",
            index=False,
        )

        pd.DataFrame(X).to_csv(
            debug_dir / "native_X.csv",
            index=False,
        )

        pd.DataFrame(y.reshape(-1, 1), columns=["native_y_stack"]).to_csv(
            debug_dir / "native_y_stack.csv",
            index=False,
        )

        pd.DataFrame(
            {
                "instrument_index": range(1, len(instrument_names) + 1),
                "instrument_name": list(instrument_names),
            }
        ).to_csv(
            debug_dir / "native_instrument_names.csv",
            index=False,
        )

        pd.DataFrame(
            {
                "regressor_index": range(1, len(names) + 1),
                "regressor_name": list(names),
            }
        ).to_csv(
            debug_dir / "native_regressor_names.csv",
            index=False,
        )

        pd.DataFrame(
            [
                {
                    "Z_rows": int(Z.shape[0]),
                    "Z_cols": int(Z.shape[1]),
                    "X_rows": int(X.shape[0]),
                    "X_cols": int(X.shape[1]),
                    "y_rows": int(y.reshape(-1, 1).shape[0]),
                    "u_rows": int(_u_col.shape[0]),
                    "Ze_rows": int(_ztu.shape[0]),
                    "Ze_cols": int(_ztu.shape[1]),
                    "W_rows": int(W.shape[0]),
                    "W_cols": int(W.shape[1]),
                    "native_j_stat": _j_stat,
                    "native_ztu_norm": _ztu_norm,
                    "native_w_norm": _w_norm,
                }
            ]
        ).to_csv(
            debug_dir / "native_debug_shapes.csv",
            index=False,
        )

        try:
            pd.DataFrame(row_meta).to_csv(
                debug_dir / "native_row_meta.csv",
                index=False,
            )
        except Exception:
            pass

    return NativeGMMResult(
"""

if needle not in text:
    raise SystemExit(
        "Could not find the expected return block. "
        "Open native_gmm.py and inspect the _ztu/_j_stat area manually."
    )

text = text.replace(needle, insert, 1)
path.write_text(text, encoding="utf-8")

print("Re-added native GMM debug export block successfully.")
