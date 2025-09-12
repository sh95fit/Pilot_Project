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


# import streamlit as st
# from typing import Optional, Dict, Any
# from .api_client import APIClient
# from .cookie_utils import StreamlitCookieManager
# import time

# # 쿠키 매니저 전역 인스턴스
# @st.cache_resource
# def get_cookie_manager():
#     return StreamlitCookieManager()

# def init_session_state():
#     """세션 상태 초기화 및 쿠키에서 인증 상태 복원"""
    
#     # 기본 세션 상태 초기화
#     if "authenticated" not in st.session_state:
#         st.session_state.authenticated = False
#     if "user_info" not in st.session_state:
#         st.session_state.user_info = None
#     if "api_client" not in st.session_state:
#         st.session_state.api_client = APIClient()
#     if "auth_checked" not in st.session_state:
#         st.session_state.auth_checked = False
    
#     # 쿠키 매니저 초기화 (한 번만)
#     if "cookie_manager" not in st.session_state:
#         st.session_state.cookie_manager = get_cookie_manager()
    
#     # 쿠키에서 인증 상태 복원 (최초 한 번만)
#     if not st.session_state.auth_checked:
#         restore_auth_from_cookies()
#         st.session_state.auth_checked = True

# def restore_auth_from_cookies():
#     """쿠키에서 인증 상태 복원"""
#     try:
#         cookie_manager = st.session_state.cookie_manager
        
#         # 브라우저 쿠키에서 토큰 정보 확인
#         if cookie_manager.has_cookie("access_token") and cookie_manager.has_cookie("session_id"):
#             access_token = cookie_manager.get_cookie("access_token")
#             session_id = cookie_manager.get_cookie("session_id")
            
#             if access_token and session_id:
#                 # API 클라이언트에 쿠키 설정
#                 api_client = st.session_state.api_client
#                 api_client.session.cookies.set("access_token", access_token)
#                 api_client.session.cookies.set("session_id", session_id)
                
#                 # 서버에서 인증 상태 확인
#                 auth_status = api_client.check_auth()
#                 if auth_status.get("authenticated", False):
#                     # 사용자 정보 가져오기
#                     user_info = api_client.get_current_user()
#                     if user_info:
#                         st.session_state.authenticated = True
#                         st.session_state.user_info = user_info
#                         st.info("세션이 복원되었습니다.", icon="🔄")
#                 else:
#                     # 인증 실패 시 쿠키 정리
#                     clear_auth_cookies()
                    
#     except Exception as e:
#         st.warning(f"세션 복원 중 오류 발생: {e}")
#         clear_auth_cookies()

# def clear_auth_cookies():
#     """인증 관련 쿠키 모두 삭제"""
#     try:
#         cookie_manager = st.session_state.cookie_manager
#         cookie_manager.delete_cookie("access_token")
#         cookie_manager.delete_cookie("session_id")
#     except Exception as e:
#         st.error(f"쿠키 삭제 실패: {e}")

# def check_authentication() -> bool:
#     """현재 인증 상태 확인"""
#     try:
#         if not st.session_state.authenticated:
#             return False
        
#         # API 서버에 인증 상태 확인 (주기적)
#         api_client = st.session_state.api_client
#         auth_status = api_client.check_auth()
        
#         if auth_status.get("authenticated", False):
#             return True
#         else:
#             # 인증 실패 시 로그아웃 처리
#             logout_user()
#             return False
            
#     except Exception as e:
#         st.error(f"인증 확인 실패: {e}")
#         logout_user()
#         return False

# def login_user(email: str, password: str) -> tuple[bool, str]:
#     """사용자 로그인"""
#     try:
#         api_client = st.session_state.api_client
#         cookie_manager = st.session_state.cookie_manager
        
#         # 로그인 API 호출
#         response = api_client.session.post(
#             f"{api_client.base_url}/auth/login",
#             json={"email": email, "password": password},
#             timeout=30
#         )
        
#         if response.status_code == 200:
#             result = response.json()
            
#             if result.get("success", False):
#                 # 서버에서 설정된 쿠키를 브라우저에 동기화
#                 sync_cookies_to_browser(api_client.session, cookie_manager)
                
#                 # 세션 상태 업데이트
#                 st.session_state.authenticated = True
#                 st.session_state.user_info = result.get("user")
                
#                 return True, "로그인 성공!"
#             else:
#                 return False, result.get("message", "로그인 실패")
#         else:
#             error_data = response.json() if response.content else {}
#             return False, error_data.get("detail", "로그인 실패")
            
#     except Exception as e:
#         return False, f"로그인 오류: {str(e)}"

# def logout_user() -> tuple[bool, str]:
#     """사용자 로그아웃"""
#     try:
#         api_client = st.session_state.api_client
#         cookie_manager = st.session_state.cookie_manager
        
#         # 서버에 로그아웃 요청
#         try:
#             response = api_client.logout()
#         except:
#             response = {"success": False, "message": "서버 연결 실패"}
        
#         # 세션 상태 초기화
#         st.session_state.authenticated = False
#         st.session_state.user_info = None
        
#         # 브라우저 쿠키 삭제
#         clear_auth_cookies()
        
#         # API 클라이언트 쿠키도 삭제
#         api_client.session.cookies.clear()
        
#         return True, "로그아웃 완료!"
        
#     except Exception as e:
#         # 오류 발생해도 로그아웃은 진행
#         st.session_state.authenticated = False
#         st.session_state.user_info = None
#         clear_auth_cookies()
#         return False, f"로그아웃 오류: {str(e)}"

# def sync_cookies_to_browser(requests_session, cookie_manager):
#     """requests 세션의 쿠키를 브라우저 쿠키로 동기화"""
#     try:
#         for cookie in requests_session.cookies:
#             if cookie.name in ["access_token", "session_id"]:
#                 # 만료 시간 계산
#                 expires_days = 7 if cookie.name == "session_id" else 1
                
#                 # 브라우저에 쿠키 설정
#                 cookie_manager.set_cookie(
#                     name=cookie.name,
#                     value=cookie.value,
#                     expires_days=expires_days
#                 )
#     except Exception as e:
#         st.warning(f"쿠키 동기화 실패: {e}")

# def get_auth_status_info() -> Dict[str, Any]:
#     """현재 인증 상태 상세 정보"""
#     try:
#         cookie_manager = st.session_state.cookie_manager
#         all_cookies = cookie_manager.get_all_cookies()
        
#         return {
#             "authenticated": st.session_state.authenticated,
#             "user_info": st.session_state.user_info,
#             "has_access_token": "access_token" in all_cookies,
#             "has_session_id": "session_id" in all_cookies,
#             "cookie_count": len(all_cookies)
#         }
#     except Exception:
#         return {"authenticated": False, "error": "상태 확인 실패"}


#############################################################################################


import streamlit as st
from typing import Dict, Any
from .cookie_utils import get_cookie_manager
from .api_client import APIClient

def init_session_state():
    """세션 상태 초기화 및 쿠키 복원"""
    if "auth_checked" not in st.session_state:
        st.session_state.auth_checked = False

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "user_info" not in st.session_state:
        st.session_state.user_info = None

    if "cookie_manager" not in st.session_state:
        st.session_state.cookie_manager = get_cookie_manager()

    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient()

    if not st.session_state.auth_checked:
        restore_auth_from_cookies()
        st.session_state.auth_checked = True

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

def clear_auth_cookies():
    cookie_manager = st.session_state.cookie_manager
    cookie_manager.delete_cookie("access_token")
    cookie_manager.delete_cookie("session_id")

def check_authentication() -> bool:
    if not st.session_state.authenticated:
        return False
    api_client = st.session_state.api_client
    auth_status = api_client.check_auth()
    if auth_status.get("authenticated", False):
        return True
    logout_user()
    return False

def login_user(email: str, password: str) -> tuple[bool, str]:
    api_client = st.session_state.api_client
    cookie_manager = st.session_state.cookie_manager

    try:
        result = api_client.login(email, password)
        if result.get("success"):
            for name in ["access_token", "session_id"]:
                val = api_client.session.cookies.get(name)
                if val:
                    cookie_manager.set_cookie(name, val)
            st.session_state.authenticated = True
            st.session_state.user_info = result.get("user")
            return True, "로그인 성공!"
        else:
            return False, result.get("message", "로그인 실패")
    except Exception as e:
        return False, f"로그인 오류: {e}"

def logout_user() -> tuple[bool, str]:
    api_client = st.session_state.api_client
    clear_auth_cookies()
    api_client.session.cookies.clear()
    st.session_state.authenticated = False
    st.session_state.user_info = None
    return True, "로그아웃 완료!"

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
