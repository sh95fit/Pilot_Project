from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any


class TokenInfo(BaseModel):
    """토큰 정보"""
    access_token: str
    session_id: str
    expires_in: int


class TokenRefreshResponse(BaseModel):
    """토큰 갱신 응답"""
    success: bool
    message: str
    tokens: Optional[TokenInfo] = None  # Streamlit 환경용 토큰 정보


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginResponse(BaseModel):
    success: bool
    message: str
    user: Optional[Dict[str, Any]] = None
    tokens: Optional[TokenInfo] = None


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