import streamlit as st
from components.auth_components import show_login_form
from utils.auth_utils import init_session_state, check_authentication

def show_login_page():
    """
    로그인 페이지
    """
    init_session_state()
    
    # 이미 인증된 사용자라면 대시보드로 리다이렉트
    if check_authentication():
        st.switch_page("pages/dashboard")
    
    # 페이지 설정
    st.set_page_config(
        page_title="Login - Pilot Auth",
        page_icon="🔐",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # 중앙 정렬을 위한 컨테이너 할당
    col1, col2, col3 = st.columns([1,2,1])
    
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