from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import uuid

class User(BaseModel):
    id: uuid.UUID
    email: EmailStr
    cognito_sub: str = Field(..., description="Cognito User Sub ID")
    display_name: Optional[str] = Field(None, max_length=100)
    role: str = Field(default="user", pattern=r"^(admin|user|manager)$")
    is_active: bool = Field(default=True)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            uuid.UUID: str
        }

    @field_validator('display_name')
    @classmethod
    def validate_display_name(cls, v):
        if v and len(v.strip()) == 0:
            return None
        return v.strip() if v else None


class UserCreate(BaseModel):
    email: EmailStr
    cognito_sub: str = Field(..., description="Cognito User Sub ID")
    display_name: Optional[str] = Field(None, max_length=100)
    role: str = Field(default="user", pattern=r"^(admin|user|manager)$")

    @field_validator('display_name')
    @classmethod
    def validate_display_name(cls, v):
        if v and len(v.strip()) == 0:
            return None
        return v.strip() if v else None

    class Config:
        json_encoders = {
            uuid.UUID: str
        }