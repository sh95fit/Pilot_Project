from fastapi import APIRouter, HTTPException, Depends
import logging
from backend.app.core.config import settings
from backend.app.core.database.google_sheets_client import GoogleSheetsClient
from backend.app.services.google_sheets_service import GoogleSheetsService
from backend.app.api.v1.schemas.google_sheets import (
    MetricDashboardRequest,
    MetricDashboardAllRequest,
    MetricDashboardResponse
)
from backend.app.core.exceptions import DataValidationError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/google-sheets", tags=["google-sheets"])

def get_google_sheets_service() -> GoogleSheetsService:
    """Google Sheets 서비스 의존성"""
    try:
        credentials = settings.google_sheets_credentials_sales
        if not credentials:
            raise HTTPException(
                status_code=500,
                detail="Google Sheets credentials not configured"
            )
        
        client = GoogleSheetsClient(credentials)
        return GoogleSheetsService(client)
    except Exception as e:
        logger.error(f"Failed to initialize Google Sheets service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check(
    service: GoogleSheetsService = Depends(get_google_sheets_service)
):
    """Google Sheets 연결 상태 확인"""
    try:
        is_healthy = service.sheets_repo.sheets.health_check()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "service": "Google Sheets"
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/metric-dashboard/all", response_model=MetricDashboardResponse)
async def get_all_metric_dashboard(
    request: MetricDashboardAllRequest,
    service: GoogleSheetsService = Depends(get_google_sheets_service)
):
    """
    메트릭 대시보드 전체 데이터 조회
    
    spreadsheet_id는 환경변수에서 자동으로 가져옵니다
    """
    try:
        spreadsheet_id = settings.google_sheet_id_sales
        if not spreadsheet_id:
            raise HTTPException(status_code=500, detail="Spreadsheet ID not configured")
        
        result = await service.get_metric_dashboard_all(request, spreadsheet_id)
        return result
    except DataValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get all metric dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/metric-dashboard/period", response_model=MetricDashboardResponse)
async def get_metric_dashboard_by_period(
    request: MetricDashboardRequest,
    service: GoogleSheetsService = Depends(get_google_sheets_service)
):
    """
    메트릭 대시보드 기간별 데이터 조회
    
    spreadsheet_id는 환경변수에서 자동으로 가져옵니다
    """
    try:
        spreadsheet_id = settings.google_sheet_id_sales
        if not spreadsheet_id:
            raise HTTPException(status_code=500, detail="Spreadsheet ID not configured")
        
        result = await service.get_metric_dashboard_by_period(request, spreadsheet_id)
        return result
    except DataValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get metric dashboard by period: {e}")
        raise HTTPException(status_code=500, detail=str(e))