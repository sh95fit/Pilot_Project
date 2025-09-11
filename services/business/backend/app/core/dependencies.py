from functools import lru_cache
from typing import Generator
from fastapi import Depends

from shared.auth.jwt_handler import JWTHandler
from shared.auth.crypto import CryptoHandler
from shared.auth.cognito_client import CognitoClient
from shared.database.supabase_client import SupabaseClient
from shared.database.redis_client import RedisClient
from .config import settings

# 의존성 주입을 위한 팩토리 함수들

@lru_cache()
def get_jwt_handler() -> JWTHandler:
    """JWT 핸들러 의존성"""
    return JWTHandler(
        private_key=settings.jwt_private_key,
        public_key=settings.jwt_public_key,
        algorithm=settings.jwt_algorithm,
        issuer=settings.jwt_issuer
    )

@lru_cache()
def get_crypto_handler() -> CryptoHandler:
    """암호화 핸들러 의존성"""
    return CryptoHandler(
        encryption_key=settings.encryption_key,
        salt_key=settings.salt_key
    )

@lru_cache()
def get_cognito_client() -> CognitoClient:
    """Cognito 클라이언트 의존성"""
    return CognitoClient(
        region_name=settings.aws_region,
        user_pool_id=settings.cognito_user_pool_id,
        client_id=settings.cognito_client_id,
        # client_secret=settings.cognito_client_secret
    )

@lru_cache()
def get_supabase_client() -> SupabaseClient:
    """Supabase 클라이언트 의존성"""
    return SupabaseClient(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_key
    )

@lru_cache()
def get_redis_client() -> RedisClient:
    """Redis 클라이언트 의존성"""
    return RedisClient(
        redis_url=settings.redis_url,
        redis_username=settings.redis_username,
        redis_password=settings.redis_password
    )


# 전역 인스턴스 (기존 코드 호환용 - 점진적 마이그레이션을 위해)
# 추후 제거 예정
# jwt_handler = get_jwt_handler()
# crypto_handler = get_crypto_handler()
# cognito_client = get_cognito_client()
# supabase_client = get_supabase_client()
# redis_client = get_redis_client()