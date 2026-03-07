# webapp/backend/services/ranking_service.py

from __future__ import annotations

import os
import sys

# Add quant_engine to the path so the imports below work
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "quant_engine"))

from quant_engine.src.prediction.pipeline import run_ranking_pipeline  # noqa: E402

from webapp.backend.services.serialisers import serialise_ranking_result  # noqa: E402

# Run the ranking pipeline and return a serialised dict for the API
def execute_ranking(start: str, end: str | None) -> dict:
    result = run_ranking_pipeline(start=start, end=end)
    return serialise_ranking_result(result)
