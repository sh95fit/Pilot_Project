from pydantic import BaseModel
from typing import List, Optional

class ProcedureRequest(BaseModel):
    procedure_name: str
    params: Optional[List] = None
    db_name: Optional[str] = None