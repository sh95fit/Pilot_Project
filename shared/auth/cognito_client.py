# import boto3
import aioboto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)

class RefreshTokenError(Exception):
    """Refresh Token 관련 커스텀 예외"""
    def __init__(self, error_type: str, message: str):
        self.error_type = error_type  # "expired", "invalid", "server_error"
        self.message = message
        super().__init__(self.message)

class CognitoClient:
    def __init__(
        self, 
        region_name: str, 
        user_pool_id: str, 
        client_id: str, 
        client_secret: Optional[str]=None
    ):
        self.region_name = region_name
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        # self.client_secret = client_secret
        
        # Cognito Identity Provider 클라이언트 생성
        # self.client = boto3.client('cognito-idp', region_name=region_name)
        
        # aioboto3 세션 생성
        self.session = aioboto3.Session()
        
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        사용자 인증 및 토큰 발급
        """
        async with self.session.client('cognito-idp', region_name=self.region_name) as client:
            try:
                auth_params = {
                    "USERNAME": email,
                    "PASSWORD": password
                }
                
                # Client Secret이 있는 경우 SECRET_HASH 추가
                # if self.client_secret:
                #     auth_params["SECRET_HASH"] = self._calculate_secret_hash(email)
                
                # response = self.client.initiate_auth(
                response = await client.initiate_auth(
                    ClientId=self.client_id,
                    AuthFlow="USER_PASSWORD_AUTH",
                    AuthParameters=auth_params
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
                logger.error(f"Cognito authentication error: {error_code} - {e}")
                
                # 구체적인 에러 처리
                if error_code in ['NotAuthorizedException', 'UserNotFoundException']:
                    return None
                elif error_code == 'PasswordResetRequiredException':
                    raise ValueError("Password reset required")
                elif error_code == 'UserNotConfirmedException':
                    raise ValueError("User email not confirmed")
                else:
                    raise e
        
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh token으로 새 토큰 발급
        
        Returns:
            성공: 새로운 토큰 딕셔너리
            실패: None
            
        Raises:
            RefreshTokenError: Refresh token 관련 명확한 에러 정보와 함께
        """
        async with self.session.client('cognito-idp', region_name=self.region_name) as client:
            
            try:
                auth_params = {
                    "REFRESH_TOKEN": refresh_token
                }
                
                # Client Secret이 있는 경우 SECRET_HASH 추가 (refresh token에서는 username 대신 client_id 사용)
                # if self.client_secret:
                #     auth_params["SECRET_HASH"] = self._calculate_secret_hash_for_refresh(refresh_token)
                
                # response = self.client.initiate_auth(
                response = await client.initiate_auth(
                    ClientId=self.client_id,
                    AuthFlow="REFRESH_TOKEN_AUTH",
                    AuthParameters=auth_params
                )
                
                auth_result = response.get("AuthenticationResult")
                
                if auth_result:
                    # Refresh Token Rotation 여부 로깅
                    new_refresh = auth_result.get("RefreshToken")
                    if new_refresh:
                        logger.info("Cognito returned new refresh token (rotation enabled)")
                    else:
                        logger.debug("Cognito did not return new refresh token (rotation disabled)")
                    
                    return {
                        "access_token": auth_result.get("AccessToken"),
                        "id_token": auth_result.get("IdToken"),
                        "refresh_token": new_refresh,  # None일 수 있음
                        "expires_in": auth_result.get("ExpiresIn"),
                        "token_type": auth_result.get("TokenType")
                    }
                    
                # auth_result가 없는 경우
                logger.error("Cognito refresh_token response missing AuthenticationResult")
                raise RefreshTokenError(
                    "server_error",
                    "Invalid response from Cognito"
                )
            
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error'].get('Message', str(e))
                
                logger.error(f"Cognito token refresh error: {error_code} - {error_message}")
                
                # 명확한 에러 타입 구분
                if error_code == 'NotAuthorizedException':
                    # Refresh Token 만료 또는 무효화
                    if 'Refresh Token has expired' in error_message or 'Invalid Refresh Token' in error_message:
                        raise RefreshTokenError(
                            "expired",
                            "Refresh token has expired"
                        )
                    else:
                        raise RefreshTokenError(
                            "invalid",
                            f"Refresh token is invalid: {error_message}"
                        )
                
                elif error_code == 'InvalidParameterException':
                    raise RefreshTokenError(
                        "invalid",
                        f"Invalid refresh token parameter: {error_message}"
                    )
                
                elif error_code == 'UserNotFoundException':
                    raise RefreshTokenError(
                        "invalid",
                        "User not found"
                    )
                
                else:
                    # 기타 서버 오류
                    raise RefreshTokenError(
                        "server_error",
                        f"Cognito error ({error_code}): {error_message}"
                    )
        
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Access token으로 사용자 정보 조회
        """
        async with self.session.client('cognito-idp', region_name=self.region_name) as client:
            try:
                # response = self.client.get_user(AccessToken=access_token)
                response = await client.get_user(AccessToken=access_token)
                
                # 사용자 속성을 딕셔너리로 변환
                user_attributes = {}
                for attr in response.get("UserAttributes", []):
                    user_attributes[attr['Name']] = attr['Value']
                
                return {
                    'username': response.get('Username'),
                    'user_attributes': user_attributes,
                    'sub': user_attributes.get('sub'),
                    'email': user_attributes.get('email'),
                    'email_verified': user_attributes.get('email_verified') == 'true',
                    # 'given_name': user_attributes.get('given_name'),
                    # 'family_name': user_attributes.get('family_name')
                }
                
            except ClientError as e:
                logger.error(f"Error getting user info: {e}")
                return None
        
    async def global_sign_out(self, access_token: str) -> bool:
        """
        모든 디바이스에서 사용자 로그아웃
        """
        async with self.session.client('cognito-idp', region_name=self.region_name) as client:
            try:
                # self.client.global_sign_out(AccessToken=access_token)
                await client.global_sign_out(AccessToken=access_token)
                return True
            except ClientError as e:
                logger.error(f"Error in global sign out: {e}")
                return False
        
    # def _calculate_secret_hash(self, username: str) -> str:
    #     """Client Secret과 Username으로 SECRET_HASH 계산"""
    #     import hmac
    #     import hashlib
    #     import base64
        
    #     message = username + self.client_id
    #     dig = hmac.new(
    #         self.client_secret.encode('utf-8'),
    #         msg=message.encode('utf-8'),
    #         digestmod=hashlib.sha256
    #     ).digest()
    #     return base64.b64encode(dig).decode()
    
    # def _calculate_secret_hash_for_refresh(self, refresh_token: str) -> str:
    #     """Refresh token용 SECRET_HASH 계산 (refresh token에서는 username 대신 client_id 사용)"""
    #     import hmac
    #     import hashlib
    #     import base64
        
    #     # refresh token에서는 username을 추출하거나 빈 문자열 사용
    #     message = self.client_id
    #     dig = hmac.new(
    #         self.client_secret.encode('utf-8'),
    #         msg=message.encode('utf-8'),
    #         digestmod=hashlib.sha256
    #     ).digest()
    #     return base64.b64encode(dig).decode()