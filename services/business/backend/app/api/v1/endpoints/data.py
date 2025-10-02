from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, Any, List
import logging
from backend.app.core.database import database_manager
from backend.app.api.v1.schemas.data import (
    ProcedureRequest, 
    SalesSummaryWrapper, 
    SalesSummaryRequest,
    ActiveAccountsWrapper,
    ActiveAccountsRequest
)
from backend.app.core.exceptions import DataValidationError
from backend.app.core.dependencies.data import get_db
from backend.app.services.data_service import DataService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data", tags=["data"])

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
async def get_min_order_summary(
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
    

# @router.post("/get_sales_summary", response_model=SalesSummaryWrapper)
# async def get_sales_summary(
#     request: ProcedureRequest
# ):
#     """매출 요약 조회 (MySQL 프로시저 호출)"""
#     try:
#         result = await database_manager.mysql.execute_procedure(
#             proc_name=request.procedure_name,
#             params=tuple(request.params) if request.params else None,
#             db_name=request.db_name
#         )
        
#         return {
#             "success": True,
#             "count": len(result or []),
#             "data": result
#         }
#     except Exception as e:
#         logger.error(f"MySQL procedure error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

    

# 파일 분리 예시 (base.py -> data_repository.py -> data_service.py -> endpoints/data.py)
@router.post("/get_sales_summary", response_model=SalesSummaryWrapper)
async def get_sales_summary(
    request: SalesSummaryRequest,
    db = Depends(get_db)
): 
    """
    매출 요약 통계 조회
    
    - 날짜 범위: 최대 5년
    - 반환: 기간별 매출 합계
    """
    service = DataService(db)
    
    try:
        result = await service.get_sales_summary(request)
        return result
    except DataValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get_active_accounts", response_model=ActiveAccountsWrapper)
async def get_active_accounts(
    request: ActiveAccountsRequest,
    db = Depends(get_db)
):
    """
    활성 계정 통계 조회
    
    - 날짜 범위: 최대 5년
    - 반환: 일자별 활성 계정 수 및 누적 활성 계정 수
    - 제외 대상: 테스트, 런치랩, 도준선 계정
    """
    service = DataService(db)
    
    try:
        result = await service.get_active_accounts(request)
        return result
    except DataValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Active accounts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))