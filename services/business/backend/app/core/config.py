from pydantic_settings import BaseSettings
from typing import Optional
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

class Settings(BaseSettings):
    # 기본 설정
    environment: str = "dev"
    debug: bool = True
    log_level: str = "DEBUG"

    # CORS 설정
    allowed_origins: list = ["http://localhost:8501", "http://frontend:8501"]
    
    # AWS Cognito 설정
    aws_region: str
    cognito_user_pool_id: str
    cognito_client_id: str
    # cognito_client_secret: str

    # Supabase 설정
    supabase_url: str
    supabase_service_key: str
    
    # Redis 설정
    redis_url: str = "redis://redis:6379"
    redis_username: str = "default"
    redis_password: str
    
    # JWT 설정
    jwt_algorithm: str = "RS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_issuer: str 
    jwt_audience: str 
    
    # 암호화 설정
    encryption_key: str
    salt_key: str
    jwt_private_key_path: Optional[str] = None
    jwt_public_key_path: Optional[str] = None
    
    # RSA 키

    # Private/Public Key 읽기
    @property
    def jwt_private_key(self):
        if self.jwt_private_key_path:
            with open(self.jwt_private_key_path, "rb") as f:
                return serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                )
        return None

    @property
    def jwt_public_key(self):
        if self.jwt_public_key_path:
            with open(self.jwt_public_key_path, "rb") as f:
                return serialization.load_pem_public_key(
                    f.read(),
                    backend=default_backend()
                )
        return None

# 전역 설정 인스턴스
settings = Settings()