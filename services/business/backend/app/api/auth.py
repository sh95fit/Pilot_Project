from fastapi import APIRouter, HTTPException, Depends, Response, Request, status
from pydantic import BaseModel, EmailStr
from typing import Dict, Any
import logging

from backend.app.services.auth_service import AuthService
from backend.app.core.security import get_current_user_from_cookie
from backend.app.models.auth import (
    LoginRequest, LoginResponse, TokenRefreshResponse, 
    LogoutResponse, UserInfoResponse
)

from shared.auth.jwt_handler import JWTHandler
from shared.auth.crypto import CryptoHandler
from shared.auth.cognito_client import CognitoClient
from shared.database.supabase_client import SupabaseClient
from shared.database.redis_client import RedisClient
from backend.app.core.dependencies.auth import (
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
    사용자 로그아웃 - 쿠키와 헤더 모두 지원
    """
    
    # 1. 쿠키에서 session_id 시도
    session_id = request.cookies.get("session_id")
    access_token = request.cookies.get("access_token")

    # 2. 쿠키가 없으면 헤더에서 시도 (Streamlit 환경 대응)
    if not session_id:
        cookie_header = request.headers.get("cookie", "")
        if cookie_header:
            cookies = {}
            for item in cookie_header.split(';'):
                if '=' in item:
                    key, value = item.strip().split('=', 1)
                    cookies[key] = value
            session_id = cookies.get('session_id')
            access_token = cookies.get('access_token')
    
    if not session_id:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail="No active session found"
        )
        
    try:
        # Streamlit 환경을 위한 토큰 기반 로그아웃도 지원
        if access_token and session_id:
            result = await AuthService.logout_with_tokens(
                access_token=access_token,
                session_id=session_id,
                response=response,
                redis_client=redis_client,
                supabase_client=supabase_client
            )
        else:
            # 기존 방식 (쿠키만 있는 경우)
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
    토큰 갱신 - 쿠키와 헤더 모두 지원 (Streamlit 헤더 처리를 위한 추가)
    """
    
    # 1. 쿠키에서 session_id 시도
    session_id = request.cookies.get("session_id")
    
    # 2. 쿠키가 없으면 헤더에서 시도 (Streamlit 환경 대응)
    if not session_id:
        cookie_header = request.headers.get("cookie", "")
        if cookie_header:
            cookies = {}
            for item in cookie_header.split(';'):
                if '=' in item:
                    key, value = item.strip().split('=', 1)
                    cookies[key] = value
            session_id = cookies.get('session_id')
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No session ID found"
        )
    
    try:
        success, token_info = await AuthService.refresh_tokens(
            session_id=session_id,
            response=response,
            redis_client=redis_client,
            supabase_client=supabase_client,
            crypto_handler=crypto_handler,
            cognito_client=cognito_client,
            jwt_handler=jwt_handler
        )
        
        if success:
            # 기본 응답
            refresh_response = {
                "success": True,
                "message": "Tokens refreshed successfully",
                
            }
            
            # Streamlit 환경을 위한 토큰 정보 추가
            if token_info:
                refresh_response["tokens"] = token_info
            
            return TokenRefreshResponse(**refresh_response)
        else:
            # 실패 시 HTTP 401 반환 (Refresh Token 만료)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired or invalid"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh route error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.get("/me")
async def get_current_user(
    request: Request,
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    redis_client: RedisClient = Depends(get_redis_client),
    supabase_client: SupabaseClient = Depends(get_supabase_client)
) -> Dict[str, Any]:
    """
    현재 사용자 정보 조회 - 쿠키와 헤더 모두 지원
    """
    try:
        current_user = None
        
        # 1. 쿠키 방식 시도
        try:
            current_user = await get_current_user_from_cookie(
                request, jwt_handler, redis_client, supabase_client
            )
        except HTTPException:
            pass
        
        # 2. 쿠키가 없으면 헤더 방식 시도 (Streamlit 환경 대응)
        if not current_user:
            auth_result = await AuthService.check_auth_with_headers(
                request, redis_client, supabase_client, jwt_handler
            )
            if auth_result and auth_result.get("authenticated"):
                current_user = {
                    "sub": auth_result.get("user_id"),
                    "session_id": auth_result.get("session_id"),
                    "roles": auth_result.get("roles", ["user"])
                }
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # 사용자 정보 조회
        user_info = await AuthService.get_current_user_info(
            current_user, supabase_client
        )
        
        # 프론트엔드가 기대하는 구조로 응답
        return {
            "success": True,
            "user_info": user_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user info route error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user info"
        )

@router.get("/check")
async def check_auth(
    request: Request,
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    redis_client: RedisClient = Depends(get_redis_client),
    supabase_client: SupabaseClient = Depends(get_supabase_client)
) -> Dict[str, Any]:
    """
    인증 상태 확인 - 쿠키와 헤더 모두 지원
    """
    try:
        # 1. 기존 쿠키 방식 시도
        try:
            user = await get_current_user_from_cookie(
                request,
                jwt_handler=jwt_handler,
                redis_client=redis_client,
                supabase_client=supabase_client,
            )
            
            return {
                "authenticated": True, 
                "user_id": user.get("sub"),
                "session_id": user.get("session_id"),
                "roles": user.get("roles", ["user"])
            }
        except HTTPException:
            pass  # 쿠키 방식 실패시 헤더 방식 시도
    
        # 2. Streamlit 환경을 위한 헤더 방식 시도
        auth_result = await AuthService.check_auth_with_headers(
            request, redis_client, supabase_client, jwt_handler
        )
        
        if auth_result:
            return auth_result
        else:
            return {"authenticated": False, "error": "Invalid or expired token"}    
    
        
    except HTTPException:
        return {"authenticated": False, "error": "Invalid or expired token"}
    except Exception as e:
        logger.warning(f"Auth check error: {e}")
        return {"authenticated": False, "error": "Authentication check failed"}

@router.post("/revoke-all-sessions")
async def revoke_all_sessions(
    request: Request,
    response: Response,
    supabase_client: SupabaseClient = Depends(get_supabase_client),
    redis_client: RedisClient = Depends(get_redis_client),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> Dict[str, Any]:
    """
    현재 사용자의 모든 세션 무효화 - 쿠키와 헤더 모두 지원
    """
    try:
        # 현재 사용자 정보 가져오기 (쿠키 또는 헤더에서)
        current_user = None
        
        try:
            # 1. 쿠키 방식 시도
            current_user = await get_current_user_from_cookie(
                request, jwt_handler, redis_client, supabase_client
            )
        except HTTPException:
            # 2. 헤더 방식 시도
            auth_result = await AuthService.check_auth_with_headers(
                request, redis_client, supabase_client, jwt_handler
            )
            if auth_result and auth_result.get("authenticated"):
                current_user = {
                    "sub": auth_result.get("user_id"),
                    "session_id": auth_result.get("session_id"),
                    "roles": auth_result.get("roles", ["user"])
                }
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
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
        
        
        

# Streamlit 전용 엔드포인트 예시

class StreamlitTokenRefreshRequest(BaseModel):
    """Streamlit 환경을 위한 토큰 갱신 요청"""
    access_token: str
    session_id: str


class StreamlitLogoutRequest(BaseModel):
    """Streamlit 환경을 위한 로그아웃 요청"""
    access_token: str
    session_id: str
    
@router.post("/streamlit/refresh", response_model=TokenRefreshResponse)
async def streamlit_refresh(
    token_data: StreamlitTokenRefreshRequest,
    response: Response,
    redis_client: RedisClient = Depends(get_redis_client),
    supabase_client: SupabaseClient = Depends(get_supabase_client),
    crypto_handler: CryptoHandler = Depends(get_crypto_handler),
    cognito_client: CognitoClient = Depends(get_cognito_client),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> TokenRefreshResponse:
    """Streamlit 전용 토큰 갱신 (JSON body로 토큰 전달)"""
    try:
        success, token_info = await AuthService.refresh_tokens(
            session_id=token_data.session_id,
            response=response,
            redis_client=redis_client,
            supabase_client=supabase_client,
            crypto_handler=crypto_handler,
            cognito_client=cognito_client,
            jwt_handler=jwt_handler
        )
        
        if success:
            refresh_response = {
                "success": True,
                "message": "Tokens refreshed successfully"
            }
            
            if token_info:
                refresh_response["tokens"] = token_info
            
            return TokenRefreshResponse(**refresh_response)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh tokens"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Streamlit token refresh error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/streamlit/logout")
async def streamlit_logout(
    token_data: StreamlitLogoutRequest,
    response: Response,
    redis_client: RedisClient = Depends(get_redis_client),
    supabase_client: SupabaseClient = Depends(get_supabase_client)
) -> LogoutResponse:
    """Streamlit 전용 로그아웃 (JSON body로 토큰 전달)"""
    try:
        result = await AuthService.logout_with_tokens(
            access_token=token_data.access_token,
            session_id=token_data.session_id,
            response=response,
            redis_client=redis_client,
            supabase_client=supabase_client
        )
        
        return LogoutResponse(**result)
    
    except Exception as e:
        logger.error(f"Streamlit logout error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/streamlit/check")
async def streamlit_check_auth(
    token_data: StreamlitTokenRefreshRequest,  # access_token, session_id 필요
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    redis_client: RedisClient = Depends(get_redis_client),
    supabase_client: SupabaseClient = Depends(get_supabase_client)
) -> Dict[str, Any]:
    """Streamlit 전용 인증 확인 (JSON body로 토큰 전달)"""
    try:
        # 토큰 검증
        try:
            payload = jwt_handler.verify_token(token_data.access_token)
            token_session_id = payload.get('jti')
            
            # 세션 ID 일치 확인
            if token_session_id != token_data.session_id:
                return {"authenticated": False, "error": "Session ID mismatch"}
            
            # 세션 유효성 확인
            session_data = await AuthService._get_session_data(
                token_data.session_id, redis_client, supabase_client
            )
            
            if not session_data:
                return {"authenticated": False, "error": "Invalid session"}
            
            return {
                "authenticated": True,
                "user_id": payload.get("sub"),
                "session_id": token_data.session_id,
                "roles": payload.get("roles", ["user"])
            }
            
        except ValueError as e:
            return {"authenticated": False, "error": f"Token validation failed: {str(e)}"}
            
    except Exception as e:
        logger.error(f"Streamlit auth check error: {e}")
        return {"authenticated": False, "error": "Authentication check failed"}