"""
Streamlit 애플리케이션 설정
"""
import os
from typing import Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Settings:
    """애플리케이션 설정 클래스"""
    
    # FastAPI 백엔드 설정
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://backend:8000")

    # 쿠키 설정
    ACCESS_TOKEN_COOKIE_NAME: str = "access_token"
    SESSION_ID_COOKIE_NAME: str = "session_id"
    
    # 페이지 설정
    PAGE_TITLE: str = "Pilot Dashboard"
    PAGE_ICON: str = "🔐"
    LAYOUT: str = "wide"
    INITIAL_SIDEBAR_STATE: str = "expanded"

    # 로그인 페이지 설정
    LOGIN_PAGE_TITLE: str = "로그인"
    DASHBOARD_PAGE_TITLE: str = "대시보드"

    # JWT 만료 기간
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 15

    # API 엔드포인트
    @property
    def LOGIN_ENDPOINT(self) -> str:
        return f"{self.BACKEND_URL}/auth/login"
    
    @property
    def LOGOUT_ENDPOINT(self) -> str:
        return f"{self.BACKEND_URL}/auth/logout"
    
    @property
    def REFRESH_ENDPOINT(self) -> str:
        return f"{self.BACKEND_URL}/auth/refresh"
    
    @property
    def CHECK_AUTH_ENDPOINT(self) -> str:
        return f"{self.BACKEND_URL}/auth/check"
    
    @property
    def ME_ENDPOINT(self) -> str:
        return f"{self.BACKEND_URL}/auth/me"
    
    @property
    def DASHBOARD_ENDPOINT(self) -> str:
        return f"{self.BACKEND_URL}/api/dashboard"


# 설정 인스턴스
settings = Settings()