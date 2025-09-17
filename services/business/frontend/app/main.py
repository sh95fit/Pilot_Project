import streamlit as st
from auth.auth_manager import AuthManager
from components.layout.sidebar import render_sidebar
from views.login import show_login_page
from views.dashboard_management import show_management_dashboard
from views.dashboard_operations import show_operations_dashboard
from config.settings import settings
import logging
import time

logger = logging.getLogger(__name__)

def init_session_state():
    """세션 상태 초기화"""
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
    if "auth_checked" not in st.session_state:
        st.session_state.auth_checked = False

def check_and_update_auth_state():
    """인증 상태 체크 및 세션 상태 업데이트"""
    try:
        auth_manager = AuthManager()
        is_authenticated, user_info = auth_manager.check_authentication()

        st.session_state.is_authenticated = is_authenticated
        st.session_state.user_info = user_info if is_authenticated else None
        st.session_state.auth_checked = True

        email = user_info.get("email") if user_info else None
        logger.info(f"Auth status updated: authenticated={is_authenticated}, user={email}")

        return is_authenticated, user_info
    except Exception as e:
        logger.error(f"Error checking authentication: {e}")
        st.session_state.is_authenticated = False
        st.session_state.user_info = None
        st.session_state.auth_checked = True
        return False, None
        
def main():
    # 페이지 설정
    st.set_page_config(
        page_title=settings.PAGE_TITLE,
        page_icon=settings.PAGE_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 로딩 상태 관리
    if "app_loading" not in st.session_state:
        st.session_state.app_loading = True
    
    # 세션 상태 초기화
    init_session_state()
    
    # 대시보드 페이지 정의
    pages = {
        "💼 경영 대시보드": show_management_dashboard,
        "⚙️ 운영 대시보드": show_operations_dashboard
    }
    
    # 로딩 중일 때 스피너 표시
    if st.session_state.app_loading:
        with st.spinner("🔄 시스템 로딩 중..."):
            time.sleep(0.5)  # 초기 로딩 시뮬레이션
            st.session_state.app_loading = False
            st.rerun()
    
    # 인증 상태 확인 (페이지 로드마다 실행)
    with st.spinner("🔐 인증 상태 확인 중..."):
        is_authenticated, user_info = check_and_update_auth_state()
    
    if not is_authenticated:
        # 로그인 페이지 표시 (사이드바 숨김)
        st.markdown(
            """
            <style>
            .css-1d391kg {display: none;}
            [data-testid="stSidebar"] {display: none;}
            .css-1lcbmhc {margin-left: 0rem;}
            .css-1y4p8pa {padding-left: 1rem; padding-right: 1rem;}
            
            /* 로딩 화면 스타일 */
            .loading-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(255, 255, 255, 0.95);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
            }
            
            /* 로그인 페이지 전용 스타일 개선 */
            .login-page {
                min-height: 80vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                margin: -1rem -1rem 0 -1rem;
                padding: 2rem;
            }
            
            /* 제목 크기 조정 */
            .login-container h1 {
                font-size: 1.8rem !important;
                font-weight: 600 !important;
            }
            
            .login-container h2 {
                font-size: 1.5rem !important;
                font-weight: 600 !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        show_login_page()
    else:
        # 인증된 사용자: 메인 대시보드 표시
        # 사이드바 렌더링
        selected_page = render_sidebar(user_info, pages)
        
        # 선택된 페이지 실행
        if selected_page in pages:
            try:
                pages[selected_page]()
            except Exception as e:
                st.error(f"페이지 로드 중 오류가 발생했습니다: {e}")
                logger.error(f"Error loading page {selected_page}: {e}")
        else:
            # 기본 페이지
            pages["💼 경영 대시보드"]()

if __name__ == "__main__":
    main()