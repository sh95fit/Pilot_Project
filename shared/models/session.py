from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
import uuid


class UserSession(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    session_id: str = Field(..., description="Unique session identifier")
    refresh_token_enc: str = Field(..., description="Encrypted refresh token")
    refresh_expires_at: datetime
    revoked: bool = Field(default=False)
    device_info: Optional[Dict[str, Any]] = Field(default=None)
    device_key: Optional[str] = Field(default=None, description="Cognito Device Key")
    device_group_key: Optional[str] = Field(default=None, description="Cognito Device Group Key")
    created_at: datetime
    last_used_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            uuid.UUID: str
        }

    @field_validator('device_info')
    @classmethod
    def validate_device_info(cls, v):
        if v is None:
            return {}
        
        # 필수 필드 확인 및 기본값 설정
        default_info = {
            'ip_address': 'unknown',
            'user_agent': 'unknown'
        }
        
        if isinstance(v, dict):
            default_info.update(v)
            return default_info
        
        return default_info


class SessionCreate(BaseModel):
    user_id: uuid.UUID
    session_id: str = Field(..., description="Unique session identifier")
    refresh_token_enc: str = Field(..., description="Encrypted refresh token")
    refresh_expires_at: datetime
    device_info: Optional[Dict[str, Any]] = Field(default=None)
    device_key: Optional[str] = Field(default=None, description="Cognito Device Key")
    device_group_key: Optional[str] = Field(default=None, description="Cognito Device Group Key")

    @field_validator('device_info')
    @classmethod
    def validate_device_info(cls, v):
        if v is None:
            return {}
        
        # 필수 필드 확인 및 기본값 설정
        default_info = {
            'ip_address': 'unknown',
            'user_agent': 'unknown'
        }
        
        if isinstance(v, dict):
            default_info.update(v)
            return default_info
        
        return default_info

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            uuid.UUID: str
        }