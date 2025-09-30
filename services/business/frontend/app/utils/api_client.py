import requests
import streamlit as st
from typing import Dict, Any, Optional
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self):
        self.base_url = settings.BACKEND_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        self.timeout = getattr(settings, "API_TIMEOUT", 30)


    def _handle_response(self, response: requests.Response, endpoint: str) -> Optional[Dict[str, Any]]:
        """
        응답 처리 공통 메서드
        """
        try:
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                logger.warning(f"{endpoint}: Unauthorized (401)")
                return {"success": False, "message": "인증이 필요합니다"}
            elif response.status_code == 403:
                logger.warning(f"{endpoint}: Forbidden (403)")
                return {"success": False, "message": "접근 권한이 없습니다"}
            elif response.status_code == 404:
                logger.warning(f"{endpoint}: Not Found (404)")
                return {"success": False, "message": "요청한 리소스를 찾을 수 없습니다"}
            elif response.status_code >= 500:
                logger.error(f"{endpoint}: Server Error ({response.status_code})")
                return {"success": False, "message": "서버 내부 오류가 발생했습니다"}
            else:
                logger.error(f"{endpoint}: HTTP {response.status_code} - {response.text}")
                return {"success": False, "message": f"HTTP {response.status_code} 오류"}
                
        except ValueError as e:
            logger.error(f"{endpoint}: JSON decode error - {e}")
            return {"success": False, "message": "서버 응답 형식 오류"}
        except Exception as e:
            logger.error(f"{endpoint}: Response handling error - {e}")
            return {"success": False, "message": "응답 처리 중 오류 발생"}     
        
        
    def login(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        로그인 API 호출
        """
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json={"email": email, "password": password},
                timeout=self.timeout
            )
            
            result = self._handle_response(response, "login")
            
            if result and response.status_code == 200:
                logger.info(f"Login successful for user: {email}")
                return result
            else:
                logger.warning(f"Login failed for user: {email} / {response.status_code} - {response.text}")
                return result
        
        except requests.exceptions.Timeout:
            logger.error("Login request timeout")
            return {"success": False, "message": "로그인 요청 시간 초과"}
        except requests.exceptions.ConnectionError:
            logger.error("Login connection error")
            return {"success": False, "message": "서버 연결 실패"}
        except Exception as e:
            logger.error(f"Login API error: {e}")
            return {"success": False, "message": "로그인 중 오류가 발생했습니다"}
    
    
    def get_current_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        현재 사용자 정보 조회 - /auth/me API 호출 (새로 추가)
        """
        try:
            # 쿠키 헤더에 access_token만 보내면 서버가 세션 조회 시 누락될 수 있어
            # session_id도 함께 보낸다
            session_id = st.session_state.get('session_id')
            if session_id:
                headers = {
                    'cookie': f'access_token={access_token}; session_id={session_id}'
                }
            else:
                headers = {
                    'cookie': f'access_token={access_token}'
                }
            
            response = self.session.get(
                f"{self.base_url}/auth/me",
                headers=headers,
                timeout=self.timeout
            )
            
            result = self._handle_response(response, "/auth/me")
            
            if result and response.status_code == 200:
                logger.debug("Successfully retrieved current user info")
                return result
            else:
                logger.warning("Failed to retrieve current user info")
                return result
        
        except requests.exceptions.Timeout:
            logger.error("/auth/me request timeout")
            return {"success": False, "message": "사용자 정보 요청 시간 초과"}
        except requests.exceptions.ConnectionError:
            logger.error("/auth/me connection error")
            return {"success": False, "message": "서버 연결 실패"}
        except Exception as e:
            logger.error(f"/auth/me API error: {e}")
            return {"success": False, "message": "사용자 정보 조회 중 오류 발생"}    
    
    
    # def refresh_token(self, access_token: str, session_id: str) -> Optional[Dict[str, Any]]:
    def refresh_token(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        토큰 갱신 API 호출
        
        Args:
            session_id: 세션 ID (쿠키로 전송)
        
        Returns:
            성공: {"success": True, "message": "...", "tokens": {...}}
            실패: {"success": False, "message": "..."}        
        """
        try:
            # Cookie 헤더로 전송 (Streamlit -> Fastapi)
            headers = {
                # 'cookie': f"access_token={access_token}; session_id={session_id}"
                'cookie': f"session_id={session_id}"
            }
            
            logger.debug(f"Token refresh request for session: {session_id[:8]}...")
            
            response = self.session.post(
                f"{self.base_url}/auth/refresh",
                headers=headers,
                timeout=self.timeout
            )
            
            result = self._handle_response(response, "token refresh")

            if result:
                result['status_code'] = response.status_code  # ← 추가
            else:
                # result가 None인 경우에도 status_code 포함
                result = {
                    'success': False,
                    'status_code': response.status_code,
                    'message': 'No response data'
                }            
                
            if result and result.get('success'):
                logger.debug("Token refresh successful")
            else:
                logger.warning(f"Token refresh failed: {result.get('message') if result else 'no response'}")
            
            return result
        
        except requests.exceptions.Timeout:
            logger.error("Token refresh request timeout")
            return {"success": False, "message": "토큰 갱신 요청 시간 초과"}
        except requests.exceptions.ConnectionError:
            logger.error("Token refresh connection error")
            return {"success": False, "message": "서버 연결 실패"}
        except Exception as e:
            logger.error(f"Token refresh API error: {e}")
            return {"success": False, "message": "토큰 갱신 중 오류 발생"}
    
    
    def logout(self, access_token: str, session_id: str) -> bool:
        """
        로그아웃 호출
        """
        try:
            headers = {
                'cookie': f"access_token={access_token}; session_id={session_id}"
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/logout",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info("Logout successful")
                return True
            else:
                logger.warning(f"Logout failed: {response.status_code}")
                return False
    
        except requests.exceptions.Timeout:
            logger.error("Logout request timeout")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("Logout connection error")
            return False
        except Exception as e:
            logger.error(f"Logout API error: {e}")
            return False
        
        
    def check_auth(self, access_token: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        인증 상태 확인 API 호출
        """
        try:
            headers = {
                'cookie': f'access_token={access_token}; session_id={session_id}'
            }
            
            response = self.session.get(
                f"{self.base_url}/auth/check",
                headers=headers,
                timeout=self.timeout
            )
            
            result = self._handle_response(response, "auth check")
            
            if result and response.status_code == 200:
                logger.debug("Auth check successful")
                return result
            else:
                logger.warning("Auth check failed")
                return result
        
        except requests.exceptions.Timeout:
            logger.error("Auth check request timeout")
            return {"authenticated": False, "message": "인증 확인 요청 시간 초과"}
        except requests.exceptions.ConnectionError:
            logger.error("Auth check connection error")
            return {"authenticated": False, "message": "서버 연결 실패"}
        except Exception as e:
            logger.error(f"Auth check API error: {e}")
            return {"authenticated": False, "message": "인증 확인 중 오류 발생"}
    
    
    def health_check(self) -> Optional[Dict[str, Any]]:
        """
        서버 상태 확인 API 호출
        """
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            
            result = self._handle_response(response, "health check")
            
            if result and response.status_code == 200:
                logger.debug("Health check successful")
                return result
            else:
                logger.warning("Health check failed")
                return result
        
        except requests.exceptions.Timeout:
            logger.error("Health check request timeout")
            return {"success": False, "message": "서버 상태 확인 요청 시간 초과"}
        except requests.exceptions.ConnectionError:
            logger.error("Health check connection error")
            return {"success": False, "message": "서버 연결 실패"}
        except Exception as e:
            logger.error(f"Health check API error: {e}")
            return {"success": False, "message": "서버 상태 확인 중 오류 발생"}                
        
        
    def close(self):
        """
        세션 정리
        """
        try:
            self.session.close()
            logger.debug("API client session closed")
        except Exception as e:
            logger.error(f"Error closing API client session: {e}")
    
    
    # def __del__(self):
    #     """
    #     소멸자에서 세션 정리
    #     """
    #     try:
    #         if hasattr(self, 'session'):
    #             self.session.close()
    #     except:
    #         pass        