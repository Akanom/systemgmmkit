from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from .presets import build_dynamic_panel_gmm_spec
from .reporting import model_card_markdown
from .validation import validate_panel


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="systemgmmkit",
        description="Generic panel-data workflow helper for FE and Difference/System GMM models.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate a panel dataset")
    validate.add_argument("csv", type=Path)
    validate.add_argument("--entity", required=True)
    validate.add_argument("--time", required=True)
    validate.add_argument("--vars", nargs="*", default=[])
    validate.add_argument("--json", action="store_true")

    spec = sub.add_parser("spec", help="Print a generic dynamic-panel GMM model card")
    spec.add_argument("--dependent", required=True)
    spec.add_argument("--regressors", nargs="+", required=True)
    spec.add_argument("--controls", nargs="*", default=[])
    spec.add_argument("--interactions", nargs="*", default=[])
    spec.add_argument("--endogenous", nargs="*", default=[])
    spec.add_argument("--predetermined", nargs="*", default=[])
    spec.add_argument("--exogenous", nargs="*", default=[])
    spec.add_argument(
        "--difference", action="store_true", help="Use Difference GMM instead of System GMM"
    )
    spec.add_argument("--no-collapse", action="store_true")
    spec.add_argument("--no-time-dummies", action="store_true")
    spec.add_argument("--name", default="dynamic_panel_gmm")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        df = pd.read_csv(args.csv)
        report = validate_panel(df, entity=args.entity, time=args.time, variables=args.vars)
        print(json.dumps(report.to_dict(), indent=2))
        return 0

    if args.command == "spec":
        model_spec = build_dynamic_panel_gmm_spec(
            name=args.name,
            dependent=args.dependent,
            regressors=args.regressors,
            controls=args.controls,
            interactions=args.interactions,
            endogenous=args.endogenous,
            predetermined=args.predetermined,
            exogenous=args.exogenous,
            system=not args.difference,
            collapse=not args.no_collapse,
            time_dummies=not args.no_time_dummies,
        )
        print(model_card_markdown(model_spec))
        return 0

    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
