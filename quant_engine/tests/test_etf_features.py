

import numpy as np
import pandas as pd

from src.features.etf_features import build_etf_features

ETF_NAMES = ["XLK", "XLF", "XLE"]



def _make_prices(n: int=300, etfs: list[str] = ETF_NAMES, seed: int=0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2010-01-01", periods=n)
    data = {}
    for etf in etfs:
        log_rets = rng.normal(0.003,0.01, size=n)
        data[etf] = 100 * np.exp(np.cumsum(log_rets))
    
    return pd.DataFrame(data, index=idx)


def _make_benchmark(n: int=300, seed: int=99) -> pd.Series:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2010-01-01", periods=n)
    log_rets = rng.normal(0.003,0.01, size=n)

    return pd.Series(100 * np.exp(np.cumsum(log_rets)), index=idx, name="bench")


def _make_regime_labels(n: int=300) -> pd.Series:
    rng = np.random.default_rng(7)
    idx = pd.bdate_range("2010-01-01", periods=n)

    return pd.Series(rng.integers(0,3,size=n), index=idx, name="regime")


def test_output_is_dataframe():
    etf = _make_prices()
    bench = _make_benchmark()
    regimes = _make_regime_labels()
    result = build_etf_features(etf, bench, regimes)

    assert isinstance(result, pd.DataFrame)

def test_no_non_in_output():
    etf = _make_prices()
    bench = _make_benchmark()
    regimes = _make_regime_labels()
    result = build_etf_features(etf, bench, regimes)

    assert result.isna().sum().sum() == 0


def test_expected_columns_present():
    etf = _make_prices()
    bench = _make_benchmark()
    regimes = _make_regime_labels()
    result = build_etf_features(etf, bench, regimes)

    for etf_name in ETF_NAMES:
        for suffix in ["mom_1m", "mom_3m", "vol_1m", "vol_3m", "rel_str_3m"]:
            assert f"{etf_name}_{suffix}" in result.columns, f"Missing column: {etf_name}_{suffix}"
        
    assert "regime" in result.columns

def test_regime_column_values_match_input():
    etf = _make_prices()
    bench = _make_benchmark()
    regimes = _make_regime_labels()
    result = build_etf_features(etf, bench, regimes)

    assert set(result["regime"].unique()).issubset(set(regimes.unique()))

def test_output_shorter_than_input():
    n = 300
    etf = _make_prices(n)
    bench = _make_benchmark(n)
    regimes = _make_regime_labels(n)
    result = build_etf_features(etf, bench, regimes)

    assert len(result) < n


def test_volatility_is_not_negative():
    etf = _make_prices()
    bench = _make_benchmark()
    regimes = _make_regime_labels()
    result = build_etf_features(etf, bench, regimes)

    vol_columns = [c for c in result.columns if "_vol_" in c]

    assert (result[vol_columns] >= 0).all().all()