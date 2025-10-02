import streamlit as st
from .session_manager import SessionManager
from utils.api_client import APIClient
from config.settings import settings
from typing import Optional, Dict, Any, Tuple
import logging
import time

logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self):
        self.session_manager = SessionManager()
        self.api_client = APIClient()
        
    def login(self, email: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        로그인 처리 - 동기화 완료까지 대기
        """
        try:
            logger.info(f"Login attempt for email: {email}")
            
            # 1. API 로그인 호출
            result = self.api_client.login(email, password)
            
            if not result or not result.get('success'):
                error_msg = "이메일 또는 비밀번호가 올바르지 않습니다."
                logger.warning(f"Login failed: {error_msg}")
                return False, error_msg
            
            # 2. 토큰 및 사용자 정보 추출
            tokens = result.get('tokens', {})
            user_info = result.get('user', {})
            
            access_token = tokens.get('access_token')
            session_id = tokens.get('session_id')
            expires_in = tokens.get('expires_in', 3600)
            
            if not access_token or not session_id:
                error_msg = "유효하지 않은 토큰입니다."
                logger.error(f"Login failed: {error_msg}")
                return False, error_msg
            
            # 3. 토큰 저장 및 동기화 대기
            expires_minutes = expires_in // 60
            token_set_success = self.session_manager.set_auth_tokens(
                access_token, session_id, expires_minutes
            )
            
            if not token_set_success:
                error_msg = "토큰 저장에 실패했습니다."
                logger.error(f"Login failed: {error_msg}")
                return False, error_msg
            
            # st.session_state에도 명시적으로 저장
            st.session_state['access_token'] = access_token
            st.session_state['session_id'] = session_id            
            
            # 4. 사용자 정보 저장
            st.session_state['user_info'] = user_info
            st.session_state['last_activity'] = time.time()
            
            # 5. 로그인 성공 상태 설정 (쿠키 동기화 완료 후에도 안전장치로 유지)
            st.session_state['login_success'] = True
            # st.session_state['login_timestamp'] = time.time()
            
            # 6. 동기화 상태 로깅
            sync_status = self.session_manager.get_sync_status()
            logger.info(f"Login successful for {email}. Sync status: {sync_status}")
            return True, None
        
        except Exception as e:
            error_msg = "로그인 중 오류가 발생했습니다."
            logger.error(f"Login error: {e}")
            return False, error_msg
        
    def logout(self) -> bool:
        """
        로그아웃 처리 - 동기화된 토큰 삭제
        """
        try:
            logger.info("Logout attempt")
            
            # 1. 현재 토큰 정보 가져오기
            access_token, session_id = self.session_manager.get_auth_tokens()
            
            # 2. API 로그아웃 호출 (토큰이 있는 경우)
            if access_token and session_id:
                try:
                    self.api_client.logout(access_token, session_id)
                    logger.debug("API logout called successfully")
                except Exception as e:
                    logger.warning(f"API logout failed: {e}")
            
            # 3. 로컬 상태 정리
            clear_success = self._clear_auth_state()            
                        
            logger.info(f"Logout completed. Clear success: {clear_success}")
            return True

        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
 
    def check_authentication(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        인증 상태 확인 - 개선된 로직
        
        Flow:
        1. 토큰 존재 확인 (없으면 즉시 False)
        2. 토큰 만료 확인
        3. 만료되었거나 임박하면 갱신 (서버가 Redis→DB→Cognito 순으로 처리)
        4. 갱신 성공하면 계속, 실패하면 로그아웃
        """
        try:                       
            # # 1. 로그인 성공 직후 상태 확인 (기존 로직 유지)
            # if st.session_state.get('login_success'):
            #     login_time = st.session_state.get('login_timestamp', 0)
            #     current_time = time.time()
                
            #     # 로그인 성공 후 5초 이내라면 세션 상태 우선 사용 (단축)
            #     if current_time - login_time < 5:
            #         user_info = st.session_state.get('user_info')
            #         if user_info:
            #             logger.debug("Using session state for recent login")
                        
            #             # 백그라운드에서 쿠키 동기화 상태 확인
            #             self._check_and_update_sync_status()
                        
            #             return True, user_info
            #     else:
            #         # 5초 경과 후에는 login_success 플래그 제거
            #         self._clear_login_success_flags()
            
            # 1. 토큰 기반 인증 확인
            access_token, session_id = self.session_manager.get_auth_tokens()
            
            if not session_id:
                logger.debug("No tokens found")
                return False, None

            # access_token이 없으면 즉시 갱신 시도
            if not access_token:
                logger.info("No access_token found, attempting refresh with session_id")
                refresh_success, refresh_reason = self._refresh_token(None, session_id)
                
                if refresh_success:
                    # 갱신된 토큰 다시 가져오기
                    access_token, session_id = self.session_manager.get_auth_tokens()
                    logger.info("Access token refreshed successfully from session_id only")
                    
                    # 갱신 성공 시 실패 카운터 초기화
                    if 'refresh_fail_count' in st.session_state:
                        del st.session_state['refresh_fail_count']
                else:
                    logger.error(f"Failed to refresh access_token: {refresh_reason}")
                    self._clear_auth_state()
                    st.session_state['logout_reason'] = "세션이 만료되었습니다. 다시 로그인해주세요."
                    return False, None


            # 2. 토큰 만료 및 갱신 필요 여부 확인
            token_expired = self.session_manager.is_token_expired(access_token)
            needs_refresh = self.session_manager.should_refresh_token(
                access_token, 
                settings.TOKEN_REFRESH_THRESHOLD_MINUTES
            )      

            # 3. 토큰 갱신 처리
            if token_expired or needs_refresh:
                refresh_type = "expired" if token_expired else "threshold reached"
                logger.debug(f"Token {refresh_type}, attempting refresh")
                
                refresh_success, refresh_reason = self._refresh_token(access_token, session_id)
                
                if refresh_success:
                    # 갱신된 토큰 다시 가져오기
                    access_token, session_id = self.session_manager.get_auth_tokens()
                    logger.info(f"Token refreshed successfully ({refresh_type})")
                    
                    # 갱신 성공 시 실패 카운터 초기화
                    if 'refresh_fail_count' in st.session_state:
                        del st.session_state['refresh_fail_count']
                else:
                    logger.warning(f"Token refresh failed ({refresh_type}): {refresh_reason}")
                    
                    # Refresh Token 만료 시 즉시 로그아웃
                    if refresh_reason == "refresh_token_expired":
                        logger.error("Refresh Token expired - immediate logout required")
                        self._clear_auth_state()
                        st.session_state['logout_reason'] = "세션이 만료되었습니다. 다시 로그인해주세요."
                        return False, None
                    
                    # 토큰이 완전히 만료된 경우에만 인증 상태 삭제
                    if token_expired:
                        logger.error("Token expired and refresh failed - clearing auth state")
                        self._clear_auth_state()
                        st.session_state['logout_reason'] = "토큰이 만료되었습니다. 다시 로그인해주세요."
                        return False, None
                    
                    # needs_refresh인 경우도 refresh 실패 시 재시도 제한
                    # 연속 실패 카운트 추가
                    refresh_fail_count = st.session_state.get('refresh_fail_count', 0) + 1
                    st.session_state['refresh_fail_count'] = refresh_fail_count
                    
                    logger.warning(
                        f"Token refresh failed {refresh_fail_count} time(s) - "
                        f"possible refresh token expiration"
                    )
                    
                    if refresh_fail_count >= 3:
                        # 2회 연속 실패 시 로그아웃 (Refresh Token 만료로 판단)
                        logger.error(
                            f"Token refresh failed {refresh_fail_count} times - "
                            f"clearing auth state"
                        )
                        self._clear_auth_state()
                        st.session_state['logout_reason'] = "토큰 갱신에 반복적으로 실패했습니다. 다시 로그인해주세요."
                        return False, None
                    else:
                        # 1회 실패는 경고만 (다음 체크에서 재시도)
                        logger.warning(
                            f"Token refresh failed ({refresh_fail_count}/2) - "
                            f"will retry on next check" 
                        )     
                        
            else:
                # 갱신 불필요 시 카운터 초기화
                if 'refresh_fail_count' in st.session_state:
                    del st.session_state['refresh_fail_count']

            # 4. 사용자 정보 확인 (주기적으로만 서버 확인)
            user_info = self._get_or_refresh_user_info(access_token)
            
            if user_info:
                st.session_state['last_activity'] = time.time()
                return True, user_info
            else:
                logger.warning("User info unavailable")
                self._clear_auth_state()
                return False, None
                
        except Exception as e:
            logger.error(f"Authentication check error: {e}", exc_info=True)
            self._clear_auth_state()
            return False, None

            # # 5. 서버에서 인증 상태 최종 확인 (기존 유지)
            # auth_result = self.api_client.check_auth(access_token, session_id)
            
            # if auth_result and auth_result.get('authenticated'):
            #     # 인증 성공 시 /auth/me API로 최신 사용자 정보 조회
            #     user_info = self._get_current_user_info(access_token)
                
            #     if user_info:
            #         # 최신 사용자 정보로 업데이트
            #         st.session_state.user_info = user_info
            #         st.session_state.last_auth_check = time.time()
            #         logger.debug(f"Authentication verified with updated user info: {user_info.get('email', 'unknown')}")
            #         return True, user_info
            #     else:
            #         # /auth/me 실패 시 check_auth 결과의 user_info나 세션 값 사용
            #         fallback_user_info = auth_result.get('user_info') or st.session_state.get('user_info')
            #         if fallback_user_info:
            #             st.session_state.user_info = fallback_user_info
            #             logger.warning("Using fallback user info due to /auth/me failure")
            #             return True, fallback_user_info
            #         else:
            #             # 사용자 정보 없지만 인증은 성공했으므로 최소 상태만 유지
            #             st.session_state.user_info = {"user_id": auth_result.get("user_id")}
            #             logger.warning("No detailed user info; using minimal auth state")
            #             return True, st.session_state.user_info
            # else:
            #     logger.warning("Server authentication check failed")
            #     # 서버 인증 실패 시에만 삭제
            #     self._clear_auth_state()
            #     return False, None
                
        # except Exception as e:
        #     logger.error(f"Authentication check error: {e}")
        #     # 예외 발생 시에만 삭제
        #     self._clear_auth_state()
        #     return False, None
   
 
    def _get_or_refresh_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        사용자 정보 조회 - 캐시 우선, 주기적으로만 서버 확인
        """
        try:
            # 캐시된 정보 확인
            cached_user_info = st.session_state.get('user_info')
            last_check = st.session_state.get('last_user_info_check', 0)
            current_time = time.time()
            
            # 5분마다만 서버에서 갱신
            check_interval = 300
            
            if cached_user_info and (current_time - last_check) < check_interval:
                return cached_user_info
            
            # 서버에서 최신 정보 조회
            logger.debug("Fetching fresh user info from server")
            response = self.api_client.get_current_user(access_token)
            
            if response and response.get('success'):
                user_info = response.get('user_info', {})
                
                if user_info.get('email'):
                    st.session_state['user_info'] = user_info
                    st.session_state['last_user_info_check'] = current_time
                    logger.debug(f"User info updated: {user_info['email']}")
                    return user_info
            
            # 서버 조회 실패 시 캐시 사용
            if cached_user_info:
                logger.warning("Using cached user info (server fetch failed)")
                return cached_user_info
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            # 예외 발생 시에도 캐시 사용
            return st.session_state.get('user_info') 
 
 
    def _check_and_update_sync_status(self):
        """
        쿠키 동기화 상태 확인 및 업데이트 (백그라운드 처리)
        """
        try:
            access_token = st.session_state.get('access_token')
            session_id = st.session_state.get('session_id')
            
            if access_token and session_id:
                # 동기화 상태 확인
                sync_verified = self.session_manager._verify_cookie_sync(access_token, session_id)
                
                if sync_verified:
                    # 동기화 완료되면 login_success 플래그 정리
                    self._clear_login_success_flags()
                    logger.debug("Cookie sync completed, cleared login_success flags")
                    
        except Exception as e:
            logger.debug(f"Sync status check error: {e}")
    
    def _clear_login_success_flags(self):
        """
        로그인 성공 관련 임시 플래그들 정리
        """
        flags_to_clear = ['login_success', 'login_timestamp']
        for flag in flags_to_clear:
            if flag in st.session_state:
                del st.session_state[flag]
    
    def _refresh_token(self, access_token: str, session_id: str) -> bool:
        """
        토큰 갱신 - 서버에 session_id만 전달
        서버가 Redis → Supabase → Cognito 순으로 처리
        
        Args:
            access_token: 현재 액세스 토큰 (없을 수도 있음)
            session_id: 세션 ID (필수)
        
        Returns:
            Tuple[성공여부, 실패사유]
        """
        try:
            logger.debug(f"Refreshing token for session: {session_id[:8]}...")
            
            # result = self.api_client.refresh_token(access_token, session_id)
            
            # session_id만 전달
            result = self.api_client.refresh_token(session_id)
            
            if not result:
                return False, "network_error"
            
            status_code = result.get('status_code', 0)
                
            # HTTP 401 = Refresh Token 만료 (즉시 로그아웃 필요)
            if status_code == 401:
                logger.error("Refresh Token expired (HTTP 401)")
                return False, "refresh_token_expired"    
                
            # 성공 여부 확인
            if not result.get('success'):
                error_msg = result.get('message', 'Unknown error')
                
                if status_code >= 500:
                    logger.warning(f"Token refresh server error: {error_msg} (HTTP {status_code})")
                    return False, "server_error"
                else:
                    logger.warning(f"Token refresh failed: {error_msg} (HTTP {status_code})")
                    return False, "server_error"


            # # 새로운 토큰 정보가 있으면 업데이트
            # tokens = result.get('tokens')
            # if tokens:
            #     new_access_token = tokens.get("access_token")
            #     new_session_id = tokens.get('session_id')
            #     expires_in = tokens.get('expires_in', 3600)
                
            #     if new_access_token and new_session_id:
            #         # 새로운 토큰으로 업데이트 (동기화 포함)
            #         expires_minutes = expires_in // 60
            #         update_success = self.session_manager.set_auth_tokens(
            #             new_access_token, new_session_id, expires_minutes
            #         )
                    
            #         if update_success:
            #             logger.debug("Token refresh and sync completed")
            #             return True
            #         else:
            #             logger.error("Token refresh succeeded but sync failed")
            #             return False
            
            # # 토큰 정보가 없어도 서버에서 갱신이 성공했다면 true 반환
            # logger.debug("Token refreshed on server (no new tokens provided)")
            # return True
        

            # tokens는 result의 두 번째 값 (Tuple 반환 구조)
            tokens = result.get('tokens')

            # tokens가 None인 경우 갱신 실패
            if not tokens:
                logger.warning("Token refresh failed: no tokens in response")
                return False, "no_tokens"
            
            new_access_token = tokens.get("access_token")
            new_session_id = tokens.get('session_id')
            expires_in = tokens.get('expires_in', 3600)
            
            if not new_access_token or not new_session_id:
                logger.warning(
                    f"Invalid tokens in refresh response: "
                    f"access_token={bool(new_access_token)}, "
                    f"session_id={bool(new_session_id)}"
                )
                return False, "invalid_tokens"
            
            # 세션 ID 변경 확인
            if new_session_id != session_id:
                logger.info(
                    f"Session ID changed during refresh: "
                    f"{session_id[:8]}... -> {new_session_id[:8]}..."
                )
            
            
            # 새로운 토큰으로 업데이트 (동기화 포함)
            expires_minutes = expires_in // 60
            update_success = self.session_manager.set_auth_tokens(
                new_access_token, 
                new_session_id, 
                expires_minutes
            )
            
            if not update_success:
                logger.error("Token refresh succeeded but sync failed")
                return False, "sync_failed"
             
            st.session_state['access_token'] = new_access_token
                               
            # 세션 상태 업데이트 (변경된 경우)
            if new_session_id != session_id:
                st.session_state['session_id'] = new_session_id
                logger.debug(f"Updated session_state with new session_id")
            
            # 디버깅: 동기화 상태 확인
            sync_status = self.session_manager.get_sync_status()
            logger.debug(f"Post-refresh sync status: {sync_status}")

            # 갱신 시간 기록
            # logger.info("Token refresh successful")
            st.session_state['last_token_refresh'] = time.time()
            
            return True, "success"

        except Exception as e:
            logger.error(f"Token refresh error: {e}", exc_info=True)
            return False
        
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        현재 사용자 정보 반환
        """
        return st.session_state.get("user_info")
    
    def get_auth_status(self) -> Dict[str, Any]:
        """
        현재 인증 상태 정보 반환 (디버깅용)
        """
        sync_status = self.session_manager.get_sync_status()
        auth_status = {
            'is_authenticated': sync_status['authenticated'],
            'has_user_info': bool(st.session_state.get('user_info')),
            'login_success_pending': st.session_state.get('login_success', False),
            'login_timestamp': st.session_state.get('login_timestamp'),
            **sync_status
        }
        
        return auth_status
    
    def force_sync_check(self) -> bool:
        """
        동기화 강제 확인
        """
        try:
            access_token, session_id = self.session_manager.get_auth_tokens()
            
            if not access_token or not session_id:
                return False
            
            # 서버 인증 상태 확인
            auth_result = self.api_client.check_auth(access_token, session_id)
            
            if auth_result and auth_result.get('authenticated'):
                # /auth/me를 통한 사용자 정보 추가 확인
                user_info = self._get_current_user_info(access_token)
                if user_info:
                    st.session_state.user_info = user_info
                
                logger.info("Force sync check successful")
                return True
            else:
                logger.warning("Force sync check failed")
                return False
                
        except Exception as e:
            logger.error(f"Force sync check error: {e}")
            return False

    def _get_current_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        /auth/me API를 통한 현재 사용자 정보 조회
        """
        try:
            # API 호출
            response = self.api_client.get_current_user(access_token)
            
            if response and response.get('success'):
                user_info = response.get('user_info', {})
                
                # 필수 필드 검증
                if user_info.get('email'):
                    logger.debug(f"Successfully retrieved user info for: {user_info['email']}")
                    return user_info
                else:
                    logger.warning("User info missing required fields")
                    return None
            else:
                error_msg = response.get('message', 'Unknown error') if response else 'No response'
                logger.warning(f"/auth/me API failed: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting current user info: {e}")
            return None

    def force_refresh_user_info(self) -> bool:
        """
        사용자 정보 강제 새로고침
        """
        try:
            access_token, _ = self.session_manager.get_auth_tokens()
            
            if not access_token:
                return False

            # 캐시 무시하고 서버에서 조회
            st.session_state['last_user_info_check'] = 0            
            user_info = self._get_current_user_info(access_token)
            
            if user_info:
                st.session_state.user_info = user_info
                logger.info("User info force refreshed successfully")
                return True
            else:
                logger.warning("Failed to force refresh user info")
                return False
                
        except Exception as e:
            logger.error(f"Force refresh user info error: {e}")
            return False
        
    def _clear_auth_state(self):
        """
        인증 상태 완전 초기화
        """
        # 토큰 정리
        self.session_manager.clear_auth_tokens()
        
        # 세션 상태 정리
        auth_keys = [
            'user_info', 'login_success', 'login_timestamp', 'last_token_refresh', 'refresh_fail_count', 'access_token', 'session_id',
            'is_authenticated', 'auth_checked', 'last_auth_check', 'last_activity', 'last_user_info_check'
        ]
        
        for key in auth_keys:
            if key in st.session_state:
                del st.session_state[key]
        
        logger.debug("Auth state cleared")        