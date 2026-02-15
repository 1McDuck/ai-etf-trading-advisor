# quant_engine/src/backtest/engine.py

# Backtesting engine, simulates the full strategy pipe over the given historic date range rebal frequency is given as days

# outputs:
# - portfolio_returns: pd.Series of daily portfolio log returns
# - benchmark_returns: pd.Series of daily benchmark log returns
# - turnover: pd.Series of daily weight change magnitudes

from __future__ import annotations

import numpy as np
import pandas as pd

def run_backtest(
    etf_prices: pd.DataFrame,
    benchmark: pd.Series,
    weights_schedule: pd.DataFrame
) -> dict[str, pd.Series]:
    # params:
    # - etf_prices: daily close px for each sectors etf (cols=ETF names)
    # - benchmark: daily close pd for the bench (MSCI world)
    # - weights_schedule: target weights per ETF on each rebalance date (date, cols=ETF names)
    
    # return dict portfolio_returns, benchmark_returns, turnover

    log_etf = np.log(etf_prices/etf_prices.shift(1)).fillna(0)
    log_bench = np.log(benchmark/benchmark.shift(1)).fillna(0)

    current_weights = weights_schedule.iloc[0]
    portfolio_returns = []
    turnovers = []

    for date in log_etf.index:
        if date in weights_schedule.index:
            new_weights = weights_schedule.loc[date]
            turnover = (new_weights-current_weights).abs().sum()
            turnovers.append((date, turnover))
            current_weights = new_weights
        
        daily_return = (log_etf.loc[date] * current_weights).sum()
        portfolio_returns.append((date, daily_return))
    
    portfolio_series = pd.Series(dict(portfolio_returns), name="portfolio")
    benchmark_series = log_bench.loc[portfolio_series.index].rename("benchmark")
    turnover_series = pd.Series(dict(turnovers), name="turnover").reindex(portfolio_series.index).fillna(0)
    
    return {
        "portfolio_returns": portfolio_series,
        "benchmark_returns": benchmark_series,
        "turnover": turnover_series
    }