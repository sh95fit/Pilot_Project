from supabase import create_client, Client
from typing import Optional, Dict, Any, List
import os
from shared.models.user import User, UserCreate
from shared.models.session import UserSession, SessionCreate
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    def __init__(self, supabase_url: str, supabase_key: str):
        try:
            self.client: Client = create_client(supabase_url, supabase_key)
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
        
    # User 관련 메서드
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        이메일로 사용자 조회
        """
        try:
            response = self.client.table("users").select("*").eq("email", email).execute()
            if response.data:
                return User(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {e}")
            return None
    
    async def get_user_by_cognito_sub(self, cognito_sub: str) -> Optional[User]:
        """
        Cognito Sub로 사용자 조회
        """
        try:
            response = self.client.table("users").select("*").eq("cognito_sub", cognito_sub).execute()
            if response.data:
                return User(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching user by cognito_sub {cognito_sub}: {e}")
            return None
        
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        사용자 ID로 사용자 조회
        """
        try:
            response = self.client.table("users").select("*").eq("id", str(user_id)).execute()
            if response.data:
                return User(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching user by id {user_id}: {e}")
            return None
        
    async def create_user(self, user_data: UserCreate) -> Optional[User]:
        """
        새 사용자 생성
        """
        try:
            response = self.client.table("users").insert(user_data.model_dump()).execute()
            if response.data:
                return User(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
        
    async def upsert_user(self, user_data: UserCreate) -> Optional[User]:
        """
        사용자 생성 또는 업데이트 (JIT provisioning)
        """
        try:
            # 기존 사용자 여부 확인
            existing_user = await self.get_user_by_cognito_sub(user_data.cognito_sub)
            
            if existing_user:
                # 기존 사용자가 있는 경우 정보 업데이트
                update_data = {
                    "email": user_data.email, 
                    "display_name": user_data.display_name,
                    "updated_at": datetime.utcnow().isoformat()
                }
                response = self.client.table("users").update(update_data).eq("cognito_sub", user_data.cognito_sub).execute()
                
                if response.data:
                    return User(**response.data[0])
                return existing_user
            else:
                # 새 사용자 생성
                return await self.create_user(user_data)
                
        except Exception as e:
            logger.error(f"Error upserting user: {e}")
            return None
        
    # Session 처리 메서드
    async def create_session(self, session_data: SessionCreate) -> Optional[UserSession]:        
        """
        새 세션 생성 (순수 데이터 레이어)
        
        Note: 세션 정책(단일/다중)은 호출자(auth_service)에서 처리
        """
        try:
            # 신규 세션 생성을 위한 데이터 준비
            session_dict = session_data.model_dump()
            session_dict["user_id"] = str(session_dict["user_id"])
            session_dict["session_id"] = str(session_dict["session_id"]) 
            session_dict["refresh_expires_at"] = session_dict["refresh_expires_at"].isoformat()
            
            response = self.client.table("user_sessions").insert(session_dict).execute()
            
            if response.data:
                logger.info(
                    f"Created new session {session_dict['session_id']} "
                    f"for user {session_dict['user_id']}"
                )
                return UserSession(**response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
        
    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """
        세션 ID로 세션 조회
        """
        try:
            response = self.client.table("user_sessions").select("*").eq("session_id", session_id).eq("revoked", False).execute()
            if response.data:
                return UserSession(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching session {session_id}: {e}")
            return None
        
    async def update_session_refresh_token(self, session_id: str, refresh_token_enc: str, expires_at: datetime) -> bool:
        """세션의 refresh token 업데이트"""
        try:
            response = self.client.table("user_sessions").update({
                "refresh_token_enc": refresh_token_enc,
                "refresh_expires_at": expires_at.isoformat(),
                "last_used_at": datetime.utcnow().isoformat(),
            }).eq("session_id", session_id).execute()
            
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error updating session refresh token for {session_id}: {e}")
            return False
    
    async def revoke_session(self, session_id: str) -> bool:
        """
        특정 세션 무효화 (논리적 삭제)
        감사 추적을 위해 레코드는 유지하고 revoked=True로 표시
        """ 
        try:
            response = self.client.table("user_sessions").update({
                "revoked": True,
                "last_used_at": datetime.utcnow().isoformat()
            }).eq("session_id", session_id).eq("revoked", False).execute()
            
            if len(response.data) > 0:
                logger.info(f"Revoked session {session_id}")
                return True
            
            logger.debug(f"Session {session_id} not found or already revoked")
            return False
        except Exception as e:
            logger.error(f"Error revoking session {session_id}: {e}")
            return False
        
    async def revoke_all_user_sessions(self, user_id: str) -> bool:
        """
        특정 사용자의 모든 활성 세션 무효화
        단일 세션 정책 적용 시 또는 보안 이벤트 발생 시 사용
        """
        try:
            response = self.client.table("user_sessions").update({
                "revoked": True,
                "last_used_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).eq("revoked", False).execute()
            
            revoked_count = len(response.data) if response.data else 0
            if revoked_count > 0:
                logger.info(f"Revoked {revoked_count} active sessions for user {user_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error revoking all user sessions for {user_id}: {e}")
            return False
        
    async def cleanup_expired_session(self) -> int:
        """
        만료된 세션 정리
        """
        try:
            response = self.client.table("user_sessions").update({
                "revoked": True
            }).lt("refresh_expires_at", datetime.utcnow().isoformat()).eq("revoked", False).execute()
            
            cleaned_count = len(response.data) if response.data else 0
            logger.info(f"Cleaned up {cleaned_count} expired sessions")
            return cleaned_count
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
        
    async def get_active_session(self, user_id: str) -> Optional[UserSession]:
        """
        사용자의 활성 세션 조회 (만료되지 않고 revoke되지 않은 세션)
        가장 최근 생성된 세션 반환
        """
        try:
            response = self.client.table("user_sessions").select("*").eq(
                "user_id", str(user_id)
            ).eq(
                "revoked", False
            ).gt(
                "refresh_expires_at", datetime.utcnow().isoformat()
            ).order(
                "created_at", desc=True
            ).limit(1).execute()
            
            if response.data:
                return UserSession(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching active session for user {user_id}: {e}")
            return None

    async def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[UserSession]:
        """
        사용자의 세션 목록 조회
        
        Args:
            user_id: 사용자 ID
            active_only: True면 활성 세션만, False면 모든 세션 (revoked 포함)        
        """
        try:
            query = self.client.table("user_sessions").select("*").eq("user_id", str(user_id))
            
            if active_only:
                query = query.eq("revoked", False).gt("refresh_expires_at", datetime.utcnow().isoformat())
                
            response = query.order("created_at", desc=True).execute()
            
            if response.data:
                sessions = [UserSession(**session) for session in response.data]
                
                if active_only:
                    sessions = [s for s in sessions if s.last_used_at is not None]
                    
                return sessions
            return []
        
        except Exception as e:
            logger.error(f"Error fetching user sessions for {user_id}: {e}")
            return []
        
    async def delete_session_permanently(self, session_id: str) -> bool:
        """
        세션 물리적 삭제 (영구 삭제)
        
        주의: 감사 추적이 불가능하므로 신중히 사용
        사용 시나리오:
        - 주기적 정리 작업 (30일+ 된 revoked 세션)
        - GDPR 삭제 요청
        - 관리자 명령
        """
        try:
            response = self.client.table("user_sessions").delete().eq("session_id", session_id).execute()
            if len(response.data) > 0:
                logger.warning(f"Permanently deleted session {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error permanently deleting session {session_id}: {e}")
            return False

    async def get_old_revoked_sessions(self, cutoff_date: datetime) -> List[UserSession]:
        """
        특정 날짜 이전에 revoke된 세션 조회 (물리적 삭제용)
        
        Args:
            cutoff_date: 기준 날짜 (이 날짜 이전에 revoke된 세션 반환)
        """
        try:
            response = self.client.table("user_sessions").select("*").eq(
                "revoked", True
            ).lt(
                "last_used_at", cutoff_date.isoformat()
            ).execute()
            
            if response.data:
                return [UserSession(**session) for session in response.data]
            return []
        except Exception as e:
            logger.error(f"Error fetching old revoked sessions: {e}")
            return []
            
    async def delete_old_revoked_sessions(self, days: int = 30) -> int:
        """
        오래된 revoked 세션 일괄 물리적 삭제
        
        Args:
            days: 며칠 이전의 revoked 세션을 삭제할지 (기본 30일)
            
        Returns:
            삭제된 세션 수
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            response = self.client.table("user_sessions").delete().eq(
                "revoked", True
            ).lt(
                "last_used_at", cutoff_date.isoformat()
            ).execute()
            
            deleted_count = len(response.data) if response.data else 0
            if deleted_count > 0:
                logger.info(f"Permanently deleted {deleted_count} old revoked sessions (older than {days} days)")
            
            return deleted_count
        except Exception as e:
            logger.error(f"Error deleting old revoked sessions: {e}")
            return 0
        
        
    async def update_session_last_used(self, session_id: str) -> bool:
        """
        세션의 last_used_at 타임스탬프만 업데이트
        Refresh Token Rotation이 없는 경우 사용
        """
        try:
            response = self.client.table("user_sessions").update({
                "last_used_at": datetime.utcnow().isoformat()
            }).eq("session_id", session_id).execute()
            
            if len(response.data) > 0:
                logger.debug(f"Updated last_used_at for session {session_id}")
                return True
            else:
                logger.warning(f"Session {session_id} not found for last_used_at update")
                return False
        except Exception as e:
            logger.error(f"Error updating last_used_at for {session_id}: {e}")
            return False