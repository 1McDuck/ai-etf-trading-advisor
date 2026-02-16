# quant_engine/src/features/regime_features.py

# Regime feature engineering
# Turns market prices into multi dimensional feature matrix
# used for unsupervised clustering (GMM)

# Features:
# - Trend/Momentum: rolling log returns at 1m, 3m, 12m
# - Volatility: rolling std of the log returns at 1m, 3m, 12m
# - Drawdown: 12m rolling max drawdown
# - VIX: 1m avg log vix, 1m cumulative change in log vix
# - crossasset momentum: 3m gold mom, 3m usd index mom

import numpy as np
import pandas as pd


def _log_returns(prices: pd.Series) -> pd.Series:
    return np.log(prices/prices.shift(1))


def build_regime_features(
        msci: pd.Series,
        gold: pd.Series,
        usdidx: pd.Series,
        vix: pd.Series
) -> pd.DataFrame:
    
    log_msci = _log_returns(msci)
    log_gold = _log_returns(gold)
    log_usdidx = _log_returns(usdidx)
    log_vix = _log_returns(vix)

    features: dict[str, pd.Series] = {}

    # trend/mom
    for label, window in [("1m", 20), ("3m", 60), ("12m", 240)]:
        features[f"msci_ret_{label}"] = log_msci.rolling(window).sum()
        features[f"msci_vol_{label}"] = log_msci.rolling(window).std()
    
    # drawdown
    rolling_peak = msci.rolling(240, min_periods=20).max()
    features["msci_rolling_12m"] = (msci - rolling_peak) / rolling_peak

    # VIX
    features["vix_level_1m"] = log_vix.rolling(20).mean()
    features["vix_change_1m"] = log_vix.rolling(20).sum()

    # Gold/usdidx mom
    features["gold_mom_3m"] = log_gold.rolling(60).sum()
    features["usdidx_mom_3m"] = log_usdidx.rolling(60).sum()

    df = pd.DataFrame(features, index=msci.index)

    return df.dropna()

        

