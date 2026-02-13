# Regime detection pipeline tests

from unittest.mock import patch

import pytest
import numpy as np
import pandas as pd

from src.regimes.pipeline import RegimeResult, run_regime_pipeline


# Helper

def _make_price_series(n: int=500, seed: int=0) -> pd.Series:
    rng = np.random.default_rng(seed)
    log_rets = rng.normal(0.0003, 0.01, size=n) 
    prices = 100 * np.exp(np.cumsum(log_rets))
    idx = pd.bdate_range("2010-01-01", periods=n)

    return pd.Series(prices, index=idx, name="price")

def _make_macro_df(n: int=500) -> pd.DataFrame:
    idx = pd.bdate_range("2010-01-01", periods=n)
    rng = np.random.default_rng(1)

    return pd.DataFrame(
        {
            "GOLD": 1750 * np.exp(np.cumsum(rng.normal(0, 0.005, n))),
            "EURUSD": 1.1 + rng.normal(0, 0.002, n).cumsum(),
            "VIX": 15 + 5 * np.abs(rng.normal(0, 1, n)),
            "US10Y": 2.5 + rng.normal(0, 0.01, n).cumsum(),
        },
        index=idx
    )


# Tests

@patch("src.regimes.pipeline.get_price_data")
@patch("src.regimes.pipeline.multi_tickers")
def test_pipeline_returns_regime_result(mock_multi, mock_single):
    macro = _make_macro_df(500)
    benchmark = _make_price_series(500, seed=99)
    mock_multi.return_value = macro
    mock_single.return_value = benchmark

    result = run_regime_pipeline(start="2010-01-01", end="2020-01-01")

    assert isinstance(result, RegimeResult)
    assert isinstance(result.labels, pd.Series)
    assert isinstance(result.confidence, pd.Series)
    assert isinstance(result.transition_matrix, pd.DataFrame)

@patch("src.regimes.pipeline.get_price_data")
@patch("src.regimes.pipeline.multi_tickers")
def test_pipeline_confidence_is_bounded(mock_multi, mock_single):
    mock_multi.return_value = _make_macro_df(500)
    mock_single.return_value = _make_price_series(500)

    result = run_regime_pipeline()

    assert (result.confidence >= 0).all()
    assert (result.confidence <= 1).all()

@patch("src.regimes.pipeline.get_price_data")
@patch("src.regimes.pipeline.multi_tickers")
def test_pipeline_label_names_collect_labels(mock_multi, mock_single):
    mock_multi.return_value = _make_macro_df(500)
    mock_single.return_value = _make_price_series(500)

    result = run_regime_pipeline()
    names= result.label_names()

    assert set(names.unique()).issubset({"risk-on", "neutral", "risk-off"})



# test actual data with full pipeline. pytest -m integration
@pytest.mark.integration
def test_live_pipeline():
    result = run_regime_pipeline(start="2010-01-01", end="2020-12-31")
    
    assert len(result.labels) > 1000
    assert set(result.labels.unique()).issubset({0,1,2})