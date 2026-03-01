# quant_engine/src/backtest/engine.py
#
# Backtest simulation engine.
#
# Given a set of daily ETF prices and a target weight schedule, this module
# simulates the daily portfolio log returns as if the strategy had been run
# historically with no look-ahead bias.
#
# Assumptions:
# - Returns are computed as daily log returns
# - Weights are updated at the open on each rebalance date and held constant 
#   until the next scheduled rebalance
# - Turnover is the sum of absolute weight changes on each rebalance day
#   (a common measure of how actively the portfolio is managed)
# - Input prices are assumed to be aligned on the same NYSE trading calendar,
#   with any missing dates already forward-filled by the ingestion layer
#
# Outputs:
# - portfolio_returns: daily log returns of the strategy portfolio
# - benchmark_returns: daily log returns of the benchmark (aligned to portfolio)
# - turnover: daily weight-change magnitude (0 on non-rebalance days)

from __future__ import annotations

import numpy as np
import pandas as pd


# Simulate daily portfolio returns from a target weight schedule
# Iterates through each trading day in order; on rebalance dates the portfolio
# is updated to the new target weights and turnover is recorded
# The benchmark series is sliced to match the portfolio date range
def run_backtest(
        etf_prices: pd.DataFrame, 
        benchmark: pd.Series, 
        weights_schedule: pd.DataFrame
) -> dict[str, pd.Series]:
    # etf_prices: DataFrame of daily close prices, columns = ETF names
    # benchmark: Series of daily benchmark close prices (MSCI World)
    # weights_schedule: DataFrame of target weights indexed by rebalance dates,
    #                   columns = ETF names
    # returns: dict with keys:
    # - "portfolio_returns": pd.Series of daily portfolio log returns
    # - "benchmark_returns": pd.Series of daily benchmark log returns
    # - "turnover": pd.Series of daily turnover (0 on non-rebalance days)

    # Compute daily log returns for all ETFs and the benchmark
    log_etf   = np.log(etf_prices / etf_prices.shift(1)).fillna(0)
    log_bench = np.log(benchmark / benchmark.shift(1)).fillna(0)

    # Initialise the portfolio with the first scheduled weight row
    current_weights = weights_schedule.iloc[0]

    portfolio_returns = []
    turnovers = []

    for date in log_etf.index:
        # On rebalance dates: update weights and record turnover before calculating returns
        if date in weights_schedule.index:
            new_weights = weights_schedule.loc[date]
            turnover = (new_weights - current_weights).abs().sum()
            turnovers.append((date, turnover))
            current_weights = new_weights

        # Daily portfolio return = weighted sum of individual ETF log returns
        daily_return = (log_etf.loc[date] * current_weights).sum()
        portfolio_returns.append((date, daily_return))

    # Convert the list of (date, value) pairs to indexed series
    portfolio_series = pd.Series(dict(portfolio_returns), name="portfolio")
    benchmark_series = log_bench.loc[portfolio_series.index].rename("benchmark")

    # Turnover is only recorded on rebalance days; fill the rest with 0
    turnover_series = (
        pd.Series(dict(turnovers), name="turnover").reindex(portfolio_series.index).fillna(0)
    )

    return {
        "portfolio_returns": portfolio_series,
        "benchmark_returns": benchmark_series,
        "turnover": turnover_series
    }
