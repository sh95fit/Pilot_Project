"""
Streamlit 경영 대시보드 (캐싱 최적화)

개선 사항:
- API 호출 캐싱 (5분)
- 함수 분리 및 모듈화
- 에러 핸들링 강화
- 타입 힌팅 추가
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import logging
import altair as alt
from config.settings import settings


# ------------------------------
# 설정
# ------------------------------
API_URL = f"{settings.BACKEND_URL}/api/v1/data/get_sales_summary"

# logger 설정
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# =============================================================================
# API 호출 함수 (캐싱)
# =============================================================================

@st.cache_data(ttl=300, show_spinner="데이터 조회 중...")
def fetch_sales_summary(
    start_date: str, 
    end_date: str, 
    access_token: str, 
    session_id: str
) -> List[Dict]:
    """
    매출 요약 API 호출 (5분 캐싱)
    
    Args:
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        access_token: 인증 토큰
        session_id: 세션 ID
    
    Returns:
        List[Dict]: 매출 데이터
    
    Raises:
        requests.HTTPError: API 호출 실패
    """
    headers = {
        "cookie": f"access_token={access_token}; session_id={session_id}"
    }
    
    # 파일 미분리 형태
    # payload = {
    #     "procedure_name": "get_sales_summary",
    #     "params": [start_date, end_date]
    # }

    # 파일 분리 형태
    payload = {
        "start_date": start_date,
        "end_date": end_date
    }
    
    logger.info(f"API 호출: {start_date} ~ {end_date}")
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()["data"]
        logger.info(f"데이터 수신: {len(data)}건")
        return data
        
    except requests.Timeout:
        logger.error("API 타임아웃")
        raise Exception("서버 응답 시간이 초과되었습니다.")
    except requests.HTTPError as e:
        logger.error(f"HTTP 에러: {e}")
        raise
    except Exception as e:
        logger.exception(f"예상치 못한 에러: {e}")
        raise


# =============================================================================
# 데이터 처리 함수
# =============================================================================

def calculate_total_sales(df: pd.DataFrame, period_type: str = "total") -> float:
    """
    특정 기간 타입의 총 매출 계산
    
    Args:
        df: 매출 데이터프레임
        period_type: 기간 타입 (total, year, month)
    
    Returns:
        float: 총 매출액
    """
    filtered = df[df["period_type"] == period_type]
    return filtered["total_amount_sum"].sum() if not filtered.empty else 0.0


def prepare_monthly_chart_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    월별 차트용 데이터 준비
    
    Args:
        df: 원본 데이터프레임
    
    Returns:
        pd.DataFrame: 차트용 가공 데이터
    """
    month_df = df[df["period_type"] == "month"].copy()
    
    if month_df.empty:
        return pd.DataFrame()
    
    # 날짜 변환
    month_df['해당_월'] = pd.to_datetime(month_df['period_label'])
    # 금액 포맷
    month_df['월_매출액'] = month_df['total_amount_sum'].apply(lambda x: f"{x:,.0f}원")
    
    return month_df.sort_values('해당_월')


# =============================================================================
# 차트 생성 함수
# =============================================================================

def create_monthly_sales_chart(df: pd.DataFrame) -> alt.Chart:
    """
    월별 매출 라인 차트 생성
    
    Args:
        df: 차트용 데이터프레임
    
    Returns:
        alt.Chart: Altair 차트 객체
    """
    if df.empty:
        return None
    
    # 라인 + 포인트
    line = alt.Chart(df).mark_line(
        point=alt.OverlayMarkDef(size=80, filled=True)
    ).encode(
        x=alt.X(
            '해당_월:T',
            axis=alt.Axis(
                title='기간',
                format='%Y년 %m월',
                labelAngle=-45
            )
        ),
        y=alt.Y(
            'total_amount_sum:Q',
            title='월 매출액 (원)',
            axis=alt.Axis(format=',.0f')
        ),
        tooltip=[
            alt.Tooltip('해당_월:T', title='해당 월', format='%Y년 %m월'),
            alt.Tooltip('월_매출액:N', title='월 매출액')
        ]
    ).properties(
        height=400
    )
    
    # 포인트 위 텍스트
    text = alt.Chart(df).mark_text(
        dy=-15,
        color='#1f77b4',
        fontSize=11,
        fontWeight='bold'
    ).encode(
        x='해당_월:T',
        y='total_amount_sum:Q',
        text='월_매출액:N'
    )
    
    return line + text

# =============================================================================
# UI 컴포넌트
# =============================================================================

def render_date_range_selector() -> Tuple[date, date]:
    """
    날짜 범위 선택 UI
    
    Returns:
        Tuple[date, date]: (시작일, 종료일)
    """
    col_start, col_end, _ = st.columns([1, 1, 6])
    
    with col_start:
        start_date = st.date_input(
            "시작일",
            value=datetime(2023, 1, 1),
            key="start_date"
        )
    
    with col_end:
        end_date = st.date_input(
            "종료일",
            value=datetime.today(),
            key="end_date"
        )
    
    # 날짜 검증
    if start_date > end_date:
        st.error("시작일은 종료일보다 이전이어야 합니다.")
        return None, None
    
    return start_date, end_date

def render_metrics(
    total_sales: float,
    year_sales: float,
    period_sales: float,
    current_year: int,
    start_date: date,
    end_date: date
):
    """
    메트릭 카드 렌더링
    
    Args:
        total_sales: 총 매출
        year_sales: 연 매출
        period_sales: 선택 기간 매출
        current_year: 현재 연도
        start_date: 시작일
        end_date: 종료일
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "총 매출 (from 2023)",
            f"₩{total_sales:,.0f}",
            help="2023년 1월 1일부터 현재까지"
        )
    
    with col2:
        st.metric(
            f"연 매출 ({current_year})",
            f"₩{year_sales:,.0f}",
            help=f"{current_year}년 1월 1일부터 현재까지"
        )
    
    with col3:
        st.metric(
            "선택 기간 매출",
            f"₩{period_sales:,.0f}",
            help=f"{start_date} ~ {end_date}"
        )
    
    with col4:
        # 전월 대비 증감률 (추후 구현)
        st.metric(
            "전월 대비",
            "집계 중",
            delta=None,
            help="다음 업데이트에서 제공 예정"
        )

def render_additional_charts():
    """추가 분석 차트 (샘플 데이터)"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 월별 목표 달성률")
        target_data = pd.DataFrame({
            '월': ['1월', '2월', '3월', '4월'],
            '달성률': [95, 102, 88, 110]
        })
        
        chart = alt.Chart(target_data).mark_bar().encode(
            x=alt.X('월:N', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('달성률:Q', scale=alt.Scale(domain=[0, 120])),
            color=alt.condition(
                alt.datum.달성률 >= 100,
                alt.value('#4CAF50'),  # 초록색
                alt.value('#FF9800')   # 주황색
            ),
            tooltip=['월', '달성률']
        ).properties(height=300)
        
        st.altair_chart(chart, use_container_width=None)
    
    with col2:
        st.subheader("🌍 지역별 매출 비중")
        region_data = pd.DataFrame({
            '지역': ['서울', '경기', '부산', '대구', '기타'],
            '매출_비중': [45, 25, 12, 8, 10]
        })
        
        chart = alt.Chart(region_data).mark_arc(innerRadius=50).encode(
            theta=alt.Theta('매출_비중:Q'),
            color=alt.Color('지역:N', legend=alt.Legend(title="지역")),
            tooltip=['지역', alt.Tooltip('매출_비중:Q', title='비중(%)', format='.1f')]
        ).properties(height=300)
        
        st.altair_chart(chart, use_container_width=None)


# =============================================================================
# 메인 대시보드
# =============================================================================

def show_management_dashboard():
    """경영 대시보드 메인 함수"""
    
    st.header("📈 경영 대시보드")
    
    # 인증 확인
    access_token = st.session_state.get("access_token")
    session_id = st.session_state.get("session_id")
    
    if not access_token or not session_id:
        st.warning("⚠️ 로그인이 필요합니다.")
        st.info("좌측 사이드바에서 로그인해주세요.")
        return
    
    # 날짜 범위 선택
    start_date_input, end_date_input = render_date_range_selector()
    
    if not start_date_input or not end_date_input:
        return
    
    try:
        # 현재 날짜
        today = datetime.today().strftime("%Y-%m-%d")
        current_year = datetime.today().year
        
        # API 호출 (캐싱됨)
        with st.spinner("데이터를 불러오는 중..."):
            # 1. 총 매출 (2023-01-01 ~ 오늘)
            total_data = fetch_sales_summary(
                "2023-01-01",
                today,
                access_token,
                session_id
            )
            
            # 2. 연 매출 (올해)
            year_data = fetch_sales_summary(
                f"{current_year}-01-01",
                today,
                access_token,
                session_id
            )
            
            # 3. 선택 기간 매출
            period_data = fetch_sales_summary(
                start_date_input.strftime("%Y-%m-%d"),
                end_date_input.strftime("%Y-%m-%d"),
                access_token,
                session_id
            )
        
        # 데이터프레임 변환
        total_df = pd.DataFrame(total_data)
        year_df = pd.DataFrame(year_data)
        period_df = pd.DataFrame(period_data)
        
        # 매출 계산
        total_sales = calculate_total_sales(total_df, "total")
        year_sales = calculate_total_sales(year_df, "year")
        period_sales = calculate_total_sales(period_df, "month")
        
        # 메트릭 표시
        render_metrics(
            total_sales,
            year_sales,
            period_sales,
            current_year,
            start_date_input,
            end_date_input
        )
        
        st.divider()
        
        # 월별 매출 차트
        st.subheader("📊 매출 추이 (월별)")
        
        monthly_data = prepare_monthly_chart_data(period_df)
        
        if not monthly_data.empty:
            chart = create_monthly_sales_chart(monthly_data)
            if chart:
                st.altair_chart(chart, use_container_width=None)
                
                # 데이터 테이블 (토글)
                with st.expander("📋 상세 데이터 보기"):
                    display_df = monthly_data[['해당_월', '월_매출액']].copy()
                    display_df['해당_월'] = display_df['해당_월'].dt.strftime('%Y년 %m월')
                    st.dataframe(
                        display_df,
                        hide_index=True,
                        width="stretch"
                    )
        else:
            st.info("📭 선택한 기간에 월별 매출 데이터가 없습니다.")
        
        st.divider()
        
        # 추가 분석
        render_additional_charts()
        
        # 데이터 새로고침 버튼
        st.divider()
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("🔄 데이터 새로고침", width="stretch"):
                st.cache_data.clear()
                st.rerun()
        with col2:
            if st.button("📥 데이터 다운로드", width="stretch"):
                csv = monthly_data.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="CSV 다운로드",
                    data=csv,
                    file_name=f"매출데이터_{start_date_input}_{end_date_input}.csv",
                    mime="text/csv"
                )
        
    except requests.HTTPError as http_err:
        st.error(f"❌ API 호출 실패: {http_err}")
        logger.error(f"HTTP error: {http_err}")
        
        if st.button("재시도"):
            st.cache_data.clear()
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ 오류가 발생했습니다: {str(e)}")
        logger.exception(f"대시보드 처리 중 오류: {e}")
        
        # with st.expander("🔍 상세 오류 정보"):
        #     st.code(str(e))
        
        if st.button("재시도"):
            st.cache_data.clear()
            st.rerun()


# =============================================================================
# 실행
# =============================================================================

if __name__ == "__main__":
    show_management_dashboard()