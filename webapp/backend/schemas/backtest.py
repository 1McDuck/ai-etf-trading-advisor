from __future__ import annotations

from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    start: str = Field(default="2000-01-01", pattern=r"^\d{4}-\d{2}-\d{2}$")
    end: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    risk_level: str = Field(default="moderate", pattern=r"^(conservative|moderate|aggressive)$")
    rebalance_freq: int = Field(default=20, ge=1, le=240)
    n_estimators: int = Field(default=300, ge=50, le=1000)
