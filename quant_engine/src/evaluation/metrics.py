# quant_engine/src/evaluation/metrics.py
#
# Performance and clustering evaluation metrics used across the pipeline.
#
# Regime quality metrics (from sklearn):
# - Silhouette score: measures how well-separated the clusters are (higher = better)
# - Davies-Bouldin index: measures cluster compactness vs separation (lower = better)
#
# Portfolio performance metrics (all calculated from daily log returns):
# - Annual return: annualised mean log return
# - Annual volatility: annualised standard deviation of daily log returns
# - Sharpe ratio: risk adjusted return (excess return/volatility)
# - Max drawdown: largest peak-to-trough decline over the full period
# - Excess return: portfolio annual return minus benchmark annual return
# - Annual turnover: average portfolio turnover per year

from __future__ import annotations

import numpy as np
import pandas as pd

from sklearn.metrics import silhouette_score, davies_bouldin_score

# Number of trading days in a year, used to annualise daily metrics
TRADING_DAYS = 252


# Regime clustering quality metrics

# Compute the silhouette score for the regime clustering result
# Higher score (closer to 1) = clusters are dense and well separated
# Score near 0 or negative = overlapping or poorly separated regimes
def regime_silhouette(features: np.ndarray, labels: np.ndarray) -> float:
    return float(silhouette_score(features, labels))


# Compute the Davies-Bouldin index for the regime clustering result
# Lower score = clusters are more compact and better separated
def regime_davies_bouldin(features: np.ndarray, labels: np.ndarray) -> float:
    return float(davies_bouldin_score(features, labels))


# Portfolio performance metrics

# Annualised mean log return
# Multiply mean daily log return by trading days per year
# This approximates the CAGR for small daily returns
def annual_return(log_returns: pd.Series) -> float:
    return float(log_returns.mean() * TRADING_DAYS)


# Worst peak-to-trough drop over the full period
# Builds the growth curve then finds the biggest fall from any previous high
def max_drawdown(log_returns: pd.Series) -> float:
    cum = log_returns.cumsum().apply(np.exp)
    rolling_max = cum.cummax()
    drawdown = (cum - rolling_max) / rolling_max
    return float(drawdown.min())


# Annualised volatility of daily log returns
# Uses the square-root-of-time rule to scale daily std dev to an annual figure
def annual_volatility(log_returns: pd.Series) -> float:
    return float(log_returns.std() * np.sqrt(TRADING_DAYS))


# Sharpe ratio: annualised excess return divided by annualised volatility
# Risk-free rate defaults to 0 for simplicity
# Returns NaN if volatility is zero to avoid division by zero
def sharpe_ratio(log_returns: pd.Series, risk_free: float = 0.0) -> float:
    excess = annual_return(log_returns) - risk_free
    vol = annual_volatility(log_returns)
    return float(excess / vol) if vol > 0 else np.nan


# Annual excess return of the portfolio over the benchmark
def excess_return(portfolio: pd.Series, benchmark: pd.Series) -> float:
    return annual_return(portfolio) - annual_return(benchmark)


# Annualised portfolio turnover
# Each rebalance day's turnover is the total absolute weight change,
# scaled up to a yearly figure by multiplying the daily mean by 252
def annual_turnover(turnover: pd.Series) -> float:
    return float(turnover.mean() * TRADING_DAYS)


# Bundle all main portfolio metrics into a single dictionary
# Convenience function used by the tearsheet and API serialiser
def summary_stats(
        portfolio: pd.Series,
        benchmark: pd.Series,
        turnover: pd.Series,
        risk_free: float = 0.0
) -> dict:
    # portfolio: Series of daily portfolio log returns
    # benchmark: Series of daily benchmark log returns
    # turnover: Series of daily turnover values
    # risk_free: annual risk-free rate (default 0.0)
    # returns: dict mapping metric name -> float value
    return {
        "annual_return": annual_return(portfolio),
        "annual_volatility": annual_volatility(portfolio),
        "sharpe_ratio": sharpe_ratio(portfolio, risk_free),
        "max_drawdown": max_drawdown(portfolio),
        "excess_return_vs_benchmark": excess_return(portfolio, benchmark),
        "benchmark_sharpe": sharpe_ratio(benchmark, risk_free),
        "annual_turnover": annual_turnover(turnover)
    }
