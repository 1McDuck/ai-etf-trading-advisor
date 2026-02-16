# scripts/train_etf_ranker.py

# Train the ETF ranking model and save the results

# usage python scripts/train_etf_ranker.py

# out:
# etf_ranker.joblib - trained RandomForestClassifier
# feature_importances.csv - featurte importance scores
# cv_results.txt - cross validation hit rate summary
# regime_overlay.png - regime chart 

import argparse
import os
import sys

import joblib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "quant_engine"))

from src.prediction.pipeline import run_ranking_pipeline
from src.regimes.pipeline import run_regime_pipeline
from src.regimes.visualisation import plot_regime_overlay, plot_transition_heatmap

def main() -> None:
    parser = argparse.ArgumentParser(description="Train the AI ETF ranking model")
    parser.add_argument("--start", default="2000-01-01")
    parser.add_argument("--end", default=None)
    parser.add_argument("--out", default="outputs/")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    # Run regime pipeline first for reuse
    print("Regime Detection")
    regime_result = run_regime_pipeline(start=args.start, end=args.end)

    # Save regime chart
    fig = plot_regime_overlay(
        prices=regime_result.benchmark_prices,
        labels=regime_result.labels,
        label_names=regime_result.label_names()
    )
    fig.savefig(os.path.join(args.out, "regime_overlay.png"), dpi=150, bbox_inches="tight")

    fig2 = plot_transition_heatmap(regime_result.transition_matrix)
    fig2.savefig(os.path.join(args.out, "transition_heatmap.png"), dpi=150, bbox_inches="tight")

    # train the ranker, reused regime labels
    print("ETF Ranking Model")
    result = run_ranking_pipeline(start=args.start, end=args.end, regime_result=regime_result)

    # Save model
    model_path = os.path.join(args.out, "etf_ranker.joblib")
    joblib.dump(result.model, model_path)
    print(f"Saved Model: {model_path}")

    # Save feature importances
    fi_path = os.path.join(args.out, "feature_importances.csv")
    result.feature_importances.to_csv(fi_path, header=True)
    print(f"Saved feature importnaces: {fi_path}")

    # Save CV summary
    cv_path = os.path.join(args.out, "cv_results.csv")
    with open(cv_path, "w") as f:
        f.write(f"CV Hit Rate: {result.cv_hit_rate_mean:.4f} +- {result.cv_hit_rate_std:.4f}\n")
        f.write(f"CV Log Loss: {result.cv_log_loss_mean:.4f}\n")
        f.write(f"ETFs trained on: {', '.join(result.etf_names)}\n")
    print(f"Saved CV results: {cv_path}")

    print("----Summary----")
    print(f"CV hit rate: {result.cv_hit_rate_mean:.1%} +- {result.cv_hit_rate_std:.1%}")
    print(f"Baseline: 50%")
    print(f"Top Feature: {result.feature_importances.index[0]}")
    
     




if __name__ == "__main__":
    main()