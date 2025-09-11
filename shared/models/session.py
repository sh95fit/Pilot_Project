from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
import uuid


class UserSession(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    session_id: str
    refresh_token_enc: str
    refresh_expires_at: datetime
    revoked: bool = False
    device_info: Optional[Dict[str, Any]] = None
    created_at: datetime
    last_used_at: datetime


class SessionCreate(BaseModel):
    user_id: uuid.UUID
    session_id: str
    refresh_token_enc: str
    refresh_expires_at: datetime
    device_info: Optional[Dict[str, Any]] = None