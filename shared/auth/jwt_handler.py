from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from jwt import PyJWTError
import uuid

class JWTHandler:
    def __init__(
        self,
        private_key: str,
        public_key: str,
        algorithm: str = "RS256",
        issuer: str = "business-auth-api"
    ):
        self.private_key = private_key
        self.public_key = public_key
        self.algorithm = algorithm
        self.issuer = issuer
    
    def create_access_token(
        self,
        user_id: str,
        session_id: str,
        roles: list = None,
        expires_delta: Optional[timedelta] = None,
        jwt_access_token_expire_minutes: Optional[int] = 15
    ) -> str:
        """
        Access Token 생성
        """
        if expire_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=jwt_access_token_expire_minutes)
        
        payload = {
            "iss": self.issuer,
            "sub": user_id,
            "aud": "business-auth-client",
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": session_id,
            "roles": roles or ["user"],
            "token_type": "access"
        }
        
        return jwt.encode(payload, self.private_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Token 검증 및 페이로드 반환
        """
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.algorithm],
                audience="business-auth-client",
                issuer=self.issuer
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e :
            raise ValueError(f"Invalid token: {e}")
    
    def decode_token_without_verification(self, token: str) -> Dict[str, Any]:
        """
        검증 없이 토큰 디코드 (만료된 토큰의 정보를 얻을 때 활용)
        """
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            raise ValueError(f"Failed to decode token: {e}")