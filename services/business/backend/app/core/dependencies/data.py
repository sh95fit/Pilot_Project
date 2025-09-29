from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from backend.app.core.database import database_manager

security = HTTPBearer()

async def get_db() :
    """
    DB 매니저 의존성
    
    모든 엔드포인트에서 재사용
    """
    if not database_manager._initialized:
        await database_manager.initialize()
    return database_manager
