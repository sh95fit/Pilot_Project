# import os
# import streamlit as st

# from pages.login import show_login_page
# from pages.dashboard import show_dashboard_page
# from utils.auth_utils import init_session_state, check_authentication

# def hide_streamlit_ui_if_prod():
#     """운영 환경에서 Streamlit 상단 메뉴와 Footer 숨김"""
#     # ENV = os.getenv("ENVIRONMENT") == "prod"
#     ENV = True
#     if ENV:
#         hide_streamlit_style = """
#             <style>
#             #MainMenu {visibility: hidden;}   /* 햄버거 메뉴  */
#             footer {visibility: hidden;}     /* 하단 footer 숨김 */
#             .stDeployButton {visibility: hidden;} /* Deploy 버튼 숨김  */
#             </style>
#         """
#         st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# def main():
#     """메인 애플리케이션"""
#     # 세션 상태 초기화
#     init_session_state()

#     # 운영 모드 UI 처리
#     hide_streamlit_ui_if_prod()
    
#     # 인증 상태에 따라 페이지 라우팅
#     if check_authentication():
#         show_dashboard_page()
#     else:
#         show_login_page()

# if __name__ == "__main__":
#     main()

#################################################################################

# import streamlit as st
# from pages.login import show_login_page
# from pages.dashboard import show_dashboard_page
# from utils.auth_utils import init_session_state, check_authentication

# def main():
#     # 페이지 설정 (사이드바 표시 안 함)
#     st.set_page_config(
#         page_title="Pilot Auth",
#         page_icon="🔐",
#         layout="wide",
#         initial_sidebar_state="collapsed"  # 사이드바 숨기기
#     )

#     # 세션 초기화 및 쿠키 복원
#     init_session_state()

#     # 로그인 상태 확인 후 페이지 전환
#     if check_authentication():
#         show_dashboard_page()
#     else:
#         show_login_page()

# if __name__ == "__main__":
#     main()

#################################################################################

import streamlit as st
from streamlit_cookies_controller import CookieController
import requests

BACKEND_URL = "http://localhost:8000"  # FastAPI 백엔드 주소
cookies = CookieController()

def is_authenticated() -> bool:
    access_token = cookies.get("access_token")
    session_id = cookies.get("session_id")

    if not access_token or not session_id:
        return False

    try:
        res = requests.get(
            f"{BACKEND_URL}/auth/check",
            cookies={
                "access_token": access_token,
                "session_id": session_id
            },
            timeout=5
        )
        return res.ok and res.json().get("authenticated", False)
    except Exception as e:
        st.error(f"Auth check failed: {e}")
        return False


def main():
    st.set_page_config(page_title="Pilot Project", layout="wide")

    if not is_authenticated():
        st.switch_page("pages/login.py")
    else:
        st.switch_page("pages/dashboard.py")


if __name__ == "__main__":
    main()