from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
import uuid


class User(BaseModel):
    id: uuid.UUID
    email: EmailStr
    cognito_sub: str
    display_name: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    cognito_sub: str
    display_name: Optional[str] = None
    role: str = "user"