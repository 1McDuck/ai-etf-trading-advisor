# webapp/backend/api/routes_regime.py

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from webapp.backend.schemas.regime import RegimeRequest
from webapp.backend.schemas.tasks import TaskResponse, TaskResultResponse
from webapp.backend.services.regime_service import execute_regime

router = APIRouter(prefix="/api/regime", tags=["regime"])


# Same helper as routes_backtest.py
def _task_to_response(task, include_result: bool = False):
    cls = TaskResultResponse if include_result else TaskResponse
    return cls(
        task_id=task.task_id,
        status=task.status.value,
        task_type=task.task_type,
        created_at=task.created_at.isoformat(),
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        params=task.params,
        error=task.error,
        **({"result": task.result} if include_result else {})
    )

# Submit a new regime detection job - returns task_id immediately
@router.post("/", response_model=TaskResponse)
def submit_regime(req: RegimeRequest, request: Request):
    tm = request.app.state.task_manager
    params = req.model_dump()
    task_id = tm.submit(
        "regime",
        params,
        execute_regime,
        req.start,
        req.end,
        req.n_regimes,
        req.smooth_window
    )
    return _task_to_response(tm.get_task(task_id))

# List all regime tasks (status only)
@router.get("/", response_model=list[TaskResponse])
def list_regimes(request: Request):
    tm = request.app.state.task_manager
    return [_task_to_response(t) for t in tm.list_tasks("regime")]

# Get a task by ID - includes the result once the job is done
@router.get("/{task_id}", response_model=TaskResultResponse)
def get_regime(task_id: str, request: Request):
    task = request.app.state.task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    return _task_to_response(task, include_result=True)
