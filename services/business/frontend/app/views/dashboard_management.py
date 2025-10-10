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

def calculate_total_sales(df: pd.DataFrame, period_type: str = "total", fee_ratio: float = 0.9) -> float:
    """
    특정 기간 타입의 총 매출 계산
    
    Args:
        df: 매출 데이터프레임
        period_type: 기간 타입 (total, year, month)
    
    Returns:
        float: 총 매출액 * 0.9 (VAT 제외)
    """
    filtered = df[df["period_type"] == period_type]
    total = filtered["total_amount_sum"].sum() if not filtered.empty else 0.0
    return total * fee_ratio


def prepare_monthly_chart_data(df: pd.DataFrame, fee_ratio: float = 0.9) -> pd.DataFrame:
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
    
    # 수수료 적용
    month_df['total_amount_sum'] = month_df['total_amount_sum'] * fee_ratio
    
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
    
    # 3개당 1개만 텍스트 표시하기 위한 인덱스 추가
    df_copy = df.copy()
    df_copy['row_index'] = range(len(df_copy))
    df_copy['show_text'] = df_copy['row_index'] % 3 == 0
    
    # 라인 + 포인트
    line = alt.Chart(df_copy).mark_line(
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
    
    # 포인트 위 텍스트 (3개당 1개만 표시)
    text = alt.Chart(df_copy).transform_filter(
        alt.datum.show_text == True
    ).mark_text(
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

def render_metrics(
    total_sales: float,
    year_sales: float,
    current_month_sales: float,
    period_sales: float,
    current_year: int,
    current_month: int,
    start_date: date,
    end_date: date
):
    """
    메트릭 카드 렌더링
    
    Args:
        total_sales: 총 매출
        year_sales: 연 매출
        current_month_sales: 현재 월 매출
        period_sales: 선택 기간 매출
        current_year: 현재 연도
        current_month: 현재 월
        start_date: 시작일
        end_date: 종료일
    """
    # 카드 스타일
    st.markdown("""
    <style>
    .metric-card {
        background: white;
        padding: 1rem 1.3rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 0.8rem;
    }
    .metric-card-title {
        font-size: 0.85rem;
        font-weight: 500;
        color: #666;
        margin-bottom: 0.7rem;
        text-align: left;
    }
    .metric-card-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #333;
        margin: 0;
        text-align: center;
    }
    .metric-card-subtitle {
        font-size: 0.75rem;
        color: #999;
        margin-top: 0.4rem;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1], gap="medium")
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-title">총 매출 (VAT 제외)</div>
            <div class="metric-card-value">{total_sales:,.0f} 원</div>
            <div class="metric-card-subtitle">2023년 1월 1일부터</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-title">연 매출 ({current_year}) (VAT 제외)</div>
            <div class="metric-card-value">{year_sales:,.0f} 원</div>
            <div class="metric-card-subtitle">{current_year}년 1월 1일부터</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-title">현재 월 매출 ({current_month}월) (VAT 제외)</div>
            <div class="metric-card-value">{current_month_sales:,.0f} 원</div>
            <div class="metric-card-subtitle">{current_year}년 {current_month}월 1일부터</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-title">선택 기간 매출 (VAT 제외)</div>
            <div class="metric-card-value">{period_sales:,.0f} 원</div>
            <div class="metric-card-subtitle">{start_date} ~ {end_date}</div>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# 메인 대시보드
# =============================================================================

def show_management_dashboard():
    """경영 대시보드 메인 함수"""
    
    # 인증 확인
    access_token = st.session_state.get("access_token")
    session_id = st.session_state.get("session_id")
    
    if not access_token or not session_id:
        st.warning("로그인이 필요합니다.")
        st.info("좌측 사이드바에서 로그인해주세요.")
        return
    
    # 날짜 선택 박스 스타일
    st.markdown("""
    <style>
    /* 날짜 선택 위젯 스타일 */
    div[data-testid="stDateInput"] > div > div {
        background-color: white;
        border-radius: 6px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
        border: 1px solid #e0e0e0;
    }
    div[data-testid="stDateInput"] label {
        font-size: 0.75rem;
        font-weight: 500;
        color: #666;
    }
    /* 날짜 입력 필드 크기 축소 */
    div[data-testid="stDateInput"] input {
        font-size: 0.85rem;
        padding: 0.4rem 0.6rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 헤더와 날짜 선택을 같은 줄에 배치
    col_title, col_space, col_start, col_end = st.columns([3, 2.5, 1.2, 1.2])
    
    with col_title:
        st.header("📈 경영 대시보드")
    
    with col_start:
        start_date_input = st.date_input(
            "시작일",
            value=datetime(2023, 1, 1),
            key="start_date"
        )
    
    with col_end:
        end_date_input = st.date_input(
            "종료일",
            value=datetime.today(),
            key="end_date"
        )
    
    # 날짜 검증
    if start_date_input > end_date_input:
        st.error("시작일은 종료일보다 이전이어야 합니다.")
        return
    
    st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
    
    try:
        # 현재 날짜
        today = datetime.today().strftime("%Y-%m-%d")
        current_year = datetime.today().year
        
        # 현재 월 시작일
        current_month_start = datetime.today().replace(day=1).strftime("%Y-%m-%d")
        current_month = datetime.today().month
        
        # API 호출 (캐싱됨)
        with st.spinner(""):
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
            
            # 3. 현재 월 매출
            month_data = fetch_sales_summary(
                current_month_start,
                today,
                access_token,
                session_id
            )
            
            # 4. 선택 기간 매출
            period_data = fetch_sales_summary(
                start_date_input.strftime("%Y-%m-%d"),
                end_date_input.strftime("%Y-%m-%d"),
                access_token,
                session_id
            )
        
        # 데이터프레임 변환
        total_df = pd.DataFrame(total_data)
        year_df = pd.DataFrame(year_data)
        month_df = pd.DataFrame(month_data)
        period_df = pd.DataFrame(period_data)
        
        # 매출 계산
        total_sales = calculate_total_sales(total_df, "total")
        year_sales = calculate_total_sales(year_df, "year")
        current_month_sales = calculate_total_sales(month_df, "month")
        period_sales = calculate_total_sales(period_df, "month")
        
        # 메트릭 표시
        render_metrics(
            total_sales,
            year_sales,
            current_month_sales,
            period_sales,
            current_year,
            current_month,
            start_date_input,
            end_date_input
        )
        
        st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)
        
        # 월별 매출 차트
        st.subheader("📊 매출 추이 (월별) (VAT 제외)")
        
        monthly_data = prepare_monthly_chart_data(period_df)
        
        if not monthly_data.empty:
            chart = create_monthly_sales_chart(monthly_data)
            if chart:
                st.altair_chart(chart, use_container_width=True)
                
            with st.expander("📋 월별 매출 요약 보기", expanded=False):
                display_df = monthly_data[['해당_월', '월_매출액']].copy()
                display_df['해당_월'] = display_df['해당_월'].dt.strftime('%Y-%m')  # YYYY-MM 포맷
                
                st.dataframe(
                    display_df,
                    hide_index=True,
                    use_container_width=True,
                    height=400
                )                
        else:
            st.info("선택한 기간에 월별 매출 데이터가 없습니다.")
        
        # # 데이터 새로고침 버튼
        # col1, col2, col3 = st.columns([1, 1, 6])
        # with col1:
        #     if st.button("🔄 데이터 새로고침", use_container_width=True):
        #         st.cache_data.clear()
        #         st.rerun()
        # with col2:
        #     if st.button("📥 데이터 다운로드", use_container_width=True):
        #         csv = monthly_data.to_csv(index=False).encode('utf-8-sig')
        #         st.download_button(
        #             label="CSV 다운로드",
        #             data=csv,
        #             file_name=f"매출데이터_{start_date_input}_{end_date_input}.csv",
        #             mime="text/csv",
        #             use_container_width=True
        #         )
        
    except requests.HTTPError as http_err:
        st.error(f"API 호출 실패: {http_err}")
        logger.error(f"HTTP error: {http_err}")
        
        if st.button("재시도"):
            st.cache_data.clear()
            st.rerun()
            
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
        logger.exception(f"대시보드 처리 중 오류: {e}")
        
        if st.button("재시도"):
            st.cache_data.clear()
            st.rerun()


# =============================================================================
# 실행
# =============================================================================

if __name__ == "__main__":
    show_management_dashboard()