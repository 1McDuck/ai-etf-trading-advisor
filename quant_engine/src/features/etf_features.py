# quant_engine/src/features/etf_features.py
#
# Builds the supervised feature matrix used by the ETF ranking model.
#
# For each sector ETF the following features are calculated on a rolling basis:
# - Momentum (1mth and 3mth): cumulative log return over the window
# - Volatility (1mth and 3mth): rolling standard deviation of daily log returns
# - Relative strength (3mth): ETF 3mth momentum minus benchmark 3mth momentum
#
# The regime label from the GMM is also joined in as a numeric feature, giving the
# model information about the prevailing market environment at each point in time.
#
# All calculations use only past data so there is no lookahead bias.
# Rows with insufficient history (NaNs from the rolling windows) are dropped.

from __future__ import annotations

import numpy as np
import pandas as pd

# Window sizes in trading days
O_MONTH = 21 # approx 1 calendar month
T_MONTH = 63 # approx 3 calendar months


# Build the wide format feature matrix for all sector ETFs
# Each row is a trading day: columns are {ETF}_mom_1m, {ETF}_mom_3m, {ETF}_vol_1m,
# {ETF}_vol_3m, {ETF}_rel_str_3m for every ETF, plus a shared regime column
# The wide format is later reshaped to long format in the prediction pipeline for model training
def build_etf_features(
        etf_prices: pd.DataFrame,
        benchmark: pd.Series,
        regime_labels: pd.Series
) -> pd.DataFrame:
    # etf_prices: DataFrame of daily close prices, columns = ETF names
    # benchmark: Series of daily benchmark close prices (MSCI World)
    # regime_labels: Series of integer regime labels aligned to the same date index
    # returns: DataFrame with one row per trading day, NaN rows dropped

    # Calculate daily log returns for ETFs and the benchmark
    etf_log = np.log(etf_prices / etf_prices.shift(1))
    bench_log = np.log(benchmark / benchmark.shift(1))

    # Benchmark 3mth cumulative return - used to calculate relative strength for each ETF
    bench_mom_3m = bench_log.rolling(T_MONTH).sum()

    parts: list[pd.DataFrame] = []

    for etf in etf_prices.columns:
        etf_return = etf_log[etf]
        df = pd.DataFrame(index=etf_prices.index)

        # Momentum: cumulative log return over each window
        df[f"{etf}_mom_1m"] = etf_return.rolling(O_MONTH).sum()
        df[f"{etf}_mom_3m"] = etf_return.rolling(T_MONTH).sum()

        # Volatility: rolling standard deviation of daily log returns
        df[f"{etf}_vol_1m"] = etf_return.rolling(O_MONTH).std()
        df[f"{etf}_vol_3m"] = etf_return.rolling(T_MONTH).std()

        # Relative strength: how much the ETF has outperformed the benchmark over 3 months
        df[f"{etf}_rel_str_3m"] = df[f"{etf}_mom_3m"] - bench_mom_3m

        parts.append(df)

    features = pd.concat(parts, axis=1)

    # Join the integer regime label as a shared feature column across all ETFs
    features = features.join(regime_labels.rename("regime"), how="inner")

    # Drop rows where any rolling window has not filled yet (early dates)
    return features.dropna()
