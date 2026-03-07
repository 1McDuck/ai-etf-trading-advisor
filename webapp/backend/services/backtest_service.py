# webapp/backend/services/backtest_service.py

# calls quant_engine backtest pipeline

from __future__ import annotations

import os
import sys

# Add the quant_engine directory to the Python path so we can import the backtest pipeline function
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "quant_engine"))

from quant_engine.src.backtest.pipeline import run_full_backtest  # noqa: E402

from webapp.backend.services.serialisers import serialise_backtest_result  # noqa: E402

# Run the backtest and return a serialised dict for the API
def execute_backtest(start: str, end: str | None, risk_level: str, rebalance_freq: int, n_estimators: int) -> dict:
    result = run_full_backtest(
        start=start,
        end=end,
        risk_level=risk_level,
        rebalance_freq=rebalance_freq,
        n_estimators=n_estimators
    )
    
    return serialise_backtest_result(result)
