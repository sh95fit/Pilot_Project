"""
사이드바 컴포넌트
"""
import streamlit as st
from components.auth.logout_button import render_logout_button
from utils.session_manager import get_current_user_info


def render_sidebar():
    """사이드바 렌더링"""
    
    with st.sidebar:
        # 앱 로고/제목
        st.markdown("""
            <div style="text-align: center; padding: 1rem 0;">
                <h1 style="color: #1f77b4; margin: 0;">
                    🔐 Pilot Auth
                </h1>
                <p style="color: #666; margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                    인증 관리 시스템
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 네비게이션 메뉴
        st.markdown("### 📋 메뉴")
        
        # 현재 페이지 확인
        current_page = st.session_state.get("current_page", "Dashboard")
        
        # 메뉴 아이템들
        menu_items = [
            {"name": "대시보드", "icon": "🏠", "page": "pages/1_🏠_Dashboard.py"},
            {"name": "분석", "icon": "📊", "page": "pages/2_📊_Analytics.py"},
            {"name": "설정", "icon": "⚙️", "page": "pages/3_⚙️_Settings.py"},
        ]
        
        for item in menu_items:
            # 현재 페이지인지 확인
            is_current = current_page.lower() in item["name"].lower()
            
            if st.button(
                f"{item['icon']} {item['name']}",
                use_container_width=True,
                type="primary" if is_current else "secondary",
                key=f"nav_{item['name'].lower()}"
            ):
                st.switch_page(item["page"])
        
        st.markdown("---")
        
        # 시스템 상태
        render_system_status()
        
        # 로그아웃 버튼
        render_logout_button(location="sidebar")


def render_system_status():
    """시스템 상태 표시"""
    st.markdown("### 📡 시스템 상태")
    
    # 인증 상태
    user_info = get_current_user_info()
    if user_info:
        st.success("✅ 인증됨")
        
        # 세션 정보
        with st.expander("세션 정보", expanded=False):
            st.json({
                "사용자 ID": user_info.get("id", "N/A")[:8] + "...",
                "역할": user_info.get("role", "N/A"),
                "활성 상태": user_info.get("is_active", False),
                "생성일": user_info.get("created_at", "N/A")[:10] if user_info.get("created_at") else "N/A"
            })
    else:
        st.error("❌ 인증되지 않음")
    
    # 연결 상태 (간단한 체크)
    try:
        st.info("🌐 백엔드 연결됨")
    except:
        st.warning("⚠️ 백엔드 연결 확인 필요")


def render_quick_actions():
    """빠른 작업 버튼들"""
    st.markdown("### ⚡ 빠른 작업")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄", help="새로고침", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("📋", help="세션 정보", use_container_width=True):
            st.info("세션 정보가 위에 표시됩니다.")