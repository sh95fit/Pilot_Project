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
    subscription_date: str = Field(..., description="생성일")
    daily_new_accounts: int = Field(..., description="일별 활성 계정 수")
    cumulative_active_accounts: int = Field(..., description="누적 활성 계정 수")
    
    class Config:
        # datetime을 자동으로 문자열로 변환
        json_encoders = {
            'date': lambda v: v.isoformat() if v else None
        }

class ActiveAccountsWrapper(BaseModel):
    """활성 계정 응답 래퍼"""
    success: bool = Field(default=True, description="성공 여부")
    count: int = Field(..., description="결과 개수")
    data: List[ActiveAccountsResponse] = Field(..., description="활성 계정 데이터")


class NumberOfProductResponse(BaseModel):
    """일자별 품목별 판매 식수 응답"""
    delivery_date: str = Field(..., description="배송일")
    product_name: str = Field(..., description="품목명")
    total_quantity: int = Field(..., description="총 판매 수량")
    total_amount: int = Field(..., description="총 판매 금액")
    
class NumberOfProductRequest(BaseModel):
    """일자별 품목별 판매 식수 조회 요청"""
    start_date: date = Field(..., description="조회 시작일")
    end_date: date = Field(..., description="조회 종료일")
    is_grouped: bool = Field(..., description="조회형태(0:분리,1:통합)")

class NumberOfProductWrapper(BaseModel):
    """일자별 품목별 판매 식수 응답 래퍼"""
    success: bool = Field(default=True, description="성공 여부")
    count: int = Field(..., description="결과 개수")
    data: List[NumberOfProductResponse] = Field(..., description="품목별 판매 식수 데이터")    