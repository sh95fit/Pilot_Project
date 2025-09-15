import redis
import json
from typing import Optional, Dict, Any
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self, redis_url: str, redis_username: str = "default", redis_password: str = None):
        try:
            self.redis = redis.from_url(
                redis_url,
                username=redis_username,
                password=redis_password,
                decode_responses=True,
                encoding='utf-8',
                retry_on_error=[redis.TimeoutError, redis.ConnectionError],
                health_check_interval=30
            )
            # 연결 테스트
            self.redis.ping()
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    
    def set_session(self, session_id: str, session_data: Dict[str, Any], ttl_seconds: int) -> bool:
        """
        세션 데이터를 Redis에 저장
        """
        try:
            key = f"session:{session_id}"
            self.redis.setex(key, ttl_seconds, json.dumps(session_data, default=str))
            return True
        except Exception as e:
            logger.error(f"Error setting session in Redis: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Redis에서 세션 데이터 조회
        """
        try:
            key = f"session:{session_id}"
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting session from Redis: {e}")
            return None
        
    def delete_session(self, session_id: str) -> bool:
        """
        Redis에서 세션 삭제
        """
        try:
            key = f"session:{session_id}"
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Error deleting session from Redis: {e}")
            return False
        
    def update_session_ttl(self, session_id: str, ttl_seconds: int) -> bool:
        """
        세션의 TTL 업데이트
        """
        try:
            key = f"session:{session_id}"
            return bool(self.redis.expire(key, ttl_seconds))
        except Exception as e:
            logger.error(f"Error updating session TTL: {e}")
            return False
        
    def session_exists(self, session_id: str) -> bool:
        """
        세션 존재 여부 확인
        """
        try:
            key = f"session:{session_id}"
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error(f"Error checking session existence: {e}")
            return False
        
    # 블랙리스트 관리
    def add_to_blacklist(self, jti: str, ttl_seconds: int) -> bool:
        """
        토큰을 블랙리스트에 추가
        """
        try:
            key = f"blacklist:{jti}"
            self.redis.setex(key, ttl_seconds, "revoked")
            return True
        except Exception as e:
            logger.error(f"Error adding to blacklist: {e}")
            return False
        
    def is_blacklisted(self, jti: str) -> bool:
        """
        토큰이 블랙리스트에 있는지 확인
        """
        try:
            key = f"blacklist:{jti}"
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error(f"Error checking blacklist: {e}")
            return False