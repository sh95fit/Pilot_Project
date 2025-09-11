import os
import streamlit as st

from pages.login import show_login_page
from pages.dashboard import show_dashboard_page
from utils.auth_utils import init_session_state, check_authentication

def hide_streamlit_ui_if_prod():
    """운영 환경에서 Streamlit 상단 메뉴와 Footer 숨김"""
    # ENV = os.getenv("ENVIRONMENT") == "prod"
    ENV = True
    if ENV:
        hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}   /* 햄버거 메뉴  */
            footer {visibility: hidden;}     /* 하단 footer 숨김 */
            .stDeployButton {visibility: hidden;} /* Deploy 버튼 숨김  */
            </style>
        """
        st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def main():
    """메인 애플리케이션"""
    # 세션 상태 초기화
    init_session_state()

    # 운영 모드 UI 처리
    hide_streamlit_ui_if_prod()
    
    # 인증 상태에 따라 페이지 라우팅
    if check_authentication():
        show_dashboard_page()
    else:
        show_login_page()

if __name__ == "__main__":
    main()