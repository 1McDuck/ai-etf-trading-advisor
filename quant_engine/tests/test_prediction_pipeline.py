# ETF rankingg test prediction
# mock network calls

from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd

from src.prediction.pipeline import wide_to_long_feature_matrix, build_targets_long, train_ranking_model, RankingTrainResult, FEATURE_COLUMNS

# HELPERS

ETF_NAMES = ["XLK", "XLF", "XLE", "XLY"]

def _make_prices(n: int=500, seed: int=0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2010-01-01", periods=n)
    prices = {etf: 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, n))) for etf in ETF_NAMES}

    return pd.DataFrame(prices, index=idx)

def _make_benchmark(n: int=500, seed: int=0) -> pd.Series:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2010-01-01", periods=n)
    bench = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.0002, 0.008, n))), index=idx)

    return bench

def _make_wide_features(n: int=500) -> pd.DataFrame:
    from src.features.etf_features import build_etf_features
    etf = _make_prices(n)
    bench = _make_benchmark(n)
    rng = np.random.default_rng(5)
    regimes = pd.Series(rng.integers(0,3, size=n), index=pd.bdate_range("2010-01-01", periods=n))
    
    return build_etf_features(etf, bench, regimes)


# wide_to_long_feature_matrix tests

def test_wide_to_long_produces_multiindex():
    wide = _make_wide_features()
    long = wide_to_long_feature_matrix(wide, ETF_NAMES)

    assert long.index.names == ["date", "etf"]

def test_wide_to_long_has_all_feature_cols():
    wide = _make_wide_features()
    long = wide_to_long_feature_matrix(wide, ETF_NAMES)

    for column in ["mom_1m", "mom_3m", "vol_1m", "vol_3m", "rel_str_3m", "regime"]:
        assert column in long.columns

def test_wide_to_long_row_count():
    wide = _make_wide_features()
    long = wide_to_long_feature_matrix(wide, ETF_NAMES)

    assert len(long) == len(wide) * len(ETF_NAMES)


# build_targets_long tests

def test_targets_binary():
    wide = _make_wide_features()
    long = wide_to_long_feature_matrix(wide, ETF_NAMES)
    etf_prices = _make_prices()
    bench = _make_benchmark()

    result = build_targets_long(long, etf_prices=etf_prices, benchmark=bench)
    
    assert set(result["target"].unique()).issubset({0,1})

def test_targets_no_NaN():
    wide = _make_wide_features()
    long = wide_to_long_feature_matrix(wide, ETF_NAMES)
    etf_prices = _make_prices()
    bench = _make_benchmark()

    result = build_targets_long(long, etf_prices=etf_prices, benchmark=bench)
    
    assert result.isna().sum().sum() == 0

def test_targets_shorter_than_features():
    wide = _make_wide_features()
    long = wide_to_long_feature_matrix(wide, ETF_NAMES)
    etf_prices = _make_prices()
    bench = _make_benchmark()

    result = build_targets_long(long, etf_prices=etf_prices, benchmark=bench)

    assert len(result) < len(long)

    
# train_ranking_model tests

def test_train_returns_result():
    wide = _make_wide_features()
    long = wide_to_long_feature_matrix(wide, ETF_NAMES)
    etf_prices = _make_prices()
    bench = _make_benchmark()
    long_with_targets = build_targets_long(long, etf_prices=etf_prices, benchmark=bench)

    result = train_ranking_model(long_with_targets, n_splits=3, n_estimators=20)

    assert isinstance(result, RankingTrainResult)

def test_cv_hit_rate_between_zero_and_one():
    wide = _make_wide_features()
    long = wide_to_long_feature_matrix(wide, ETF_NAMES)
    etf_prices = _make_prices()
    bench = _make_benchmark()
    long_with_targets = build_targets_long(long, etf_prices=etf_prices, benchmark=bench)
    
    result = train_ranking_model(long_with_targets, n_splits=3, n_estimators=20)
    
    assert 0.0 <= result.cv_hit_rate_mean <= 1.0


def test_feature_importances_sum_to_one():
    wide = _make_wide_features()
    long = wide_to_long_feature_matrix(wide, ETF_NAMES)
    etf_prices = _make_prices()
    bench = _make_benchmark()
    long_with_targets = build_targets_long(long, etf_prices=etf_prices, benchmark=bench)
    
    result = train_ranking_model(long_with_targets, n_splits=3, n_estimators=20)

    assert abs(result.feature_importances.sum() - 1.0) < 1e-9