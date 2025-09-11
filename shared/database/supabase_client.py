from supabase import create_client, Client
from typing import Optional, Dict, Any, List
import os
from shared.models.user import User, UserCreate
from shared.models.session import UserSession, SessionCreate

class SupabaseClient:
    def __init__(self, supabase_url: str, supabase_key: str):
        self.client: Client = create_client(supabase_url, supabase_key)
        
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
            print(f"Error fetching user by email: {e}")
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
            print(f"Error fetching user by cognito_sub: {e}")
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
        except Exception as e :
            print(f"Error creating user: {e}")
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
                update_data = {"email": user_data.email, "display_name": user_data.display_name}
                response = self.client.table("users").update(update_data).eq("cognito_sub", user_data.cognito_sub).execute()
                
                if response.data:
                    return User(**response.data[0])
                return existing_user
            
            else:
                # 새 사용자 생성
                return await self.create_user(user_data)
        except Exception as e:
            print(f"Error upserting user: {e}")
            return None
        
    # Session 처리 메서드
    async def create_session(self, session_data: SessionCreate) -> Optional[UserSession]:
        """
        새 세션 생성
        """
        try:
            response = self.client.table("user_session").insert(session_data.model_dump()).execute()
            if response.data:
                return UserSession(**response.data[0])
            return None
        except Exception as e :
            print(f"Error creating session: {e}")
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
            print(f"Error fetching session: {e}")
            return None
        
    async def update_session_refresh_token(self, session_id: str, refresh_token_enc: str, expires_at) -> bool:
        """
        세션의 refresh token 업데이트
        """
        try:
            response = self.client.table("user_sessions").update({
                "refresh_token_enc": refresh_token_enc,
                "refresh_expires_at": expires_at.isoformat(),
                "last_used_at": "now()",
            }).eq("session_id", session_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error updating session refresh token: {e}")
            return False
    
    async def revoke_session(self, session_id: str) -> bool:
        """
        세션 무효화
        """
        try:
            response = self.client.table("user_sessions").update({
                "revoked": True
            }).eq("session_id", session_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error revoking session: {e}")
            return False
        
    async def revoke_all_user_sessions(self, user_id: str) -> bool:
        """
        특정 사용자의 모든 세션 무효화
        """
        try:
            response = self.client.table("user_sessions").update({
                "revoked": True
            }).eq("user_id", user_id).execute()
            return True
        except Exception as e:
            print(f"Error revoking all user sessions: {e}")
            return False
        
    async def cleanup_expired_session(self) -> int:
        """
        만료된 세션 정리
        """
        try:
            response = self.client.table("user_sessions").update({
                "revoked": True
            }).lt("refresh_expires_at", "now()").execute()
            return len(response.data)
        except Exception as e:
            print(f"Error cleaning up expired sessions: {e}")
            return 0