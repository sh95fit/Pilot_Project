"""
Streamlit 애플리케이션 설정
"""
import os
from typing import Optional
from dotenv import load_dotenv
from dataclasses import dataclass

# .env 파일 로드
load_dotenv()

class Settings:
    """애플리케이션 설정 클래스"""
    
    # 환경 설정
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    @classmethod
    def is_dev(cls) -> bool:
        """개발 환경 여부 확인"""
        return cls.ENVIRONMENT.lower() in ['dev', 'development', 'local']

    # 쿠키 설정
    COOKIE_SECURE: bool = ENVIRONMENT.lower() not in ['dev', 'development', 'local']
    COOKIE_SAMESITE: str = "lax" if ENVIRONMENT.lower() in ['dev', 'development', 'local'] else "strict"
    ACCESS_TOKEN_COOKIE_NAME: str = "access_token"
    SESSION_ID_COOKIE_NAME: str = "session_id"
    
    # 페이지 설정
    PAGE_TITLE: str = "Business Dashboard"
    PAGE_ICON: str = "📊"
    LAYOUT: str = "wide"
    INITIAL_SIDEBAR_STATE: str = "expanded"

    # 로그인 페이지 설정
    LOGIN_PAGE_TITLE: str = "로그인"
    DASHBOARD_PAGE_TITLE: str = "대시보드"
    
    # 세션 설정
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))  # 사용자 비활성 상태에서 자동 로그아웃 시간 설정
    TOKEN_REFRESH_THRESHOLD_MINUTES: int = int(os.getenv("TOKEN_REFRESH_THRESHOLD_MINUTES", "5"))   # JWT 토큰 만료 5분 전 access token 갱신 처리

    # FastAPI 백엔드 설정
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://backend:8000")
    # 요청 타임아웃 (초)
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))

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