from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from backend.app.repositories.data_repository import DataRepository
from backend.app.core.exceptions import DataValidationError
from backend.app.api.v1.schemas.data import SalesSummaryResponse, SalesSummaryRequest, SalesSummaryWrapper
import logging

logger = logging.getLogger(__name__)

class DataService:
    """
    데이터 서비스 (비즈니스 로직)
    
    책임:
    - 데이터 검증
    - 비즈니스 규칙 적용
    - Repository 조합
    - 데이터 변환
    """
    def __init__(self, db):
        self.db = db
        self.data_repo = DataRepository(db)

    async def get_sales_summary(
        self, 
        request: SalesSummaryRequest
    ) -> SalesSummaryWrapper:
        """
        매출 요약 조회
        
        비즈니스 로직:
        1. 날짜 검증 (최대 5년)
        2. 매출 데이터 조회
        """
        start_date = request.start_date
        end_date = request.end_date        
        
        # 1. 날짜 검증        
        if end_date < start_date:
            raise DataValidationError("End date must be after start date")
        
        if (end_date - start_date).days > 1825:
            raise DataValidationError("Date range cannot exceed 5 year")      
        
        """매출 요약 조회 (MySQL 프로시저 호출)"""
        try:
            results = await self.data_repo.get_sales_summary(start_date, end_date)
        
            return SalesSummaryWrapper(
                success=True,
                count=len(results),
                data=[
                    SalesSummaryResponse(
                        period_label=r["period_label"],
                        period_type=r["period_type"],
                        total_amount_sum=float(r["total_amount_sum"])  # Decimal → float 변환
                    )
                    for r in results
                ]
            )
        
        except Exception as e:
            logger.error(f"MySQL procedure error: {e}")
            raise HTTPException(status_code=500, detail=str(e))