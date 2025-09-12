# import requests
# from typing import Dict, Any, Optional
# import os

# class APIClient:
#     def __init__(self, base_url: str = None):
#         self.base_url = base_url or os.getenv("BACKEND_URL", "http://backend:8000")
#         self.session = requests.Session()
        
#     def login(self, email: str, password: str) -> Dict[str, Any]:
#         """
#         로그인 API 호출
#         """
#         try:
#             response = self.session.post(
#                 f"{self.base_url}/auth/login",
#                 json={"email":email, "password":password},
#                 timeout=30
#             )
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             return {"success": False, "message": f"Login failed: {str(e)}"}
        
#     def logout(self) -> Dict[str, Any]:
#         """
#         로그아웃 API 호출
#         """
#         try:
#             response = self.session.post(
#                 f"{self.base_url}/auth/logout",
#                 timeout=30                
#             )
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             return {"success": False, "message": f"Logout failed: {str(e)}"}
    
#     def check_auth(self) -> Dict[str, Any]:
#         """
#         인증 상태 확인
#         """
#         try:
#             response = self.session.get(
#                 f"{self.base_url}/auth/check",
#                 timeout=30
#             )
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             return {"authenticated": False, "error": str(e)}
        
#     def get_current_user(self) -> Optional[Dict[str, Any]]:
#         """
#         현재 사용자 정보 조회
#         """
#         try:
#             response = self.session.get(
#                 f"{self.base_url}/auth/me",
#                 timeout=30
#             )
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             return None
    
#     def get_dashboard_data(self) -> Dict[str, Any]:
#         """
#         대시보드 데이터 조회 (샘플)
#         """
#         try:
#             response = self.session.get(
#                 f"{self.base_url}/api/dashboard",
#                 timeout=30
#             )
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             return {"error": str(e)}
        
##########################################################################################        
        
# import requests
# from typing import Dict, Any, Optional
# import os
# import streamlit as st

# class APIClient:
#     def __init__(self, base_url: str = None):
#         self.base_url = base_url or os.getenv("BACKEND_URL", "http://backend:8000")
#         self.session = requests.Session()
        
#         # 기존 쿠키 복원
#         self._restore_cookies()
    
#     def _restore_cookies(self):
#         """세션 상태에서 쿠키 복원"""
#         try:
#             if hasattr(st.session_state, 'cookie_manager'):
#                 cookie_manager = st.session_state.cookie_manager
                
#                 access_token = cookie_manager.get_cookie("access_token")
#                 session_id = cookie_manager.get_cookie("session_id")
                
#                 if access_token:
#                     self.session.cookies.set("access_token", access_token)
#                 if session_id:
#                     self.session.cookies.set("session_id", session_id)
#         except Exception:
#             # 복원 실패는 무시 (초기 로딩 시 정상)
#             pass
    
#     def login(self, email: str, password: str) -> Dict[str, Any]:
#         """로그인 API 호출"""
#         try:
#             response = self.session.post(
#                 f"{self.base_url}/auth/login",
#                 json={"email": email, "password": password},
#                 timeout=30
#             )
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             return {"success": False, "message": f"로그인 실패: {str(e)}"}
    
#     def logout(self) -> Dict[str, Any]:
#         """로그아웃 API 호출"""
#         try:
#             response = self.session.post(
#                 f"{self.base_url}/auth/logout",
#                 timeout=30
#             )
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             return {"success": False, "message": f"로그아웃 실패: {str(e)}"}
    
#     def check_auth(self) -> Dict[str, Any]:
#         """인증 상태 확인"""
#         try:
#             response = self.session.get(
#                 f"{self.base_url}/auth/check",
#                 timeout=10
#             )
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             return {"authenticated": False, "error": str(e)}
    
#     def get_current_user(self) -> Optional[Dict[str, Any]]:
#         """현재 사용자 정보 조회"""
#         try:
#             response = self.session.get(
#                 f"{self.base_url}/auth/me",
#                 timeout=30
#             )
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             return None
    
#     def get_dashboard_data(self) -> Dict[str, Any]:
#         """대시보드 데이터 조회"""
#         try:
#             response = self.session.get(
#                 f"{self.base_url}/api/dashboard",
#                 timeout=30
#             )
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             return {"error": str(e)}


##########################################################################################

import requests
import os
import streamlit as st

class APIClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("BACKEND_URL", "http://backend:8000")
        self.session = requests.Session()

    def login(self, email: str, password: str):
        try:
            res = self.session.post(f"{self.base_url}/auth/login", json={"email": email, "password": password}, timeout=30)
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            return {"success": False, "message": str(e)}

    def logout(self):
        try:
            res = self.session.post(f"{self.base_url}/auth/logout", timeout=30)
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            return {"success": False, "message": str(e)}

    def check_auth(self):
        try:
            res = self.session.get(f"{self.base_url}/auth/check", timeout=10)
            res.raise_for_status()
            return res.json()
        except requests.RequestException:
            return {"authenticated": False}

    def get_current_user(self):
        try:
            res = self.session.get(f"{self.base_url}/auth/me", timeout=30)
            res.raise_for_status()
            return res.json()
        except requests.RequestException:
            return None

    def get_dashboard_data(self):
        try:
            res = self.session.get(f"{self.base_url}/api/dashboard", timeout=30)
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            return {"error": str(e)}
