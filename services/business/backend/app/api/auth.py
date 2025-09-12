from fastapi import APIRouter, HTTPException, Depends, Response, Request, status
from pydantic import BaseModel, EmailStr
from typing import Dict, Any
from ..services.auth_service import AuthService
from ..core.security import get_current_user_from_cookie
from ..models.auth import LoginRequest, LoginResponse

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
):
    """
    사용자 로그인
    """
    try:
        return await AuthService.login(
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
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login route error: {e}")
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
    ):
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
        return result
    except Exception as e:
        print(f"Logout route error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.post("/refresh")
async def refresh(
    response: Response, 
    request: Request,
    redis_client: RedisClient = Depends(get_redis_client),
    supabase_client: SupabaseClient = Depends(get_supabase_client),
    crypto_handler: CryptoHandler = Depends(get_crypto_handler),
    cognito_client: CognitoClient = Depends(get_cognito_client),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
    ):
    """
    토큰 갱신
    """
    session_id = request.cookies.get("session_id")
    
    if not session_id :
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
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
            return {"success": True, "message": "Tokens refreshed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh tokens"
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Token refresh route error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.get("/me")
async def get_current_user(
    current_user: Dict[str, Any] = Depends(get_current_user_from_cookie),
    supabase_client: SupabaseClient = Depends(get_supabase_client)
):
    """
    현재 사용자 정보 조회
    """
    try:
        return await AuthService.get_current_user_info(current_user, supabase_client)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get user info route error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user info"
        )

@router.get("/check")
async def check_auth(request: Request):
    """
    인증 상태 확인
    """
    try:
        # get_current_user_from_cookie를 직접 호출하지 말고 의존성으로 처리하는 것이 좋지만
        # 이 엔드포인트는 예외 상황도 정상 응답으로 처리해야 하므로 예외

        # 직접 호출 시 타 의존성 주입 단계에서 예외 발생
        # ex> Auth check error: 'Depends' object has no attribute 'verify_token'
        # user = await get_current_user_from_cookie(request) # 사용 불가

        # 의존성 직접 주입 대신 수동으로 가져오기
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
        return {"authenticated": False}
    except Exception as e:
        print(f"Auth check error: {e}")
        return {"authenticated": False}

