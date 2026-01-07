from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class MetricData(BaseModel):
    """월별 메트릭 데이터"""
    period: str = Field(..., description="기간 (YYYY-MM)")
    lead_count: int = Field(..., description="리드수")
    trial_conversion: int = Field(..., description="체험전환")
    subscription_conversion: int = Field(..., description="구독전환")
    end_of_use_count: int = Field(..., description="이탈수")
    

class MetricDashboardRequest(BaseModel):
    """메트릭 대시보드 조회 요청 (기간 필터링)"""
    worksheet_name: str = Field(default="System_Matrix", description="워크시트 이름")
    start_period: str = Field(..., description="시작 기간 (YYYY-MM)")
    end_period: str = Field(..., description="종료 기간 (YYYY-MM)")

class MetricDashboardAllRequest(BaseModel):
    """메트릭 대시보드 전체 조회 요청"""
    worksheet_name: str = Field(default="System_Matrix", description="워크시트 이름")

class MetricDashboardResponse(BaseModel):
    """메트릭 대시보드 응답"""
    success: bool
    count: int
    data: List[MetricData]
    message: Optional[str] = None