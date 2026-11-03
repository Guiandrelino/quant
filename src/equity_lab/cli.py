"""Command-line entry point; offline synthetic demo is the safe default."""

import argparse

from equity_lab.backtest import BacktestConfig
from equity_lab.data import load_csv, synthetic_data
from equity_lab.research import ResearchConfig, run_research


def main() -> None:
    parser = argparse.ArgumentParser(description="Brazilian Equity Lab — auditable factor research")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ["demo", "run"]:
        p = sub.add_parser(command)
        p.add_argument("--output", default=f"outputs/{command}")
        p.add_argument("--holdout-start", default="2023-01-01")
        p.add_argument("--seed", type=int, default=42)
        p.add_argument("--cost-bps", type=float, default=10)
        if command == "run":
            p.add_argument("--data", required=True)
    args = parser.parse_args()
    data = synthetic_data(args.seed) if args.command == "demo" else load_csv(args.data)
    manifest = run_research(
        data,
        args.output,
        ResearchConfig(holdout_start=args.holdout_start, seed=args.seed),
        BacktestConfig(commission_bps=args.cost_bps, slippage_bps=0),
    )
    print(f"Dataset: {manifest['dataset']}")
    print(f"Report: {args.output}/report.html")
    print(f"Data SHA-256: {manifest['data_sha256']}")


if __name__ == "__main__":
    main()
