from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from backend.app.repositories.data_repository import DataRepository
from backend.app.core.exceptions import DataValidationError
from backend.app.api.v1.schemas.data import (
    SalesSummaryResponse, 
    SalesSummaryRequest, 
    SalesSummaryWrapper,
    ActiveAccountsResponse,
    ActiveAccountsRequest,
    ActiveAccountsWrapper,
    NumberOfProductResponse,
    NumberOfProductRequest,
    NumberOfProductWrapper
)
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
            raise DataValidationError("Date range cannot exceed 5 years")      
        
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
            logger.error(f"MySQL procedure error in get_sales_summary: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        
        
    async def get_active_accounts(
        self, 
        request: ActiveAccountsRequest
    ) -> ActiveAccountsWrapper:
        """
        활성 계정 통계 조회
        
        비즈니스 로직:
        1. 날짜 검증 (최대 5년)
        2. 활성 계정 데이터 조회
        
        Args:
            request: 활성 계정 조회 요청
            
        Returns:
            일자별 활성 계정 수 및 누적 활성 계정 수
        """
        start_date = request.start_date
        end_date = request.end_date
        
        # 1. 날짜 검증
        if end_date < start_date:
            raise DataValidationError("End date must be after start date")
        
        if (end_date - start_date).days > 1825:
            raise DataValidationError("Date range cannot exceed 5 years")
        
        # 2. 활성 계정 데이터 조회 (MySQL 프로시저 호출)
        try:
            results = await self.data_repo.get_active_accounts(start_date, end_date)
            
            return ActiveAccountsWrapper(
                success=True,
                count=len(results),
                data=[
                    ActiveAccountsResponse(
                        created_date=r["created_date"],
                        daily_active_accounts=int(r["daily_active_accounts"]),
                        cumulative_active_accounts=int(r["cumulative_active_accounts"])
                    )
                    for r in results
                ]
            )
        
        except DataValidationError:
            # 비즈니스 로직 에러는 그대로 전파
            raise
        except Exception as e:
            logger.error(f"MySQL procedure error in get_active_accounts: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    
    async def get_number_of_product_sold(
        self,
        request: NumberOfProductRequest
    ) -> NumberOfProductWrapper:
        """
        일자별 품목별 판매 식수 조회
        
        비즈니스 로직:
        1. 날짜 검증 (최대 5년)
        2. 일자별 품목별 판매 식수 데이터 조회        
        
        Args:
            request: 일자별 품목별 판매 식수 조회 요청
            
        Returns:
            일자별 품목별 판매 식수 및 금액
        """        
        start_date = request.start_date
        end_date = request.end_date
        is_grouped = request.is_grouped
        
        # 1. 날짜 검증
        if end_date < start_date:
            raise DataValidationError("End date must be after start date")
        
        if (end_date - start_date).days > 1825:
            raise DataValidationError("Date range cannot exceed 5 years")        

        # 2. 일자별 품목별 판매 식수 데이터 조회 (MySQL 프로시저 호출)
        try:
            results = await self.data_repo.get_number_of_product_sold(start_date, end_date,is_grouped)
            
            return NumberOfProductWrapper(
                success=True,
                count=len(results),
                data=[
                    NumberOfProductResponse(
                        delivery_date=r["delivery_date"],
                        product_name=r["product_name"],
                        total_quantity=int(r["total_quantity"]),
                        total_amount=int(r["total_amount"])
                    )
                    for r in results
                ]
            )
        
        except DataValidationError:
            # 비즈니스 로직 에러는 그대로 전파
            raise
        except Exception as e:
            logger.error(f"MySQL procedure error in get_number_of_product_sold: {e}")
            raise HTTPException(status_code=500, detail=str(e))