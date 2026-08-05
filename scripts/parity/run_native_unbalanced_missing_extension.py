from __future__ import annotations

import pandas as pd

from systemgmmkit.native_gmm import _build_native_matrices, run_native_dynamic_panel_gmm

if __package__:
    from .system_gmm_unbalanced_missing_extension import build_native_spec, extension_specs
else:
    from system_gmm_unbalanced_missing_extension import build_native_spec, extension_specs


def main() -> None:
    for config in extension_specs():
        data = pd.read_csv(config.fixture)
        spec = build_native_spec(config.spec_id)
        result = run_native_dynamic_panel_gmm(
            spec,
            data,
            entity="id",
            time="t",
            windmeijer=True,
        )
        _, _, _, _, _, _, _, row_meta = _build_native_matrices(
            spec,
            data,
            entity="id",
            time="t",
        )

        params = pd.DataFrame(
            {
                "param": result.params.index,
                "native_coef": result.params.to_numpy(dtype=float),
                "native_std_err": result.std_errors.reindex(result.params.index).to_numpy(
                    dtype=float
                ),
            }
        )
        diagnostics = pd.DataFrame(
            [
                {
                    "spec": config.spec_id,
                    "native_nobs": result.nobs,
                    "native_n_groups": result.n_groups,
                    "native_n_instruments": result.n_instruments,
                    "native_hansen_j_stat": result.hansen_j_stat,
                    "native_hansen_p": result.hansen_p,
                    "native_sargan_j_stat": result.sargan_j_stat,
                    "native_sargan_p": result.sargan_p,
                    "native_overid_df": result.overid_df,
                    "native_ar1_z": result.ar1_z,
                    "native_ar1_p": result.ar1_p,
                    "native_ar2_z": result.ar2_z,
                    "native_ar2_p": result.ar2_p,
                }
            ]
        )
        level_indices = [
            metadata["original_index"] for metadata in row_meta if metadata["equation"] == "level"
        ]
        sample = (
            data.loc[level_indices, ["id", "t"]]
            .drop_duplicates()
            .sort_values(["id", "t"])
            .reset_index(drop=True)
        )

        params.to_csv(config.output_dir / "native_params.csv", index=False)
        diagnostics.to_csv(config.output_dir / "native_diagnostics.csv", index=False)
        sample.to_csv(config.output_dir / "native_sample.csv", index=False)
        print(
            f"{config.spec_id}: N={result.nobs}, groups={result.n_groups}, "
            f"instruments={result.n_instruments}, sample_keys={len(sample)}"
        )


if __name__ == "__main__":
    main()
