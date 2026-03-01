# quant_engine/src/backtest/tearsheet.py
#
# Performance summary tearsheet for a completed backtest.
#
# Produces two things from a set of daily log return series:
# 1. A 4-panel matplotlib figure:
#       - Panel 1: Cumulative returns (growth of £1) - strategy vs benchmark
#       - Panel 2: Drawdown chart - strategy vs benchmark
#       - Panel 3: Rolling 12mth Sharpe ratio for the strategy
#       - Panel 4: Annual returns bar chart - strategy vs benchmark side by side
#
# 2. A stats dict of key performance metrics formatted as display strings.
#
# Conventions used throughout:
# - All inputs are daily log returns
# - Cumulative growth is computed as exp(cumsum(log returns))
# - Annual returns per calendar year are exp(sum of log returns in that year) - 1
# - The rolling Sharpe uses a 252-day window (one full trading year)

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from src.evaluation.metrics import (
    annual_return, annual_volatility, sharpe_ratio,
    max_drawdown, excess_return, annual_turnover
)

TRADING_DAYS = 252
ROLL_SHARPE_WINDOW = 252  # rolling window for the Sharpe ratio panel


# Main entry point - builds both the figure and then stats dict
def build_tearsheet(
        portfolio_returns: pd.Series,
        benchmark_returns: pd.Series,
        turnover: pd.Series,
        title: str = "AI ETF Advisor: Backtest Tearsheet",
        risk_free: float = 0.0
) -> tuple[plt.Figure, dict]:
    # portfolio_returns: daily log returns of the strategy portfolio
    # benchmark_returns: daily log returns of the benchmark
    # turnover: daily portfolio turnover series
    # title: title displayed at the top of the figure
    # risk_free: annual risk-free rate used in the Sharpe calculation
    # returns: tuple of (matplotlib Figure, stats dict)
    stats = _compute_stats(portfolio_returns, benchmark_returns, turnover, risk_free)
    fig = _plot_tearsheet(portfolio_returns, benchmark_returns, stats, title)

    return fig, stats


# Compute all the summary stats and format them as strings for display
# All values are returned as formatted strings so the caller can drop them
# straight into a table without any extra formatting
def _compute_stats(portfolio, benchmark, turnover, risk_free) -> dict:
    return {
        "Annual Return (Strategy)": f"{annual_return(portfolio):.2%}",
        "Annual Return (Benchmark)": f"{annual_return(benchmark):.2%}",
        "Excess Return": f"{excess_return(portfolio, benchmark):.2%}",
        "Annual Volatility (Strategy)": f"{annual_volatility(portfolio):.2%}",
        "Annual Volatility (Benchmark)": f"{annual_volatility(benchmark):.2%}",
        "Sharpe (Strategy)": f"{sharpe_ratio(portfolio, risk_free):.2f}",
        "Sharpe (Benchmark)": f"{sharpe_ratio(benchmark, risk_free):.2f}",
        "Max Drawdown (Strategy)": f"{max_drawdown(portfolio):.2%}",
        "Max Drawdown (Benchmark)": f"{max_drawdown(benchmark):.2%}",
        "Annual Turnover": f"{annual_turnover(turnover):.2%}",
        "Start Date": str(portfolio.index[0].date()),
        "End Date": str(portfolio.index[-1].date()),
        "Trading Days": str(len(portfolio))
    }


# Build the 4panel tearsheet figure
def _plot_tearsheet(portfolio, benchmark, stats, title) -> plt.Figure:
    # Convert log returns to cumulative growth curves for the charts
    cum_portfolio = portfolio.cumsum().apply(np.exp)
    cum_benchmark = benchmark.cumsum().apply(np.exp)

    # Drawdown series: how far each curve is below its running peak
    dd_portfolio = _drawdown_series(cum_portfolio)
    dd_benchmark = _drawdown_series(cum_benchmark)

    # Rolling 12mth Sharpe ratio for the strategy
    rolling_sharpe = portfolio.rolling(ROLL_SHARPE_WINDOW).apply(
        lambda x: sharpe_ratio(pd.Series(x)), raw=False
    )

    # Annual returns aggregated by calendar year
    annual_portfolio = _annual_returns(portfolio)
    annual_benchmark = _annual_returns(benchmark)

    fig  = plt.figure(figsize=(14, 14))
    grid = fig.add_gridspec(4, 1, hspace=0.45)

    # Panel 1: Cumulative returns 
    p1 = fig.add_subplot(grid[0])
    p1.plot(cum_portfolio.index, 
            cum_portfolio.values, 
            label="Strategy", 
            color="#2980b9", 
            linewidth=1.5
    )
    p1.plot(cum_benchmark.index, 
            cum_benchmark.values,
            label="Benchmark", 
            color="#7f8c8d", 
            linewidth=1.2, 
            linestyle="--"
    )
    p1.set_ylabel("Growth of £1", fontsize=10)
    p1.set_title("Cumulative Returns", fontsize=11, fontweight="bold")
    p1.legend(fontsize=9)
    p1.grid(axis="y", linestyle="--", alpha=0.4)
    p1.yaxis.set_major_formatter(mtick.FormatStrFormatter("£%.1f"))

    # Panel 2: Drawdown chart
    p2 = fig.add_subplot(grid[1])
    p2.fill_between(dd_portfolio.index, 
                    dd_portfolio.values,
                    label="Strategy", 
                    color="#e74c3c", 
                    alpha=0.6
    )
    p2.fill_between(dd_benchmark.index, 
                    dd_benchmark.values,
                    label="Benchmark", 
                    color="#7f8c8d", 
                    alpha=0.3, 
                    linestyle="--"
    )
    p2.set_ylabel("Drawdown", fontsize=10)
    p2.set_title("Underwater Chart", fontsize=11, fontweight="bold")
    p2.legend(fontsize=9)
    p2.grid(axis="y", linestyle="--", alpha=0.4)
    p2.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1))

    # Panel 3: Rolling 12mth Sharpe ratio 
    p3 = fig.add_subplot(grid[2])
    p3.plot(rolling_sharpe.index, 
            rolling_sharpe.values, 
            color="#8e44ad", 
            linewidth=1.2
    )
    p3.axhline(0, color="black", linewidth=0.8, linestyle="--")  # zero line
    p3.axhline(1, color="#27ae60", linewidth=0.6, linestyle=":")  # Sharpe = 1 reference
    p3.set_ylabel("Sharpe Ratio", fontsize=10)
    p3.set_title("Rolling 12mth Sharpe Ratio", fontsize=11, fontweight="bold")
    p3.grid(axis="y", linestyle="--", alpha=0.4)

    # Panel 4: Annual returns bar chart
    p4 = fig.add_subplot(grid[3])
    years = annual_portfolio.index.union(annual_benchmark.index)
    x = np.arange(len(years))
    w = 0.35  # bar width

    p4.bar(x - w/2, 
           annual_portfolio.reindex(years).fillna(0) * 100,
           w, 
           label="Strategy", 
           color="#2980b9", 
           alpha=0.8
    )
    p4.bar(x + w/2, 
           annual_benchmark.reindex(years).fillna(0) * 100,
           w, 
           label="Benchmark", 
           color="#7f8c8d", 
           alpha=0.8
    )
    p4.axhline(0, color="black", linewidth=0.8)
    p4.set_xticks(x)
    p4.set_xticklabels([str(y) for y in years], rotation=45, ha="right", fontsize=8)
    p4.set_ylabel("Return (%)", fontsize=10)
    p4.set_title("Annual Returns", fontsize=11, fontweight="bold")
    p4.legend(fontsize=9)
    p4.grid(axis="y", linestyle="--", alpha=0.4)

    # Stats summary as a text box below the panels
    stats_text = "\n".join(f"{k:<35} {v}" for k, v in stats.items())
    fig.text(0.01, 
            -0.02, 
            stats_text, 
            fontsize=8, 
            family="monospace",
            verticalalignment="top",
            bbox=dict(boxstyle="round",
                    facecolor="lightyellow", 
                    alpha=0.8
            )
    )

    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.01)

    return fig


# Helper functions

# Compute the drawdown series from a cumulative growth curve
# Drawdown at each point is the % drop from the running peak — always <= 0
def _drawdown_series(cum_returns: pd.Series) -> pd.Series:
    rolling_max = cum_returns.cummax()
    return (cum_returns - rolling_max) / rolling_max


# Aggregate daily log returns into annual simple returns by calendar year
# Sums log returns within each year then converts with exp(sum) - 1
def _annual_returns(log_returns: pd.Series) -> pd.Series:
    return log_returns.groupby(log_returns.index.year).sum().apply(np.exp).subtract(1)
