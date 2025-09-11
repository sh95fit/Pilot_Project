from shared.auth.jwt_handler import JWTHandler
from shared.auth.crypto import CryptoHandler
from shared.auth.cognito_client import CognitoClient
from shared.database.supabase_client import SupabaseClient
from shared.database.redis_client import RedisClient
from .config import settings

# 전역 인스턴스 초기화

jwt_handler = JWTHandler(
    private_key = settings.jwt_private_key,
    public_key = settings.jwt_public_key,
    algorithm = settings.jwt_algorithm,
    issuer = settings.jwt_issuer
)

crypto_handler = CryptoHandler(settings.encryption_key, settings.salt_key)

cognito_client = CognitoClient(
    region_name = settings.aws_region,
    user_pool_id = settings.cognito_user_pool_id,
    client_id = settings.cognito_client_id,
    # client_secret=settings.cognito_client_secret
)

supabase_client = SupabaseClient(
    supabase_url = settings.supabase_url,
    supabase_key = settings.supabase_service_key
)

redis_client = RedisClient(
    redis_url = settings.redis_url,
    redis_username = settings.redis_username,
    redis_password = settings.redis_password
)