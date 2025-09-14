"""
세션 상태 관리 유틸리티
"""
from typing import Optional, Dict, Any
import streamlit as st
from utils.auth_client import auth_client
from utils.cookie_manager import cookie_manager


class SessionManager:
    """세션 관리 클래스"""
    
    # 세션 키 상수
    USER_KEY = "user"
    AUTHENTICATED_KEY = "authenticated"
    LOGIN_ATTEMPTED_KEY = "login_attempted"
    USER_INFO_KEY = "user_info"
    
    @staticmethod
    def initialize_session():
        """세션 상태 초기화"""
        if SessionManager.AUTHENTICATED_KEY not in st.session_state:
            st.session_state[SessionManager.AUTHENTICATED_KEY] = False
        
        if SessionManager.USER_KEY not in st.session_state:
            st.session_state[SessionManager.USER_KEY] = None
        
        if SessionManager.LOGIN_ATTEMPTED_KEY not in st.session_state:
            st.session_state[SessionManager.LOGIN_ATTEMPTED_KEY] = False
        
        if SessionManager.USER_INFO_KEY not in st.session_state:
            st.session_state[SessionManager.USER_INFO_KEY] = None
    
    @staticmethod
    def is_authenticated() -> bool:
        """인증 상태 확인"""
        SessionManager.initialize_session()
        return st.session_state.get(SessionManager.AUTHENTICATED_KEY, False)
    
    @staticmethod
    def get_user() -> Optional[Dict[str, Any]]:
        """현재 사용자 정보 반환"""
        SessionManager.initialize_session()
        return st.session_state.get(SessionManager.USER_KEY)
    
    @staticmethod
    def get_user_info() -> Optional[Dict[str, Any]]:
        """상세 사용자 정보 반환"""
        SessionManager.initialize_session()
        return st.session_state.get(SessionManager.USER_INFO_KEY)
    
    @staticmethod
    def set_user(user_data: Dict[str, Any]):
        """사용자 정보 설정"""
        st.session_state[SessionManager.USER_KEY] = user_data
        st.session_state[SessionManager.AUTHENTICATED_KEY] = True
    
    @staticmethod
    def set_user_info(user_info: Dict[str, Any]):
        """상세 사용자 정보 설정"""
        st.session_state[SessionManager.USER_INFO_KEY] = user_info
    
    @staticmethod
    def clear_session():
        """세션 정보 클리어"""
        st.session_state[SessionManager.USER_KEY] = None
        st.session_state[SessionManager.AUTHENTICATED_KEY] = False
        st.session_state[SessionManager.LOGIN_ATTEMPTED_KEY] = False
        st.session_state[SessionManager.USER_INFO_KEY] = None
    
    @staticmethod
    def check_authentication() -> bool:
        """
        실제 인증 상태 확인 (쿠키 + 백엔드 확인)
        
        Returns:
            bool: 인증 여부
        """
        SessionManager.initialize_session()
        
        # 1. 쿠키 확인
        if not cookie_manager.has_auth_cookies():
            SessionManager.clear_session()
            return False
        
        # 2. 세션 상태가 이미 인증되어 있고, 사용자 정보가 있다면 재검증 생략
        if (SessionManager.is_authenticated() and 
            SessionManager.get_user() is not None):
            return True
        
        # 3. 백엔드 인증 상태 확인
        is_auth, auth_data = auth_client.check_auth()
        
        if is_auth and auth_data:
            # 인증 성공 시 세션 설정
            SessionManager.set_user(auth_data)
            
            # 상세 사용자 정보도 가져오기
            success, user_info, _ = auth_client.get_user_info()
            if success and user_info:
                SessionManager.set_user_info(user_info)
            
            return True
        else:
            # 인증 실패 시 세션 클리어
            SessionManager.clear_session()
            return False
    
    @staticmethod
    def login(email: str, password: str) -> tuple[bool, Optional[str]]:
        """
        로그인 처리
        
        Args:
            email: 이메일
            password: 비밀번호
            
        Returns:
            tuple[bool, Optional[str]]: (성공여부, 에러메시지)
        """
        st.session_state[SessionManager.LOGIN_ATTEMPTED_KEY] = True
        
        success, response_data, error_msg = auth_client.login(email, password)
        
        if success and response_data:
            # ✅ 백엔드에서 내려준 토큰(body 포함)
            tokens = response_data.get("tokens", {})

            if tokens:
                try:
                    # Access Token 저장
                    cookie_manager.controller.set(
                        settings.ACCESS_TOKEN_COOKIE_NAME,
                        tokens.get("access_token"),
                        max_age=settings.jwt_access_token_expire_minutes * 60
                    )

                    # Session ID 저장
                    cookie_manager.controller.set(
                        settings.SESSION_ID_COOKIE_NAME,
                        tokens.get("session_id"),
                        max_age=7 * 24 * 60 * 60  # 7일
                    )
                except Exception as e:
                    st.error(f"쿠키 저장 오류: {e}")
                    return False, "쿠키 저장 실패"

            # 로그인 성공 시 페이지 새로고침하여 쿠키 반영
            st.rerun()
            return True, None
        else:
            return False, error_msg
        

    @staticmethod
    def logout() -> tuple[bool, Optional[str]]:
        """
        로그아웃 처리
        
        Returns:
            tuple[bool, Optional[str]]: (성공여부, 에러메시지)
        """
        try:
            # 1. 백엔드 로그아웃 API 호출
            success, error_msg = auth_client.logout()
            
            # 2. 로컬 세션 클리어 (성공 여부와 관계없이)
            SessionManager.clear_session()
            
            # 3. 쿠키 클리어 플래그 설정
            cookie_manager.clear_auth_cookies()
            
            if success:
                # 4. 성공 시 페이지 새로고침하여 쿠키 반영
                st.success("✅ 로그아웃되었습니다.")
                # 잠시 대기 후 리다이렉트
                import time
                time.sleep(1)
                st.switch_page("main.py")
                return True, None
            else:
                # 5. 실패해도 로컬에서는 로그아웃 처리하고 리다이렉트
                st.warning("⚠️ 서버 로그아웃에 실패했지만, 로컬 세션은 종료되었습니다.")
                import time
                time.sleep(1)
                st.switch_page("main.py")
                return False, error_msg
                
        except Exception as e:
            # 6. 예외 발생 시에도 로컬 세션 클리어하고 리다이렉트
            SessionManager.clear_session()
            st.error(f"로그아웃 중 오류 발생: {str(e)}")
            import time
            time.sleep(1)
            st.switch_page("main.py")
            return False, str(e)
    
    @staticmethod
    def require_auth():
        """
        인증 필수 데코레이터 역할
        인증되지 않은 경우 로그인 페이지로 리다이렉트
        """
        if not SessionManager.check_authentication():
            st.switch_page("main.py")  # 로그인 페이지로 리다이렉트
            st.stop()


# 편의 함수들
def get_current_user() -> Optional[Dict[str, Any]]:
    """현재 사용자 정보 반환"""
    return SessionManager.get_user()

def get_current_user_info() -> Optional[Dict[str, Any]]:
    """현재 상세 사용자 정보 반환"""
    return SessionManager.get_user_info()

def is_authenticated() -> bool:
    """인증 상태 확인"""
    return SessionManager.check_authentication()

def require_auth():
    """인증 필수"""
    SessionManager.require_auth()