import streamlit as st
from auth.auth_manager import AuthManager
import time
import logging

logger = logging.getLogger(__name__)

def render_login_form():
    """
    로그인 폼 렌더링 - 중복 렌더링 방지와 원격 서버 호환성 개선
    """
    # 고유한 폼 키 생성 (페이지 리로드마다 새로운 키)
    if "form_counter" not in st.session_state:
        st.session_state.form_counter = 0
    
    form_key = f"login_form_{st.session_state.form_counter}"

    # 페이지 중앙 정렬
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # 헤더
        st.markdown('<h3 style="text-align:center;">🔐 로그인</h3>', unsafe_allow_html=True)

        # 로그인 폼
        with st.form(key=form_key, clear_on_submit=False):
            email = st.text_input(
                "이메일",
                placeholder="example@company.com",
                key=f"{form_key}_email"
            )
            password = st.text_input(
                "비밀번호",
                type="password",
                placeholder="비밀번호를 입력하세요",
                key=f"{form_key}_password"
            )
            submit_button = st.form_submit_button(
                "🚀 로그인",
                key=f"{form_key}_submit",
                use_container_width=True
            )

            if submit_button:
                _handle_login_submission(email, password)


def _handle_login_submission(email: str, password: str):
    """로그인 처리 로직"""
    # 입력 검증
    if not email or not password:
        st.error("⚠️ 이메일과 비밀번호를 모두 입력해주세요.")
        return
    
    if "@" not in email:
        st.error("⚠️ 올바른 이메일 형식을 입력해주세요.")
        return

    try:
        auth_manager = AuthManager()
        login_start = time.time()
        
        with st.spinner("🔄 로그인 처리 중..."):
            success, error_message = auth_manager.login(email, password)
            duration = time.time() - login_start
            logger.info(f"Login attempt for {email}: {'success' if success else 'failed'} ({duration:.2f}s)")

        if success:
            st.success("✅ 로그인 성공! 대시보드로 이동합니다.")
            
            # 세션 상태 즉시 업데이트
            st.session_state.is_authenticated = True
            st.session_state.auth_checked = True
            
            # 폼 카운터 증가 (새로운 폼 렌더링을 위해)
            st.session_state.form_counter += 1
            
            # 짧은 지연 후 리로드
            time.sleep(0.2)
            st.rerun()
            
        else:
            st.error(f"❌ {error_message or '이메일 또는 비밀번호가 올바르지 않습니다.'}")
            st.warning("🔒 여러 번 로그인에 실패하면 계정이 일시적으로 잠길 수 있습니다.")
            
            # 폼 카운터 증가 (새로운 폼 렌더링을 위해)
            st.session_state.form_counter += 1
            
            logger.warning(f"Login failed for {email}: {error_message}")
            
    except Exception as e:
        st.error("❌ 시스템 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
        st.info("💬 문제가 지속되면 시스템 관리자에게 문의해주세요.")
        
        # 폼 카운터 증가
        st.session_state.form_counter += 1
        
        logger.error(f"Unexpected login error for {email}: {str(e)}")


def render_logout_button():
    """
    로그아웃 버튼 렌더링 - 사이드바에서 사용
    """
    if st.button("🚪 로그아웃", key="main_logout_button", type="secondary", use_container_width=True):
        try:
            auth_manager = AuthManager()
            
            with st.spinner("🔄 로그아웃 처리 중..."):
                logout_success = auth_manager.logout()
                
            if logout_success:
                # 모든 관련 세션 상태 초기화
                _clear_auth_session_state()
                
                st.success("✅ 안전하게 로그아웃 되었습니다.")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ 로그아웃 처리 중 오류가 발생했습니다.")
                
        except Exception as e:
            st.error("❌ 로그아웃 처리 중 시스템 오류가 발생했습니다.")
            logger.error(f"Logout error: {e}")


def _clear_auth_session_state():
    """인증 관련 세션 상태 초기화"""
    auth_keys = [
        "is_authenticated", 
        "user_info", 
        "auth_checked", 
        "form_counter",
        "login_header_rendered",
        "footer_rendered"
    ]
    
    for key in auth_keys:
        if key in st.session_state:
            del st.session_state[key]


def _render_debug_info():
    """
    개발 환경용 디버그 정보 (개발용)
    """
    if st.secrets.get("environment", "prod") == "dev":
        try:
            auth_manager = AuthManager()
            auth_status = auth_manager.get_auth_status()
            
            with st.expander("🔧 개발자 디버그", expanded=False):
                st.json({
                    "session_state": {
                        "is_authenticated": st.session_state.get("is_authenticated", False),
                        "user_info": st.session_state.get("user_info"),
                        "auth_checked": st.session_state.get("auth_checked", False),
                        "form_counter": st.session_state.get("form_counter", 0)
                    },
                    "auth_manager_status": auth_status
                })
                
        except Exception as e:
            st.error(f"디버그 정보 로드 실패: {e}")