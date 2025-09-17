import requests
import streamlit as st
from typing import Dict, Any, Optional
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self):
        self.base_url = settings.BACKEND_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
    def login(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        로그인 API 호출
        """
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json={"email": email, "password": password}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Login failed: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"Login API error: {e}")
            return None
    
    def refresh_token(self, access_token: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        토큰 갱신 API 호출
        """
        try:
            # Cookie 헤더로 전송 (Streamlit -> Fastapi)
            headers = {
                'cookie': f"access_token={access_token}; session_id={session_id}"
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/refresh",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Token refresh failed: {response.status_code}")
                return None
        
        except Exception as e:
            logger.error(f"Token refresh API error: {e}")
            return None
    
    def logout(self, access_token: str, session_id: str) -> bool:
        """
        로그아웃 호출
        """
        try:
            headers = {
                'cookie': f"access_token={access_token}; session_id={session_id}"
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/logout",
                headers=headers
            )
            
            return response.status_code == 200
    
        except Exception as e:
            logger.error(f"Logout API error: {e}")
            return False
        
    def check_auth(self, access_token: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        인증 상태 확인 API 호출
        """
        try:
            headers = {
                'cookie': f'access_token={access_token}; session_id={session_id}'
            }
            
            response = self.session.get(
                f"{self.base_url}/auth/check",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        
        except Exception as e:
            logger.error(f"Auth check API error: {e}")
            return None
    
                