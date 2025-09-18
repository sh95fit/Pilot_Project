import streamlit as st
from auth.auth_manager import AuthManager
from components.layout.sidebar import render_sidebar
from views.login import show_login_page
from views.dashboard_management import show_management_dashboard
from views.dashboard_operations import show_operations_dashboard
from config.settings import settings
from utils.loading_manager import loading_manager, show_refresh_loading, show_page_loading
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
    if "app_initialized" not in st.session_state:
        st.session_state.app_initialized = False
    if "last_page" not in st.session_state:
        st.session_state.last_page = None
    # 로딩 상태 추가
    if "is_loading" not in st.session_state:
        st.session_state.is_loading = False
    if "loading_type" not in st.session_state:
        st.session_state.loading_type = None

def check_and_update_auth_state():
    """인증 상태 체크 및 세션 상태 업데이트"""
    try:        
        # 새로고침 감지 (app_initialized가 False면 새로고침)
        if not st.session_state.get("app_initialized", False):
            # 로딩 상태 설정 (UI 렌더링 방지)
            st.session_state.is_loading = True
            st.session_state.loading_type = "refresh"
            
            # 새로고침 로딩 표시
            show_refresh_loading()
            st.session_state.app_initialized = True
            
            # 로딩 완료
            st.session_state.is_loading = False
            st.session_state.loading_type = None
            
        # 인증 체크 
        auth_manager = AuthManager()
        is_authenticated, user_info = auth_manager.check_authentication()
        
        # 세션 상태 업데이트
        st.session_state.is_authenticated = is_authenticated
        st.session_state.user_info = user_info
        st.session_state.auth_checked = True
        
        logger.info(f"Auth status updated: authenticated={is_authenticated}, user={user_info.get('email') if user_info else None}")
        
        return is_authenticated, user_info
        
    except Exception as e:
        logger.error(f"Error checking authentication: {e}")
        st.session_state.is_authenticated = False
        st.session_state.user_info = None
        st.session_state.auth_checked = True
        st.session_state.is_loading = False
        st.session_state.loading_type = None
        return False, None

def main():
    # 페이지 설정
    st.set_page_config(
        page_title=settings.PAGE_TITLE,
        page_icon=settings.PAGE_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 세션 상태 초기화 및 로딩 매니저 초기화
    init_session_state()
    loading_manager.init_loading_state()
    
    # 대시보드 페이지 정의
    pages = {
        "💼 경영 대시보드": show_management_dashboard,
        "⚙️ 운영 대시보드": show_operations_dashboard
    }
    
    # 로딩 중이면 로딩 화면만 표시하고 다른 UI 렌더링 중단
    if st.session_state.get("is_loading", False):
        loading_type = st.session_state.get("loading_type")
        if loading_type == "refresh":
            st.markdown("<div style='text-align: center; margin-top: 10rem;'><h3>🔄 새로고침 중...</h3></div>", unsafe_allow_html=True)
        elif loading_type == "auth":
            st.markdown("<div style='text-align: center; margin-top: 10rem;'><h3>🔐 인증 확인 중...</h3></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align: center; margin-top: 10rem;'><h3>⏳ 로딩 중...</h3></div>", unsafe_allow_html=True)
        st.stop()  # 여기서 실행 중단
    
    # 인증 상태 확인 (새로고침 감지 및 로딩 포함)
    is_authenticated, user_info = check_and_update_auth_state()
    
    # 인증 체크가 완료되지 않은 경우 대기
    if not st.session_state.get("auth_checked", False):
        st.markdown("<div style='text-align: center; margin-top: 10rem;'><h3>🔍 인증 상태 확인 중...</h3></div>", unsafe_allow_html=True)
        st.stop()
    
    if not is_authenticated:
        # 로그인 페이지 표시 (사이드바 숨김)
        st.markdown("""
        <style>
        .css-1d391kg {display: none;}
        [data-testid="stSidebar"] {display: none;}
        .css-1lcbmhc {margin-left: 0rem;}
        .css-1y4p8pa {padding-left: 1rem; padding-right: 1rem;}
        
        /* 로그인 페이지 애니메이션 */
        .main > div {
            animation: fadeIn 0.5s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        </style>
        """, unsafe_allow_html=True)
        
        show_login_page()
    else:
        # 인증된 사용자: 메인 대시보드 표시
        try:
            # 사이드바 렌더링
            selected_page = render_sidebar(user_info, pages)
            
            # 페이지 전환 로딩 처리 (첫 로드 제외)
            if (st.session_state.get("last_page") != selected_page and 
                st.session_state.get("last_page") is not None):
                
                # 페이지 전환 로딩 상태 설정
                st.session_state.is_loading = True
                st.session_state.loading_type = "page_transition"
                
                show_page_loading(selected_page)
                
                # 로딩 완료
                st.session_state.is_loading = False
                st.session_state.loading_type = None
            
            st.session_state.last_page = selected_page
            
            # 메인 콘텐츠 영역
            with st.container():
                st.markdown('<div class="main-content">', unsafe_allow_html=True)
                
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
                
                st.markdown('</div>', unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"애플리케이션 실행 중 오류가 발생했습니다: {e}")
            logger.error(f"Application error: {e}")

if __name__ == "__main__":
    main()