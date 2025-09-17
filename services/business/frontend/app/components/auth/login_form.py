import streamlit as st
from auth.auth_manager import AuthManager
import time
import logging

logger = logging.getLogger(__name__)

def render_login_form():
    """로그인 폼 렌더링 - 개선된 동기화 처리"""
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: auto;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: white;
    }
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
        color: #1f2937;
    }
    .sync-info {
        font-size: 0.8rem;
        color: #6b7280;
        margin-top: 1rem;
        padding: 0.5rem;
        background-color: #f9fafb;
        border-radius: 0.375rem;
        border-left: 4px solid #3b82f6;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown('<h2 class="login-header">🔐 로그인</h2>', unsafe_allow_html=True)
            
            # 로그인 상태 디버그 정보 (개발 환경에서만)
            # if st.secrets.get("environment", "prod") == "dev":
            #     _render_debug_info()
            
            with st.form("login_form"):
                email = st.text_input(
                    "이메일",
                    placeholder="이메일을 입력하세요",
                    key="login_email"
                )
                
                password = st.text_input(
                    "비밀번호",
                    type="password",
                    placeholder="비밀번호를 입력하세요",
                    key="login_password"
                )
                
                col_a, col_b, col_c = st.columns([1, 2, 1])
                with col_b:
                    submit_button = st.form_submit_button(
                        "로그인",
                        use_container_width=True,
                        type="primary"
                    )
                
                if submit_button:
                    _handle_login_submission(email, password)


def _handle_login_submission(email: str, password: str):
    """
    로그인 제출 처리 - 개선된 동기화 및 에러 처리
    """
    if not email or not password:
        st.error("이메일과 비밀번호를 모두 입력해주세요.")
        return
    
    try:
        auth_manager = AuthManager()
        
        # 로그인 시작 시간 기록
        login_start_time = time.time()
        
        with st.spinner("로그인 처리 중..."):
            # 로그인 실행 (동기화 대기 포함)
            success, error_message = auth_manager.login(email, password)
            
            login_duration = time.time() - login_start_time
            logger.info(f"Login process completed in {login_duration:.2f}s")
        
        if success:
            # 로그인 성공
            st.success("✅ 로그인 성공!")
            
            # 동기화 상태 확인 (선택적)
            # if st.secrets.get("environment", "production") == "development":
            #     sync_status = auth_manager.get_auth_status()
            #     if sync_status.get('cookies_synced'):
            #         st.info("🔄 쿠키 동기화 완료")
            #     else:
            #         st.warning("⚠️ 쿠키 동기화 대기 중 (세션 상태 사용)")
            
            # 약간의 지연 후 페이지 새로고침 (사용자 경험 개선)
            with st.spinner("페이지 이동 중..."):
                time.sleep(0.3)  # 사용자가 성공 메시지를 볼 수 있도록 짧은 지연
                
            # 페이지 새로고침으로 인증 상태 반영
            st.rerun()
            
        else:
            # 로그인 실패
            error_msg = error_message or "로그인에 실패했습니다."
            st.error(f"❌ {error_msg}")
            
            # 실패 원인 로깅
            logger.warning(f"Login failed for email: {email}, reason: {error_msg}")
            
    except Exception as e:
        # 예상치 못한 오류 처리
        error_msg = "로그인 처리 중 예상치 못한 오류가 발생했습니다."
        st.error(f"❌ {error_msg}")
        logger.error(f"Unexpected login error for email: {email}, error: {e}")

def _render_debug_info():
    """
    개발 환경용 디버그 정보 표시
    """
    try:
        auth_manager = AuthManager()
        auth_status = auth_manager.get_auth_status()
        
        with st.expander("🔧 디버그 정보", expanded=False):
            st.json(auth_status)
            
            # 동기화 강제 확인 버튼
            if st.button("🔄 동기화 상태 확인", key="force_sync_check"):
                with st.spinner("동기화 확인 중..."):
                    sync_result = auth_manager.force_sync_check()
                    if sync_result:
                        st.success("✅ 동기화 확인됨")
                    else:
                        st.warning("⚠️ 동기화 미완료 또는 토큰 없음")
                        
    except Exception as e:
        st.error(f"디버그 정보 로드 실패: {e}")

def render_logout_button():
    """
    로그아웃 버튼 렌더링 (다른 페이지에서 사용할 수 있도록 분리)
    """
    if st.button("🚪 로그아웃", key="logout_button"):
        try:
            auth_manager = AuthManager()
            
            with st.spinner("로그아웃 처리 중..."):
                logout_success = auth_manager.logout()
                
            if logout_success:
                st.success("✅ 로그아웃 되었습니다.")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ 로그아웃 처리 중 오류가 발생했습니다.")
                
        except Exception as e:
            st.error("❌ 로그아웃 처리 중 예상치 못한 오류가 발생했습니다.")
            logger.error(f"Logout error: {e}")