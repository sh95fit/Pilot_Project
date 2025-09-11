from pydantic import BaseModel, EmailStr
from typing import Dict, Any

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    user: Dict[str, Any]