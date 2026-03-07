# quant_engine/src/backtest/pipeline.py
#
# Full end-to-end backtest pipeline.
#
# Runs the entire strategy workflow in sequence:
# 1. Data ingestion - download historical ETF and benchmark prices from yfinance
# 2. Regime detection - fit GMM to macro features, label each day risk-on/neutral/risk-off
# 3. Feature engineering - build the ETF technical feature matrix (momentum, vol, rel strength)
# 4. Ranking model - train a Random Forest to predict ETF outperformance vs benchmark
# 5. Weights schedule - apply the model at each rebalance date to generate target allocations
# 6. Simulation - run the backtest engine to calculate daily portfolio returns
# 7. Tearsheet stats - calculate summary performance metrics
#
# Design notes:
# - GMM is fitted on the full period - a simplification that assumes regime structure
#   doesn't shift over time (no rolling refit).
# - The ranking model is trained on the full period and then used to generate weights at
#   each rebalance date using only features available at that point (no lookahead in features).
# - Regime labels used as model features (integer cluster IDs) are separate from the semantic
#   labels used for portfolio construction (named strings). strategy.py for details.
# - All price series are aligned to the same date index before being passed to the engine.

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.backtest.engine import run_backtest
from src.backtest.strategy import build_weights_schedule
from src.backtest.tearsheet import build_tearsheet
from src.data.ingestion import multi_tickers, get_price_data, SECTOR_ETFS, BENCHMARK_TICKER
from src.features.etf_features import build_etf_features
from src.prediction.pipeline import wide_to_long_feature_matrix, build_targets_long, train_ranking_model
from src.regimes.pipeline import run_regime_pipeline, RegimeResult


# Container for all the outputs from a completed full backtest run
@dataclass
class BacktestResult:
    # portfolio_returns: daily log returns of the strategy portfolio
    # benchmark_returns: daily log returns of the benchmark
    # turnover: daily portfolio turnover (0 on non-rebalance days)
    # weights_schedule: target weights at each rebalance date (date x ETF)
    # stats: dict of summary performance statistics from the tearsheet
    # regime_result: full RegimeResult from the regime detection step
    portfolio_returns: pd.Series
    benchmark_returns: pd.Series
    turnover: pd.Series
    weights_schedule: pd.DataFrame
    stats: dict
    regime_result: RegimeResult


# Run the complete strategy backtest from data download through to performance stats
def run_full_backtest(
        start: str = "2000-01-01",
        end: str | None = None,
        risk_level: str = "moderate",
        rebalance_freq: int = 21,
        n_estimators: int = 300
) -> BacktestResult:
    # start: start date in YYYY-MM-DD format
    # end: end date in YYYY-MM-DD format (defaults to today)
    # risk_level: investor risk profile: conservative, moderate, or aggressive
    # rebalance_freq: number of trading days between portfolio rebalances
    # n_estimators: number of trees in the Random Forest ranking model
    # returns: BacktestResult containing returns, weights, stats and regime data
    if end is None:
        end = pd.Timestamp.today().strftime("%Y-%m-%d")

    # Step 1: Download historical price data for the sector ETFs and benchmark
    print(f"[Backtest] Downloading data {start} to {end}")
    etf_prices = multi_tickers(SECTOR_ETFS, start=start, end=end)
    benchmark  = get_price_data(BENCHMARK_TICKER, start=start, end=end)

    # Step 2: Detect market regimes using the GMM pipeline
    print(f"[Backtest] Running regime pipeline...")
    regime_result = run_regime_pipeline(start=start, end=end)

    # Step 3: Build the ETF feature matrix
    # wide_features index becomes the shared date index for the rest of the pipeline
    print(f"[Backtest] Building ETF features...")
    wide_features = build_etf_features(
        etf_prices=etf_prices,
        benchmark=benchmark,
        regime_labels=regime_result.labels
    )

    # Step 4: Train the ranking model on the full historical feature set
    print(f"[Backtest] Training ranking model...")
    etf_names = list(etf_prices.columns)
    long_df = wide_to_long_feature_matrix(wide_features, etf_names)
    long_df = build_targets_long(long_df, etf_prices=etf_prices, benchmark=benchmark)
    rank_result = train_ranking_model(long_df, n_estimators=n_estimators)
    print(f"CV hit rate: {rank_result.cv_hit_rate_mean:.1%} +/- {rank_result.cv_hit_rate_std:.1%}")

    # Step 5: Generate the rebalance weight schedule
    # regime_labels - raw GMM integers used as numeric model input features
    # regime_label_names - VIX ordered string labels used for portfolio construction rules
    print(f"[Backtest] Generating weights schedule, rebalance every {rebalance_freq} days, risk_level={risk_level}")
    weights_schedule = build_weights_schedule(
        wide_features=wide_features,
        regime_labels=regime_result.labels,
        regime_label_names=regime_result.label_names(),
        model=rank_result.model,
        etf_names=etf_names,
        risk_level=risk_level,
        rebalance_freq=rebalance_freq
    )

    # Step 6: Simulate the portfolio - align prices to the feature date index first
    print("[Backtest] Simulating portfolio...")
    line_etf = etf_prices.loc[wide_features.index]
    line_bench = benchmark.loc[wide_features.index]
    sim = run_backtest(etf_prices=line_etf, benchmark=line_bench, weights_schedule=weights_schedule)

    # Step 7: Calculate tearsheet stats from the simulated returns
    print(f"[Backtest] Calculating tearsheet...")
    _, stats = build_tearsheet(
        portfolio_returns=sim["portfolio_returns"],
        benchmark_returns=sim["benchmark_returns"],
        turnover=sim["turnover"]
    )

    print("[Backtest] ---- Results ----")
    for k, v in stats.items():
        print(f"{k:<35} {v}")

    return BacktestResult(
        portfolio_returns=sim["portfolio_returns"],
        benchmark_returns=sim["benchmark_returns"],
        turnover=sim["turnover"],
        weights_schedule=weights_schedule,
        stats=stats,
        regime_result=regime_result
    )
