# tests for portfolio construction

import pandas as pd

import pytest

from src.portfolio.constructor import build_portfolio, REGIME_RISK_ON, REGIME_NEUTRAL, REGIME_RISK_OFF

ETF_NAMES = {"XLK", "XLF", "XLY", "XLP", "XLE", "XLI", "XLV"}

def _make_rankings(scores: list[float]) -> pd.Series:
    return pd.Series(scores, index=ETF_NAMES, name="outperform_prob").sort_values(ascending=False)


def test_weights_sum_to_one():
    rankings = _make_rankings([0.8,0.7,0.6,0.5,0.4,0.3,0.2])
    for regime in [REGIME_RISK_ON, REGIME_NEUTRAL, REGIME_RISK_OFF]:
        weights = build_portfolio(regime, rankings)
        assert abs(weights.sum()-1.0) < 1e-9

def test_neutral_regime_equal_weights():
    rankings = _make_rankings([0.8,0.7,0.6,0.5,0.4,0.3,0.2])
    weights = build_portfolio(REGIME_NEUTRAL, rankings)
    expected = 1.0 / len(ETF_NAMES)

    assert all(abs(v - expected) < 1e-9 for v in weights)

def test_risk_on_top():
    rankings = _make_rankings([0.8,0.7,0.6,0.5,0.4,0.3,0.2])
    weights = build_portfolio(REGIME_RISK_ON, rankings, risk_level="aggressive")

    assert weights.max() == pytest.approx(1.0)
    assert (weights>0).sum() == 1

def test_risk_off_does_not_add_bottom():
    rankings = _make_rankings([0.8,0.7,0.6,0.5,0.4,0.3,0.2])
    weights = build_portfolio(REGIME_RISK_OFF, rankings)
    bottom_2 = rankings.tail(2).index
    for etf in bottom_2:
        assert weights[etf] == 0.0