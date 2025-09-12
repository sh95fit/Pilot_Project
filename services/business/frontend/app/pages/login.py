import streamlit as st
from utils.auth_utils import login_user, get_auth_status_info
from components.auth_components import show_login_form

def show_login_page():
    """로그인 페이지"""
    
    # 페이지 설정 (한 번만)
    st.set_page_config(
        page_title="Login - Pilot Auth",
        page_icon="🔐",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # 사이드바 숨기기
    hide_sidebar_style = """
        <style>
        [data-testid="stSidebar"] {display: none !important;}
        </style>
    """
    st.markdown(hide_sidebar_style, unsafe_allow_html=True)
    
    # 중앙 정렬 컨테이너
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        show_login_form()
    
    # 하단 정보
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #666;">
            <p>🔒 Secure authentication powered by AWS Cognito</p>
            <p>Demo credentials: contact your administrator</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # 개발용 디버그 정보
    if st.checkbox("🔍 디버그 정보 표시"):
        st.json(get_auth_status_info())
