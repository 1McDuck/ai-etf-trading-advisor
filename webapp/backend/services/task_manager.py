# webapp/backend/services/task_manager.py


from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

# Task status enum - maps to the string values used in the API response
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

# Stores everything about a single task run
@dataclass
class TaskRecord:
    task_id: str
    task_type: str
    status: TaskStatus
    created_at: datetime
    completed_at: datetime | None = None
    params: dict = field(default_factory=dict)
    result: Any = None
    error: str | None = None

# Thread pool backed task queue.
# Runs pipeline jobs in the background so the API doesn't block.
class TaskManager:

    def __init__(self, max_workers: int = 2):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks: dict[str, TaskRecord] = {}
        self._futures: dict[str, Future] = {}

    def submit(self, task_type: str, params: dict, fn: Callable, *args: Any) -> str:
        task_id = str(uuid.uuid4())
        record = TaskRecord(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            params=params
        )
        
        self._tasks[task_id] = record
        future = self._executor.submit(self._run_task, task_id, fn, *args)
        self._futures[task_id] = future
        return task_id

    def _run_task(self, task_id: str, fn: Callable, *args: Any) -> None:
        record = self._tasks[task_id]
        record.status = TaskStatus.RUNNING
        try:
            record.result = fn(*args)
            record.status = TaskStatus.COMPLETED
        except Exception as exc:
            record.status = TaskStatus.FAILED
            record.error = str(exc)
        finally:
            record.completed_at = datetime.now(timezone.utc)

    def get_task(self, task_id: str) -> TaskRecord | None:
        return self._tasks.get(task_id)

    def list_tasks(self, task_type: str | None = None) -> list[TaskRecord]:
        tasks = list(self._tasks.values())
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def delete_task(self, task_id: str) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            self._futures.pop(task_id, None)
            return True
        return False

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False)
