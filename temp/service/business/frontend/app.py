import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="Business Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API 베이스 URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

# 사이드바
st.sidebar.title("📊 Business Dashboard")
page = st.sidebar.selectbox(
    "페이지 선택",
    ["대시보드", "매출 분석", "고객 분석", "설정"]
)

# API 호출 함수
@st.cache_data(ttl=300)  # 5분 캐시
def fetch_dashboard_data():
    try:
        response = requests.get(f"{API_BASE_URL}/dashboard", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API 호출 오류: {e}")
        return None

@st.cache_data(ttl=300)
def fetch_sales_data():
    try:
        response = requests.get(f"{API_BASE_URL}/sales", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"매출 데이터 호출 오류: {e}")
        return None

# 메인 대시보드 페이지
def show_dashboard():
    st.title("📊 비즈니스 대시보드")
    
    # 데이터 로드
    dashboard_data = fetch_dashboard_data()
    
    if not dashboard_data:
        st.error("데이터를 불러올 수 없습니다.")
        return
    
    metrics = dashboard_data["metrics"]
    sales_data = dashboard_data["sales_data"]
    
    # 상단 메트릭 카드
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 총 매출",
            value=f"₩{metrics['revenue']:,.0f}",
            delta="12.5%"
        )
    
    with col2:
        st.metric(
            label="👥 고객 수",
            value=f"{metrics['customers']:,}",
            delta="8.2%"
        )
    
    with col3:
        st.metric(
            label="📈 전환율",
            value=f"{metrics['conversion_rate']:.1f}%",
            delta="0.5%"
        )
    
    with col4:
        st.metric(
            label="🕐 마지막 업데이트",
            value=datetime.now().strftime("%H:%M"),
            delta="실시간"
        )
    
    st.divider()
    
    # 차트 영역
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 월별 매출 추이")
        
        df_sales = pd.DataFrame(sales_data)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_sales['period'],
            y=df_sales['sales'],
            mode='lines+markers',
            name='실제 매출',
            line=dict(color='#1f77b4', width=3)
        ))
        fig.add_trace(go.Scatter(
            x=df_sales['period'],
            y=df_sales['target'],
            mode='lines+markers',
            name='목표 매출',
            line=dict(color='#ff7f0e', width=2, dash='dash')
        ))
        
        fig.update_layout(
            xaxis_title="기간",
            yaxis_title="매출 (원)",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 목표 달성률")
        
        for data in sales_data:
            achievement_rate = (data['sales'] / data['target']) * 100
            st.metric(
                label=f"{data['period']}",
                value=f"{achievement_rate:.1f}%",
                delta=f"{data['growth_rate']:.1f}% 성장"
            )

# 매출 분석 페이지
def show_sales_analysis():
    st.title("📈 매출 분석")
    
    sales_data = fetch_sales_data()
    
    if not sales_data:
        st.error("매출 데이터를 불러올 수 없습니다.")
        return
    
    df = pd.DataFrame(sales_data)
    
    # 필터링 옵션
    st.sidebar.subheader("필터 옵션")
    selected_periods = st.sidebar.multiselect(
        "기간 선택",
        df['period'].tolist(),
        default=df['period'].tolist()
    )
    
    filtered_df = df[df['period'].isin(selected_periods)]
    
    # 매출 트렌드 차트
    fig_trend = px.bar(
        filtered_df,
        x='period',
        y='sales',
        title="매출 트렌드",
        color='growth_rate',
        color_continuous_scale='RdYlGn'
    )
    
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # 데이터 테이블
    st.subheader("📋 상세 데이터")
    st.dataframe(filtered_df, use_container_width=True)

# 고객 분석 페이지
def show_customer_analysis():
    st.title("👥 고객 분석")
    st.info("고객 분석 기능은 개발 중입니다.")

# 설정 페이지
def show_settings():
    st.title("⚙️ 설정")
    
    st.subheader("API 설정")
    api_url = st.text_input("API Base URL", value=API_BASE_URL)
    
    st.subheader("새로고침 설정")
    refresh_interval = st.slider("자동 새로고침 간격 (분)", 1, 30, 5)
    
    if st.button("설정 저장"):
        st.success("설정이 저장되었습니다!")

# 페이지 라우팅
if page == "대시보드":
    show_dashboard()
elif page == "매출 분석":
    show_sales_analysis()
elif page == "고객 분석":
    show_customer_analysis()
elif page == "설정":
    show_settings()

# 푸터
st.sidebar.divider()
st.sidebar.info("🚀 Business Dashboard v1.0.0")