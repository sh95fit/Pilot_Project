from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
import asyncio
from datetime import datetime

router = APIRouter()

# Pydantic 모델
class BusinessMetrics(BaseModel):
    revenue: float
    customers: int
    conversion_rate: float
    timestamp: datetime

class SalesData(BaseModel):
    period: str
    sales: float
    target: float
    growth_rate: float

class DashboardResponse(BaseModel):
    metrics: BusinessMetrics
    sales_data: List[SalesData]
    status: str

# 샘플 데이터 생성 함수
async def get_sample_metrics() -> BusinessMetrics:
    # 실제로는 데이터베이스나 외부 API에서 데이터를 가져옴
    return BusinessMetrics(
        revenue=125000.50,
        customers=1250,
        conversion_rate=3.2,
        timestamp=datetime.now()
    )

async def get_sample_sales_data() -> List[SalesData]:
    return [
        SalesData(period="2024-01", sales=45000, target=50000, growth_rate=12.5),
        SalesData(period="2024-02", sales=52000, target=50000, growth_rate=15.6),
        SalesData(period="2024-03", sales=48000, target=55000, growth_rate=8.3),
    ]

# API 엔드포인트
@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_data():
    """대시보드 메인 데이터를 가져옵니다."""
    try:
        metrics, sales_data = await asyncio.gather(
            get_sample_metrics(),
            get_sample_sales_data()
        )
        
        return DashboardResponse(
            metrics=metrics,
            sales_data=sales_data,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/metrics", response_model=BusinessMetrics)
async def get_metrics():
    """비즈니스 메트릭을 가져옵니다."""
    return await get_sample_metrics()

@router.get("/sales", response_model=List[SalesData])
async def get_sales_data(period: Optional[str] = None):
    """매출 데이터를 가져옵니다."""
    sales_data = await get_sample_sales_data()
    
    if period:
        sales_data = [data for data in sales_data if data.period == period]
        
    return sales_data

@router.post("/sales", response_model=SalesData)
async def create_sales_record(sales_data: SalesData):
    """새로운 매출 레코드를 생성합니다."""
    # 실제로는 데이터베이스에 저장
    return sales_data