# webapp/backend/services/regime_service.py


from __future__ import annotations

import os
import sys

# Add quant_engine to the path so the imports below work
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "quant_engine"))

from quant_engine.src.regimes.pipeline import run_regime_pipeline # noqa: E402

from webapp.backend.services.serialisers import serialise_regime_result # noqa: E402

# Run regime detection and return a serialised dict for the API
def execute_regime(start: str, end: str | None, n_regimes: int, smooth_window: int) -> dict:
    result = run_regime_pipeline(
        start=start,
        end=end,
        n_regimes=n_regimes,
        smooth_window=smooth_window
    )
    return serialise_regime_result(result)
