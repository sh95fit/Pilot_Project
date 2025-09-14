from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import uuid
from fastapi import HTTPException, Response, Request, Depends

from shared.models.user import UserCreate
from shared.models.session import SessionCreate
from shared.auth.jwt_handler import JWTHandler
from shared.auth.crypto import CryptoHandler
from shared.auth.cognito_client import CognitoClient
from shared.database.supabase_client import SupabaseClient
from shared.database.redis_client import RedisClient
from ..core.config import settings


class AuthService:
    @staticmethod
    def _get_cookie_config() -> Dict[str, Any]:
        """
        환경에 따른 쿠키 설정 반환
        """
        # 환경 설정에서 개발 모드 확인
        is_dev = getattr(settings, 'environment', 'dev').lower() in ['dev', 'development', 'local']

        return {
            "httponly": True,
            "secure": not is_dev,  # 개발환경에서는 False, 운영환경에서는 True
            "samesite": "lax" if is_dev else "strict",  # 개발환경에서는 더 관대하게
        }

    @staticmethod
    async def login(
        email: str, 
        password: str, 
        response: Response, 
        request: Request,
        # staticmethod와 Depends의 충돌 이슈 발생
        # 의존성 주입은 라우터 함수에서만 동작 -> 라우터 단에서 의존성 주입하도록 수정
        # cognito_client: CognitoClient = Depends(get_cognito_client),
        # supabase_client: SupabaseClient = Depends(get_supabase_client),
        # redis_client: RedisClient = Depends(get_redis_client),
        # jwt_handler: JWTHandler = Depends(get_jwt_handler),
        # crypto_handler: CryptoHandler = Depends(get_crypto_handler)
        cognito_client: CognitoClient,  
        supabase_client: SupabaseClient,  
        redis_client: RedisClient,  
        jwt_handler: JWTHandler, 
        crypto_handler: CryptoHandler 
    ) -> Dict[str, Any]:
        """
        로그인 처리
        """
        try:
            # 1. Cognito 인증
            cognito_tokens = cognito_client.authenticate_user(email, password)
            if not cognito_tokens:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # 2. Cognito에서 사용자 정보 가져오기
            user_info = cognito_client.get_user_info(cognito_tokens['access_token'])
            if not user_info:
                raise HTTPException(status_code=500, detail="Failed to get user info")
            
            # 3. JIT 사용자 프로비저닝            
            user_create_data = UserCreate(
                email=user_info['email'],
                cognito_sub=user_info['sub'],
                display_name=user_info.get("given_name") or email.split('@')[0],
                role="user"
            )
            
            user = await supabase_client.upsert_user(user_create_data)
            if not user:
                raise HTTPException(status_code = 500, detail="Failed to create/update user")
            
            # 4. 새 세션 생성
            session_id = str(uuid.uuid4())
            
            # 5. Refresh token 암호화 및 저장
            encrypted_refresh_token = crypto_handler.encrypt(cognito_tokens['refresh_token'])
            
            # Refresh token 만료 시간 계산 (기본적으로 7일, Cognito 설정에 따라 조정)
            refresh_expires_at = datetime.utcnow() + timedelta(days=7)
            
            # 디바이스 정보 수집
            device_info = {
                "ip_address": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }
            
            session_create_data = SessionCreate(
                user_id = user.id,
                session_id = session_id,
                refresh_token_enc = encrypted_refresh_token,
                refresh_expires_at = refresh_expires_at,
                device_info = device_info
            )
            
            # Supabase에 세션 저장
            db_session = await supabase_client.create_session(session_create_data)
            if not db_session:
                raise HTTPException(status_code=500, detail="Failed to create session")
            
            # 6. Redis에 세션 캐싱
            redis_session_data = {
                "user_id": str(user.id),
                "refresh_token_enc": encrypted_refresh_token,
                "refresh_expires_at": refresh_expires_at.isoformat()
            }
            ttl_seconds = int((refresh_expires_at - datetime.utcnow()).total_seconds())
            redis_client.set_session(session_id, redis_session_data, ttl_seconds)
            
            # 7. 내부 JWT 발급
            access_token = jwt_handler.create_access_token(
                user_id = str(user.id),
                session_id = session_id,
                roles = [user.role],
                expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
            )
            
            # 8. 쿠키 설정
            # response.set_cookie(
            #     key="access_token",
            #     value=access_token,
            #     httponly=True,
            #     secure=True,
            #     samesite="strict",
            #     max_age=settings.jwt_access_token_expire_minutes * 60
            # )
            
            # response.set_cookie(
            #     key="session_id",
            #     value=session_id,
            #     httponly=True,
            #     secure=True,
            #     samesite="strict",
            #     max_age=ttl_seconds
            # )

            cookie_config = AuthService._get_cookie_config()

            response.set_cookie(
                key="access_token",
                value=access_token,
                max_age=settings.jwt_access_token_expire_minutes * 60,
                **cookie_config
            )

            response.set_cookie(
                key="session_id",
                value=session_id,
                max_age=ttl_seconds,
                **cookie_config
            )
            
            return {
                "success": True,
                "message": "Login successful",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "display_name": user.display_name,
                    "role": user.role
                },
                "tokens": {         # 쿠키를 streamlit에서 처리하지 못해 json으로 전달하여 streamlit이 처리하도록 유도
                    "access_token": access_token,
                    "session_id": session_id
                }
            }
        
        except HTTPException:
            raise
        
        except Exception as e:
            print(f"Login error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @staticmethod
    async def refresh_tokens(
        session_id: str, 
        response: Response,
        # redis_client: RedisClient = Depends(get_redis_client),
        # supabase_client: SupabaseClient = Depends(get_supabase_client),
        # crypto_handler: CryptoHandler = Depends(get_crypto_handler),
        # cognito_client: CognitoClient = Depends(get_cognito_client),
        # jwt_handler: JWTHandler = Depends(get_jwt_handler)
        redis_client: RedisClient,
        supabase_client: SupabaseClient,
        crypto_handler: CryptoHandler,
        cognito_client: CognitoClient,
        jwt_handler: JWTHandler
    ) -> bool:
        """
        토큰 갱신
        """
        try:
            # 1. Redis에서 세션 조회
            session_data = redis_client.get_session(session_id)
            
            if not session_data:
                # 2. Redis에 없으면 Supabase 조회
                db_session = await supabase_client.get_session(session_id)
                if not db_session or db_session.revoked:
                    return False

                session_data = {
                    "user_id": str(db_session.user_id),
                    "refresh_token_enc": db_session.refresh_token_enc,
                    "refresh_expires_at": db_session.refresh_expires_at.isoformat()
                }
                
            # 3. Refresh token 복호화
            encrypted_refresh_token = session_data["refresh_token_enc"]
            refresh_token = crypto_handler.decrypt(encrypted_refresh_token)
            
            # 4. Cognito에 토큰 갱신 요청
            new_tokens = cognito_client.refresh_token(refresh_token)
            if not new_tokens:
                # 갱신 실패 시 세션 무효화
                await AuthService.logout(session_id, response, redis_client, supabase_client)
                return False
            
            # 5. 새 refresh token이 있으면 rotate (Cognito 설정에 따라 상이)
            if "refresh_token" in new_tokens and new_tokens['refresh_token']:
                new_encrypted_refresh = crypto_handler.encrypt(new_tokens['refresh_token'])
                new_expires_at = datetime.utcnow() + timedelta(days=7)
                
                # DB 업데이트
                await supabase_client.update_session_refresh_token(
                    session_id, new_encrypted_refresh, new_expires_at
                )
                
                # Redis 업데이트
                session_data["refresh_token_enc"] = new_encrypted_refresh
                session_data["refresh_expires_at"] = new_expires_at.isoformat()
                ttl_seconds = int((new_expires_at - datetime.utcnow()).total_seconds())
                redis_client.set_session(session_id, session_data, ttl_seconds)
                
            # 6. 새 access token 발급
            user_id = session_data["user_id"]
            
            user = await supabase_client.get_user_by_cognito_sub(user_id)
            roles = [user.role] if user and user.role else ["user"]
            
            access_token = jwt_handler.create_access_token(
                user_id=user_id,
                session_id=session_id,
                roles=roles, 
                expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
            )
            
            # 7. 새 access token 쿠키 설정
            # response.set_cookie(
            #     key="access_token",
            #     value=access_token,
            #     httponly=True,
            #     secure=True,
            #     samesite="strict",
            #     max_age=settings.jwt_access_token_expire_minutes * 60
            # )

            cookie_config = AuthService._get_cookie_config()

            response.set_cookie(
                key="access_token",
                value=access_token,
                max_age=settings.jwt_access_token_expire_minutes * 60,
                **cookie_config
            )
            
            return True
        
        except Exception as e:
            print(f"Token refresh error: {e}")
            return False
    
    @staticmethod
    async def logout(
        session_id: str, 
        response: Response,
        # redis_client: RedisClient = Depends(get_redis_client),
        # supabase_client: SupabaseClient = Depends(get_supabase_client)
        redis_client: RedisClient,
        supabase_client: SupabaseClient
    ) -> Dict[str, Any]:
        """
        로그아웃 처리
        """
        try:
            # 1. Redis에서 세션 삭제
            redis_client.delete_session(session_id)
            
            # 2. Supabase에서 세션 무효화
            await supabase_client.revoke_session(session_id)
            
            # 3. 쿠키 삭제 (httponly는 delete_cookie에서 지원하지 않으므로 secure와 samesite만 적용)
            # response.delete_cookie("access_token", path="/")
            # response.delete_cookie("session_id", path="/")   # path : 쿠키가 유효한 경로
            

            is_dev = getattr(settings, 'environment', 'dev').lower() in ['dev', 'development', 'local']
            
            response.delete_cookie(
                key="access_token", 
                path="/",
                secure=not is_dev,
                samesite="lax" if is_dev else "strict"
            )
            response.delete_cookie(
                key="session_id", 
                path="/",
                secure=not is_dev,
                samesite="lax" if is_dev else "strict"
            )

            return {"success": True, "message": "Logout successful"}
        
        except Exception as e:
            print(f"Logout Error: {e}")
            return {"success": False, "message": "Logout failed"}

    @staticmethod
    async def get_current_user_info(
        user_payload: Dict[str, Any],
        # supabase_client: SupabaseClient = Depends(get_supabase_client)
        supabase_client: SupabaseClient
    ) -> Dict[str, Any]:
        """
        현재 사용자 정보 조회
        """
        try:
            user_id = user_payload["sub"]
            
            # Supabase에서 사용자 정보 조회
            user = await supabase_client.get_user_by_cognito_sub(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            return {
                "id": str(user.id),
                "email": user.email,
                "display_name": user.display_name,
                "role": user.role,
                "created_at": user.created_at.isoformat(),
                "is_active": user.is_active
            }
        
        except Exception as e:
            print(f"Get user info error: {e}")
            raise HTTPException(status_code=500, detail="Failed to get user info")