import streamlit as st
from auth.auth_manager import AuthManager

def render_sidebar(user_info: dict = None, pages: dict = None):
    if pages is None:
        pages = {}

    with st.sidebar:
        # 상단 영역: 페이지 선택
        st.markdown("### 📊 대시보드")
        selected_page = st.selectbox(
            "페이지 선택",
            list(pages.keys()),
            label_visibility="collapsed"
        )

        # 하단 영역: 사용자 정보 + 로그아웃
        if user_info:
            st.markdown("### 👤 사용자 정보")
            st.write(f"**이름:** {user_info.get('display_name', 'N/A')}")
            st.write(f"**이메일:** {user_info.get('email', 'N/A')}")
            st.write(f"**역할:** {user_info.get('role', 'user')}")

            if st.button("🚪 로그아웃", use_container_width=True, type="secondary"):
                with st.spinner("로그아웃 중..."):
                    auth_manager = AuthManager()
                    success = auth_manager.logout()
                    if success:
                        st.success("로그아웃 처리 중...")
                        st.session_state.clear()
                        st.rerun()
                    else:
                        st.error("로그아웃 중 오류가 발생했습니다.")

    return selected_page