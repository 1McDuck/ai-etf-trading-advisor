# scripts/run_backtest.py

# Run the full strategy backtest and save the tearsheet

# Run instructions:
# python scrips/run_backtest.py

# Arguments:
# --start YYYY-MM-DD
# --end YYYY-MM-DD
# --risk    pick: conservative <or> moderate <or> aggressive
# --out   directory to save output (default outputs/)

# Saved files:
# tearsheet.png
# regime_overlay.png
# transition_heatmap.png
# portfolio_returns.png
# weights_history.csv
# stats_summary.txt

import argparse
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "quant_engine"))

from src.backtest.pipeline import run_full_backtest
from src.backtest.tearsheet import build_tearsheet
from src.regimes.visualisation import plot_regime_overlay, plot_transition_heatmap

def main() -> None:
    parser = argparse.ArgumentParser(description="Run AI ETF Advisor Backtest")
    parser.add_argument("--start", default="2000-01-01", help="Start date: YYYY-MM-DD")
    parser.add_argument("--end", default=None, help="End date: YYYY-MM-DD")
    parser.add_argument("--risk", default="moderate", choices=["conservative", "moderate", "aggressive"])
    parser.add_argument("--trees", type=int, default=300, help="Number of Random Forest trees (more trees = longer test)")
    parser.add_argument("--out", default="outputs/", help="Directory to save output (default outputs/)")

    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    result = run_full_backtest(
        start=args.start,
        end=args.end,
        risk_level=args.risk,
        n_estimators=args.trees
    )

    # Tearsheet
    fig_tsheet, _ = build_tearsheet(
        portfolio_returns=result.portfolio_returns,
        benchmark_returns=result.benchmark_returns,
        turnover=result.turnover,
        title=f"AI ETF Advisor Backtest: {args.risk.title()} | {args.start} to {args.end or 'today'}"
    )
    tsheet_path = os.path.join(args.out, "tearsheet.png")
    fig_tsheet.savefig(tsheet_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {tsheet_path}")

    # Regime Charts
    fig_regime = plot_regime_overlay(
        prices=result.regime_result.benchmark_prices,
        labels=result.regime_result.labels,
        label_names=result.regime_result.label_names()
    )
    fig_regime.savefig(os.path.join(args.out, "regime_overlay.png"), dpi=150, bbox_inches="tight")
    
    fig_transm = plot_transition_heatmap(result.regime_result.transition_matrix)
    fig_transm.savefig(os.path.join(args.out, "transition_heatmap.png"), dpi=150, bbox_inches="tight")


    # CSV Export
    import pandas as pd

    returns_df = pd.DataFrame({
        "portfolio": result.portfolio_returns,
        "benchmark": result.benchmark_returns,
        "turnover": result.turnover
    })
    returns_path = os.path.join(args.out, "portfolio_returns.csv")
    returns_df.to_csv(returns_path)
    print(f"Saved: {returns_path}")

    weights_path = os.path.join(args.out, "weights_history.csv")
    result.weights_schedule.to_csv(weights_path)
    print(f"Saved: {weights_path}")

    stats_path = os.path.join(args.out, "stats_summary.txt")
    with open(stats_path, "w", encoding="utf-8") as f:
        f.write(f"Backtest: {args.start} to {args.end or 'today'} | risk={args.risk}")
        f.write("=" * 60 + "\n")
        for k,v in result.stats.items():
            f.write(f"{k:<35} {v}\n")
    print(f"Saved: {stats_path}")

    print(f"All outputs saved to: {os.path.abspath(args.out)}")
    print(f"Open tearsheet.png to see performance")


if __name__ == "__main__":
    main()