# import streamlit as st
# from typing import Optional, Dict, Any
# from .api_client import APIClient

# def init_session_state():
#     """
#     세션 상태 초기화
#     """
#     if "authenticated" not in st.session_state:
#         st.session_state.authenticated = False
#     if "user_info" not in st.session_state:
#         st.session_state.user_info = None
#     if "api_client" not in st.session_state:
#         st.session_state.api_client = APIClient()

# def check_authentication() -> bool:
#     """
#     인증 상태 확인 및 갱신
#     """
#     try:
#         api_client = st.session_state.api_client
#         auth_status = api_client.check_auth()
        
#         if auth_status.get("authenticated", False):
#             if not st.session_state.authenticated:
#                 # 인증 상태가 변경되었으면 사용자 정보 갱신
#                 user_info = api_client.get_current_user()
#                 st.session_state.user_info = user_info
#                 st.session_state.authenticated = True
#             return True
#         else:
#             st.session_state.authenticated = False
#             st.session_state.user_info = None
#             return False
#     except Exception as e:
#         st.error(f"Authentication check failed: {e}")
#         return False
    
# def login_user(email: str, password: str) -> tuple[bool, str]:
#     """
#     사용자 로그인
#     """
#     try:
#         api_client = st.session_state.api_client
#         response = api_client.login(email, password)
        
#         if response.get("success", False):
#             st.session_state.authenticated = True
#             st.session_state.user_info = response.get("user")
#             return True, "Login successful!"
#         else:
#             return False, response.get("message", "Login failed")
#     except Exception as e:
#         return False, f"Login error: {str(e)}"

# def logout_user() -> tuple[bool, str]:
#     """
#     사용자 로그아웃
#     """
#     try:
#         api_client = st.session_state.api_client
#         response = api_client.logout()
        
#         st.session_state.authenticated = False
#         st.session_state.user_info = None
        
#         if response.get("success", False):
#             return True, "Logout successful!"
#         else:
#             return False, response.get("message", "Logout failed")
#     except Exception as e:
#         return False, f"Logout error: {str(e)}"


#######################################################################################################

import streamlit as st
from typing import Dict, Any
from utils.cookie_utils import StreamlitCookieManager
from utils.api_client import APIClient

# -----------------------------
# 세션 상태 초기화
# -----------------------------
def init_session_state():
    if "auth_checked" not in st.session_state:
        st.session_state.auth_checked = False
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "cookie_manager" not in st.session_state:
        st.session_state.cookie_manager = StreamlitCookieManager()
    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient()
    if "rerun_requested" not in st.session_state:
        st.session_state.rerun_requested = False  # rerun 플래그 초기화

    if not st.session_state.auth_checked:
        restore_auth_from_cookies()
        st.session_state.auth_checked = True

# -----------------------------
# 쿠키 복원
# -----------------------------
def restore_auth_from_cookies():
    cookie_manager = st.session_state.cookie_manager
    api_client = st.session_state.api_client

    access_token = cookie_manager.get_cookie("access_token")
    session_id = cookie_manager.get_cookie("session_id")

    if access_token and session_id:
        api_client.session.cookies.set("access_token", access_token)
        api_client.session.cookies.set("session_id", session_id)

        auth_status = api_client.check_auth()
        if auth_status.get("authenticated", False):
            user_info = api_client.get_current_user()
            if user_info:
                st.session_state.authenticated = True
                st.session_state.user_info = user_info
        else:
            clear_auth_cookies()

# -----------------------------
# 쿠키 삭제
# -----------------------------
def clear_auth_cookies():
    cookie_manager = st.session_state.cookie_manager
    for name in ["access_token", "session_id"]:
        if cookie_manager.has_cookie(name):
            cookie_manager.delete_cookie(name)
    # 세션 상태 안전하게 초기화
    st.session_state["cookies"] = {}
    st.session_state.authenticated = False
    st.session_state.user_info = None

    # rerun은 한 번만 호출
    if not st.session_state.rerun_requested:
        st.session_state.rerun_requested = True
        st.rerun()

# -----------------------------
# 로그인 상태 확인
# -----------------------------
def check_authentication() -> bool:
    """
    현재 세션 상태와 쿠키를 기반으로 인증 여부 확인
    """
    if st.session_state.get("authenticated", False):
        api_client = st.session_state.api_client
        auth_status = api_client.check_auth()
        if auth_status.get("authenticated", False):
            return True
        logout_user()
    return False

# -----------------------------
# 로그인
# -----------------------------
def login_user(email: str, password: str) -> tuple[bool, str]:
    api_client = st.session_state.api_client
    cookie_manager = st.session_state.cookie_manager

    # try:
    #     result = api_client.login(email, password)
    #     if result.get("success"):
    #         for name in ["access_token", "session_id"]:
    #             val = api_client.session.cookies.get(name)
    #             if val:
    #                 cookie_manager.set_cookie(name, val)
    #         st.session_state.authenticated = True
    #         st.session_state.user_info = result.get("user")
    #         # 로그인 성공 후 페이지 전환 (한 번만)
    #         if not st.session_state.rerun_requested:
    #             st.session_state.rerun_requested = True
    #             st.rerun()
    #         return True, "로그인 성공!"
    #     else:
    #         return False, result.get("message", "로그인 실패")
    # except Exception as e:
    #     return False, f"로그인 오류: {e}"



    try:
        res = api_client.session.post(
            f"{api_client.base_url}/auth/login",
            json={"email": email, "password": password},
            timeout=30
        )
        res.raise_for_status()
        result = res.json()

        if result.get("success"):
            # 여기서 res.cookies에서 직접 가져오기
            access_token = res.cookies.get("access_token")
            session_id = res.cookies.get("session_id")

            if access_token:
                cookie_manager.set_cookie("access_token", access_token)
            if session_id:
                cookie_manager.set_cookie("session_id", session_id)

            st.session_state.authenticated = True
            st.session_state.user_info = result.get("user")

            if not st.session_state.rerun_requested:
                st.session_state.rerun_requested = True
                st.rerun()
            return True, "로그인 성공!"
        else:
            return False, result.get("message", "로그인 실패")
    except Exception as e:
        return False, f"로그인 오류: {e}"


# -----------------------------
# 로그아웃
# -----------------------------
def logout_user() -> tuple[bool, str]:
    clear_auth_cookies()
    api_client = st.session_state.api_client
    api_client.session.cookies.clear()
    return True, "로그아웃 완료!"

# -----------------------------
# 인증 상태 정보 조회
# -----------------------------
def get_auth_status_info() -> Dict[str, Any]:
    cookie_manager = st.session_state.cookie_manager
    all_cookies = cookie_manager.get_all_cookies()
    return {
        "authenticated": st.session_state.authenticated,
        "user_info": st.session_state.user_info,
        "has_access_token": "access_token" in all_cookies,
        "has_session_id": "session_id" in all_cookies,
        "cookie_count": len(all_cookies)
    }