from fastapi import Depends, HTTPException, Request, status
from typing import Dict, Any, Optional

from .dependencies.auth import get_jwt_handler, get_redis_client, get_supabase_client
from shared.auth.jwt_handler import JWTHandler
from shared.database.redis_client import RedisClient
from shared.database.supabase_client import SupabaseClient


async def is_session_active(
    session_id: str,
    redis_client: RedisClient = Depends(get_redis_client),
    supabase_client: SupabaseClient = Depends(get_supabase_client)
) -> bool:
    """
    세션이 활성 상태인지 확인 (Redis 우선, DB fallback)
    """
    # 1. Redis 우선 확인
    redis_session = redis_client.get_session(session_id)
    if redis_session:
        return True

    # 2. Redis에 없으면 Supabase에서 확인
    db_session = await supabase_client.get_session(session_id)
    if db_session and not db_session.revoked:
        # Redis에 다시 캐싱 처리
        session_data = {
            "user_id": str(db_session.user_id),
            "refresh_token_enc": db_session.refresh_token_enc,
            "refresh_expires_at": db_session.refresh_expires_at.isoformat()
        }
        ttl = int((db_session.refresh_expires_at - db_session.created_at).total_seconds())
        redis_client.set_session(session_id, session_data, ttl)
        return True

    return False


async def get_current_user_from_cookie(
    request: Request,
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    redis_client: RedisClient = Depends(get_redis_client),
    supabase_client: SupabaseClient = Depends(get_supabase_client)
) -> Dict[str, Any]:
    """
    쿠키에서 access token 추출 및 검증 후 현재 사용자 정보 반환
    """
    access_token = request.cookies.get("access_token")
    session_id = request.cookies.get("session_id")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token missing"
        )

    try:
        payload = jwt_handler.verify_token(access_token)

        # 세션 유효성 확인
        jti = payload.get("jti") or session_id
        if jti and not await is_session_active(jti, redis_client, supabase_client):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session is not active"
            )

        return payload

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


async def get_optional_current_user(
    request: Request,
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    redis_client: RedisClient = Depends(get_redis_client),
    supabase_client: SupabaseClient = Depends(get_supabase_client)
) -> Optional[Dict[str, Any]]:
    """
    선택적 사용자 인증 (토큰 없어도 오류 발생하지 않음)
    """
    try:
        return await get_current_user_from_cookie(request, jwt_handler, redis_client, supabase_client)
    except HTTPException:
        return None
