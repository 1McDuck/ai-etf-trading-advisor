# quant_engine/src/portfolio/constructor.py

# Engine for portfolio construction
# Takes in the regime label and the etf ranking and produces target allocations

# Reimge Logic:
# risk-on (0): overweight top X sectors by rank
# neutral (1): equal-weight all sectors
# risk-off (2): underweight bottom X sectors

# Inpurts:
# - regime: int regime label (0,1,2)
# - etf_rankings: pd.Series, the outperform_prob per sector ETF
# - risk_level: 3 risk levels, conservative, moderate, aggressive

# Out:
# pd.Series of allocation weights

from __future__ import annotations

import numpy as np
import pandas as pd

REGIME_RISK_ON = 0
REGIME_NEUTRAL = 1
REGIME_RISK_OFF = 2

def build_portfolio(
    regime: int,
    etf_rankings: pd.Series,
    risk_level: str = "moderate"
) -> pd.Series:
    n = len(etf_rankings)
    names = etf_rankings.index.tolist()

    if regime == REGIME_NEUTRAL:
        weights = np.ones(n)/n
    
    elif regime == REGIME_RISK_ON:
        top_n = {"conservative": 3, "moderate": 2, "aggressive": 1}[risk_level]
        weights = np.zeros(n)
        top_idx = [names.index(etf) for etf in etf_rankings.head(top_n).index]
        for i in top_idx:
            weights[i] = 1.0/top_n

    else: # REGIME_RISK_OFF
        bottom_n = {"conservative": 3, "moderate": 2, "aggressive": 1}[risk_level]
        bottom_names = set(etf_rankings.tail(bottom_n).index)
        included = [etf for etf in names if etf not in bottom_names]
        weights = np.zeros(n)
        for etf in included:
            weights[names.index(etf)] = 1.0 / len(included)

    result = pd.Series(weights, index=names, name="weight")

    return result