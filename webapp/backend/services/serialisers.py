# webapp/backend/services/serialisers.py
#
# Converts quant_engine dataclass results into JSON dicts for the API.
#
# Time-series convention used are: 
# {"dates": ["2020-01-02", "2020-01-03, ..."], "values": [1.23, 1.45, ...]}
#
# Parallel arrays are used rather than {date: value} maps for recharts.
#
# NaN and Inf values are replaced with None ( _clean() ) because they are not JSON and would cause serialisation errors.

from __future__ import annotations

import math
from typing import Any

import pandas as pd


# Helper to replace NaN / Inf with None so JSON serialisation doesn't break
def _clean(val: Any) -> Any:
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val


# Convert a pandas Series to {dates, values} parallel arrays
def series_to_json(s: pd.Series) -> dict:
    return {
        "dates": s.index.strftime("%Y-%m-%d").tolist(),
        "values": [_clean(v) for v in s.values.tolist()]
    }


# Convert a pandas DataFrame to {dates, columns} where each column is an array
def dataframe_to_json(df: pd.DataFrame) -> dict:
    result = {
        "dates": df.index.strftime("%Y-%m-%d").tolist(),
        "columns": {}
    }
    for col in df.columns:
        result["columns"][col] = [_clean(v) for v in df[col].values.tolist()]
    return result


# Regime 

# Serialise a RegimeResult to a JSON-safe dict
# The GMM and scaler objects are dropped - sklearn models aren't useful to the frontend
def serialise_regime_result(r) -> dict:
    return {
        "labels": series_to_json(r.labels),
        "confidence": series_to_json(r.confidence),
        "label_names": series_to_json(r.label_names()),
        "transition_matrix": {
            "labels": [str(c) for c in r.transition_matrix.columns],
            "values": r.transition_matrix.values.tolist(),
        },
        "benchmark_prices": series_to_json(r.benchmark_prices),
        "macro_prices": dataframe_to_json(r.macro_prices)
    }


# Ranking

# Serialise a RankingTrainResult to a JSON-safe dict
def serialise_ranking_result(r) -> dict:
    return {
        "cv_hit_rate_mean": r.cv_hit_rate_mean,
        "cv_hit_rate_std": r.cv_hit_rate_std,
        "cv_log_loss_mean": r.cv_log_loss_mean,
        "feature_importances": {
            "features": r.feature_importances.index.tolist(),
            "values": r.feature_importances.values.tolist(),
        },
        "etf_names": r.etf_names
    }


# Backtest

# Serialise a BacktestResult to a JSON-safe dict
# Embeds the full regime result so the frontend gets everything in one response
def serialise_backtest_result(r) -> dict:
    return {
        "portfolio_returns": series_to_json(r.portfolio_returns),
        "benchmark_returns": series_to_json(r.benchmark_returns),
        "turnover": series_to_json(r.turnover),
        "weights_schedule": dataframe_to_json(r.weights_schedule),
        "stats": {k: _clean(v) for k, v in r.stats.items()},
        "regime": serialise_regime_result(r.regime_result)
    }
