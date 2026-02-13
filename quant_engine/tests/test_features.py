# Tests for regime and ETF features

import numpy as np
import pandas as pd
import pytest

from src.features.regime_features import build_regime_features

def _make_price_series(n: int=500, seed: int=0) -> pd.Series:
    rng = np.random.default_rng(seed)
    log_rets = rng.normal(0.0003, 0.01, size=n) 
    prices = 100 * np.exp(np.cumsum(log_rets))
    idx = pd.bdate_range("2010-01-01", periods=n)

    return pd.Series(prices, index=idx, name="price")

def test_build_regime_features_shape():
    msci = _make_price_series(500, seed=0)
    gold = _make_price_series(500, seed=1)
    eurusd = _make_price_series(500, seed=2)
    vix = _make_price_series(500, seed=3) * 0.1 + 15

    features = build_regime_features(msci, gold, eurusd, vix)

    assert isinstance(features, pd.DataFrame)
    assert len(features) > 0


def test_build_regime_features_columns():
    msci = _make_price_series(500, seed=0)
    gold = _make_price_series(500, seed=1)
    eurusd = _make_price_series(500, seed=2)
    vix = _make_price_series(500, seed=3) * 0.1 + 15

    features = build_regime_features(msci, gold, eurusd, vix)

    expected = {
        "msci_ret_1m",
        "msci_ret_3m",
        "msci_ret_12m",
        "msci_vol_1m",
        "msci_vol_3m",
        "msci_vol_12m",
        "vix_level_1m",
        "gold_mom_3m",
        "eurusd_mom_3m"     
    }

    assert expected.issubset(set(features.columns))