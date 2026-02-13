# Tests for data gathering. offline, network tests are mocked

from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

from src.data.ingestion import get_price_data, multi_tickers, MACRO_TICKERS

# Helpers

def _fake_data(ticker: str, n: int=60, start: str = "2020-01-01") -> pd.DataFrame:
    idx = pd.bdate_range(start, periods=n)
    prices = 100 * np.exp(np.cumsum(np.random.default_rng(42).normal(0, 0.01, n)))

    return pd.DataFrame({"Close": prices}, index=idx)

def _fake_multi_data(tickers: list[str], n: int=60) -> pd.DataFrame:
    idx = pd.bdate_range("2020-01-01", periods=n)
    arrays = [["Close"] * len(tickers), tickers]
    columns = pd.MultiIndex.from_arrays(arrays, names=["Price", "Ticker"])
    rng = np.random.default_rng(0)
    data = {t: 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n))) for t in tickers}
    df = pd.DataFrame({("Close", t): data[t] for t in tickers}, index=idx)
    df.columns = columns
    return df


# tests
@patch("src.data.ingestion.yf.download")
@patch("src.data.ingestion._get_nyse_trading_dates")
def test_get_price_data_returns_series(mock_dates, mock_download):
    idx = pd.bdate_range("2020-01-01", periods=60)
    mock_dates.return_value = idx
    mock_download.return_value = _fake_data("GC=F", n=60)

    result = get_price_data("GC=F", start="2020-01-01", end="2020-03-31")

    assert isinstance(result, pd.Series)
    assert not result.isna().any()

    
@patch("src.data.ingestion.yf.download")
@patch("src.data.ingestion._get_nyse_trading_dates")
def test_multi_tickers_returns_dataframe(mock_dates, mock_download):
    tickers = {"GOLD": "GC=F", "VIX": "^VIX"}
    ticker_values = list(tickers.values())
    idx = pd.bdate_range("2020-01-01", periods=60)
    mock_dates.return_value = idx
    mock_download.return_value = _fake_multi_data(ticker_values, n=60)

    result = multi_tickers(tickers, start="2020-01-01", end="2020-03-31")


    assert isinstance(result, pd.DataFrame)
    assert not result.isna().all().any()
    assert set(result.columns) == set(tickers.keys())

