# import streamlit as st
# from streamlit_cookies_controller import CookieController
# from typing import Optional, Dict


# class StreamlitCookieManager:
#     """streamlit-cookies-controller 기반 쿠키 관리 유틸"""

#     def __init__(self):
#         self.controller = CookieController()

#     def get_all_cookies(self) -> Dict[str, str]:
#         """모든 쿠키 가져오기 (세션 캐싱 적용)"""
#         if "cookies" not in st.session_state:
#             try:
#                 st.session_state["cookies"] = self.controller.getAll()
#             except Exception as e:
#                 st.error(f"모든 쿠키 읽기 실패: {e}")
#                 st.session_state["cookies"] = {}
#         return st.session_state["cookies"]

#     def get_cookie(self, name: str) -> Optional[str]:
#         """특정 쿠키 값 가져오기"""
#         cookies = self.get_all_cookies()
#         return cookies.get(name)

#     def set_cookie(self, name: str, value: str, expires_days: int = 7) -> bool:
#         """쿠키 설정 (세션 캐시 즉시 반영)"""
#         try:
#             self.controller.set(name, value, expires_days=expires_days)
#             st.session_state.setdefault("cookies", {})[name] = value
#             return True
#         except Exception as e:
#             st.error(f"쿠키 설정 실패: {e}")
#             return False

#     def delete_cookie(self, name: str) -> bool:
#         """쿠키 삭제 (세션 캐시 즉시 반영)"""
#         try:
#             self.controller.remove(name)
#             if "cookies" in st.session_state and name in st.session_state["cookies"]:
#                 del st.session_state["cookies"][name]
#             return True
#         except Exception as e:
#             st.error(f"쿠키 삭제 실패: {e}")
#             return False

#     def has_cookie(self, name: str) -> bool:
#         """쿠키 존재 여부 확인"""
#         return self.get_cookie(name) is not None
import streamlit as st
from streamlit_cookies_controller import CookieController
from typing import Optional, Dict

class StreamlitCookieManager:
    """streamlit-cookies-controller 기반 쿠키 관리 유틸"""

    def __init__(self):
        self.controller = CookieController()

    def get_all_cookies(self) -> Dict[str, str]:
        """모든 쿠키 가져오기"""
        try:
            cookies = self.controller.getAll()
            cookies = cookies if cookies is not None else {}
            st.session_state["cookies"] = cookies
            return cookies
        except Exception as e:
            st.warning(f"모든 쿠키 읽기 실패: {e}")
            return {}

    def get_cookie(self, name: str) -> Optional[str]:
        """특정 쿠키 값 가져오기"""
        try:
            value = self.controller.get(name)
            return value
        except Exception:
            return st.session_state.get("cookies", {}).get(name)

    def set_cookie(self, name: str, value: str, max_age: int = 7*24*60*60, path: str = "/") -> bool:
        """쿠키 설정"""
        try:
            self.controller.set(name, value, max_age=max_age, path=path)
            st.session_state.setdefault("cookies", {})[name] = value
            return True
        except Exception as e:
            st.warning(f"쿠키 설정 실패: {e}")
            return False

    def delete_cookie(self, name: str, path: str = "/") -> bool:
        """쿠키 삭제"""
        try:
            if self.has_cookie(name):
                self.controller.remove(name, path=path)
            if "cookies" in st.session_state:
                st.session_state["cookies"].pop(name, None)
            return True
        except Exception as e:
            st.warning(f"쿠키 삭제 실패: {e}")
            return False

    def has_cookie(self, name: str) -> bool:
        return self.get_cookie(name) is not None
