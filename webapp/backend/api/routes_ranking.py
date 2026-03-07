# webapp/backend/api/routes_ranking.py

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from webapp.backend.schemas.ranking import RankingRequest
from webapp.backend.schemas.tasks import TaskResponse, TaskResultResponse
from webapp.backend.services.ranking_service import execute_ranking

router = APIRouter(prefix="/api/ranking", tags=["ranking"])

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

# Submit a new ranking job - returns task_id immediately
@router.post("/", response_model=TaskResponse)
def submit_ranking(req: RankingRequest, request: Request):
    tm = request.app.state.task_manager
    params = req.model_dump()
    task_id = tm.submit("ranking", params, execute_ranking, req.start, req.end)
    return _task_to_response(tm.get_task(task_id))

# List all ranking tasks (status only)
@router.get("/", response_model=list[TaskResponse])
def list_rankings(request: Request):
    tm = request.app.state.task_manager
    return [_task_to_response(t) for t in tm.list_tasks("ranking")]

# Get a task by ID - includes the result once the job is done
@router.get("/{task_id}", response_model=TaskResultResponse)
def get_ranking(task_id: str, request: Request):
    task = request.app.state.task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    return _task_to_response(task, include_result=True)
