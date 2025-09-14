"""
헤더 컴포넌트
"""
import streamlit as st
from datetime import datetime
from components.auth.logout_button import render_user_menu
from utils.session_manager import get_current_user_info


def render_header(page_title: str = "대시보드", show_user_menu: bool = True):
    """
    페이지 헤더 렌더링
    
    Args:
        page_title (str): 페이지 제목
        show_user_menu (bool): 사용자 메뉴 표시 여부
    """
    
    # 헤더 컨테이너
    header_container = st.container()
    
    with header_container:
        col1, col2, col3 = st.columns([2, 3, 2])
        
        with col1:
            # 페이지 제목과 아이콘
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                    <h1 style="margin: 0; color: #1f77b4;">
                        {_get_page_icon(page_title)} {page_title}
                    </h1>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # 현재 시간 표시
            current_time = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
            st.markdown(f"""
                <div style="text-align: center; padding: 1rem 0;">
                    <div style="color: #666; font-size: 0.9rem;">
                        📅 {current_time}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # 사용자 메뉴
            if show_user_menu:
                render_user_menu()
        
        # 구분선
        st.markdown("---")


def render_breadcrumb(items: list):
    """
    브레드크럼 네비게이션 렌더링
    
    Args:
        items (list): 브레드크럼 아이템 리스트 [{"name": "홈", "url": "/"}]
    """
    
    if not items:
        return
    
    breadcrumb_html = "<div style='margin-bottom: 1rem; font-size: 0.9rem; color: #666;'>"
    
    for i, item in enumerate(items):
        if i > 0:
            breadcrumb_html += " > "
        
        if item.get("url") and i < len(items) - 1:
            breadcrumb_html += f"<a href='{item['url']}'>{item['name']}</a>"
        else:
            breadcrumb_html += f"<strong>{item['name']}</strong>"
    
    breadcrumb_html += "</div>"
    
    st.markdown(breadcrumb_html, unsafe_allow_html=True)


def render_page_metrics(metrics: list):
    """
    페이지 상단 메트릭 표시
    
    Args:
        metrics (list): 메트릭 리스트 [{"label": "총 사용자", "value": "123", "delta": "+5"}]
    """
    
    if not metrics:
        return
    
    cols = st.columns(len(metrics))
    
    for i, metric in enumerate(metrics):
        with cols[i]:
            st.metric(
                label=metric["label"],
                value=metric["value"],
                delta=metric.get("delta"),
                help=metric.get("help")
            )


def render_page_actions(actions: list):
    """
    페이지 상단 액션 버튼들
    
    Args:
        actions (list): 액션 리스트 [{"label": "새로 추가", "key": "add_new", "type": "primary"}]
    """
    
    if not actions:
        return
    
    cols = st.columns(len(actions))
    
    for i, action in enumerate(actions):
        with cols[i]:
            button_clicked = st.button(
                action["label"],
                key=action["key"],
                type=action.get("type", "secondary"),
                use_container_width=True,
                help=action.get("help")
            )
            
            # 버튼 클릭 시 콜백 실행
            if button_clicked and action.get("callback"):
                action["callback"]()


def render_status_banner(message: str, type: str = "info", dismissible: bool = False):
    """
    상태 배너 렌더링
    
    Args:
        message (str): 표시할 메시지
        type (str): 배너 타입 ("info", "success", "warning", "error")
        dismissible (bool): 닫기 가능 여부
    """
    
    banner_key = f"banner_{hash(message)}"
    
    # 닫힌 배너는 표시하지 않음
    if dismissible and st.session_state.get(f"{banner_key}_dismissed", False):
        return
    
    col1, col2 = st.columns([10, 1]) if dismissible else (st.columns([1])[0], None)
    
    with col1:
        if type == "success":
            st.success(message)
        elif type == "warning":
            st.warning(message)
        elif type == "error":
            st.error(message)
        else:
            st.info(message)
    
    if dismissible and col2:
        with col2:
            if st.button("✕", key=f"{banner_key}_close", help="닫기"):
                st.session_state[f"{banner_key}_dismissed"] = True
                st.rerun()


def _get_page_icon(page_title: str) -> str:
    """페이지별 아이콘 반환"""
    icons = {
        "대시보드": "🏠",
        "dashboard": "🏠",
        "분석": "📊",
        "analytics": "📊",
        "설정": "⚙️",
        "settings": "⚙️",
        "사용자": "👤",
        "user": "👤",
        "로그인": "🔐",
        "login": "🔐"
    }
    
    return icons.get(page_title.lower(), "📄")