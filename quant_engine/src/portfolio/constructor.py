# quant_engine/src/portfolio/constructor.py
#
# Portfolio construction rules based on the current market regime.
#
# The strategy adjusts how aggressively it concentrates or diversifies the
# portfolio depending on both the detected regime and the investor's risk preference.
#
# Regime logic:
# "risk-on": Concentrate into the top N highest-ranked ETFs. The model
#            expects momentum to persist, so we bet on the leaders.
# "neutral": Equal-weight all ETFs. No clear directional signal, so spread
#            the risk evenly across the full universe.
# "risk-off":Exclude the bottom N lowest-ranked ETFs (the most vulnerable sectors) 
#            and equal-weight the remaining holdings.
#
# Risk level sets N (how many ETFs to concentrate into or exclude):
#  - conservative: N=3
#  - moderate: N=2
#  - aggressive: N=1 (all-in on the top ETF, or only exclude 1)
#
# Note: regime is a string label here ("risk-on", "neutral", "risk-off") not a GMM int.
# strategy.py converts it before calling this.

from __future__ import annotations

import numpy as np
import pandas as pd


# Construct target portfolio weights given a regime label and ETF rankings
# The ETF rankings are the model's predicted outperformance probabilities,
# sorted from highest to lowest. Regime and risk level together determine
# how those rankings translate into weights.
def build_portfolio(
        regime: str,
        etf_rankings: pd.Series,
        risk_level: str = "moderate"
) -> pd.Series:
    # regime: "risk-on", "neutral", or "risk-off"
    # etf_rankings: outperformance probabilities per ETF, sorted descending
    # risk_level: "conservative", "moderate", or "aggressive"
    # returns: allocation weights indexed by ETF name (sum to 1.0, non-negative)
    n = len(etf_rankings)
    names = etf_rankings.index.tolist()

    if regime == "neutral":
        # No directional signal - spread risk evenly across all sectors
        weights = np.ones(n) / n

    elif regime == "risk-on":
        # Momentum driven: concentrate in the top ranked ETFs
        top_n = {"conservative": 3, "moderate": 2, "aggressive": 1}[risk_level]
        weights = np.zeros(n)
        top_idx = [names.index(etf) for etf in etf_rankings.head(top_n).index]
        for i in top_idx:
            weights[i] = 1.0 / top_n

    else:
        # "risk-off" (or any unrecognised label - treated as risk-off)
        # Defensive: exclude the weakest sectors and equal weight the rest
        bottom_n = {"conservative": 3, "moderate": 2, "aggressive": 1}[risk_level]
        bottom_names = set(etf_rankings.tail(bottom_n).index)
        included = [etf for etf in names if etf not in bottom_names]
        weights = np.zeros(n)
        for etf in included:
            weights[names.index(etf)] = 1.0 / len(included)

    result = pd.Series(weights, index=names, name="weight")

    return result
