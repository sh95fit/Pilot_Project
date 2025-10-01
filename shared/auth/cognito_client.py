# import boto3
import aioboto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger()


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
        
        # aioboto3 세션 생성
        self.session = aioboto3.Session()
        
    async def authenticate_user(
        self, 
        email: str, 
        password: str,
        device_key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        사용자 인증 (USER_PASSWORD_AUTH + Device Tracking 지원)
        """
        async with self.session.client('cognito-idp', region_name=self.region_name) as client:
            try:
                auth_params = {
                    "USERNAME": email,
                    "PASSWORD": password
                }
                
                # Device Key가 있으면 추가 (재로그인 시)
                if device_key:
                    auth_params["DEVICE_KEY"] = device_key
                    logger.info(f"🔑 Using existing device_key: {device_key[:20]}...")
                
                
                response = await client.initiate_auth(
                    ClientId=self.client_id,
                    AuthFlow="USER_PASSWORD_AUTH",
                    AuthParameters=auth_params
                )
                
                auth_result = response.get("AuthenticationResult")
                 
                # device_metadata = response.get('NewDeviceMetadata', {})
                # device_key = device_metadata.get('DeviceKey')
                
                # logger.warning(f"Cognito raw response for {email}: {response}")
                    
                if not auth_result:
                    logger.error(f"Authentication failed for {email}: No AuthenticationResult")
                    return None
                    
                access_token = auth_result.get("AccessToken")
                refresh_token = auth_result.get("RefreshToken")
                
                if not access_token or not refresh_token:
                    logger.error(f"Missing tokens for {email}")
                    return None
                
                tokens = {
                    "access_token": auth_result.get("AccessToken"),
                    "id_token": auth_result.get("IdToken"),
                    "refresh_token": auth_result.get("RefreshToken"),
                    "expires_in": auth_result.get("ExpiresIn", 3600),
                    "token_type": auth_result.get("TokenType", "Bearer")
                }                
                
                # 새 디바이스 메타데이터 처리
                device_metadata = auth_result.get('NewDeviceMetadata', {})
                
                # print(f"🔍 Response type: {type(response)}")
                # print(f"🔍 Full response keys: {list(response.keys())}")
                # print(f"{response}")
                # print(f"🔍 NewDeviceMetadata: {device_metadata}")
                # print(f"🔍 NewDeviceMetadata type: {type(device_metadata)}")
                # print(f"🔍 NewDeviceMetadata bool: {bool(device_metadata)}")
                
                if device_metadata:
                    tokens['device_key'] = device_metadata.get('DeviceKey')
                    tokens['device_group_key'] = device_metadata.get('DeviceGroupKey')
                    logger.info(
                        f"New device registered for {email}: "
                        f"device_key={tokens['device_key'][:20] if tokens.get('device_key') else 'None'}..."
                    )
                elif device_key:
                    # 기존 디바이스로 로그인 성공
                    tokens['device_key'] = device_key
                    logger.debug(f"Authenticated with existing device_key: {device_key[:20]}...")
                                    
                logger.info(f"Authentication successful for {email}")
                
                return tokens
                # return {
                #     "access_token": access_token,
                #     "id_token": auth_result.get("IdToken"),
                #     "refresh_token": refresh_token,
                #     "expires_in": auth_result.get("ExpiresIn", 3600),
                #     "token_type": auth_result.get("TokenType", "Bearer")
                # }
            
            except ClientError as e:
                error_code = e.response['Error']['Code']
                logger.error(f"Cognito authentication error: {error_code} - {e}")
                
                if error_code in ['NotAuthorizedException', 'UserNotFoundException']:
                    return None
                elif error_code == 'PasswordResetRequiredException':
                    raise ValueError("Password reset required")
                elif error_code == 'UserNotConfirmedException':
                    raise ValueError("User email not confirmed")
                else:
                    raise e

        
    async def refresh_token(self, refresh_token: str, device_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Refresh token으로 새 토큰 발급 (Device Key 포함)
        """
        async with self.session.client('cognito-idp', region_name=self.region_name) as client:
            try:
                auth_params = {
                    "REFRESH_TOKEN": refresh_token
                }
                
                # Client Secret이 있는 경우 SECRET_HASH 추가 (refresh token에서는 username 대신 client_id 사용)
                # if self.client_secret:
                #     auth_params["SECRET_HASH"] = self._calculate_secret_hash_for_refresh(refresh_token)
                
                # Device Key 추가
                if device_key:
                    auth_params["DEVICE_KEY"] = device_key
                    logger.debug(f"Refreshing with device_key: {device_key[:20]}...")                
                
                response = await client.initiate_auth(
                    ClientId=self.client_id,
                    AuthFlow="REFRESH_TOKEN_AUTH",
                    AuthParameters=auth_params
                )
                
                auth_result = response.get("AuthenticationResult")

                if not auth_result:
                    raise RefreshTokenError("server_error", "Invalid response from Cognito")
                
                tokens = {
                    "access_token": auth_result.get("AccessToken"),
                    "id_token": auth_result.get("IdToken"),
                    "expires_in": auth_result.get("ExpiresIn", 3600),
                    "token_type": auth_result.get("TokenType", "Bearer")
                }                             
                
                new_refresh = auth_result.get("RefreshToken")

                if new_refresh:
                    tokens["refresh_token"] = new_refresh
                    logger.debug("New refresh token received (rotation enabled)")
                else:
                    logger.debug("No new refresh token (rotation disabled)")

                    
                access_token = auth_result.get("AccessToken")
                if not access_token:
                    raise RefreshTokenError("server_error", "No access token received")

                # Device Key 유지
                if device_key:
                    tokens['device_key'] = device_key
                
                return tokens
            
                # return {
                #     "access_token": access_token,
                #     "id_token": auth_result.get("IdToken"),
                #     "refresh_token": new_refresh,  
                #     "expires_in": auth_result.get("ExpiresIn", 3600),
                #     "token_type": auth_result.get("TokenType", "Bearer")
                # }
                    
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error'].get('Message', str(e))
                
                logger.error(f"Token refresh error: {error_code} - {error_message}")
                
                if error_code == 'NotAuthorizedException':
                    if 'Refresh Token has expired' in error_message or 'Invalid Refresh Token' in error_message:
                        raise RefreshTokenError("expired", "Refresh token has expired")
                    else:
                        raise RefreshTokenError("invalid", f"Invalid token: {error_message}")
                elif error_code == 'InvalidParameterException':
                    raise RefreshTokenError("invalid", f"Invalid parameter: {error_message}")
                elif error_code == 'UserNotFoundException':
                    raise RefreshTokenError("invalid", "User not found")
                else:
                    raise RefreshTokenError("server_error", f"{error_code}: {error_message}")
        
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Access token으로 사용자 정보 조회
        """
        async with self.session.client('cognito-idp', region_name=self.region_name) as client:
            try:
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