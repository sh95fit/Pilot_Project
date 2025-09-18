import streamlit as st
from auth.auth_manager import AuthManager
import time
import logging

logger = logging.getLogger(__name__)

def render_login_form():
    """
    로그인 폼 렌더링 - 카드 안에 헤더와 폼을 통합
    """
    form_key = "main_login_form"

    # 이미 렌더링된 상태면 중복 방지
    if st.session_state.get("login_form_rendered", False):
        return

    # 페이지 중앙 정렬
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # 헤더
        st.markdown('<h3 style="text-align:center;">🔐 로그인</h3>', unsafe_allow_html=True)

        # 로그인 폼
        with st.form(key=form_key):
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

    # 렌더링 완료 표시
    st.session_state["login_form_rendered"] = True


def _handle_login_submission(email: str, password: str):
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
            time.sleep(1)
            st.session_state.auth_checked = False
            st.rerun()
        else:
            st.error(f"❌ {error_message or '이메일 또는 비밀번호가 올바르지 않습니다.'}")
            st.warning("🔒 여러 번 로그인에 실패하면 계정이 일시적으로 잠길 수 있습니다.")
            logger.warning(f"Login failed for {email}: {error_message}")
    except Exception as e:
        st.error("❌ 시스템 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
        st.info("💬 문제가 지속되면 시스템 관리자에게 문의해주세요.")
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
                # 세션 상태 초기화
                st.session_state.is_authenticated = False
                st.session_state.user_info = None
                st.session_state.auth_checked = False
                
                st.success("✅ 안전하게 로그아웃 되었습니다.")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ 로그아웃 처리 중 오류가 발생했습니다.")
                
        except Exception as e:
            st.error("❌ 로그아웃 처리 중 시스템 오류가 발생했습니다.")
            logger.error(f"Logout error: {e}")


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
                        "auth_checked": st.session_state.get("auth_checked", False)
                    },
                    "auth_manager_status": auth_status
                })
                
        except Exception as e:
            st.error(f"디버그 정보 로드 실패: {e}")