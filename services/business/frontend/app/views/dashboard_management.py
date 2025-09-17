import streamlit as st

def show_management_dashboard():
    """경영 대시보드"""
    st.header("📈 경영 대시보드")
    
    # 메트릭 예시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 매출", "₩1,234,567,890", "12.5%")
    
    with col2:
        st.metric("순이익", "₩234,567,890", "8.2%")
    
    with col3:
        st.metric("고객 수", "12,345", "5.1%")
    
    with col4:
        st.metric("전환율", "3.2%", "-0.1%")
    
    # 차트 섹션
    st.subheader("📊 매출 추이")
    
    # 임시 데이터
    import pandas as pd
    import numpy as np
    
    dates = pd.date_range('2024-01-01', periods=30, freq='D')
    revenue_data = pd.DataFrame({
        '날짜': dates,
        '매출': np.random.randint(1000000, 5000000, 30)
    })
    
    st.line_chart(revenue_data.set_index('날짜'))
    
    # 추가 분석
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 월별 목표 달성률")
        target_data = pd.DataFrame({
            '월': ['1월', '2월', '3월', '4월'],
            '달성률': [95, 102, 88, 110]
        })
        st.bar_chart(target_data.set_index('월'))
    
    with col2:
        st.subheader("🌍 지역별 매출")
        region_data = pd.DataFrame({
            '지역': ['서울', '경기', '부산', '대구', '기타'],
            '매출 비중': [45, 25, 12, 8, 10]
        })
        st.bar_chart(region_data.set_index('지역'))