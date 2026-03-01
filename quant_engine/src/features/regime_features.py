# quant_engine/src/features/regime_features.py
#
# Builds the multi dimensional feature matrix used for unsupervised regime clustering (GMM).
#
# The idea is to describe the current market environment from several different angles
# so the GMM can separate distinct economic states (bull, bear, transition) rather than
# just clustering on a single signal like VIX level.
#
# Features constructed:
# - Trend/Momentum: rolling cumulative log returns at 1mth, 3mth, 12mth horizons
# - Volatility: rolling standard deviation of log returns at 1mth, 3mth, 12mth
# - Drawdown: 12mth rolling max drawdown (how far below the recent peak)
# - VIX level: 1mth average log VIX (captures fear/greed regime)
# - VIX change: 1mth cumulative log VIX change (captures fear acceleration)
# - Cross-asset: 3mth momentum for Gold and the USD Index (safe haven signals)
#
# All features are calcualted on a rolling basis using only past data.
# Rows with insufficient history are dropped via dropna().

import numpy as np
import pandas as pd


# Calcualte daily log returns from a price series
# Log returns are used because they are additive over time - rolling sums then
# give clean multi-period returns without compounding headaches
def _log_returns(prices: pd.Series) -> pd.Series:
    return np.log(prices / prices.shift(1))


# Construct the feature matrix for GMM regime detection
# Each row is one trading day; features capture trend, volatility, drawdown
# and cross-asset conditions simultaneously so the GMM can find structurally
# different market environments
def build_regime_features(
        msci: pd.Series,
        gold: pd.Series,
        usdidx: pd.Series,
        vix: pd.Series
) -> pd.DataFrame:
    # msci: daily MSCI World benchmark prices (equity market proxy)
    # gold: daily Gold futures prices (safe-haven demand proxy)
    # usdidx: daily US Dollar Index prices (risk appetite proxy)
    # vix: daily VIX index prices (implied volatility/fear gauge)
    # returns: DataFrame with one row per trading day, NaN rows dropped

    log_msci = _log_returns(msci)
    log_gold = _log_returns(gold)
    log_usdidx = _log_returns(usdidx)
    log_vix = _log_returns(vix)

    features: dict[str, pd.Series] = {}

    # Trend and momentum: cumulative return over 1mth, 3mth, 12mth windows
    # Volatility: standard deviation of daily returns over the same windows
    for label, window in [("1m", 21), ("3m", 63), ("12m", 252)]:
        features[f"msci_ret_{label}"] = log_msci.rolling(window).sum()
        features[f"msci_vol_{label}"] = log_msci.rolling(window).std()

    # Drawdown: how far the market is below its 12mth rolling peak
    # min_periods=20 avoids NaN at the very start of the series
    rolling_peak = msci.rolling(252, min_periods=20).max()
    features["msci_rolling_12m"] = (msci - rolling_peak) / rolling_peak

    # VIX features: average level and cumulative change over the past month
    # These two capture both the absolute fear level and whether fear is rising/falling
    features["vix_level_1m"] = log_vix.rolling(21).mean()
    features["vix_change_1m"] = log_vix.rolling(21).sum()

    # Cross-asset momentum: 3mth trend in Gold and the USD Index
    # Gold and USD tend to rise in risk-off environments, which helps
    # the GMM separate bear regimes from bull ones
    features["gold_mom_3m"] = log_gold.rolling(63).sum()
    features["usdidx_mom_3m"] = log_usdidx.rolling(63).sum()

    df = pd.DataFrame(features, index=msci.index)

    # Drop early rows where rolling windows has not got enough data yet
    return df.dropna()
