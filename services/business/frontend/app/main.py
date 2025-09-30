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
    - 매번 새로고침 시 백엔드에서 세션 유효성 검증
    - 쿠키 기반 세션 유지 확인
    """
    try:
        auth_manager = AuthManager()
        
        # 백엔드에서 access_token과 session_id 유효성 검증
        is_authenticated, user_info = auth_manager.check_authentication()

        # 세션 상태 업데이트
        st.session_state.is_authenticated = is_authenticated
        st.session_state.user_info = user_info
        st.session_state.auth_checked = True
        st.session_state.app_initialized = True

        logger.info(
            f"Auth status checked: authenticated={is_authenticated}, "
            f"user={user_info.get('email') if user_info else None}"
        )
        
        return is_authenticated, user_info
        
    except Exception as e:
        logger.error(f"Authentication check failed: {str(e)}")
        # 인증 오류 시 안전하게 로그아웃 상태로 설정
        st.session_state.is_authenticated = False
        st.session_state.user_info = None
        st.session_state.auth_checked = True
        return False, None

def main():
    """메인 애플리케이션 실행"""
    # Streamlit 페이지 설정
    st.set_page_config(
        page_title=settings.PAGE_TITLE,
        page_icon=settings.PAGE_ICON,
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={  # 기본 메뉴 비활성화
            "Get Help": None,
            "Report a Bug": None,
            "About": None
        }
    )

    # 🎯 전역 CSS - 깜빡임 방지 및 부드러운 전환
    st.markdown("""
    <style>
    /* 페이지 로드 시 깜빡임 방지 */
    .main .block-container {
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }
    
    /* Streamlit 기본 푸터 숨김 */
    footer {visibility: hidden;}
    
    /* 헤더 여백 조정 */
    .main > div {
        padding-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # 세션 상태 초기화
    init_session_state()

    # 페이지 매핑
    pages = {
        "💼 경영 대시보드": show_management_dashboard,
        "⚙️ 운영 대시보드": show_operations_dashboard
    }

    # 인증 상태 확인 (매번 실행)
    # 🔄 인증 체크 전 로딩 표시
    if not st.session_state.auth_checked:
        # 첫 로드 시에만 로딩 표시
        with st.spinner(""):
            is_authenticated, user_info = check_auth_state()
    else:
        # 이미 체크된 경우 바로 실행
        is_authenticated, user_info = check_auth_state()


    if not is_authenticated:
        # 로그인이 필요한 경우
        _render_login_page()
    else:
        # 인증된 사용자의 경우
        _render_authenticated_app(user_info, pages)

def _render_login_page():
    """로그인 페이지 렌더링"""
    # 사이드바 숨김 + 부드러운 애니메이션
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        display: none;
    }
    .main > div {
        animation: slideIn 0.4s ease-out;
    }
    @keyframes slideIn {
        from { 
            opacity: 0; 
            transform: translateY(10px); 
        }
        to { 
            opacity: 1; 
            transform: translateY(0); 
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 로그인 페이지 표시
    show_login_page()

def _render_authenticated_app(user_info, pages):
    """인증된 사용자용 메인 애플리케이션 렌더링"""
    try:
        # 사이드바 렌더링
        selected_page = render_sidebar(user_info, pages)
        st.session_state.last_page = selected_page

        # 메인 콘텐츠 렌더링
        with st.container():
            st.markdown('<div class="main-content">', unsafe_allow_html=True)
            
            if selected_page in pages:
                try:
                    pages[selected_page]()
                except Exception as e:
                    st.error(f"페이지 로드 중 오류가 발생했습니다: {str(e)}")
                    logger.error(f"Error loading page {selected_page}: {str(e)}")
                    # 기본 페이지로 폴백
                    pages["💼 경영 대시보드"]()
            else:
                # 선택된 페이지가 없거나 잘못된 경우 기본 페이지 표시
                pages["💼 경영 대시보드"]()
                
            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"애플리케이션 실행 중 오류가 발생했습니다: {str(e)}")
        logger.error(f"Application error: {str(e)}")
        
        # 심각한 오류 시 로그아웃 처리
        st.session_state.is_authenticated = False
        st.session_state.user_info = None
        st.rerun()

if __name__ == "__main__":
    main()
