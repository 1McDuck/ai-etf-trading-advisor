# quant_engine/src/data/ingestion.py
#
# Market data ingestion using yfinance, aligned to the NYSE trading calendar.
#
# All price data in the pipeline goes through here.
# Series are reindexed to NYSE trading dates and forward-filled to fill any gaps.

import yfinance as yf
import pandas as pd
import pandas_market_calendars as mcal

# Macro market indicators used as inputs to the regime detection feature set
MACRO_TICKERS = {
    "VIX": "^VIX", # Volatility Index - fear/greed sentiment gauge
    "GOLD": "GC=F", # Gold futures - traditional safe haven asset
    "USDIDX": "DX-Y.NYB", # US Dollar Index - cross-asset risk signal
    "US10Y": "^TNX" # 10y US Treasury yield - interest rate regime indicator
}

# MSCI World index used as the benchmark for regime detection and performance comparison
BENCHMARK_TICKER = "^990100-USD-STRD"

# The nine sectorised ETFs that make up the investable ETF universe for the strategy
SECTOR_ETFS = {
    "Technology": "XLK",
    "Financials": "XLF",
    "Healthcare": "XLV",
    "ConsumerDiscretionary": "XLY",
    "ConsumerStaples": "XLP",
    "Industrials": "XLI",
    "Energy": "XLE",
    "Materials": "XLB",
    "Utilities": "XLU"
}


# Return the official NYSE trading date range between start and end
# Uses pandas_market_calendars to get the correct trading days (no weekends/holidays)
# Timestamps are normalised to midnight so they align with yfinance output
def _get_nyse_trading_dates(start: str, end: str) -> pd.DatetimeIndex:
    nyse = mcal.get_calendar("NYSE")
    schedule = nyse.schedule(start_date=start, end_date=end)
    return mcal.date_range(schedule, frequency="1D").normalize().tz_localize(None)


# Download adjusted closing prices for a single ticker from yfinance
# The series is reindexed to the NYSE calendar and forward-filled for any gaps
# Raises ValueError if yfinance returns no data for the ticker
def get_price_data(ticker: str, start: str, end: str) -> pd.Series:
    trading_dates = _get_nyse_trading_dates(start, end)
    yf_data = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
    if yf_data.empty:
        raise ValueError(f"No data for ticker: {ticker}")

    close = yf_data["Close"]

    # yfinance sometimes returns a DataFrame with one column instead of a Series
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    prices = close.squeeze()
    prices.index = pd.to_datetime(prices.index).normalize()
    prices.name = ticker

    # Align to NYSE calendar and forward-fill any missing trading days
    prices = prices.reindex(trading_dates).ffill()

    return prices


# Download adjusted closing prices for multiple tickers in a single call
# Batching all tickers into one yfinance request is faster than calling get_price_data() in a loop
# Columns are renamed from Yahoo Finance symbols to the friendly names in the tickers dict
# Raises ValueError if yfinance returns no data for the requested tickers
def multi_tickers(tickers: dict[str, str], start: str, end: str) -> pd.DataFrame:
    ticker_list = list(tickers.values())
    name_map = {v: k for k, v in tickers.items()}
    trading_dates = _get_nyse_trading_dates(start, end)

    yf_data = yf.download(ticker_list, start=start, end=end, progress=False, auto_adjust=True)
    if yf_data.empty:
        raise ValueError(f"No data for ticker: {ticker_list}")

    close = yf_data["Close"]

    close.index = pd.to_datetime(close.index).normalize()
    close = close.reindex(trading_dates).ffill()

    # Rename columns from ticker symbols to the friendly names for readability
    close = close.rename(columns=name_map)

    return close
