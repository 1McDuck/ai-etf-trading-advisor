# webapp/backend/schemas/ranking.py
#
# Pydantic request model for POST /api/ranking/
# Just a date range - the ranking pipeline handles the rest.

from __future__ import annotations

from pydantic import BaseModel, Field


class RankingRequest(BaseModel):
    start: str = Field(default="2000-01-01", pattern=r"^\d{4}-\d{2}-\d{2}$")
    end: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
