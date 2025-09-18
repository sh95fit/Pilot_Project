import streamlit as st
from components.auth.login_form import render_login_form

def show_login_page():
    """
    로그인 페이지 표시
    - 중복 렌더링 방지
    - 깔끔한 중앙 정렬 레이아웃
    """
    # 로그인 페이지 전용 스타일 (개선된 버전)
    st.markdown("""
    <style>
    .login-page {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 75vh;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        margin: -1rem -1rem 0 -1rem;
        padding: 2rem;
    }
    .main > div {
        padding-top: 1rem;
    }
    .stApp > header {
        display: none;
    }
    /* 제목 크기 강제 조정 */
    .login-page h1 {
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem !important;
    }
    .login-container h2 {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        margin: 0 !important;
    }
    /* 페이드 인 효과 */
    .login-content {
        animation: fadeIn 0.6s ease-out;
    }
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 로그인 페이지 헤더 (크기 조정 및 애니메이션 추가)
    st.markdown("""
    <div class="login-content" style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #1f2937; font-size: 1.8rem !important; font-weight: 600 !important; margin-bottom: 0.5rem;">
            🏢 Business Dashboard
        </h1>
        <p style="color: #6b7280; font-size: 1rem; margin-top: 0.5rem;">
            관리자 로그인이 필요합니다
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 로그인 폼 렌더링 (한 번만)
    render_login_form()
    
    # 푸터
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; color: #9ca3af;">
        <small>© 2025 Business Dashboard. All rights reserved.</small>
    </div>
    """, unsafe_allow_html=True)