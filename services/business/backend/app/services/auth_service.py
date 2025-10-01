from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import uuid
from fastapi import HTTPException, Response, Request, status
import logging

from shared.models.user import UserCreate
from shared.models.session import SessionCreate
from shared.auth.jwt_handler import JWTHandler
from shared.auth.crypto import CryptoHandler
from shared.auth.cognito_client import CognitoClient, RefreshTokenError
from shared.database.supabase_client import SupabaseClient
from shared.database.redis_client import RedisClient
from backend.app.core.config import settings

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
        로그인 처리 (Device Tracking 비활성화)
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
            # refresh_expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)  # 7일
            refresh_expires_at = datetime.utcnow() + timedelta(days=settings.cognito_refresh_token_expire_days)  # 30일
            
            # 디바이스 정보 수집
            device_info = AuthService._extract_device_info(request)
            
            session_create_data = SessionCreate(
                user_id=user.id,
                session_id=session_id,
                refresh_token_enc=encrypted_refresh_token,
                refresh_expires_at=refresh_expires_at,
                device_info=device_info, 
            )
                
            # 7. 세션 저장 (DB 및 Redis)
            await AuthService._create_session(
                session_create_data, supabase_client, redis_client, refresh_expires_at
            )
            
            # 8. 내부 JWT 발급
            access_token = jwt_handler.create_access_token(
                user_id = str(user.id),
                session_id = session_id,
                roles = [user.role],
                expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
            )
            
            # 9. 쿠키 설정
            AuthService._set_auth_cookies(response, access_token, session_id, refresh_expires_at)
            
            logger.info(
                f"Login successful: user={email}, session={session_id}"
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
                    "session_id": session_id,
                    "expires_in": settings.jwt_access_token_expire_minutes * 60
                }
            }
        
        except HTTPException:
            raise
        
        except Exception as e:
            logger.error(f"{email} login error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")
    
    
    @staticmethod
    async def _cleanup_existing_sessions(
        user_id: uuid.UUID, 
        redis_client: RedisClient, 
        supabase_client: SupabaseClient
    ) -> None:
        """
        세션 정리 - 최대 세션 수 정책에 따라 처리
        
        단일 세션 정책: Redis 캐시 + DB의 기존 세션 모두 revoke
        다중 세션 정책: 최대 세션 수 초과 시 오래된 세션 revoke        
        """
        try:
            if not settings.allow_multiple_sessions:
                # 단일 세션 정책: Redis 캐시 + DB의 기존 세션 모두 revoke
                existing_sessions = await supabase_client.get_user_sessions(
                    user_id, 
                    active_only=True
                )
                
                # Redis 캐시 삭제
                for session in existing_sessions:
                    redis_client.delete_session(session.session_id)
                
                # DB에서 revoke
                if existing_sessions:
                    await supabase_client.revoke_all_user_sessions(str(user_id))
                    logger.info(
                        f"User {user_id}: revoked {len(existing_sessions)} existing sessions "
                        f"(single session policy)"
                    )
                return
        
            # 다중 세션 허용: 최대 세션 수 체크
            max_sessions = getattr(settings, 'max_sessions_per_user', 3)
            existing_sessions = await supabase_client.get_user_sessions(
                user_id, 
                active_only=True
            )
        
            if len(existing_sessions) >= max_sessions:
                # 가장 오래된 세션부터 제거 (최신 세션은 유지)
                sessions_sorted = sorted(
                    existing_sessions, 
                    key=lambda x: x.created_at
                )
                
                # 새 세션 1개를 위한 공간 확보
                num_to_revoke = len(existing_sessions) - max_sessions + 1
                sessions_to_revoke = sessions_sorted[:num_to_revoke]
                
                for session in sessions_to_revoke:
                    # Redis 캐시 삭제
                    redis_client.delete_session(session.session_id)
                    # DB에서 revoke
                    await supabase_client.revoke_session(session.session_id)
                
                logger.info(
                    f"User {user_id}: revoked {len(sessions_to_revoke)} "
                    f"old sessions to maintain max {max_sessions} sessions"
                )
            else:
                logger.debug(
                    f"User {user_id}: {len(existing_sessions)}/{max_sessions} "
                    f"sessions - no cleanup needed"
                )
                    
        except Exception as e:
            logger.warning(
                f"Failed to cleanup existing sessions for user {user_id}: {e}"
            )
                   

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
            "refresh_expires_at": refresh_expires_at.isoformat(),
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
    ) -> Tuple[bool, Optional[Dict]]:
        """
        토큰 갱신 - Redis → Supabase → Cognito 순으로 처리
        
        Flow:
        1. Redis에서 세션 조회 (빠른 검증)
        2. Redis 없으면 → Supabase 조회
        3. 세션 유효성 검증 (revoked, refresh_expires_at)
        4. Refresh Token 유효하면 → 새 Access Token만 발급 (Cognito 호출 X)
        5. Refresh Token 만료되었으면 → Cognito로 갱신 시도
        6. 새 토큰으로 Redis & DB 업데이트
        """
        try:
            logger.debug(f"Token refresh request for session: {session_id[:8]}...")
            
            # 1. 세션 조회
            session_data = await AuthService._get_session_data(
                session_id, redis_client, supabase_client
            )
            
            if not session_data:
                logger.warning(f"Session {session_id} not found")
                return False, None

            # 2. 세션 만료 확인
            refresh_expires_at = datetime.fromisoformat(session_data["refresh_expires_at"])
            now = datetime.utcnow()
            
            if refresh_expires_at <= now:
                logger.warning(f"Session {session_id} has expired")
                await AuthService._invalidate_session(
                    session_id, response, redis_client, supabase_client
                )
                return False, None
            
            # 디버깅 로그 추가
            time_left = (refresh_expires_at - now).total_seconds()
            logger.debug(
                f"Session {session_id[:8]}... refresh token valid: "
                f"{time_left/3600:.1f}h remaining"
            )
                
            
            # 3. Cognito Refresh Token API 호출
            refresh_threshold = timedelta(days=getattr(settings, 'refresh_token_renewal_threshold_days', 1))
            needs_cognito_refresh = (refresh_expires_at - now) < refresh_threshold
            
            if needs_cognito_refresh:
                logger.info(
                    f"Session {session_id[:8]}... refresh token expiring soon, "
                    f"requesting new refresh token from Cognito"
                )
                
                # Cognito를 통한 Refresh Token 갱신
                refresh_token = crypto_handler.decrypt(session_data["refresh_token_enc"])
                
                try:
                    new_tokens = await cognito_client.refresh_token(refresh_token)
                    
                except RefreshTokenError as e:
                    logger.error(
                        f"Session {session_id[:8]}... Cognito refresh failed: "
                        f"{e.error_type} - {e.message}"
                    )
                    
                    # Refresh Token 만료/무효화 시 세션 정리
                    if e.error_type in ["expired", "invalid"]:
                        await AuthService._invalidate_session(
                            session_id, response, redis_client, supabase_client
                        )
                    
                    return False, None
    
                if not new_tokens:
                    logger.warning(f"Session {session_id[:8]}... no tokens from Cognito")
                    await AuthService._invalidate_session(
                        session_id, response, redis_client, supabase_client
                    )
                    return False, None
                
                # Refresh Token Rotation 처리
                if "refresh_token" in new_tokens and new_tokens['refresh_token']:
                    await AuthService._rotate_refresh_token(
                        session_id, new_tokens['refresh_token'], crypto_handler, 
                        supabase_client, redis_client, session_data
                    )
                    logger.info(f"Session {session_id[:8]}... refresh token rotated via Cognito")
                else:
                    # Rotation 없으면 last_used만 업데이트
                    await supabase_client.update_session_last_used(session_id)
                    logger.debug(f"Session {session_id[:8]}... last_used updated")
            
            else:
                # Refresh Token이 아직 유효하면 last_used만 업데이트
                await supabase_client.update_session_last_used(session_id)
                logger.debug(
                    f"Session {session_id[:8]}... refresh token still valid, "
                    f"only updating last_used (no Cognito call)"
                )
                
            # 4. 새 Access token 발급 및 쿠키 설정
            new_access_token = await AuthService._issue_new_access_token(
                session_data, session_id, jwt_handler, response, supabase_client
            )
            
            # Streamlit 환경을 위한 토큰 정보 반환
            token_info = {
                "access_token": new_access_token,
                "session_id": session_id,
                "expires_in": settings.jwt_access_token_expire_minutes * 60
            }
            
            logger.info(f"Session {session_id} token refresh successful")
            return True, token_info
        
        
        except Exception as e:
            logger.error(f"Token refresh error: {e}", exc_info=True)
            return False, None
        
    @staticmethod
    async def _get_session_data(
        session_id: str, 
        redis_client: RedisClient, 
        supabase_client: SupabaseClient
    ) -> Optional[Dict[str, Any]]:
        """
        세션 데이터 조회 - Redis 우선, Supabase fallback
        
        Redis 캐시를 먼저 확인하여 빠른 검증
        """
        # 1. Redis에서 조회 (빠름)
        session_data = redis_client.get_session(session_id)
        
        if session_data:
            logger.debug(f"Session {session_id[:8]}... found in Redis")
            return session_data
        
        # 2. Redis 없으면 DB 조회
        logger.debug(f"Session {session_id[:8]}... not in Redis, checking DB")
        db_session = await supabase_client.get_session(session_id)
        
        if not db_session or db_session.revoked:
            logger.debug(f"Session {session_id[:8]}... not found or revoked in DB")
            return None
        
        # 3. DB에서 찾았으면 Redis에 재캐싱
        session_data = {
            "user_id": str(db_session.user_id),
            "refresh_token_enc": db_session.refresh_token_enc,
            "refresh_expires_at": db_session.refresh_expires_at.isoformat(),
        }
        
        ttl_seconds = int((db_session.refresh_expires_at - datetime.utcnow()).total_seconds())
        if ttl_seconds > 0:
            redis_client.set_session(session_id, session_data, ttl_seconds)
            logger.debug(f"Session {session_id[:8]}... recached in Redis")
                
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
        Refresh Token Rotation 처리 (DB & Redis 업데이트)
        """
        new_encrypted_refresh = crypto_handler.encrypt(new_refresh_token)
        new_expires_at = datetime.utcnow() + timedelta(
            days=getattr(settings, 'cognito_refresh_token_expire_days', 30)
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
        
        Returns:
            새로 발급된 access_token
        """
        user_id = session_data["user_id"]
        user = await supabase_client.get_user_by_id(user_id)
        
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
        
        return access_token
            
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
            # JWT payload에서 user_id 우선 사용, 없으면 cognito_sub 사용
            user_id = user_payload.get("sub")  
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="유효하지 않은 사용자 토큰입니다"
                )
            
            # user_id가 UUID 형식이면 직접 조회, 아니면 cognito_sub로 조회
            try:
                # user_id가 UUID 형식인지 확인
                uuid.UUID(user_id)
                user = await supabase_client.get_user_by_id(user_id)
            except Exception as e:
                logger.error(f"User not found : {e}", exc_info=True)
                
            
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
            

    # streamlit 인증 처리를 위한 비즈니스 로직 추가 
    @staticmethod
    async def check_auth_with_headers(
        request: Request,
        redis_client: RedisClient,
        supabase_client: SupabaseClient,
        jwt_handler: JWTHandler
    ) -> Optional[Dict[str, Any]]:
        """
        Streamlit 환경을 위한 헤더 기반 인증 확인
        Cookie 헤더에서 토큰을 추출하여 인증 확인
        """
        try:
            # Cookie 헤더에서 토큰 추출
            cookie_header = request.headers.get("cookie", "")
            
            access_token = None
            session_id = None
            
            # 쿠키 파싱
            if cookie_header:
                cookies = {}
                for item in cookie_header.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookies[key] = value
                
                access_token = cookies.get('access_token')
                session_id = cookies.get('session_id')
            
            if not access_token or not session_id:
                return None
            
            # 토큰 검증
            try:
                payload = jwt_handler.verify_token(access_token)
                token_session_id = payload.get('jti')
                
                # 세션 ID 일치 확인
                if token_session_id != session_id:
                    logger.warning(f"Session ID mismatch: token={token_session_id}, provided={session_id}")
                    return None
                
                # 세션 유효성 확인
                session_data = await AuthService._get_session_data(
                    session_id, redis_client, supabase_client
                )
                
                if not session_data:
                    return None
                
                return {
                    "authenticated": True,
                    "user_id": payload.get("sub"),
                    "session_id": session_id,
                    "roles": payload.get("roles", ["user"])
                }
                
            except ValueError as e:
                logger.warning(f"Token validation failed: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Header-based auth check error: {e}")
            return None
        
    @staticmethod
    async def logout_with_tokens(
        access_token: str,
        session_id: str,
        response: Response,
        redis_client: RedisClient,
        supabase_client: SupabaseClient
    ) -> Dict[str, Any]:
        """
        Streamlit 환경을 위한 토큰 기반 로그아웃
        """
        try:
            await AuthService._invalidate_session(session_id, response, redis_client, supabase_client)
            logger.info(f"Session {session_id} has been logged out successfully")
            return {"success": True, "message": "logout successful"}
        
        except Exception as e:
            logger.error(f"Session {session_id} logout error: {e}", exc_info=True)
            return {"success": False, "message": "logout failed"}
        