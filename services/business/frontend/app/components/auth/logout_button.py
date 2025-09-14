"""
로그아웃 버튼 컴포넌트
"""
import streamlit as st
from utils.session_manager import SessionManager, get_current_user_info


def render_logout_button(location="sidebar"):
    """
    로그아웃 버튼 렌더링
    
    Args:
        location (str): 버튼 위치 ("sidebar" or "main")
    """
    user_info = get_current_user_info()
    
    if location == "sidebar":
        with st.sidebar:
            _render_logout_section(user_info)
    else:
        _render_logout_section(user_info)


def _render_logout_section(user_info):
    """로그아웃 섹션 렌더링"""
    
    # 사용자 정보 표시
    if user_info:
        st.markdown("---")
        st.markdown("### 👤 사용자 정보")
        
        # 사용자 카드 스타일
        st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1rem;
                border-radius: 10px;
                color: white;
                margin-bottom: 1rem;
            ">
                <div style="font-size: 0.9rem; opacity: 0.8;">환영합니다!</div>
                <div style="font-size: 1.1rem; font-weight: bold; margin: 0.2rem 0;">
                    {user_info.get('display_name', '사용자')}
                </div>
                <div style="font-size: 0.85rem; opacity: 0.9;">
                    {user_info.get('email', '')}
                </div>
                <div style="font-size: 0.8rem; opacity: 0.7; margin-top: 0.5rem;">
                    역할: {user_info.get('role', 'user').upper()}
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # 로그아웃 버튼
    if st.button(
        "🚪 로그아웃",
        use_container_width=True,
        type="secondary",
        help="시스템에서 안전하게 로그아웃합니다"
    ):
        _handle_logout()


def _handle_logout():
    """로그아웃 처리"""
    try:
        with st.spinner("로그아웃 중..."):
            success, error_msg = SessionManager.logout()
            
        # SessionManager.logout()에서 이미 페이지 리다이렉트 처리됨
        # 여기서는 추가 처리 불필요
        
    except Exception as e:
        st.error(f"로그아웃 처리 중 오류 발생: {str(e)}")
        # 오류 발생 시에도 강제로 로그인 페이지로 이동
        import time
        time.sleep(1)
        st.switch_page("app.py")


def render_user_menu():
    """사용자 메뉴 렌더링 (헤더용)"""
    user_info = get_current_user_info()
    
    if user_info:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"""
                <div style="
                    display: flex;
                    align-items: center;
                    padding: 0.5rem;
                    background: #f0f2f6;
                    border-radius: 5px;
                    margin-bottom: 0.5rem;
                ">
                    <div style="margin-right: 0.5rem;">👤</div>
                    <div>
                        <div style="font-weight: bold; font-size: 0.9rem;">
                            {user_info.get('display_name', '사용자')}
                        </div>
                        <div style="font-size: 0.8rem; color: #666;">
                            {user_info.get('email', '')}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button("로그아웃", type="secondary", key="header_logout"):
                _handle_logout()