"""
메인 Streamlit 애플리케이션 - 로그인 페이지
"""
import streamlit as st
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from utils.session_manager import SessionManager, is_authenticated
from components.auth.login_form import render_login_form, render_login_status
from components.layout.header import render_status_banner


def configure_page():
    """페이지 기본 설정"""
    st.set_page_config(
        page_title=settings.PAGE_TITLE,
        page_icon=settings.PAGE_ICON,
        layout=settings.LAYOUT,
        initial_sidebar_state="collapsed"  # 로그인 페이지에서는 사이드바 숨김
    )


def load_custom_css():
    """커스텀 CSS 로드"""
    st.markdown("""
        <style>
        /* 로그인 페이지 전용 스타일 */
        .main > div {
            padding-top: 2rem;
        }
        
        .stForm {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .stButton > button {
            height: 3rem;
            font-weight: bold;
            border-radius: 5px;
        }
        
        .stTextInput > div > div > input {
            height: 3rem;
            border-radius: 5px;
        }
        
        /* 반응형 디자인 */
        @media (max-width: 768px) {
            .main > div {
                padding: 1rem;
            }
        }
        
        /* 애니메이션 효과 */
        .stForm {
            animation: fadeIn 0.5s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        </style>
    """, unsafe_allow_html=True)


def main():
    """메인 애플리케이션 함수"""
    
    # 페이지 설정
    configure_page()
    
    # 커스텀 CSS 로드
    load_custom_css()
    
    # 세션 초기화
    SessionManager.initialize_session()
    
    # 로그아웃 처리 후 돌아온 경우 메시지 표시
    if st.session_state.get("logout_message"):
        st.success(st.session_state.logout_message)
        del st.session_state.logout_message
    
    # 이미 인증된 사용자는 대시보드로 리다이렉트
    if is_authenticated():
        st.success("✅ 이미 로그인되어 있습니다. 대시보드로 이동합니다...")
        st.balloons()
        
        # 잠시 대기 후 대시보드로 이동
        import time
        time.sleep(1)
        st.switch_page("pages/1_🏠_Dashboard.py")
        st.stop()
    
    # 상태 배너 (필요시)
    if st.session_state.get("show_maintenance_banner", False):
        render_status_banner(
            "시스템 점검이 예정되어 있습니다. 서비스 이용에 참고해주세요.",
            type="warning",
            dismissible=True
        )
    
    # 로그인 폼 렌더링
    render_login_form()
    
    # 로그인 상태 표시
    render_login_status()
    
    # 푸터
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.8rem; margin-top: 2rem;">
            <p>© 2024 Pilot Auth System. All rights reserved.</p>
            <p>
                <a href="#" style="color: #1f77b4; text-decoration: none;">개인정보처리방침</a> |
                <a href="#" style="color: #1f77b4; text-decoration: none;">이용약관</a> |
                <a href="#" style="color: #1f77b4; text-decoration: none;">고객지원</a>
            </p>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()