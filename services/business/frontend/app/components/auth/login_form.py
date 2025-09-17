import streamlit as st
from auth.auth_manager import AuthManager
import time
import logging

logger = logging.getLogger(__name__)

def render_login_form():
    """
    로그인 폼 렌더링 - 중복 방지 및 개선된 UI
    """
    # 폼 고유 키를 사용하여 중복 방지
    form_key = "main_login_form"
    
    # 로그인 폼 스타일
    st.markdown("""
    <style>
    .login-container {
        max-width: 420px;
        margin: 0 auto;
        padding: 2.5rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        background: white;
        border: 1px solid #e5e7eb;
    }
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
        color: #1f2937;
    }
    .form-input {
        margin-bottom: 1rem;
    }
    .login-button {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        border: none;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        width: 100%;
        padding: 0.75rem;
        transition: all 0.3s ease;
    }
    .login-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(59, 130, 246, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 메인 로그인 컨테이너
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.container():
                st.markdown("""
                <div class="login-container">
                    <div class="login-header">
                        <h2 style="font-size: 1.5rem; font-weight: 600;">🔐 로그인</h2>
                        <p style="color: #6b7280; font-size: 0.9rem; margin-top: 0.5rem;">
                            계정 정보를 입력해 주세요
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 로그인 폼 (고유 키 사용)
                with st.form(key=form_key, clear_on_submit=False):
                    email = st.text_input(
                        "이메일",
                        placeholder="example@company.com",
                        key=f"{form_key}_email",
                        help="등록된 이메일 주소를 입력해 주세요"
                    )
                    
                    password = st.text_input(
                        "비밀번호",
                        type="password",
                        placeholder="비밀번호를 입력하세요",
                        key=f"{form_key}_password",
                        help="비밀번호를 입력해 주세요"
                    )
                    
                    # 버튼 중앙 정렬
                    col_a, col_b, col_c = st.columns([1, 2, 1])
                    with col_b:
                        submit_button = st.form_submit_button(
                            "🚀 로그인",
                            use_container_width=True,
                            type="primary"
                        )
                    
                    # 로그인 처리
                    if submit_button:
                        _handle_login_submission(email, password)
                        
                # 추가 정보 (선택적)
                # with st.expander("💡 도움말", expanded=False):
                #     st.info("""
                #     **로그인 관련 도움말:**
                #     - 이메일과 비밀번호를 정확히 입력해 주세요
                #     - 로그인 정보가 기억나지 않으시면 관리자에게 문의하세요
                #     - 보안을 위해 공용 컴퓨터에서는 로그아웃을 꼭 해주세요
                #     """)


def _handle_login_submission(email: str, password: str):
    """
    로그인 제출 처리 - 개선된 에러 처리 및 사용자 피드백
    """
    # 입력 검증
    if not email or not password:
        st.error("⚠️ 이메일과 비밀번호를 모두 입력해주세요.")
        return
    
    if "@" not in email:
        st.error("⚠️ 올바른 이메일 형식을 입력해주세요.")
        return
    
    try:
        auth_manager = AuthManager()
        login_start_time = time.time()
        
        with st.spinner("🔄 로그인 처리 중..."):
            # 로그인 실행
            success, error_message = auth_manager.login(email, password)
            
            login_duration = time.time() - login_start_time
            logger.info(f"Login attempt for {email}: {'success' if success else 'failed'} in {login_duration:.2f}s")
        
        if success:
            # 로그인 성공
            st.success("✅ 로그인 성공! 대시보드로 이동합니다.")
            
            # 성공 메시지를 잠시 보여준 후 페이지 새로고침
            with st.spinner("📊 대시보드 로딩 중..."):
                time.sleep(1)  # 사용자가 성공 메시지를 볼 수 있도록
                
            # 세션 상태 업데이트 후 페이지 새로고침
            st.session_state.auth_checked = False  # 강제로 재인증 체크
            st.rerun()
            
        else:
            # 로그인 실패
            error_msg = error_message or "이메일 또는 비밀번호가 올바르지 않습니다."
            st.error(f"❌ {error_msg}")
            
            # 보안을 위한 추가 안내
            st.warning("🔒 여러 번 로그인에 실패하면 계정이 일시적으로 잠길 수 있습니다.")
            
            logger.warning(f"Login failed for {email}: {error_msg}")
            
    except Exception as e:
        # 예상치 못한 오류
        error_msg = "시스템 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        st.error(f"❌ {error_msg}")
        
        # 사용자에게 추가 도움 제공
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