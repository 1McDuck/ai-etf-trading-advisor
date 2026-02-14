# evaluation metric tests

import numpy as np
import pandas as pd

import pytest

from src.evaluation.metrics import annual_return, annual_volatility, sharpe_ratio, max_drawdown, excess_return, summary_stats

def _flat_returns(n: int=252, daily: float=0.0004) -> pd.Series:
    idx = pd.bdate_range("2020-01-01", periods=n)
    return pd.Series([daily] * n, index=idx)

def test_annual_return():
    returns = _flat_returns(daily=0.0004)
    result = annual_return(returns)

    assert result == pytest.approx(0.0004 * 252, rel=1e-6)


def test_annual_volatility_zero():
    r = _flat_returns(daily=0.0001)
    
    assert annual_volatility(r) == pytest.approx(0.0, abs=1e-10)

def test_sharpe_positive_for_positive_returns():
    r = _flat_returns(daily=0.001)
    result = sharpe_ratio(r)

    assert np.isnan(result) or result > 0

def test_max_drawdown_negative():
    rng = np.random.default_rng(0)
    r = pd.Series(rng.normal(0,0.01,252))
    dd = max_drawdown(r)

    assert dd <= 0


def test_excess_return():
    portfolio = _flat_returns(daily=0.0005)
    benchmark = _flat_returns(daily=0.0003)
    excess = excess_return(portfolio, benchmark)

    assert excess == pytest.approx((0.0005 - 0.0003) * 252, rel=1e-6)


def test_summary_stats_keys():
    portfolio = _flat_returns(daily=0.0005)
    benchmark = _flat_returns(daily=0.0003)
    turnover = _flat_returns(daily=0.002)
    stats = summary_stats(portfolio, benchmark, turnover)
    req_keys = {
        "annual_return", 
        "annual_volatility", 
        "sharpe_ratio",
        "max_drawdown",
        "excess_return_vs_benchmark",
        "benchmark_sharpe",
        "annual_turnover"
    }

    assert req_keys.issubset(stats.keys())

