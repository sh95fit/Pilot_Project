from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, Any, List
import logging
from ...core.database import database_manager
from ...models.data import ProcedureRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/data", tags=["data"])

@router.get("/health")
async def health_check():
    """데이터베이스 연결 상태 확인"""
    try:
        health_status = await database_manager.health_check()
        all_healthy = all(health_status.values())
        
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "databases": health_status
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@router.post("/get_min_order_summary")
async def execute_mysql_procedure(
    request: ProcedureRequest
):
    """MySQL 프로시저 실행"""
    try:
        result = await database_manager.mysql.execute_procedure(
            proc_name=request.procedure_name,
            params=tuple(request.params) if request.params else None,
            db_name=request.db_name
        )
        
        return {
            "success": True,
            "data": result,
            "count": len(result)
        }
        
    except Exception as e:
        logger.error(f"MySQL procedure error: {e}")
        raise HTTPException(status_code=500, detail=str(e))