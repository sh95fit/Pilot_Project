import streamlit as st
from components.auth.login_form import render_logout_button
import logging

logger = logging.getLogger(__name__)

def render_sidebar(user_info, pages):
    """
    사이드바 렌더링 - 사용자 정보 및 네비게이션
    새로고침 시에도 사용자 정보 유지
    """
    with st.sidebar:
        # 사이드바 헤더
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;">
            <h2 style="margin: 0; color: white;">🏢 Lunchlab Dashboard</h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 0.9rem;">관리자 대시보드</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 사용자 정보 표시 (항상 표시되도록 보장)
        _render_user_info(user_info)
        
        st.divider()
        
        # 네비게이션 메뉴
        selected_page = _render_navigation_menu(pages)
        
        st.divider()
        
        # 로그아웃 버튼
        _render_logout_section()
        
        # 시스템 정보 (하단)
        # _render_system_info()
        
        return selected_page

def _render_user_info(user_info):
    """
    사용자 정보 렌더링 - 새로고침 시에도 유지
    """
    if user_info:
        st.markdown("### 👤 사용자 정보")
        
        # 사용자 정보를 안전하게 표시
        with st.container():
            # 이메일 표시
            email = user_info.get('email', 'Unknown')
            name = user_info.get('name', user_info.get('username', '사용자'))
            role = user_info.get('role', 'User')
            last_login = user_info.get('last_login', '')
            
            st.markdown(f"""
            <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; border-left: 4px solid #3b82f6;">
                <div style="margin-bottom: 0.5rem;">
                    <strong>👤 이름:</strong> {name}
                </div>
                <div style="margin-bottom: 0.5rem;">
                    <strong>📧 이메일:</strong><br>
                    <code>{email}</code>
                </div>
                <div>
                    <strong>🏷️ 권한:</strong> 
                    <span style="background: #dbeafe; color: #1d4ed8; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem;">
                        {role}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
            # 최근 로그인 시간 표시
            if last_login:
                st.caption(f"🕒 최근 로그인: {last_login}")
            
            # 정보 새로고침 버튼
            st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

            if st.button("🔄 정보 새로고침", key="refresh_user_info", use_container_width=True):
                try:
                    from auth.auth_manager import AuthManager
                    auth_manager = AuthManager()
                    if auth_manager.force_refresh_user_info():
                        st.success("✅ 정보가 업데이트되었습니다")
                        st.rerun()
                    else:
                        st.error("❌ 정보 업데이트에 실패했습니다")
                except Exception as e:
                    st.error("❌ 새로고침 중 오류가 발생했습니다")
                    logger.error(f"User info refresh error: {e}")
                
    else:
        # 사용자 정보가 없는 경우
        st.warning("⚠️ 사용자 정보를 불러올 수 없습니다.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 정보 새로고침", key="refresh_user_info_fallback", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("🚪 다시 로그인", key="relogin_button", use_container_width=True):
                try:
                    from auth.auth_manager import AuthManager
                    auth_manager = AuthManager()
                    auth_manager._clear_auth_state()
                    st.rerun()
                except Exception as e:
                    logger.error(f"Relogin error: {e}")
                    st.rerun()

def _render_navigation_menu(pages):
    """
    네비게이션 메뉴 렌더링 - SelectBox 사용
    쿠키에서 복원된 last_page를 기본값으로 사용
    """
    st.markdown("### 📊 대시보드 메뉴")
    
    # 기본 페이지 결정 (쿠키에서 복원된 값 우선)
    page_list = list(pages.keys())
    default_page = st.session_state.get("last_page", page_list[0])
    
    # 유효하지 않은 페이지면 첫 번째 페이지로
    if default_page not in page_list:
        default_page = page_list[0]
    
    # 현재 선택된 페이지의 인덱스
    default_index = page_list.index(default_page)
    
    # 페이지 선택 SelectBox
    selected = st.selectbox(
        "메뉴를 선택하세요:",
        options=page_list,
        index=default_index,
        key="navigation_selectbox",
        label_visibility="collapsed"
    )
    
    # 선택된 페이지가 변경되면 로그
    if selected != st.session_state.get("last_page"):
        logger.info(f"Page changed to: {selected}")
    
    return selected

def _render_logout_section():
    """
    로그아웃 섹션 렌더링
    """
    # st.markdown("### 🚪 계정 관리")
    
    # 로그아웃 버튼 (components.auth.login_form에서 가져옴)
    render_logout_button()
    
    # 추가 보안 정보
    # with st.expander("🔒 보안 정보", expanded=False):
    #     st.info("""
    #     **보안 권장사항:**
    #     - 사용 완료 후 반드시 로그아웃해 주세요
    #     - 브라우저를 닫아도 자동 로그아웃됩니다
    #     - 의심스러운 활동이 감지되면 즉시 신고해 주세요
    #     """)

# def _render_system_info():
#     """
#     시스템 정보 렌더링 (하단)
#     """
#     st.markdown("---")
    
#     # 시스템 상태
#     with st.expander("ℹ️ 시스템 정보", expanded=False):
#         import datetime
#         import platform
        
#         current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
#         st.markdown(f"""
#         **시스템 상태:**
#         - 🕒 현재 시간: `{current_time}`
#         - 💻 플랫폼: `{platform.system()}`
#         - 🌐 Streamlit 버전: `{st.__version__}`
#         - 📱 세션 상태: `활성화`
#         """)
        
        # 세션 정보 (개발 환경에서만)
        # if st.secrets.get("environment", "prod") == "dev":
        #     session_info = {
        #         "is_authenticated": st.session_state.get("is_authenticated", False),
        #         "selected_page": st.session_state.get("selected_page", "None"),
        #         "auth_checked": st.session_state.get("auth_checked", False)
        #     }
        #     st.json(session_info)
    
    # 버전 정보
    st.caption("© 2025 lunchlab all rights reserved")

def render_mobile_navigation(pages, user_info):
    """
    모바일 환경용 네비게이션 (선택적 사용)
    """
    if st.button("📱 모바일 메뉴", key="mobile_menu_toggle"):
        st.session_state.mobile_menu_open = not st.session_state.get("mobile_menu_open", False)
    
    if st.session_state.get("mobile_menu_open", False):
        with st.container():
            st.markdown("### 📱 모바일 메뉴")
            
            # 사용자 정보 간략 표시
            if user_info:
                st.info(f"👤 {user_info.get('name', '사용자')} ({user_info.get('email', '')})")
            
            # 페이지 선택
            selected = st.selectbox(
                "페이지 선택:",
                options=list(pages.keys()),
                key="mobile_page_select"
            )
            
            # 로그아웃 버튼
            render_logout_button()
            
            return selected
    
    return st.session_state.get("last_page", list(pages.keys())[0])