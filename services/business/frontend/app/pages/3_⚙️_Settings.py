"""
분석 페이지
"""
import streamlit as st
import sys
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from utils.session_manager import require_auth, get_current_user_info
from components.layout.sidebar import render_sidebar
from components.layout.header import render_header, render_page_actions


def configure_page():
    """페이지 기본 설정"""
    st.set_page_config(
        page_title=f"분석 - {settings.PAGE_TITLE}",
        page_icon="📊",
        layout=settings.LAYOUT,
        initial_sidebar_state=settings.INITIAL_SIDEBAR_STATE
    )


def generate_sample_data():
    """샘플 분석 데이터 생성"""
    
    # 30일간의 데이터
    dates = [(datetime.now() - timedelta(days=i)) for i in range(29, -1, -1)]
    
    # 로그인 데이터
    login_data = {
        'date': dates,
        'daily_logins': np.random.poisson(50, 30) + np.random.normal(0, 5, 30),
        'unique_users': np.random.poisson(35, 30) + np.random.normal(0, 3, 30),
        'failed_attempts': np.random.poisson(5, 30)
    }
    
    # 사용자 분포 데이터
    user_data = {
        'age_group': ['18-25', '26-35', '36-45', '46-55', '55+'],
        'count': [145, 289, 234, 187, 98],
        'active_ratio': [0.85, 0.92, 0.88, 0.79, 0.73]
    }
    
    # 지역별 데이터
    region_data = {
        'region': ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '기타'],
        'users': [456, 123, 89, 67, 45, 34, 28, 158],
        'growth_rate': [0.15, 0.08, 0.12, 0.06, 0.18, 0.11, 0.09, 0.14]
    }
    
    return login_data, user_data, region_data


def render_time_series_analysis():
    """시계열 분석"""
    st.subheader("📈 로그인 트렌드 분석")
    
    login_data, _, _ = generate_sample_data()
    df = pd.DataFrame(login_data)
    
    # 날짜 포맷팅
    df['date_str'] = df['date'].dt.strftime('%m/%d')
    
    # 시계열 차트
    fig = go.Figure()
    
    # 일일 로그인 수
    fig.add_trace(go.Scatter(
        x=df['date_str'],
        y=df['daily_logins'],
        mode='lines+markers',
        name='일일 로그인',
        line=dict(color='#1f77b4', width=2),
        fill='tonexty'
    ))
    
    # 고유 사용자 수
    fig.add_trace(go.Scatter(
        x=df['date_str'],
        y=df['unique_users'],
        mode='lines+markers',
        name='고유 사용자',
        line=dict(color='#ff7f0e', width=2)
    ))
    
    # 실패한 로그인 시도
    fig.add_trace(go.Bar(
        x=df['date_str'],
        y=df['failed_attempts'],
        name='로그인 실패',
        marker_color='rgba(255, 0, 0, 0.3)',
        yaxis='y2'
    ))
    
    # 레이아웃 설정
    fig.update_layout(
        title='최근 30일 로그인 활동',
        xaxis_title='날짜',
        yaxis=dict(title='로그인 수', side='left'),
        yaxis2=dict(title='실패 횟수', side='right', overlaying='y'),
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 통계 요약
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_daily = int(df['daily_logins'].mean())
        st.metric("평균 일일 로그인", f"{avg_daily}", f"+{avg_daily-45}")
    
    with col2:
        avg_unique = int(df['unique_users'].mean())
        st.metric("평균 고유 사용자", f"{avg_unique}", f"+{avg_unique-35}")
    
    with col3:
        total_failed = int(df['failed_attempts'].sum())
        st.metric("총 로그인 실패", f"{total_failed}", f"-{total_failed-150}")
    
    with col4:
        success_rate = round((1 - df['failed_attempts'].sum() / df['daily_logins'].sum()) * 100, 1)
        st.metric("성공률", f"{success_rate}%", f"+{success_rate-94.5}%")


def render_user_demographics():
    """사용자 인구통계"""
    st.subheader("👥 사용자 인구통계 분석")
    
    _, user_data, region_data = generate_sample_data()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 연령대별 분포
        user_df = pd.DataFrame(user_data)
        
        fig_age = px.bar(
            user_df,
            x='age_group',
            y='count',
            title='연령대별 사용자 분포',
            color='count',
            color_continuous_scale='Blues',
            text='count'
        )
        fig_age.update_traces(texttemplate='%{text}', textposition='outside')
        fig_age.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_age, use_container_width=True)
        
        # 활성화 비율
        fig_active = px.bar(
            user_df,
            x='age_group',
            y='active_ratio',
            title='연령대별 활성화 비율',
            color='active_ratio',
            color_continuous_scale='Greens',
            text=[f"{x:.1%}" for x in user_df['active_ratio']]
        )
        fig_active.update_traces(texttemplate='%{text}', textposition='outside')
        fig_active.update_layout(showlegend=False, yaxis=dict(tickformat='.0%'), height=400)
        st.plotly_chart(fig_active, use_container_width=True)
    
    with col2:
        # 지역별 분포
        region_df = pd.DataFrame(region_data)
        
        fig_region = px.pie(
            region_df,
            values='users',
            names='region',
            title='지역별 사용자 분포',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_region.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_region, use_container_width=True)
        
        # 지역별 성장률
        fig_growth = px.bar(
            region_df,
            x='region',
            y='growth_rate',
            title='지역별 성장률',
            color='growth_rate',
            color_continuous_scale='RdYlGn',
            text=[f"{x:.1%}" for x in region_df['growth_rate']]
        )
        fig_growth.update_traces(texttemplate='%{text}', textposition='outside')
        fig_growth.update_layout(showlegend=False, yaxis=dict(tickformat='.0%'), height=400)
        fig_growth.update_xaxes(tickangle=45)
        st.plotly_chart(fig_growth, use_container_width=True)


def render_security_analysis():
    """보안 분석"""
    st.subheader("🔒 보안 분석")
    
    # 보안 이벤트 데이터
    security_events = {
        'event_type': ['로그인 실패', '비정상 접근', 'IP 차단', '패스워드 재설정', '2FA 활성화'],
        'count': [145, 23, 8, 67, 234],
        'severity': ['Medium', 'High', 'High', 'Low', 'Low']
    }
    
    security_df = pd.DataFrame(security_events)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 보안 이벤트 분포
        color_map = {'High': '#ff6b6b', 'Medium': '#feca57', 'Low': '#48cab2'}
        colors = [color_map[severity] for severity in security_df['severity']]
        
        fig_security = px.bar(
            security_df,
            x='event_type',
            y='count',
            title='보안 이벤트 현황',
            color='severity',
            color_discrete_map=color_map,
            text='count'
        )
        fig_security.update_traces(texttemplate='%{text}', textposition='outside')
        fig_security.update_xaxes(tickangle=45)
        st.plotly_chart(fig_security, use_container_width=True)
    
    with col2:
        # 보안 점수 게이지
        security_score = 85
        
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = security_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "보안 점수"},
            delta = {'reference': 80},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkgreen"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig_gauge.update_layout(height=400)
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    # 보안 권장사항
    st.markdown("#### 🛡️ 보안 권장사항")
    
    recommendations = [
        {"level": "high", "text": "비정상 접근 패턴을 보이는 IP 주소에 대한 추가 모니터링이 필요합니다."},
        {"level": "medium", "text": "로그인 실패율이 평균보다 높습니다. 사용자 교육을 고려해보세요."},
        {"level": "low", "text": "2FA 활성화율이 좋습니다. 지속적인 홍보를 권장합니다."}
    ]
    
    for rec in recommendations:
        if rec["level"] == "high":
            st.error(f"🚨 {rec['text']}")
        elif rec["level"] == "medium":
            st.warning(f"⚠️ {rec['text']}")
        else:
            st.success(f"✅ {rec['text']}")


def render_performance_metrics():
    """성능 메트릭"""
    st.subheader("⚡ 시스템 성능")
    
    # 성능 데이터
    performance_data = {
        'metric': ['응답 시간', 'CPU 사용률', '메모리 사용률', '디스크 I/O', '네트워크 처리량'],
        'current': [245, 68, 72, 45, 89],
        'threshold': [500, 80, 85, 70, 95],
        'unit': ['ms', '%', '%', '%', '%']
    }
    
    perf_df = pd.DataFrame(performance_data)
    
    # 성능 지표 표시
    cols = st.columns(len(perf_df))
    
    for i, (_, row) in enumerate(perf_df.iterrows()):
        with cols[i]:
            # 상태 결정
            ratio = row['current'] / row['threshold']
            if ratio < 0.7:
                status = "good"
                color = "#28a745"
                icon = "🟢"
            elif ratio < 0.9:
                status = "warning"
                color = "#ffc107"
                icon = "🟡"
            else:
                status = "critical"
                color = "#dc3545"
                icon = "🔴"
            
            st.markdown(f"""
                <div style="
                    padding: 1rem;
                    background: white;
                    border: 2px solid {color};
                    border-radius: 10px;
                    text-align: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{icon}</div>
                    <div style="font-weight: bold; color: {color};">{row['metric']}</div>
                    <div style="font-size: 1.8rem; font-weight: bold; margin: 0.5rem 0;">
                        {row['current']}{row['unit']}
                    </div>
                    <div style="font-size: 0.8rem; color: #666;">
                        임계값: {row['threshold']}{row['unit']}
                    </div>
                </div>
            """, unsafe_allow_html=True)


def render_export_options():
    """데이터 내보내기 옵션"""
    st.subheader("📤 데이터 내보내기")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 분석 리포트 다운로드", use_container_width=True):
            st.info("분석 리포트를 생성 중입니다... (준비 중)")
    
    with col2:
        if st.button("📈 차트 이미지 저장", use_container_width=True):
            st.info("차트 이미지를 저장하는 중입니다... (준비 중)")
    
    with col3:
        if st.button("📋 데이터 CSV 내보내기", use_container_width=True):
            st.info("CSV 파일을 생성하는 중입니다... (준비 중)")


def main():
    """메인 함수"""
    
    # 페이지 설정
    configure_page()
    
    # 인증 확인
    require_auth()
    
    # 현재 페이지 설정
    st.session_state.current_page = "Analytics"
    
    # 사이드바 렌더링
    render_sidebar()
    
    # 헤더 렌더링
    actions = [
        {
            "label": "📊 새로고침",
            "key": "refresh_analytics",
            "type": "secondary",
            "help": "분석 데이터를 새로고침합니다",
            "callback": lambda: st.rerun()
        }
    ]
    
    render_header("분석")
    render_page_actions(actions)
    
    # 메인 콘텐츠
    render_time_series_analysis()
    
    st.markdown("---")
    render_user_demographics()
    
    st.markdown("---")
    render_security_analysis()
    
    st.markdown("---")
    render_performance_metrics()
    
    st.markdown("---")
    render_export_options()


if __name__ == "__main__":
    main()