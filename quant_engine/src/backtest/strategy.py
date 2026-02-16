# quant_engine/src/backtest/strategy.py

# Strategy layers, generation of the portfolio weights schedule

# for each rebalance date, the strategy:
# - Looks up the current regime label
# - Extracts the feature row for each ETF
# - Gets the outperformance probailities from the trained ranker
# - Passes in rankings and regime to the portfolio constructor

# Returns a pd.Dataframe weights_schedule that feeds into the backtesting engine

# Rebalance frequency: Monthly (21 days) hardcoded for testing defaults.
# No look ahead, only the feature row for the current date is used

from __future__ import annotations

import pandas as pd

from sklearn.ensemble import RandomForestClassifier

from src.portfolio.constructor import build_portfolio
from src.prediction.pipeline import FEATURE_COLUMNS


REBALANCE_FREQ = 21 # trading days per month

def build_weights_schedule(
    wide_features: pd.DataFrame,
    regime_labels: pd.Series,
    model: RandomForestClassifier,
    etf_names: list[str],
    risk_level: str = "moderate",
    rebalance_freq: int = REBALANCE_FREQ
) -> pd.DataFrame:
    # Generate the monthly rebalance weights schedule:
    # - wide_features: daily feature matrix from build_etf_features
    # - regime_labels: smoothed ints regime for each date
    # - model: trained RandomForestClassifier from prediction pipeline
    # - etf_names: list of ETF column names
    # - risk_level: 'moderate' by default, selectable
    # - reblance_freq: days between rebalance

    # return pd.Dataframe indexed by rebal dates, columns = etf_names, values = weights

    common_dates = wide_features.index.intersection(regime_labels.index)
    rebalance_dates = common_dates[::rebalance_freq]

    rows = []
    for date in rebalance_dates:
        regime = int(regime_labels.loc[date])

        # build a one row long format feature matrix for all ETFS on this date
        etf_rows = []
        for etf in etf_names:
            feat_cols = {
                "mom_1m": f"{etf}_mom_1m",
                "mom_3m": f"{etf}_mom_3m",
                "vol_1m": f"{etf}_vol_1m",
                "vol_3m": f"{etf}_vol_3m",
                "rel_str_3m": f"{etf}_rel_str_3m"
            }
            row = {short: wide_features.loc[date, full] for short, full in feat_cols.items() if full in wide_features.columns}
            row["regime"] = regime
            etf_rows.append(row)

        X = pd.DataFrame(etf_rows, index=etf_names)[FEATURE_COLUMNS]

        # Get outperformance probabilities, fix nans
        if X.isna().any().any():
            weights = pd.Series(1.0/len(etf_names), index=etf_names)
        else:
            probability = model.predict_proba(X)[:,1]
            rankings = pd.Series(probability, index=etf_names).sort_values(ascending=False)
            weights = build_portfolio(regime, rankings, risk_level=risk_level)

        rows.append(weights.rename(date))

    return pd.DataFrame(rows)

