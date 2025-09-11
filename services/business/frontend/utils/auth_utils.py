import streamlit as st
from typing import Optional, Dict, Any
from .api_client import APIClient

def init_session_state():
    """
    세션 상태 초기화
    """
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient()

def check_authentication() -> bool:
    """
    인증 상태 확인 및 갱신
    """
    try:
        api_client = st.session_state.api_client
        auth_status = api_client.check_auth()
        
        if auth_status.get("authenticated", False):
            if not st.session_state.authenticated:
                # 인증 상태가 변경되었으면 사용자 정보 갱신
                user_info = api_client.get_current_user()
                st.session_state.user_info = user_info
                st.session_state.authenticated = True
            return True
        else:
            st.session_state.authenticated = False
            st.session_state.user_info = None
            return False
    except Exception as e:
        st.error(f"Authentication check failed: {e}")
        return False
    
def login_user(email: str, password: str) -> tuple[bool, str]:
    """
    사용자 로그인
    """
    try:
        api_client = st.session_state.api_client
        response = api_client.login(email, password)
        
        if response.get("success", False):
            st.session_state.authenticated = True
            st.session_state.user_info = response.get("user")
            return True, "Login successful!"
        else:
            return False, response.get("message", "Login failed")
    except Exception as e:
        return False, f"Login error: {str(e)}"

def logout_user() -> tuple[bool, str]:
    """
    사용자 로그아웃
    """
    try:
        api_client = st.session_state.api_client
        response = api_client.logout()
        
        st.session_state.authenticated = False
        st.session_state.user_info = None
        
        if response.get("success", False):
            return True, "Logout successful!"
        else:
            return False, response.get("message", "Logout failed")
    except Exception as e:
        return False, f"Logout error: {str(e)}"