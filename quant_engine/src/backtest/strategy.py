# quant_engine/src/backtest/strategy.py
#
# Strategy layer: converts the trained ranking model into a rebalance weight schedule.
#
# At each rebalance date this module:
# 1. Looks up the current regime (both numeric and named forms)
# 2. Builds a feature row for every ETF using data available on that date only
# 3. Asks the trained Random Forest for its predicted outperformance probability
#    for each ETF
# 4. Passes the rankings and regime label to the portfolio constructor, which
#    applies the regime-based allocation rules to produce target weights
#
# Important difference between the two regime representations:
# - regime_int (integer): the raw GMM cluster ID, used as a numeric input
#   feature for the Random Forest (must match what the model was trained on)
# - regime_str (string): the human-readable label ("risk-on", "neutral",
#   "risk-off"), used for the portfolio construction decision rules
#
# No lookahead bias: only features that are available at each rebalance date
# are used. The model is applied rowbyrow without any future information.
#
# If features are not yet available for a given date (e.g. near the start of the
# series before rolling windows fill), the portfolio falls back to equal weights.

from __future__ import annotations

import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from src.portfolio.constructor import build_portfolio
from src.prediction.pipeline import FEATURE_COLUMNS

# Default rebalance frequency in trading days (roughly 1 calendar month)
REBALANCE_FREQ = 21


# Generate the full rebalance weight schedule for the backtest period
# Selects every Nth date from the common date index as a rebalance point,
# then for each rebalance date computes the target portfolio weights by
# combining the model's predicted rankings with the current regime
def build_weights_schedule(
        wide_features: pd.DataFrame,
        regime_labels: pd.Series,
        regime_label_names: pd.Series,
        model: RandomForestClassifier,
        etf_names: list[str],
        risk_level: str = "moderate",
        rebalance_freq: int = REBALANCE_FREQ
) -> pd.DataFrame:
    # wide_features: daily feature matrix from build_etf_features()
    # regime_labels: integer GMM cluster labels indexed by date (numeric model feature)
    # regime_label_names: string regime labels indexed by date ("risk-on", "neutral", "risk-off")
    # model: trained RandomForestClassifier from the prediction pipeline
    # etf_names: list of ETF names (must match feature column prefixes)
    # risk_level: users risk preference: "conservative", "moderate", or "aggressive"
    # rebalance_freq: number of trading days between rebalances
    # returns: DataFrame indexed by rebalance dates, columns = ETF names, values = weights

    # Only use dates where both the feature matrix and regime labels are available
    common_dates    = wide_features.index.intersection(regime_labels.index)
    rebalance_dates = common_dates[::rebalance_freq]

    rows = []
    for date in rebalance_dates:
        regime_int = int(regime_labels.loc[date]) # numeric: model feature
        regime_str = str(regime_label_names.loc[date]) # named: portfolio rules

        # Build one feature row per ETF using only data available on this date
        etf_rows = []
        for etf in etf_names:
            feat_cols = {
                "mom_1m": f"{etf}_mom_1m",
                "mom_3m": f"{etf}_mom_3m",
                "vol_1m": f"{etf}_vol_1m",
                "vol_3m": f"{etf}_vol_3m",
                "rel_str_3m": f"{etf}_rel_str_3m"
            }
            row = {
                short: wide_features.loc[date, full]
                for short, full in feat_cols.items()
                if full in wide_features.columns
            }
            # The model expects the integer regime label it was trained on
            row["regime"] = regime_int
            etf_rows.append(row)

        X = pd.DataFrame(etf_rows, index=etf_names)[FEATURE_COLUMNS]

        if X.isna().any().any():
            # Feature data is incomplete - fall back to equal weighting
            weights = pd.Series(1.0 / len(etf_names), index=etf_names)
        else:
            # Predict outperformance probability for each ETF and rank them
            probability = model.predict_proba(X)[:, 1]
            rankings = pd.Series(probability, index=etf_names).sort_values(ascending=False)
            # Apply regime based allocation rules to the ranked ETFs
            weights = build_portfolio(regime_str, rankings, risk_level=risk_level)

        rows.append(weights.rename(date))

    return pd.DataFrame(rows)
