# webapp/backend/schemas/tasks.py
#
# Pydantic response models for task endpoints.
# TaskResponse is the lightweight version (status only).
# TaskResultResponse extends it to include the result dict once the job finishes.

from __future__ import annotations

from pydantic import BaseModel


# Returned on submit and in list responses - no result payload
class TaskResponse(BaseModel):
    task_id: str
    status: str
    task_type: str
    created_at: str
    completed_at: str | None = None
    params: dict
    error: str | None = None


# Same as above but includes the result - used for the by-ID endpoint
class TaskResultResponse(TaskResponse):
    result: dict | None = None
