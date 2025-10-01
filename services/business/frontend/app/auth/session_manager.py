import streamlit as st
from streamlit_cookies_controller import CookieController
from datetime import datetime, timedelta
import jwt
from typing import Dict, Any, Optional, Tuple
import logging
import time

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self):
        # CookieController를 지연 초기화하여 세션 상태 충돌 방지
        self._cookie_controller = None
    
    @property
    def cookie_controller(self):
        """지연 초기화된 CookieController 반환"""
        if self._cookie_controller is None:
            try:
                self._cookie_controller = CookieController()
            except Exception as e:
                logger.warning(f"CookieController initialization failed: {e}")
                # CookieController 실패 시 None으로 유지하고 세션 상태만 사용
                self._cookie_controller = None
        return self._cookie_controller
        
    def set_auth_tokens(self, access_token: str, session_id: str, expires_minutes: int = 60) -> bool:
        """
        인증 토큰을 쿠키에 저장하고 동기화 완료까지 대기
        
        Args:
            access_token: JWT Access Token
            session_id: Session ID
            expires_minutes: Access Token 만료 시간 (분) - 기본 60분
        """
        try:
            # # expires 시간
            # expires = datetime.now() + timedelta(minutes=expires_minutes)
            
            # Access Token 만료 시간 (짧게 - JWT 만료와 동일)
            access_expires = datetime.now() + timedelta(minutes=expires_minutes)
            
            # Session ID 만료 시간 (길게 - 7일)
            session_expires = datetime.now() + timedelta(days=7)            
            
            
            # 1. 먼저 세션 상태에 저장 (즉시 반영)
            st.session_state['access_token'] = access_token
            st.session_state['session_id'] = session_id
            st.session_state['access_token_expires'] = access_expires
            st.session_state['session_expires'] = session_expires
            st.session_state['authenticated'] = True
            logger.debug("Tokens stored in session state immediately")
            
            # 2. CookieController를 사용하여 쿠키 설정 시도
            cookie_set_success = self._set_cookies(access_token, session_id, access_expires, session_expires)
            
            if cookie_set_success:
                # 3. 토큰 동기화 대기
                sync_success = self.wait_for_token_sync(access_token, session_id, max_wait_seconds=3)
                
                if sync_success:
                    st.session_state['cookies_synced'] = True
                    logger.debug("Tokens successfully synced to cookies")
                else:
                    st.session_state['cookies_synced'] = False
                    logger.warning("Token sync timeout, but proceeding with session state")
            else:
                st.session_state['cookies_synced'] = False
                logger.warning("Cookie setting failed, using session state only")

            return True

        except Exception as e:
            logger.error(f"Error setting auth tokens: {e}")
            return False
    
    def _set_cookies(
        self, 
        access_token: str, 
        session_id: str, 
        access_expires: datetime,
        session_expires: datetime
    ) -> bool:
        """
        쿠키 설정 (내부 메서드)
        
        Args:
            access_token: JWT Access Token
            session_id: Session ID
            access_expires: Access Token 쿠키 만료 시간 (짧음, 60분)
            session_expires: Session ID 쿠키 만료 시간 (길음, 7일)
        """
        try:
            if self.cookie_controller:
                # 쿠키 설정
                self.cookie_controller.set(
                    'access_token',
                    access_token,
                    expires=access_expires,
                    secure=True,
                    # httponly=True,
                    # samesite="strict"
                )
                
                self.cookie_controller.set(
                    'session_id',
                    session_id,
                    expires=session_expires,
                    secure=True,
                    # httponly=True,
                    # samesite="strict"
                )
                
                logger.debug(
                    f"Cookies set: "
                    f"access_token expires in {(access_expires - datetime.now()).total_seconds()/60:.0f}m, "
                    f"session_id expires in {(session_expires - datetime.now()).total_seconds()/3600:.0f}h"
                )
                return True
            else:
                logger.warning("CookieController not available")
                return False
                
        except Exception as e:
            logger.warning(f"CookieController set failed: {e}")
            return False
    
    def wait_for_token_sync(self, access_token: str, session_id: str, max_wait_seconds: int = 3) -> bool:
        """
        토큰 동기화 완료까지 대기
        """
        if not self.cookie_controller:
            logger.debug("No CookieController available, skipping sync wait")
            return False
        
        start_time = time.time()
        check_interval = 0.1  # 100ms 간격으로 확인
        
        logger.debug(f"Waiting for token sync (max {max_wait_seconds}s)...")
        
        while time.time() - start_time < max_wait_seconds:
            try:
                # 쿠키에서 토큰 확인
                cookie_access_token = self.cookie_controller.get('access_token')
                cookie_session_id = self.cookie_controller.get('session_id')
                
                if (cookie_access_token == access_token and 
                    cookie_session_id == session_id):
                    elapsed = time.time() - start_time
                    logger.debug(f"Token sync completed in {elapsed:.2f}s")
                    return True
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.debug(f"Token sync check error: {e}")
                time.sleep(check_interval)
        
        elapsed = time.time() - start_time
        logger.warning(f"Token sync timeout after {elapsed:.2f}s")
        return False
        
    def get_auth_tokens(self) -> Tuple[Optional[str], Optional[str]]:
        """
        쿠키에서 인증 토큰 조회 - 세션 상태 우선, 쿠키는 보조
        """
        try:
            access_token = None
            session_id = None
            
            # 1. 세션 상태에서 조회 (우선)
            if 'access_token' in st.session_state and 'session_id' in st.session_state:
                access_token = st.session_state.get('access_token')
                session_id = st.session_state.get('session_id')
                logger.debug("Tokens retrieved from session state")
                
                # 쿠키 동기화 상태 확인 (아직 동기화되지 않은 경우)
                if not st.session_state.get('cookies_synced', False):
                    self._verify_cookie_sync(access_token, session_id)
                
                return access_token, session_id
            
            # 2. 세션 상태에 없으면 쿠키에서 조회 시도
            if self.cookie_controller:
                try:
                    cookie_access_token = self.cookie_controller.get('access_token')
                    cookie_session_id = self.cookie_controller.get('session_id')
                    
                    # Session ID만 있어도 반환 (Access Token 만료되어도 갱신 가능)
                    if cookie_session_id:
                        access_token = cookie_access_token  # None일 수 있음
                        session_id = cookie_session_id
                        
                        # 세션 상태에 복원
                        if session_id:
                            st.session_state['session_id'] = session_id
                        if access_token:
                            st.session_state['access_token'] = access_token
                            
                        st.session_state['authenticated'] = True
                        st.session_state['cookies_synced'] = True
                        
                        logger.debug(
                            f"Tokens retrieved from cookies: "
                            f"access_token={'present' if access_token else 'missing'}, "
                            f"session_id=present"
                        )
                        return access_token, session_id
                        
                except Exception as e:
                    logger.warning(f"CookieController get failed: {e}")
            
            return None, None
        
        except Exception as e:
            logger.error(f"Error getting auth tokens: {e}")
            return None, None        
        
    def _verify_cookie_sync(self, expected_access_token: str, expected_session_id: str) -> bool:
        """
        쿠키 동기화 상태 확인 및 업데이트
        """
        try:
            if self.cookie_controller:
                actual_access_token = self.cookie_controller.get('access_token')
                actual_session_id = self.cookie_controller.get('session_id')
                
                if (actual_access_token == expected_access_token and 
                    actual_session_id == expected_session_id):
                    st.session_state['cookies_synced'] = True
                    logger.debug("Cookie sync verified and updated")
                    return True
                else:
                    logger.debug("Cookie sync verification failed - tokens don't match")
                    return False
        except Exception as e:
            logger.warning(f"Cookie sync verification failed: {e}")
            return False
         
    def clear_auth_tokens(self) -> bool:
        """
        인증 토큰 삭제 - 동기화된 삭제 처리
        """
        try:
            # 1. 세션 상태에서 즉시 삭제
            session_keys_to_clear = [
                'access_token', 'session_id', 'token_expires', 
                'authenticated', 'user_info', 'cookies_synced'
            ]
            
            for key in session_keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            logger.debug("Tokens cleared from session state")
            
            # 2. CookieController에서 삭제 시도
            if self.cookie_controller:
                try:
                    # 쿠키 존재 여부 먼저 확인
                    existing_access_token = self.cookie_controller.get('access_token')
                    existing_session_id = self.cookie_controller.get('session_id')
                    
                    if existing_access_token:
                        self.cookie_controller.remove('access_token')
                        logger.debug("Access token removed from CookieController")
                    
                    if existing_session_id:
                        self.cookie_controller.remove('session_id')
                        logger.debug("Session ID removed from CookieController")
                    
                    # 실제로 삭제할 쿠키가 있었다면 대기
                    if existing_access_token or existing_session_id:
                        self._wait_for_cookie_removal()
                    
                except Exception as e:
                    logger.warning(f"CookieController remove operation failed: {e}")
                    # 쿠키 삭제 실패해도 세션은 정리되었으므로 계속 진행
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing auth tokens: {e}")
            return False
    
    def _wait_for_cookie_removal(self, max_wait_seconds: int = 1) -> bool:
        """
        쿠키 삭제 완료까지 대기
        """
        if not self.cookie_controller:
            return False
        
        start_time = time.time()
        check_interval = 0.1
        
        while time.time() - start_time < max_wait_seconds:
            try:
                access_token = self.cookie_controller.get('access_token')
                session_id = self.cookie_controller.get('session_id')
                
                if not access_token and not session_id:
                    elapsed = time.time() - start_time
                    logger.debug(f"Cookie removal completed in {elapsed:.2f}s")
                    return True
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.debug(f"Cookie removal check error: {e}")
                time.sleep(check_interval)
        
        logger.debug("Cookie removal check timeout")
        return False
            
    def is_token_expired(self, token: str) -> bool:
        """
        JWT 토큰 만료 확인
        """
        try:
            # 토큰을 검증 없이 디코드하여 만료 시간 확인
            payload = jwt.decode(token, options={"verify_signature": False})
            exp_timestamp = payload.get('exp')
            
            if exp_timestamp:
                exp_datetime = datetime.fromtimestamp(exp_timestamp)
                return datetime.now() >= exp_datetime
            
            return True   # exp가 없으면 만료된 것으로 간주
        
        except Exception as e:
            logger.error(f"Error checking token expiration: {e}")
            return True
    
    def should_refresh_token(self, token: str, threshold_minutes: int = 5) -> bool:
        """
        토큰 갱신이 필요한지 확인
        """
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            exp_timestamp = payload.get('exp')
            
            if exp_timestamp:
                exp_datetime = datetime.fromtimestamp(exp_timestamp)
                threshold_datetime = datetime.now() + timedelta(minutes=threshold_minutes)
                return threshold_datetime >= exp_datetime
            
            return True
        
        except Exception as e:
            logger.error(f"Error checking token refresh need: {e}")
            return True
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        현재 동기화 상태 정보 반환 (디버깅용)
        """
        return {
            'has_session_tokens': bool(
                st.session_state.get('access_token') and 
                st.session_state.get('session_id')
            ),
            'cookies_synced': st.session_state.get('cookies_synced', False),
            'authenticated': st.session_state.get('authenticated', False),
            'cookie_controller_available': self.cookie_controller is not None
        }