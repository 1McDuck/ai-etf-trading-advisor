# quant_engine/src/features/etf_features.py

# The etf ranking logic

# Builds a supervised feature matric used by the ETF ranking model

#Features per ETF:
# - Momentum: 1m(20d) and 3m(60d)

from __future__ import annotations

import numpy as np
import pandas as pd

O_MONTH = 20
T_MONTH = 60

def build_etf_features(
    etf_prices: pd.DataFrame,
    benchmark: pd.Series,
    regime_labels: pd.Series
) -> pd.DataFrame:
    # returns pd.Dataframe with one row per trading day..

    etf_log = np.log(etf_prices/etf_prices.shift(1))
    bench_log = np.log(benchmark/benchmark.shift(1))

    bench_mom_3m = bench_log.rolling(T_MONTH).sum()

    parts: list[pd.DataFrame] = []

    for etf in etf_prices.columns:
        etf_return = etf_log[etf]
        df = pd.DataFrame(index=etf_prices.index)
        
        df[f"{etf}_mom_1m"] = etf_return.rolling(O_MONTH).sum()
        df[f"{etf}_mom_3m"] = etf_return.rolling(T_MONTH).sum()
        df[f"{etf}_vol_1m"] = etf_return.rolling(O_MONTH).std()
        df[f"{etf}_vol_3m"] = etf_return.rolling(T_MONTH).std()
        df[f"{etf}_rel_str_3m"] = df[f"{etf}_mom_3m"] - bench_mom_3m
        parts.append(df)

    features = pd.concat(parts, axis=1)

    # align with regime labels
    features = features.join(regime_labels.rename("regime"), how="inner")

    return features.dropna()