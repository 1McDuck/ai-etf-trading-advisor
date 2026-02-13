# quant_engine/src/data/ingestion.py

# Market data gathering using yfinance alligning with nyse calendar


import yfinance as yf
import pandas as pd
import pandas_market_calendars as mcal

MACRO_TICKERS = {
    "VIX": "^VIX",
    "GOLD": "GC=F",
    "EURUSD": "EURUSD=X",
    "US10Y": "^TNX"
}

BENCHMARK_TICKER = "^990100-USD-STRD"

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



def _get_nyse_trading_dates(start: str, end: str) -> pd.DateTimeIndex:
    nyse = mcal.get_calendar("NYSE")
    schedule = nyse.schedule(start_date=start, end_date=end)
    return mcal.date_range(schedule, frequency="1D").normalize().tz_localize(None)



def get_price_data(ticker: str, start: str, end: str) -> pd.Series:
    trading_dates = _get_nyse_trading_dates(start, end)
    yf_data = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
    if yf_data.empty:
        raise ValueError(f"No data for ticker: {ticker}")
    
    close = yf_data["Close"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:,0]
    
    prices = close.squeeze()
    prices.index = pd.to_datetime(prices.index).normalize()
    prices.name = ticker
    prices = prices.reindex(trading_dates).ffill()

    return prices


def multi_tickers(tickers: dict[str, str], start: str, end: str) -> pd.DataFrame:
    ticker_list = list(tickers.values())
    name_map = {v: k for k,v in tickers.items()}
    trading_dates = _get_nyse_trading_dates(start, end)

    yf_data = yf.download(ticker_list, start=start, end=end, progress=False, auto_adjust=True)
    if yf_data.empty:
        raise ValueError(f"No data for ticker: {ticker_list}")

    close = yf_data["Close"]

    close.index = pd.to_datetime(close.index).normalize()
    close = close.reindex(trading_dates).ffill()
    close = close.rename(columns=name_map)
    
    return close



