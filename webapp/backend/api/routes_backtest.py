# webapp/backend/api/routes_backtest.py

# API routes for backtest jobs
# Same submit/list/get/delete pattern as the regime and ranking routes
# Execution logic is in services/backtest_service.py


from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from webapp.backend.schemas.backtest import BacktestRequest
from webapp.backend.schemas.tasks import TaskResponse, TaskResultResponse
from webapp.backend.services.backtest_service import execute_backtest

router = APIRouter(prefix="/api/backtest", tags=["backtest"])

# Converts a TaskRecord to the right response model
# include_result=True adds the result payload, used by the by-ID endpoint
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

# Submit a new backtest job - returns the task_id immediately
@router.post("/", response_model=TaskResponse)
def submit_backtest(req: BacktestRequest, request: Request):
    tm = request.app.state.task_manager
    params = req.model_dump()
    task_id = tm.submit(
        "backtest",
        params,
        execute_backtest,
        req.start,
        req.end,
        req.risk_level,
        req.rebalance_freq,
        req.n_estimators
    )
    return _task_to_response(tm.get_task(task_id))

# List all backtest tasks (status only, no results)
@router.get("/", response_model=list[TaskResponse])
def list_backtests(request: Request):
    tm = request.app.state.task_manager
    return [_task_to_response(t) for t in tm.list_tasks("backtest")]

# Get a task by ID - includes the result once the job is done
@router.get("/{task_id}", response_model=TaskResultResponse)
def get_backtest(task_id: str, request: Request):
    task = request.app.state.task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    return _task_to_response(task, include_result=True)

# Delete a task by ID
@router.delete("/{task_id}")
def delete_backtest(task_id: str, request: Request):
    if not request.app.state.task_manager.delete_task(task_id):
        raise HTTPException(404, "Task not found")
    return {"deleted": True}
