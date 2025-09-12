import streamlit as st
from utils.auth_utils import check_authentication
from components.auth_components import show_user_info
from datetime import datetime
import time

def show_dashboard_page():
    """대시보드 페이지"""
    
    st.set_page_config(
        page_title="Dashboard - Pilot Auth",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 인증 확인
    if not check_authentication():
        st.error("🚫 Authentication required. Redirecting to login...")
        time.sleep(2)
        st.rerun()
        return

    # 사용자 정보 사이드바
    if st.session_state.user_info:
        show_user_info(st.session_state.user_info)
    
    # 메인 대시보드
    st.title("📊 Dashboard")
    st.markdown(f"Welcome, **{st.session_state.user_info.get('display_name', 'User')}**!")
    
    # 현재 시간 표시
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.info(f"🕐 Current time: {current_time}")
    
    # 새로고침 버튼
    col1, col2, col3, col4, col5 = st.columns(5)
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # 사용자 정보 메트릭
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👤 User ID", st.session_state.user_info.get('id', 'N/A')[:8]+"...")
    with col2:
        st.metric("🔑 Role", st.session_state.user_info.get('role', 'N/A').upper())
    with col3:
        st.metric("✅ Status", "ACTIVE" if st.session_state.user_info.get('is_active') else "INACTIVE")
    
    # 보호된 API 테스트
    st.markdown("---")
    st.subheader("🔐 Protected API Test")
    if st.button("📡 Call Protected API"):
        from utils.api_client import APIClient
        with st.spinner("Calling protected API..."):
            api_client = st.session_state.api_client
            dashboard_data = api_client.get_dashboard_data()
            if "error" in dashboard_data:
                st.error(f"API Error: {dashboard_data['error']}")
            else:
                st.success("✅ Protected API call successful!")
                st.json(dashboard_data)
    
    # 세션 정보
    st.markdown("---")
    st.subheader("🎯 Session Information")
    session_info = {
        "Authentication Status": "✅ Authenticated",
        "Session State": "Active",
        "Last Check": current_time,
        "User Email": st.session_state.user_info.get('email', 'N/A'),
        "Created At": st.session_state.user_info.get('created_at', 'N/A')
    }
    for key, value in session_info.items():
        st.write(f"**{key}:** {value}")
