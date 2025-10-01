from pydantic_settings import BaseSettings
from typing import Optional
import os
import logging

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

import paramiko

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # 기본 설정
    environment: str = "dev"
    debug: bool = True
    log_level: str = "DEBUG"

    # CORS 설정
    allowed_origins: list = ["http://localhost:8501", "http://frontend:8501", "http://127.0.0.1:8501", "https://prototype.lunchlab.me"]
    
    # AWS Cognito 설정
    aws_region: str
    cognito_user_pool_id: str
    cognito_client_id: str
    # cognito_client_secret: str

    # Supabase 설정 (Auth - lunchlab_erp)
    supabase_url: str
    supabase_service_key: str
    
    # Supabase 설정 (Data - lunchlab)
    supabase_data_url: str
    supabase_data_service_key: str
    
    # MySQL by SSH Tunneling
    ssh_host: str
    ssh_port: int 
    ssh_user: str
    ssh_key_path: str
    
    # SSH 키 property 추가
    @property
    def ssh_private_key(self):
        """SSH private key 객체 반환"""
        if self.ssh_key_path and os.path.exists(self.ssh_key_path):
            try:
                # paramiko 호환 키 객체 생성
                return paramiko.RSAKey.from_private_key_file(self.ssh_key_path)
            except paramiko.ssh_exception.SSHException:
                try:
                    # ED25519 키 시도
                    return paramiko.Ed25519Key.from_private_key_file(self.ssh_key_path)
                except paramiko.ssh_exception.SSHException:
                    try:
                        # ECDSA 키 시도
                        return paramiko.ECDSAKey.from_private_key_file(self.ssh_key_path)
                    except paramiko.ssh_exception.SSHException:
                        logger.error(f"Unsupported SSH key format: {self.ssh_key_path}")
                        return None
            except Exception as e:
                logger.error(f"Error loading SSH private key: {e}")
                return None
        return None
    
    @property 
    def ssh_private_key_string(self):
        """SSH private key를 문자열로 반환 (sshtunnel 호환)"""
        if self.ssh_key_path and os.path.exists(self.ssh_key_path):
            try:
                with open(self.ssh_key_path, 'r') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading SSH key file: {e}")
                return None
        return None
    
    
    
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_main_database: str
    mysql_account_database: str
    
    # Redis 설정
    redis_url: str = "redis://redis:6379"
    redis_username: str = "default"
    redis_password: str
    
    # JWT 설정
    refresh_token_expire_days: int = 7
    jwt_algorithm: str = "RS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_issuer: str 
    jwt_audience: str 
    
    # 암호화 설정
    encryption_key: str
    salt_key: str
    jwt_private_key_path: Optional[str] = None
    jwt_public_key_path: Optional[str] = None
    
    # Session Settings
    allow_multiple_sessions: bool = False  # 다중 세션 허용 여부
    session_cleanup_interval_hours: int = 24  # 만료된 세션 정리 주기
    
    # Security Settings
    cookie_secure: bool = True
    cookie_samesite: str = "strict"
    
    
    # 단일 세션 정책 적용 여부
    allow_multiple_sessions: bool = False
    max_sessions_per_user: int = 3
 
    # # Refresh Token 설정
    refresh_token_renewal_threshold_days: int = 1  # Refresh Token 갱신 임계값 추가 (1일 이내 만료 시)
    cognito_refresh_token_expire_days: int = 30 # Cognito Refresh Token 만료 기간
    
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

    def validate_settings(self) -> bool:
        """설정 유효성 검증"""
        errors = []
        
        # 필수 설정 확인
        if not self.aws_region:
            errors.append("AWS region not configured")
        if not self.cognito_user_pool_id:
            errors.append("Cognito user pool ID not configured")
        if not self.cognito_client_id:
            errors.append("Cognito client ID not configured")
        if not self.supabase_url:
            errors.append("Supabase URL not configured")
        if not self.supabase_service_key:
            errors.append("Supabase service key not configured")
        if not self.encryption_key:
            errors.append("Encryption key not configured")
        if not self.salt_key:
            errors.append("Salt key not configured")
            
        # JWT 키 파일 존재 확인
        if self.jwt_private_key_path and not os.path.exists(self.jwt_private_key_path):
            errors.append(f"JWT private key file not found: {self.jwt_private_key_path}")
        if self.jwt_public_key_path and not os.path.exists(self.jwt_public_key_path):
            errors.append(f"JWT public key file not found: {self.jwt_public_key_path}")
            
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            return False
            
        return True

# 전역 설정 인스턴스
settings = Settings()