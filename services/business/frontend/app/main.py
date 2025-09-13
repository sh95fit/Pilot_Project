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

# 페이지 기본 설정
st.set_page_config(
    page_title="Test",        # 브라우저 탭 제목
    page_icon="🍱",             # 파비콘 (emoji 또는 이미지 URL)
    layout="centered",          # 레이아웃 (centered, wide)
    initial_sidebar_state="auto"  # 사이드바 초기 상태
)

# 최소 표시용
st.title("Hello, Streamlit!")
st.write("Main page is working!")