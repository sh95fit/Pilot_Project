from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from backend.app.celery_app.tasks import cohort_tasks
from backend.app.celery_app.celery_config import celery_app

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/celery", tags=["celery"])


class TaskResponse(BaseModel):
    task_id: str
    task_name: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/tasks/cohort/not-ordered", response_model=TaskResponse)
async def trigger_not_ordered_cohort():
    """미주문 고객사 코호트 업데이트 태스크 수동 실행"""
    try:
        task = cohort_tasks.update_not_ordered_cohort.delay()
        
        return TaskResponse(
            task_id=task.id,
            task_name="update_not_ordered_cohort",
            status="PENDING",
            message="Task has been queued"
        )
    except Exception as e:
        logger.error(f"Failed to trigger NOT ORDERED cohort task: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """태스크 실행 상태 조회"""
    try:
        task_result = celery_app.AsyncResult(task_id)
        
        response = TaskStatusResponse(
            task_id=task_id,
            status=task_result.status
        )
        
        if task_result.ready():
            if task_result.successful():
                response.result = task_result.result
            elif task_result.failed():
                response.error = str(task_result.info)
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workers/stats")
async def get_worker_stats():
    """Celery Worker 상태 조회"""
    try:
        # Active tasks
        active_tasks = celery_app.control.inspect().active()
        
        # Registered tasks
        registered_tasks = celery_app.control.inspect().registered()
        
        # Queue stats
        stats = celery_app.control.inspect().stats()
        
        return {
            "active_tasks": active_tasks,
            "registered_tasks": registered_tasks,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get worker stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workers/purge")
async def purge_all_tasks():
    """모든 대기 중인 태스크 제거 (주의: 신중하게 사용)"""
    try:
        purged_count = celery_app.control.purge()
        
        return {
            "message": "Tasks purged successfully",
            "purged_count": purged_count
        }
    except Exception as e:
        logger.error(f"Failed to purge tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))