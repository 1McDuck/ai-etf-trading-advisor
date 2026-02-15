# quant_engine/src/backtest/pipeline.py

# The full backtest pipeline controls
# Brings in:
# Regime pipeline: regime labels
# Ranking pipeline: trained model and wide features
# Strategy layer: weights schedule (monthly)
# Engine: daily portfolio returns
# Tearsheet: performance stats and charts

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.backtest.engine import run_backtest
from src.backtest.strategy import build_weights_schedule
from src.backtest.tearsheet import build_tearsheet

from src.data.ingestion import multi_tickers, get_price_data, SECTOR_ETFS, BENCHMARK_TICKER

from src.features.etf_features import build_etf_features

from src.prediction.pipeline import run_ranking_pipeline, wide_to_long_feature_matrix, build_targets_long, train_ranking_model

from src.regimes.pipeline import run_regime_pipeline, RegimeResult


@dataclass
class BacktestResult:
    portfolio_returns: pd.Series
    benchmark_returns: pd.Series
    turnover: pd.Series
    weights_schedule: pd.DataFrame
    stats: dict
    regime_result: RegimeResult


def run_full_backtest(
    start: str = "2000-01-01",
    end: str | None = None,
    risk_level: str = "moderate",
    rebalance_freq: int = 21,
    n_estimators: int = 300
) -> BacktestResult:
    # Run the full strategy backtest end to end
    # Regime GMM is fitted on all data
    # Ranking model is trained on the full period then used for weightings
    # Rebalance weights only use features avaliable at each rebalance date

    # Params:
    # - start: start date
    # - end: end date (default today)
    # - risk_level: "conservative", "moderate", aggressive"
    # - rebalance_freq: trading days between rebalances
    # - n_estimators: RandomForest tree count

    # return BacktestResult with portfolio and benchmark returns, weights, tearsheet stats, regime result

    if end is None:
        end = pd.Timestamp.today().strftime("%Y-%m-%d")

    # market data:
    print(f"[Backtest] Downloading data {start} to {end}")
    etf_prices = multi_tickers(SECTOR_ETFS, start=start, end=end)
    benchmark = get_price_data(BENCHMARK_TICKER, start=start, end=end)

    # Regime detection:
    print(f"[Backtest] Running regime pipeline...")
    regime_result = run_regime_pipeline(start=start, end=end)

    # ETF Features
    print(f"[Backtest] Building ETF features...")
    wide_features = build_etf_features(etf_prices=etf_prices, benchmark=benchmark, regime_labels=regime_result.labels)

    # Train ranking model
    print(f"[Backtest] Training ranking model...")
    etf_names = list(etf_prices.columns)
    long_df = wide_to_long_feature_matrix(wide_features, etf_names)
    long_df = build_targets_long(long_df, etf_prices=etf_prices, benchmark=benchmark)
    rank_result = train_ranking_model(long_df, n_estimators=n_estimators)
    print(f"CV hit rate: {rank_result.cv_hit_rate_mean:.1%} plus or minus {rank_result.cv_hit_rate_std:.1%}")

    # Build weights schedule:
    print(f"[Backtest] Generating weights schedule, rebalance every {rebalance_freq} days, risk_level={risk_level}")
    weights_schedule = build_weights_schedule(
        wide_features=wide_features,
        regime_labels=regime_result.labels,
        model=rank_result.model,
        etf_names=etf_names,
        risk_level=risk_level,
        rebalance_freq=rebalance_freq
    )

    # Simulate portfolio
    print("[Backtest] Simulating portfolio...")
    line_etf = etf_prices.loc[wide_features.index]
    line_bench = benchmark.loc[wide_features.index]
    
    sim = run_backtest(
        etf_prices=line_etf,
        benchmark=line_bench,
        weights_schedule=weights_schedule
    )

    # Tearsheet
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
        portfolio_returns=sim["benchmark_returns"],
        benchmark_returns=sim["benchmark_returns"],
        turnover=sim["turnover"],
        weights_schedule=weights_schedule,
        stats=stats,
        regime_result=regime_result
    )