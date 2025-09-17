import streamlit as st
from auth.auth_manager import AuthManager
from components.layout.sidebar import render_sidebar
from views.login import show_login_page
from views.dashboard_management import show_management_dashboard
from views.dashboard_operations import show_operations_dashboard
from config.settings import settings


def main():
    st.set_page_config(
        page_title=settings.PAGE_TITLE,
        page_icon=settings.PAGE_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 네비게이션 방식에서 적용
    # pages = {
    #     "📊 대시보드": [
    #         st.Page(show_management_dashboard, title="경영 대시보드", icon="💼"),
    #         st.Page(show_operations_dashboard, title="운영 대시보드", icon="⚙️"),
    #     ]
    # }
    
    pages = {
        "💼 경영 대시보드": show_management_dashboard,
        "⚙️ 운영 대시보드": show_operations_dashboard
    }    

    # 인증 상태 확인
    auth_manager = AuthManager()
    is_authenticated, user_info = auth_manager.check_authentication()

    if not is_authenticated:
        # 로그인 페이지 전용 뷰
        show_login_page()
    else:
        # 사이드바는 사용자 정보 + 로그아웃만 렌더링
        selected_page = render_sidebar(user_info, pages)

        # # 네비게이션 메뉴 정의  (render_sidebar를 덮어써서 사용 불가가)
        # nav = st.navigation(pages)
        # nav.run()

        # 선택된 페이지 실행
        pages[selected_page]()        

if __name__ == "__main__":
    main()