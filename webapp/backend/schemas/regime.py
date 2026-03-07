# webapp/backend/schemas/regime.py
#
# Pydantic request model for POST /api/regime/
# n_regimes is locked to 3 for now - more makes the output hard to interpret.

from __future__ import annotations

from pydantic import BaseModel, Field


class RegimeRequest(BaseModel):
    start: str = Field(default="2000-01-01", pattern=r"^\d{4}-\d{2}-\d{2}$")
    end: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    n_regimes: int = Field(default=3, ge=3, le=3)
    smooth_window: int = Field(default=5, ge=1, le=20)
