"""
대시보드 페이지
"""
import streamlit as st
import sys
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from utils.session_manager import require_auth, get_current_user_info, get_current_user
from utils.auth_client import auth_client
from components.layout.sidebar import render_sidebar
from components.layout.header import render_header, render_page_metrics, render_status_banner


def configure_page():
    """페이지 기본 설정"""
    st.set_page_config(
        page_title=f"대시보드 - {settings.PAGE_TITLE}",
        page_icon="🏠",
        layout=settings.LAYOUT,
        initial_sidebar_state=settings.INITIAL_SIDEBAR_STATE
    )


def load_dashboard_data():
    """대시보드 데이터 로드"""
    success, data, error = auth_client.get_dashboard_data()
    
    if success:
        return data
    else:
        if error == "인증이 필요합니다":
            st.error("세션이 만료되었습니다. 다시 로그인해주세요.")
            if st.button("로그인 페이지로 이동"):
                st.switch_page("app.py")
        else:
            st.error(f"대시보드 데이터 로드 실패: {error}")
        return None


def render_welcome_section():
    """환영 섹션"""
    user_info = get_current_user_info()
    current_user = get_current_user()
    
    if user_info:
        display_name = user_info.get('display_name', '사용자')
        
        st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 2rem;
                border-radius: 15px;
                color: white;
                margin-bottom: 2rem;
                text-align: center;
            ">
                <h2 style="margin: 0 0 0.5rem 0;">👋 환영합니다, {display_name}님!</h2>
                <p style="margin: 0; opacity: 0.9; font-size: 1.1rem;">
                    오늘도 좋은 하루 되세요. 최신 대시보드 정보를 확인해보세요.
                </p>
            </div>
        """, unsafe_allow_html=True)


def render_system_metrics():
    """시스템 메트릭 표시"""
    
    # 샘플 메트릭 데이터 (실제로는 백엔드에서 가져와야 함)
    metrics = [
        {
            "label": "📊 총 사용자",
            "value": "1,234",
            "delta": "+12",
            "help": "등록된 전체 사용자 수"
        },
        {
            "label": "🔐 활성 세션",
            "value": "89",
            "delta": "+3",
            "help": "현재 활성화된 세션 수"
        },
        {
            "label": "📈 오늘 로그인",
            "value": "156",
            "delta": "+23",
            "help": "오늘 로그인한 사용자 수"
        },
        {
            "label": "⚡ 시스템 상태",
            "value": "정상",
            "delta": None,
            "help": "전체 시스템 상태"
        }
    ]
    
    render_page_metrics(metrics)


def render_activity_chart():
    """활동 차트"""
    st.subheader("📈 최근 7일 활동")
    
    # 샘플 데이터 생성
    dates = [(datetime.now() - timedelta(days=i)) for i in range(6, -1, -1)]
    data = {
        '날짜': [d.strftime('%m/%d') for d in dates],
        '로그인': [45, 52, 48, 61, 58, 67, 72],
        '활성 사용자': [89, 94, 87, 103, 98, 112, 119],
        '새 가입': [3, 5, 2, 8, 4, 6, 9]
    }
    
    df = pd.DataFrame(data)
    
    # Plotly 차트 생성
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['날짜'], y=df['로그인'],
        mode='lines+markers',
        name='로그인',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['날짜'], y=df['활성 사용자'],
        mode='lines+markers',
        name='활성 사용자',
        line=dict(color='#ff7f0e', width=3),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Bar(
        x=df['날짜'], y=df['새 가입'],
        name='새 가입',
        marker_color='#2ca02c',
        opacity=0.7
    ))
    
    fig.update_layout(
        title='사용자 활동 추이',
        xaxis_title='날짜',
        yaxis_title='수량',
        hovermode='x unified',
        showlegend=True,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_recent_activity():
    """최근 활동 로그"""
    st.subheader("📋 최근 활동")
    
    # 샘플 활동 데이터
    activities = [
        {"time": "2분 전", "user": "김철수", "action": "로그인", "status": "성공"},
        {"time": "5분 전", "user": "이영희", "action": "비밀번호 변경", "status": "성공"},
        {"time": "8분 전", "user": "박민수", "action": "로그아웃", "status": "성공"},
        {"time": "12분 전", "user": "최지은", "action": "프로필 업데이트", "status": "성공"},
        {"time": "15분 전", "user": "정태호", "action": "로그인 실패", "status": "실패"},
    ]
    
    for activity in activities:
        status_color = "#28a745" if activity["status"] == "성공" else "#dc3545"
        status_icon = "✅" if activity["status"] == "성공" else "❌"
        
        st.markdown(f"""
            <div style="
                display: flex;
                align-items: center;
                padding: 0.75rem;
                margin: 0.5rem 0;
                background: #f8f9fa;
                border-left: 4px solid {status_color};
                border-radius: 5px;
            ">
                <div style="margin-right: 1rem; font-size: 1.2rem;">{status_icon}</div>
                <div style="flex: 1;">
                    <strong>{activity["user"]}</strong>이(가) <em>{activity["action"]}</em>
                    <div style="font-size: 0.8rem; color: #666; margin-top: 0.2rem;">
                        {activity["time"]} • 상태: {activity["status"]}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)


def render_system_status():
    """시스템 상태 섹션"""
    st.subheader("🖥️ 시스템 상태")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div style="padding: 1rem; background: #d4edda; border-radius: 8px; text-align: center;">
                <div style="font-size: 2rem;">🟢</div>
                <div style="font-weight: bold; margin: 0.5rem 0;">API 서버</div>
                <div style="color: #155724;">정상 작동</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style="padding: 1rem; background: #d4edda; border-radius: 8px; text-align: center;">
                <div style="font-size: 2rem;">🟢</div>
                <div style="font-weight: bold; margin: 0.5rem 0;">데이터베이스</div>
                <div style="color: #155724;">정상 작동</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div style="padding: 1rem; background: #fff3cd; border-radius: 8px; text-align: center;">
                <div style="font-size: 2rem;">🟡</div>
                <div style="font-weight: bold; margin: 0.5rem 0;">캐시</div>
                <div style="color: #856404;">점검 중</div>
            </div>
        """, unsafe_allow_html=True)


def render_quick_stats():
    """빠른 통계"""
    st.subheader("⚡ 빠른 통계")

    col1, col2 = st.columns(2)

    with col1:
        roles_data = pd.DataFrame({
            'Role': ['관리자', '일반 사용자', '게스트'],
            'Count': [5, 89, 12]
        })
        fig_roles = px.pie(
            roles_data,
            values='Count',
            names='Role',
            title='사용자 역할 분포',
            color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c']
        )
        fig_roles.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_roles, use_container_width=True)

    with col2:
        months_data = pd.DataFrame({
            'Month': ['1월', '2월', '3월', '4월', '5월', '6월'],
            'New_Users': [23, 31, 28, 45, 38, 52]
        })
        fig_monthly = px.bar(
            months_data,
            x='Month',
            y='New_Users',
            title='월별 신규 가입자',
            color='New_Users',
            color_continuous_scale='Blues'
        )
        fig_monthly.update_layout(showlegend=False)
        st.plotly_chart(fig_monthly, use_container_width=True)

def main():
    """메인 함수"""
    
    # 페이지 설정
    configure_page()
    
    # 인증 확인 (인증되지 않으면 로그인 페이지로 리다이렉트)
    require_auth()
    
    # 현재 페이지 설정
    st.session_state.current_page = "Dashboard"
    
    # 사이드바 렌더링
    render_sidebar()
    
    # 헤더 렌더링
    render_header("대시보드")
    
    # 대시보드 데이터 로드
    dashboard_data = load_dashboard_data()
    
    if dashboard_data:
        # 성공 메시지 (한 번만 표시)
        if not st.session_state.get("dashboard_loaded", False):
            render_status_banner(
                f"✅ {dashboard_data.get('message', '대시보드 데이터를 성공적으로 로드했습니다.')}",
                type="success",
                dismissible=True
            )
            st.session_state.dashboard_loaded = True
    
    # 환영 섹션
    render_welcome_section()
    
    # 시스템 메트릭
    render_system_metrics()
    
    # 메인 콘텐츠
    st.markdown("---")
    
    # 활동 차트
    render_activity_chart()
    
    # 두 컬럼 레이아웃
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_recent_activity()
    
    with col2:
        render_system_status()
    
    # 빠른 통계
    st.markdown("---")
    render_quick_stats()
    
    # 새로고침 버튼
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("🔄 데이터 새로고침", use_container_width=True):
            # 캐시 클리어 및 페이지 새로고침
            st.session_state.dashboard_loaded = False
            st.rerun()


if __name__ == "__main__":
    main()
    
