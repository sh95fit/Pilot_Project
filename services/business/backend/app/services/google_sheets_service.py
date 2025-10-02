from typing import List
from datetime import datetime
from backend.app.repositories.google_sheets_repository import GoogleSheetsRepository
from backend.app.core.database.google_sheets_client import GoogleSheetsClient
from backend.app.core.exceptions import DataValidationError
from backend.app.api.v1.schemas.google_sheets import (
    MetricDashboardRequest,
    MetricDashboardAllRequest,
    MetricDashboardResponse,
    MetricData
)
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """Google Sheets 서비스"""
    
    def __init__(self, google_sheets_client: GoogleSheetsClient):
        self.sheets_repo = GoogleSheetsRepository(google_sheets_client)
    
    async def get_metric_dashboard_all(
        self,
        request: MetricDashboardAllRequest,
        spreadsheet_id: str
    ) -> MetricDashboardResponse:
        """메트릭 대시보드 전체 조회"""
        try:
            records = await self.sheets_repo.get_metric_dashboard_data(
                spreadsheet_id=spreadsheet_id,
                worksheet_name=request.worksheet_name,
                start_period=None,
                end_period=None
            )
            
            metric_data = [
                MetricData(
                    period=record['period'],
                    lead_count=record['lead_count'],
                    trial_conversion=record['trial_conversion'],
                    subscription_conversion=record['subscription_conversion']
                )
                for record in records
            ]
            
            return MetricDashboardResponse(
                success=True,
                count=len(metric_data),
                data=metric_data,
                message=f"Successfully retrieved all {len(metric_data)} records"
            )
            
        except Exception as e:
            logger.error(f"Failed to get all metric dashboard: {e}")
            raise
    
    async def get_metric_dashboard_by_period(
        self,
        request: MetricDashboardRequest,
        spreadsheet_id: str
    ) -> MetricDashboardResponse:
        """메트릭 대시보드 기간별 조회"""
        
        # 기간 형식 검증
        try:
            datetime.strptime(request.start_period, '%Y-%m')
        except ValueError:
            raise DataValidationError("start_period must be YYYY-MM format")
        
        try:
            datetime.strptime(request.end_period, '%Y-%m')
        except ValueError:
            raise DataValidationError("end_period must be YYYY-MM format")
        
        if request.start_period > request.end_period:
            raise DataValidationError("start_period must be before end_period")
        
        try:
            records = await self.sheets_repo.get_metric_dashboard_data(
                spreadsheet_id=spreadsheet_id,
                worksheet_name=request.worksheet_name,
                start_period=request.start_period,
                end_period=request.end_period
            )
            
            metric_data = [
                MetricData(
                    period=record['period'],
                    lead_count=record['lead_count'],
                    trial_conversion=record['trial_conversion'],
                    subscription_conversion=record['subscription_conversion']
                )
                for record in records
            ]
            
            return MetricDashboardResponse(
                success=True,
                count=len(metric_data),
                data=metric_data,
                message=f"Retrieved {len(metric_data)} records from {request.start_period} to {request.end_period}"
            )
            
        except Exception as e:
            logger.error(f"Failed to get metric dashboard by period: {e}")
            raise