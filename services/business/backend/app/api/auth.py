from fastapi import APIRouter, HTTPException, Depends, Response, Request, status
from pydantic import BaseModel, EmailStr
from typing import Dict, Any
from ..services.auth_service import AuthService
from ..core.dependencies import get_current_user_from_cookie
from ..models.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    response: Response,
    request: Request
):
    """
    사용자 로그인
    """
    return await AuthService.login(
        email=login_data.email,
        password=login_data.password,
        response=response,
        request=request
    )

@router.post("/logout")
async def logout(response: Response, request: Request):
    """
    사용자 로그아웃
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail="No active session found"
        )

@router.post("/refresh")
async def refresh(response: Response, request: Request):
    """
    토큰 갱신
    """
    session_id = request.cookies.get("session_id")
    
    if not session_id :
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail="No session ID found"
        )
    
    success = await AuthService.refresh_tokens(session_id, response)
    if success:
        return {"success": True, "message": "Tokens refreshed successfully"}
    else:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh tokens"
        )

@router.get("/me")
async def get_current_user(
    current_user: Dict[str, Any] = Depends(get_current_user_from_cookie)
):
    """
    현재 사용자 정보 조회
    """
    return await AuthService.get_current_user_info(current_user)

@router.get("/check")
async def check_auth(request: Request):
    """
    인증 상태 확인
    """
    try:
        user = await get_current_user_from_cookie(request)
        return {"authenticated": True, "user": user["sub"]}
    except HTTPException:
        return {"authenticated": False}