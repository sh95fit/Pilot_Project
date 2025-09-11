import requests
from typing import Dict, Any, Optional
import os

class APIClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("BACKEND_URL", "http://backend:8000")
        self.session = requests.Session()
        
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        로그인 API 호출
        """
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json={"email":email, "password":password},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "message": f"Login failed: {str(e)}"}
        
    def logout(self) -> Dict[str, Any]:
        """
        로그아웃 API 호출
        """
        try:
            response = self.session.post(
                f"{self.base_url}/auth/logout",
                timeout=30                
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "message": f"Logout failed: {str(e)}"}
    
    def check_auth(self) -> Dict[str, Any]:
        """
        인증 상태 확인
        """
        try:
            response = self.session.get(
                f"{self.base_url}/auth/check",
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"authenticated": False, "error": str(e)}
        
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        현재 사용자 정보 조회
        """
        try:
            response = self.session.get(
                f"{self.base_url}/auth/me",
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return None
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        대시보드 데이터 조회 (샘플)
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/dashboard",
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
        
    