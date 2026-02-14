# quant_engine/src/evaluation/metrics.py

# evaluation metrics:
# Regime quality: slihouette score, davies-bouldin index
# Ranking model: RMSE, MAE, hit rate
# Portfolio: max_drawdown, annual volatility, sharpe ratio, excess return vs bench, annual turnover

from __future__ import annotations

import numpy as np
import pandas as pd

from sklearn.metrics import silhouette_score, davies_bouldin_score

TRADING_DAYS = 252

# Regime

def regime_silhouette(features: np.ndarray, labels: np.ndarray) -> float:
    return float(silhouette_score(features, labels))

def regime_davies_bouldin(features: np.ndarray, labels: np.ndarray) -> float:
    return float(davies_bouldin_score(features, labels))


# Portfolio

def annual_return(log_returns: pd.Series) -> float:
    return float(log_returns.mean() * TRADING_DAYS)

def max_drawdown(log_returns: pd.Series) -> float:
    cum = log_returns.cumsum().apply(np.exp)
    rolling_max = cum.cummax()
    drawdown = (cum - rolling_max)/rolling_max
    return float(drawdown.min())

def annual_volatility(log_returns: pd.Series) -> float:
    return float(log_returns.std() * np.sqrt(TRADING_DAYS))

def sharpe_ratio(log_returns: pd.Series, risk_free: float = 0.0) -> float:
    excess = annual_return(log_returns) - risk_free
    vol = annual_volatility(log_returns)
    return float(excess/vol) if vol > 0 else np.nan

def excess_return(portfolio: pd.Series, benchmark: pd.Series) -> float:
    return annual_return(portfolio) - annual_return(benchmark)

def annual_turnover(turnover: pd.Series) -> float:
    return float(turnover.mean() * TRADING_DAYS)



def summary_stats(
    portfolio: pd.Series,
    benchmark: pd.Series,
    turnover: pd.Series,
    risk_free: float = 0.0
) -> dict:
    return {
        "annual_return": annual_return(portfolio),
        "annual_volatility": annual_volatility(portfolio),
        "sharpe_ratio": sharpe_ratio(portfolio, risk_free),
        "max_drawdown": max_drawdown(portfolio),
        "excess_return_vs_benchmark": excess_return(portfolio, benchmark),
        "benchmark_sharpe": sharpe_ratio(benchmark, risk_free),
        "annual_turnover": annual_turnover(turnover)
    }



