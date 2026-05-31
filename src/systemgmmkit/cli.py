from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from .presets import aid_growth_ta_decomposition_spec, aid_growth_techshare_spec
from .reporting import model_card_markdown
from .validation import validate_panel


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="systemgmmkit", description="Dynamic-panel System GMM workflow helper"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate a panel dataset")
    validate.add_argument("csv", type=Path)
    validate.add_argument("--entity", required=True)
    validate.add_argument("--time", required=True)
    validate.add_argument("--vars", nargs="*", default=[])
    validate.add_argument("--json", action="store_true")

    preset = sub.add_parser("preset", help="Print a preset model card")
    preset.add_argument("name", choices=["techshare", "ta-decomp"])
    preset.add_argument("--no-controls", action="store_true")
    preset.add_argument("--no-three-way", action="store_true")
    preset.add_argument(
        "--difference", action="store_true", help="Use Difference GMM instead of System GMM"
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        df = pd.read_csv(args.csv)
        report = validate_panel(df, entity=args.entity, time=args.time, variables=args.vars)
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(json.dumps(report.to_dict(), indent=2))
        return 0

    if args.command == "preset":
        kwargs = {
            "include_controls": not args.no_controls,
            "include_three_way": not args.no_three_way,
            "system": not args.difference,
        }
        spec = (
            aid_growth_techshare_spec(**kwargs)
            if args.name == "techshare"
            else aid_growth_ta_decomposition_spec(**kwargs)
        )
        print(model_card_markdown(spec))
        return 0

    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
