"""
쿠키 관리 유틸리티
"""
from typing import Optional, Dict, Any
import streamlit as st
from streamlit_cookies_controller import CookieController
from config.settings import settings


class CookieManager:
    """쿠키 관리 클래스"""
    
    def __init__(self):
        self.controller = CookieController()
    
    def get_access_token(self) -> Optional[str]:
        """Access Token 쿠키 조회"""
        try:
            cookies = self.controller.getAll()
            return cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME)
        except Exception as e:
            st.error(f"쿠키 조회 오류: {e}")
            return None
    
    def get_session_id(self) -> Optional[str]:
        """Session ID 쿠키 조회"""
        try:
            cookies = self.controller.getAll()
            return cookies.get(settings.SESSION_ID_COOKIE_NAME)
        except Exception as e:
            st.error(f"세션 ID 조회 오류: {e}")
            return None
    
    def get_all_cookies(self) -> Dict[str, Any]:
        """모든 쿠키 조회"""
        try:
            return self.controller.getAll()
        except Exception as e:
            st.error(f"전체 쿠키 조회 오류: {e}")
            return {}
    
    def has_auth_cookies(self) -> bool:
        """인증 관련 쿠키 존재 여부 확인"""
        access_token = self.get_access_token()
        session_id = self.get_session_id()
        return bool(access_token and session_id)
    
    def clear_auth_cookies(self):
        """인증 관련 쿠키 삭제"""
        try:
            # streamlit-cookie-controller는 직접 삭제 기능이 제한적이므로
            # 백엔드 로그아웃 API 호출 후 페이지 새로고침으로 쿠키 삭제 처리
            # 실제 쿠키 삭제는 백엔드의 response.delete_cookie()에서 처리됨
            
            # 로컬 상태 초기화 (선택적)
            if hasattr(st.session_state, 'auth_cleared'):
                st.session_state.auth_cleared = True
                
        except Exception as e:
            st.error(f"쿠키 삭제 오류: {e}")
    
    def is_cookies_available(self) -> bool:
        """쿠키 컨트롤러 사용 가능 여부 확인"""
        try:
            self.controller.getAll()
            return True
        except Exception:
            return False


# 싱글톤 인스턴스
cookie_manager = CookieManager()