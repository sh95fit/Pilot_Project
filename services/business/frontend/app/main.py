import streamlit as st
from auth.auth_manager import AuthManager
from components.layout.sidebar import render_sidebar
from views.login import show_login_page
from views.dashboard_management import show_management_dashboard
from views.dashboard_operations import show_operations_dashboard
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

def init_session_state():
    """세션 상태 초기화"""
    defaults = {
        "user_info": None,
        "is_authenticated": False,
        "auth_checked": False,
        "app_initialized": False,
        "last_page": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def check_auth_state():
    """
    인증 상태 체크
    """
    auth_manager = AuthManager()
    
    # 로그인 세션 유지 확인
    is_authenticated, user_info = auth_manager.check_authentication()

    st.session_state.is_authenticated = is_authenticated
    st.session_state.user_info = user_info
    st.session_state.auth_checked = True
    st.session_state.app_initialized = True

    logger.info(
        f"Auth status updated: authenticated={is_authenticated}, user={user_info.get('email') if user_info else None}"
    )
    return is_authenticated, user_info

def main():
    st.set_page_config(
        page_title=settings.PAGE_TITLE,
        page_icon=settings.PAGE_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )

    init_session_state()

    pages = {
        "💼 경영 대시보드": show_management_dashboard,
        "⚙️ 운영 대시보드": show_operations_dashboard
    }

    # 인증 상태 확인
    is_authenticated, user_info = check_auth_state()

    if not is_authenticated:
        # 로그인 폼 상태 초기화
        st.session_state["login_form_rendered"] = False
        st.session_state["footer_rendered"] = False
        
        # 로그인 페이지 표시 (사이드바 숨김)
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {display: none;}
        .main > div {animation: fadeIn 0.5s ease-out;}
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        </style>
        """, unsafe_allow_html=True)
        
        show_login_page()
    else:
        try:
            selected_page = render_sidebar(user_info, pages)

            st.session_state.last_page = selected_page

            # 메인 콘텐츠 렌더링
            with st.container():
                st.markdown('<div class="main-content">', unsafe_allow_html=True)
                if selected_page in pages:
                    try:
                        pages[selected_page]()
                    except Exception as e:
                        st.error(f"페이지 로드 중 오류가 발생했습니다: {e}")
                        logger.error(f"Error loading page {selected_page}: {e}")
                else:
                    pages["💼 경영 대시보드"]()
                st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"애플리케이션 실행 중 오류가 발생했습니다: {e}")
            logger.error(f"Application error: {e}")

if __name__ == "__main__":
    main()
