"""
로그인 폼 컴포넌트
"""
import streamlit as st
from utils.session_manager import SessionManager


def render_login_form():
    """로그인 폼 렌더링"""
    
    st.markdown("""
        <div style="max-width: 400px; margin: 2rem auto;">
            <h1 style="text-align: center; color: #1f77b4; margin-bottom: 2rem;">
                🔐 로그인
            </h1>
        </div>
    """, unsafe_allow_html=True)
    
    # 중앙 정렬을 위한 컨테이너
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 로그인 폼
        with st.form("login_form", clear_on_submit=False):
            st.markdown("### 계정 정보를 입력해주세요")
            
            email = st.text_input(
                "이메일",
                placeholder="your@email.com",
                help="등록된 이메일 주소를 입력해주세요"
            )
            
            password = st.text_input(
                "비밀번호",
                type="password",
                placeholder="비밀번호를 입력해주세요",
                help="비밀번호는 안전하게 보호됩니다"
            )
            
            # 로그인 버튼
            submitted = st.form_submit_button(
                "로그인",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                if not email or not password:
                    st.error("이메일과 비밀번호를 모두 입력해주세요.")
                else:
                    # 로딩 상태 표시
                    with st.spinner("로그인 중..."):
                        success, error_msg = SessionManager.login(email, password)
                    
                    if not success:
                        st.error(f"로그인 실패: {error_msg}")
        
        # 추가 정보
        st.markdown("---")
        
        with st.expander("📋 시스템 정보"):
            st.info("""
            **인증 시스템 특징:**
            - 🔐 AWS Cognito 기반 보안 인증
            - 🍪 쿠키 기반 세션 관리
            - 🔄 자동 토큰 갱신
            - 📱 반응형 UI 지원
            """)

def render_login_status():
    """로그인 상태 표시"""
    if st.session_state.get("login_attempted", False):
        if SessionManager.is_authenticated():
            st.success("✅ 로그인 성공! 잠시 후 대시보드로 이동합니다.")
            st.balloons()
        else:
            st.warning("🔄 인증 상태를 확인하는 중입니다...")