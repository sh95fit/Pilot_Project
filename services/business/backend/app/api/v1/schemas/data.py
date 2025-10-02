from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class ProcedureRequest(BaseModel):
    procedure_name: str
    params: Optional[List] = None
    db_name: Optional[str] = None
    
class SalesSummaryResponse(BaseModel):
    period_label: str
    period_type: str  # month / year / total
    total_amount_sum: float

class SalesSummaryWrapper(BaseModel):
    success: bool
    count: int
    data: List[SalesSummaryResponse]

class SalesSummaryRequest(BaseModel):
    start_date: date
    end_date: date
    
    
class ActiveAccountsRequest(BaseModel):
    """활성 계정 조회 요청"""
    start_date: date = Field(..., description="조회 시작일")
    end_date: date = Field(..., description="조회 종료일")

class ActiveAccountsResponse(BaseModel):
    """활성 계정 응답 (단일 레코드)"""
    created_date: str = Field(..., description="생성일")
    daily_active_accounts: int = Field(..., description="일별 활성 계정 수")
    cumulative_active_accounts: int = Field(..., description="누적 활성 계정 수")

class ActiveAccountsWrapper(BaseModel):
    """활성 계정 응답 래퍼"""
    success: bool = Field(default=True, description="성공 여부")
    count: int = Field(..., description="결과 개수")
    data: List[ActiveAccountsResponse] = Field(..., description="활성 계정 데이터")
