from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginResponse(BaseModel):
    success: bool
    message: str
    user: Optional[Dict[str, Any]] = None
    tokens: Optional[Dict[str, str]] = None


class TokenRefreshResponse(BaseModel):
    success: bool
    message: str


class LogoutResponse(BaseModel):
    success: bool
    message: str


class UserInfoResponse(BaseModel):
    id: str
    email: EmailStr
    display_name: Optional[str]
    role: str
    created_at: str
    is_active: bool