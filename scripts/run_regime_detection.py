# scripts/run_regime_detection.py

# Run the full regime detection pipeline and save charts

# Usage:
# python scripts/run_regime_detection.py

# Arguments:
# --start YYYY-MM-DD
# --end YYYY-MM-DD

# Out (written to outputs/)
# regime_overlay.png: MSCIN world price and regime
# transition_heatmap.png: Regime switching probability matrix
# regime_labels.csv: date, int label, str label, confidence

import argparse
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "quant_engine"))

from src.regimes.pipeline import run_regime_pipeline
from src.regimes.visualisation import plot_regime_overlay, plot_transition_heatmap

def main() -> None:
    parser = argparse.ArgumentParser(description="Run AI ETF regime detection pipeline")
    parser.add_argument("--start", default="2000-01-01", help="Start date: YYYY-MM-DD")
    parser.add_argument("--end", default=None, help="End date: YYYY-MM-DD")
    parser.add_argument("--out", default="outputs", help="Output directory")
    parser.add_argument("--components", type=int, default=3, help="Number of GMM components")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    result = run_regime_pipeline(start=args.start, end=args.end, n_regimes=args.components)

    # Regime chart
    c1 = plot_regime_overlay(prices=result.benchmark_prices, labels=result.labels, label_names=result.label_names())
    path1 = os.path.join(args.out, "regime_overlay.png")
    c1.savefig(path1, dpi=150, bbox_inches="tight")
    print(f"Saved: {path1}")

    # Transition heatmap
    c2 = plot_transition_heatmap(result.transition_matrix)
    path2 = os.path.join(args.out, "transition_heatmap.png")
    c2.savefig(path2, dpi=150, bbox_inches="tight")
    print(f"Saved: {path2}")

    # CSV
    import pandas as pd
    df = pd.DataFrame({
        "regime_int": result.labels,
        "regime_name": result.label_names(),
        "confidence": result.confidence
    })
    path3 = os.path.join(args.out, "regime_labels.csv")
    df.to_csv(path3)
    print(f"Saved: {path3}")



if __name__ == "__main__":
    main()
