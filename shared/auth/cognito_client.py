import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional
import json

class CognitoClient:
    # def __init__(self, region_name: str, user_pool_id: str, client_id: str, client_secret: str):
    def __init__(self, region_name: str, user_pool_id: str, client_id: str, client_secret: Optional[str]=None):
        self.region_name = region_name
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        # self.client_secret = client_secret
        
        # Cognito Identity Provider 클라이언트 생성
        self.client = boto3.client('cognito-idp', region_name=region_name)
        
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        사용자 인증 및 토큰 발급
        """
        try:
            response = self.client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": email,
                    "PASSWORD": password,
                    # "SECRET_HASH": self._calculate_secret_hash(email)
                }
            )
            
            auth_result = response.get("AuthenticationResult")
            if auth_result:
                return {
                    "access_token": auth_result.get("AccessToken"),
                    "id_token": auth_result.get("IdToken"),
                    "refresh_token": auth_result.get("RefreshToken"),
                    "expires_in": auth_result.get("ExpiresIn"),
                    "token_type": auth_result.get("TokenType")
                }
            return None
        
        except ClientError as e:
            print(f"Cognito authentication error: {e}")
            return None
        
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh token으로 새 토큰 발급
        """
        try:
            response = self.client.initiate_auth(
                ClientId = self.client_id,
                AuthFlow = "REFRESH_TOKEN_AUTH",
                AuthParameters = {
                    "REFRESH_TOKEN": refresh_token,
                    # "SECRET_HASH": self._calculate_secret_hash_for_refresh(refresh_token)
                }
            )
            
            auth_result = response.get("AuthenticationResult")
            if auth_result:
                return {
                    "access_token": auth_result.get("AccessToken"),
                    "id_token": auth_result.get("IdToken"),
                    "refresh_token": auth_result.get("RefreshToken"),
                    "expires_in": auth_result.get("ExpiresIn"),
                    "token_type": auth_result.get("TokenType")
                }
            return None
        
        except ClientError as e:
            print(f"Cognito token refresh error: {e}")
            return None
        
    def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Access token으로 사용자 정보 조회
        """
        try:
            response = self.client.get_user(AccessToken=access_token)
            
            # 사용자 속성을 딕셔너리로 변환
            user_attributes = {}
            for attr in response.get("UserAttributes", []):
                user_attributes[attr['Name']] = attr['Value']
            
            return {
                'username': response.get('Username'),
                'user_attributes': user_attributes,
                'sub': user_attributes.get('sub'),
                'email': user_attributes.get('email'),
                'email_verified': user_attributes.get('email_verified') == 'true'
            }
            
        except ClientError as e:
            print(f"Error revoking token: {e}")
            return False
        
    def global_sign_out(self, access_token: str) -> bool:
        """
        모든 디바이스에서 사용자 로그아웃
        """
        try:
            self.client.global_sign_out(AccessToken=access_token)
            return True
        except ClientError as e:
            print(f"Error in global sign out: {e}")
            return False
        
    # def _calculate_secret_hash(self, username: str) -> str:
    #     """SECRET_HASH 계산 (Cognito 클라이언트 시크릿 사용시 필요)"""
    #     import hmac
    #     import hashlib
    #     import base64
        
    #     message = username + self.client_id
    #     dig = hmac.new(
    #         str(self.client_secret).encode('utf-8'),
    #         msg=str(message).encode('utf-8'),
    #         digestmod=hashlib.sha256
    #     ).digest()
    #     return base64.b64encode(dig).decode()

    # def _calculate_secret_hash_for_refresh(self, refresh_token: str) -> str:
    #     """Refresh token용 SECRET_HASH 계산"""
    #     import hmac
    #     import hashlib
    #     import base64
        
    #     # refresh token의 경우 username 대신 refresh token 사용
    #     message = refresh_token + self.client_id
    #     dig = hmac.new(
    #         str(self.client_secret).encode('utf-8'),
    #         msg=str(message).encode('utf-8'),
    #         digestmod=hashlib.sha256
    #     ).digest()
    #     return base64.b64encode(dig).decode()