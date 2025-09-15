from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import uuid
from fastapi import HTTPException, Response, Request, status
import logging

from shared.models.user import UserCreate
from shared.models.session import SessionCreate
from shared.auth.jwt_handler import JWTHandler
from shared.auth.crypto import CryptoHandler
from shared.auth.cognito_client import CognitoClient
from shared.database.supabase_client import SupabaseClient
from shared.database.redis_client import RedisClient
from ..core.config import settings

logger = logging.getLogger(__name__)


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
            cognito_tokens = await cognito_client.authenticate_user(email, password)
            if not cognito_tokens:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # 2. Cognito에서 사용자 정보 가져오기
            user_info = await cognito_client.get_user_info(cognito_tokens['access_token'])
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
            
            # 기존 활성 세션 정리
            if not settings.allow_multiple_sessions:
                await AuthService._cleanup_existing_sessions(user.id, redis_client, supabase_client)
            
            # 4. 새 세션 생성
            session_id = str(uuid.uuid4())
            
            # 5. Refresh token 암호화 및 저장
            encrypted_refresh_token = crypto_handler.encrypt(cognito_tokens['refresh_token'])
            
            # Refresh token 만료 시간 계산 (기본적으로 7일, Cognito 설정에 따라 조정)
            refresh_expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
            
            # 디바이스 정보 수집
            device_info = AuthService._extract_device_info(request)
            
            session_create_data = SessionCreate(
                user_id = user.id,
                session_id = session_id,
                refresh_token_enc = encrypted_refresh_token,
                refresh_expires_at = refresh_expires_at,
                device_info = device_info
            )
            
            
            # 6. 세션 저장 (DB 및 Redis)
            await AuthService._create_session(
                session_create_data, supabase_client, redis_client, refresh_expires_at
            )
            
            # 7. 내부 JWT 발급
            access_token = jwt_handler.create_access_token(
                user_id = str(user.id),
                session_id = session_id,
                roles = [user.role],
                expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
            )
            
            # 8. 쿠키 설정
            AuthService._set_auth_cookies(response, access_token, session_id, refresh_expires_at)
            
            logger.info(f"User {email} logged in successfully with session {session_id}")
            
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
            logger.error(f"{email} login error: {e}", exc_info=True)
            # print(f"Login error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @staticmethod
    async def _cleanup_existing_sessions(
        user_id: uuid.UUID, 
        redis_client: RedisClient, 
        supabase_client: SupabaseClient
    ) -> None:
        """
        기존 활성 세션 정리 (단일 세션 정책)
        """
        try:
            existing_session = await supabase_client.get_active_session(user_id)
            if existing_session:
                redis_client.delete_session(existing_session.session_id)
                await supabase_client.revoke_session(existing_session.session_id)
                logger.info(f"{user_id}'s existing sessions ({existing_session.session_id}) have been cleared")
        except Exception as e:
            logger.warning(f"Failed to cleanup existing sessions for user {user_id}: {e}")
    
    @staticmethod
    def _extract_device_info(request: Request) -> Dict[str, str]:
        """
        요청에서 디바이스 정보 추출
        """
        return {
            "ip_address": getattr(request.client, 'host', 'unknown') if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
    
    @staticmethod
    async def _create_session(
        session_data: SessionCreate,
        supabase_client: SupabaseClient,
        redis_client: RedisClient,
        refresh_expires_at: datetime
    ) -> None:
        """
        세션 생성 (DB + Redis)
        """
        # supabase에 세션 저장
        db_session = await supabase_client.create_session(session_data)
        if not db_session:
            raise HTTPExeption(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session"
            )
        
        # Redis에 세션 캐싱
        redis_session_data = {
            "user_id": str(session_data.user_id),
            "refresh_token_enc": session_data.refresh_token_enc,
            "refresh_expires_at": refresh_expires_at.isoformat()
        }
        ttl_seconds = int((refresh_expires_at - datetime.utcnow()).total_seconds())
        
        if not redis_client.set_session(session_data.session_id, redis_session_data, ttl_seconds):
            logger.warning(f"Failed to cache session {session_data.session_id} in Redis")
    
    @staticmethod
    def _set_auth_cookies(
        response: Response, 
        access_token: str, 
        session_id: str, 
        refresh_expires_at: datetime
    ) -> None:
        """
        인증 쿠키 설정
        """
        cookie_config = AuthService._get_cookie_config()
        ttl_seconds = int((refresh_expires_at - datetime.utcnow()).total_seconds())
    
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
    
    
    @staticmethod
    async def refresh_tokens(
        session_id: str, 
        response: Response,
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
            session_data = await AuthService._get_session_data(
                session_id, redis_client, supabase_client
            )
            
            if not session_data:
                logger.warning(f"Session {session_id} not found")
                return False

            # 2. 세션 만료 확인
            refresh_expires_at = datetime.fromisoformat(session_data["refresh_expires_at"])
            if refresh_expires_at <= datetime.utcnow():
                logger.warning(f"Session {session_id} has expired")
                await AuthService._invalidate_session(session_id, response, redis_client, supabase_client)
                return False
                
            # 3. Refresh token 복호화 및 갱신
            refresh_token = crypto_handler.decrypt(session_data["refresh_token_enc"])
            new_tokens = await cognito_client.refresh_token(refresh_token)
            
            if not new_tokens:
                logger.warning(f"Session {session_id} token could not be refreshed")
                await AuthService._invalidate_session(session_id, response, redis_client, supabase_client)
                return False
            
            # 4. Refresh token rotation 처리
            if "refresh_token" in new_tokens and new_tokens['refresh_token']:
                await AuthService._rotate_refresh_token(
                    session_id, new_tokens['refresh_token'], crypto_handler, 
                    supabase_client, redis_client, session_data
                )
            
            # 5. 새 Access token 발급 및 쿠키 설정
            await AuthService._issue_new_access_token(
                session_data, session_id, jwt_handler, response, supabase_client
            )
            
            logger.info(f"Session {session_id} token refresh successful")
            return True
        
        except Exception as e:
            print(f"Token refresh error: {e}")
            return False
    
    @staticmethod
    async def _get_session_data(
        session_id: str, 
        redis_client: RedisClient, 
        supabase_client: SupabaseClient
    ) -> Optional[Dict[str, Any]]:
        """
        세션 데이터 조회 (Redis -> DB 순)
        """
        session_data = redis_client.get_session(session_id)
        
        if not session_data:
            # DB에서 조회
            db_session = await supabase_client.get_session(session_id)
            if not db_session or db_session.revoked:
                return None
            
            session_data = {
                "user_id": str(db_session.user_id),
                "refresh_token_enc": db_session.refresh_token_enc,
                "refresh_expires_at": db_session.refresh_expires_at.isoformat()
            }
            
            # Redis에 다시 캐싱
            ttl_seconds = int((db_session.refresh_expires_at - datetime.utcnow()).total_seconds())
            if ttl_seconds > 0:
                redis_client.set_session(session_id, session_data, ttl_seconds)
                logger.debug(f"세션 {session_id}을 Redis에 재캐싱했습니다")
                
        return session_data            
    
    @staticmethod
    async def _rotate_refresh_token(
        session_id: str,
        new_refresh_token: str,
        crypto_handler: CryptoHandler,
        supabase_client: SupabaseClient,
        redis_client: RedisClient,
        session_data: Dict[str, Any]
    ) -> None :
        """
        Refresh token rotation 처리
        """
        new_encrypted_refresh = crypto_handler.encrypt(new_refresh_token)
        new_expires_at = datetime.utcnow() + timedelta(
            days=getattr(settings, 'refresh_token_expire_days', 7)
        )
        
        # DB 업데이트
        success = await supabase_client.update_session_refresh_token(
            session_id, new_encrypted_refresh, new_expires_at
        )

        if not success:
            logger.error(f"Session {session_id} refresh token DB update failed")
            return
        
        # Redis 업데이트
        session_data["refresh_token_enc"] = new_encrypted_refresh
        session_data["refresh_expires_at"] = new_expires_at.isoformat()
        ttl_seconds = int((new_expires_at - datetime.utcnow()).total_seconds())
        
        if not redis_client.set_session(session_id, session_data, ttl_seconds):
            logger.warning(f"Session {session_id} refresh token Redis update failed")    
    
    @staticmethod
    async def _issue_new_access_token(
        session_data: Dict[str, Any],
        session_id: str,
        jwt_handler: JWTHandler,
        response: Response,
        supabase_client: SupabaseClient
    ) -> None:
        """
        새 access token 발급 및 쿠키 설정
        """
        user_id = session_data["user_id"]
        user = await supabase_client.get_user_by_cognito_sub(user_id)
        
        if not user:
            logger.error(f"사용자 {user_id}를 찾을 수 없습니다")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        roles = [user.role] if user.role else ["user"]
        
        access_token = jwt_handler.create_access_token(
            user_id=user_id,
            session_id=session_id,
            roles=roles, 
            expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes)
        )
        
        cookie_config = AuthService._get_cookie_config()
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=settings.jwt_access_token_expire_minutes * 60,
            **cookie_config
        )        
            
    async def _invalidate_session(
        session_id: str,
        response: Response,
        redis_client: RedisClient,
        supabase_client: SupabaseClient
    ) -> None:
        """세션 무효화"""
        try:
            redis_client.delete_session(session_id)
            await supabase_client.revoke_session(session_id)
            AuthService._clear_auth_cookies(response)
            logger.info(f"Session {session_id} has been invalidated")
        except Exception as e:
            logger.error(f"Session {session_id} invalidation error: {e}")    
    
    @staticmethod
    def _clear_auth_cookies(response: Response) -> None:
        """인증 쿠키 삭제"""
        cookie_config = AuthService._get_cookie_config()
        # delete_cookie에서는 httponly 옵션을 지원하지 않으므로 제외
        delete_config = {k: v for k, v in cookie_config.items() if k != 'httponly'}
        
        for cookie_name in ["access_token", "session_id"]:
            response.delete_cookie(
                key=cookie_name, 
                path="/",
                **delete_config
            )
    
    @staticmethod
    async def logout(
        session_id: str, 
        response: Response,
        redis_client: RedisClient,
        supabase_client: SupabaseClient
    ) -> Dict[str, Any]:
        """
        로그아웃 처리
        """
        try:
            await AuthService._invalidate_session(session_id, response, redis_client, supabase_client)
            logger.info(f"Session {session_id} has been logged out successfully")
            return {"success": True, "message": "logout successful"}
        
        except Exception as e:
            logger.error(f"Session {session_id} logout error: {e}", exc_info=True)
            return {"success": False, "message": "logout failed"}

    @staticmethod
    async def get_current_user_info(
        user_payload: Dict[str, Any],
        supabase_client: SupabaseClient
    ) -> Dict[str, Any]:
        """
        현재 사용자 정보 조회
        """
        try:
            user_id = user_payload["sub"]
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="유효하지 않은 사용자 토큰입니다"
                )
            
            user = await supabase_client.get_user_by_cognito_sub(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="사용자를 찾을 수 없습니다"
                )
            
            return {
                "id": str(user.id),
                "email": user.email,
                "display_name": user.display_name,
                "role": user.role,
                "created_at": user.created_at.isoformat(),
                "is_active": user.is_active
            }
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User {user_payload.get('sub')} data retrieval error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Failed to retrieve user information"
            )