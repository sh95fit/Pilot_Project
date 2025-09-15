from fastapi import APIRouter, HTTPException, Depends, Response, Request, status
from pydantic import BaseModel, EmailStr
from typing import Dict, Any
import logging

from ..services.auth_service import AuthService
from ..core.security import get_current_user_from_cookie
from ..models.auth import (
    LoginRequest, LoginResponse, TokenRefreshResponse, 
    LogoutResponse, UserInfoResponse
)

from shared.auth.jwt_handler import JWTHandler
from shared.auth.crypto import CryptoHandler
from shared.auth.cognito_client import CognitoClient
from shared.database.supabase_client import SupabaseClient
from shared.database.redis_client import RedisClient
from ..core.dependencies import (
    get_cognito_client, 
    get_supabase_client, 
    get_redis_client, 
    get_jwt_handler, 
    get_crypto_handler
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    response: Response,
    request: Request,
    cognito_client: CognitoClient = Depends(get_cognito_client),
    supabase_client: SupabaseClient = Depends(get_supabase_client),
    redis_client: RedisClient = Depends(get_redis_client),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    crypto_handler: CryptoHandler = Depends(get_crypto_handler)
) -> LoginResponse:
    """
    사용자 로그인
    """
    try:
        result = await AuthService.login(
            email=login_data.email,
            password=login_data.password,
            response=response,
            request=request,
            cognito_client=cognito_client,
            supabase_client=supabase_client,
            redis_client=redis_client,
            jwt_handler=jwt_handler,
            crypto_handler=crypto_handler
        )
        
        return LoginResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login route error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/logout")
async def logout(
    response: Response, 
    request: Request,
    redis_client: RedisClient = Depends(get_redis_client),
    supabase_client: SupabaseClient = Depends(get_supabase_client)
) -> LogoutResponse:
    """
    사용자 로그아웃
    """
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail="No active session found"
        )
        
    try:
        result = await AuthService.logout(
            session_id=session_id,
            response=response,
            redis_client=redis_client,
            supabase_client=supabase_client
        )
        
        return LogoutResponse(**result)
    
    except Exception as e:
        logger.error(f"Logout route error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh(
    response: Response, 
    request: Request,
    redis_client: RedisClient = Depends(get_redis_client),
    supabase_client: SupabaseClient = Depends(get_supabase_client),
    crypto_handler: CryptoHandler = Depends(get_crypto_handler),
    cognito_client: CognitoClient = Depends(get_cognito_client),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> TokenRefreshResponse:
    """
    토큰 갱신
    """
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No session ID found"
        )
    
    try:
        success = await AuthService.refresh_tokens(
            session_id=session_id,
            response=response,
            redis_client=redis_client,
            supabase_client=supabase_client,
            crypto_handler=crypto_handler,
            cognito_client=cognito_client,
            jwt_handler=jwt_handler
        )
        
        if success:
            return TokenRefreshResponse(
                success=True, 
                message="Tokens refreshed successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh tokens"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh route error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.get("/me", response_model=UserInfoResponse)
async def get_current_user(
    current_user: Dict[str, Any] = Depends(get_current_user_from_cookie),
    supabase_client: SupabaseClient = Depends(get_supabase_client)
) -> UserInfoResponse:
    """
    현재 사용자 정보 조회
    """
    try:
        user_info = await AuthService.get_current_user_info(
            current_user, supabase_client
        )
        return UserInfoResponse(**user_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user info route error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user info"
        )

@router.get("/check")
async def check_auth(request: Request) -> Dict[str, Any]:
    """
    인증 상태 확인
    """
    try:
        # 의존성을 수동으로 가져와서 예외 상황도 정상 응답으로 처리
        jwt_handler = get_jwt_handler()
        redis_client = get_redis_client()
        supabase_client = get_supabase_client()

        user = await get_current_user_from_cookie(
            request,
            jwt_handler=jwt_handler,
            redis_client=redis_client,
            supabase_client=supabase_client,
        )

        return {
            "authenticated": True, 
            "user_id": user.get("sub"),
            "session_id": user.get("session_id")
        }
        
    except HTTPException:
        return {"authenticated": False, "error": "Invalid or expired token"}
    except Exception as e:
        logger.warning(f"Auth check error: {e}")
        return {"authenticated": False, "error": "Authentication check failed"}

@router.post("/revoke-all-sessions")
async def revoke_all_sessions(
    current_user: Dict[str, Any] = Depends(get_current_user_from_cookie),
    supabase_client: SupabaseClient = Depends(get_supabase_client),
    redis_client: RedisClient = Depends(get_redis_client),
    response: Response = None
) -> Dict[str, Any]:
    """현재 사용자의 모든 세션 무효화"""
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user information"
            )
        
        # 모든 사용자 세션 무효화
        success = await supabase_client.revoke_all_user_sessions(user_id)
        
        if success:
            # 현재 세션 쿠키도 삭제
            if response:
                AuthService._clear_auth_cookies(response)
            
            return {"success": True, "message": "All sessions revoked successfully"}
        else:
            return {"success": False, "message": "Failed to revoke sessions"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke all sessions error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke sessions"
        )