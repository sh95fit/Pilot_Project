from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from ..services.auth_service import AuthService
from ..core.security import get_current_user_from_cookie, get_optional_current_user
import json

class AuthMiddleware(BaseHTTPMiddleware):
    """
    인증 미들웨어 - 토큰 자동 갱신 처리
    """
    def __init__(self, app, excluded_paths: list = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            '/health',
            '/docs',
            '/redocs',
            '/openapi.json',
            '/auth/login'
        ]
        
    async def dispatch(self, request: Request, call_next):
        # 제외된 경로는 미들웨어 통과
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # 보호된 API 경로인지 확인
        if request.url.path.startswith("/api"):
            try:
                # 토큰 검증 시도
                user_payload = await get_current_user_from_cookie(request)
                # 검증 성공 시 사용자 정보를 request state에 저장
                request.state.user = user_payload
            
            except HTTPException as e :
                if e.status_code == 401 :
                    # 토큰이 만료되었거나 없는 경우 refresh 시도
                    session_id = request.cookies.get("session_id")
                    
                    if session_id:
                        response = Response()
                        refresh_success = await AuthService.refresh_tokens(session_id, response)
                        
                        if refresh_success:
                            # 새 토큰으로 다시 검증
                            try:
                                # 새로 설정된 쿠키를 request에 반영하여 재검증
                                new_access_token = None
                                for cookie in response.headers.getlist("set-cookie"):
                                    if "access_token=" in cookie:
                                        new_access_token = cookie.split("access_token=")[1].split(";")[0]
                                        break
                                
                                if new_access_token:
                                    # 임시로 쿠키 업데이트
                                    request._cookies = request.cookies.copy()
                                    request._cookies["access_token"] = new_access_token
                                    
                                    user_payload = await get_current_user_from_cookie(request)
                                    request.state.user = user_payload
                                    
                                    # 원래 요청 처리 후 새 쿠키 헤더 추가
                                    response_obj = await call_next(request)
                                    for header_name, header_value in response.headers.items():
                                        if header_name.lower() == 'set-cookie':
                                            response_obj.headers.append(header_name, header_value)
                                    return response_obj
                                else:
                                    raise HTTPException(status_code=401, detail="Token refresh failed")
                            
                            except HTTPException:
                                return JSONResponse(
                                    status_code = 401,
                                    content={"detail": "Authentication required"}
                                )
                                
                        else:
                            return JSONResponse(
                                status_code = 401,
                                content={"detail": "Authentication required"}
                            )
                            
                    else:
                        return JSONResponse(
                            status_code = 401,
                            content={"detail": "Authentication required"}
                        )
                        
                else :
                    raise e

        response = await call_next(request)
        return response         