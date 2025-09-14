"""
FastAPI 백엔드 인증 클라이언트
"""
from typing import Optional, Dict, Any, Tuple
import requests
import streamlit as st
from config.settings import settings
from utils.cookie_manager import cookie_manager


class AuthClient:
    """인증 클라이언트 클래스"""
    
    def __init__(self):
        self.session = requests.Session()
        # 쿠키 자동 처리를 위한 설정
        self.session.cookies.clear()
    
    def _get_cookies_for_request(self) -> Dict[str, str]:
        """요청용 쿠키 딕셔너리 생성"""
        cookies = {}
        access_token = cookie_manager.get_access_token()
        session_id = cookie_manager.get_session_id()
        
        if access_token:
            cookies[settings.ACCESS_TOKEN_COOKIE_NAME] = access_token
        if session_id:
            cookies[settings.SESSION_ID_COOKIE_NAME] = session_id
            
        return cookies
    
    def login(self, email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        로그인 요청
        
        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: (성공여부, 응답데이터, 에러메시지)
        """
        try:
            data = {
                "email": email,
                "password": password
            }
            
            response = self.session.post(
                settings.LOGIN_ENDPOINT,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return True, response.json(), None
            else:
                error_detail = response.json().get("detail", "로그인 실패")
                return False, None, error_detail
                
        except requests.exceptions.RequestException as e:
            return False, None, f"네트워크 오류: {str(e)}"
        except Exception as e:
            return False, None, f"예상치 못한 오류: {str(e)}"
    
    def logout(self) -> Tuple[bool, Optional[str]]:
        """
        로그아웃 요청
        
        Returns:
            Tuple[bool, Optional[str]]: (성공여부, 에러메시지)
        """
        try:
            cookies = self._get_cookies_for_request()
            
            # 쿠키가 없어도 로그아웃 시도 (서버에서 처리)
            response = self.session.post(
                settings.LOGOUT_ENDPOINT,
                cookies=cookies,
                timeout=30
            )
            
            # 응답 상태 확인
            if response.status_code == 200:
                # 성공 시 세션 쿠키 클리어
                self.session.cookies.clear()
                return True, None
            elif response.status_code == 400:
                # 활성 세션이 없어도 성공으로 처리 (이미 로그아웃된 상태)
                return True, "이미 로그아웃된 상태입니다"
            else:
                try:
                    error_detail = response.json().get("detail", "로그아웃 실패")
                except:
                    error_detail = f"HTTP {response.status_code} 오류"
                return False, error_detail
                
        except requests.exceptions.RequestException as e:
            return False, f"네트워크 오류: {str(e)}"
        except Exception as e:
            return False, f"예상치 못한 오류: {str(e)}"
    
    def check_auth(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        인증 상태 확인
        
        Returns:
            Tuple[bool, Optional[Dict]]: (인증여부, 사용자정보)
        """
        try:
            cookies = self._get_cookies_for_request()
            
            response = self.session.get(
                settings.CHECK_AUTH_ENDPOINT,
                cookies=cookies,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("authenticated", False):
                    return True, data
                else:
                    return False, None
            else:
                return False, None
                
        except requests.exceptions.RequestException:
            return False, None
        except Exception:
            return False, None
    
    def refresh_token(self) -> bool:
        """
        토큰 갱신
        
        Returns:
            bool: 갱신 성공 여부
        """
        try:
            cookies = self._get_cookies_for_request()
            
            response = self.session.post(
                settings.REFRESH_ENDPOINT,
                cookies=cookies,
                timeout=30
            )
            
            return response.status_code == 200
            
        except Exception:
            return False
    
    def get_user_info(self) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        현재 사용자 정보 조회
        
        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: (성공여부, 사용자정보, 에러메시지)
        """
        try:
            cookies = self._get_cookies_for_request()
            
            response = self.session.get(
                settings.ME_ENDPOINT,
                cookies=cookies,
                timeout=30
            )
            
            if response.status_code == 200:
                return True, response.json(), None
            else:
                error_detail = response.json().get("detail", "사용자 정보 조회 실패")
                return False, None, error_detail
                
        except requests.exceptions.RequestException as e:
            return False, None, f"네트워크 오류: {str(e)}"
        except Exception as e:
            return False, None, f"예상치 못한 오류: {str(e)}"
    
    def get_dashboard_data(self) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        대시보드 데이터 조회
        
        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: (성공여부, 대시보드데이터, 에러메시지)
        """
        try:
            cookies = self._get_cookies_for_request()
            
            response = self.session.get(
                settings.DASHBOARD_ENDPOINT,
                cookies=cookies,
                timeout=30
            )
            
            if response.status_code == 200:
                return True, response.json(), None
            elif response.status_code == 401:
                # 토큰 만료 시 갱신 시도
                if self.refresh_token():
                    # 갱신 후 재시도
                    updated_cookies = self._get_cookies_for_request()
                    retry_response = self.session.get(
                        settings.DASHBOARD_ENDPOINT,
                        cookies=updated_cookies,
                        timeout=30
                    )
                    if retry_response.status_code == 200:
                        return True, retry_response.json(), None
                
                return False, None, "인증이 필요합니다"
            else:
                error_detail = response.json().get("detail", "대시보드 데이터 조회 실패")
                return False, None, error_detail
                
        except requests.exceptions.RequestException as e:
            return False, None, f"네트워크 오류: {str(e)}"
        except Exception as e:
            return False, None, f"예상치 못한 오류: {str(e)}"


# 싱글톤 인스턴스
auth_client = AuthClient()