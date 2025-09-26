from pydantic import BaseModel
from typing import List, Optional

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