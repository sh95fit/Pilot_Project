import streamlit as st

# 임시 (리펙토링 시 파일 분리 예정)
import pandas as pd
import requests
from datetime import datetime
import logging
from config.settings import settings
import altair as alt


# ------------------------------
# 설정
# ------------------------------
API_URL = f"{settings.BACKEND_URL}/api/v1/data/get_sales_summary"

# logger 설정
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ------------------------------
# 대시보드 함수
# ------------------------------
def show_management_dashboard():
    st.header("📈 경영 대시보드")

    # ------------------------------
    # 로그인 상태 확인
    # ------------------------------
    access_token = st.session_state.get("access_token")
    session_id = st.session_state.get("session_id")
    if not access_token or not session_id:
        st.warning("로그인이 필요합니다.")
        return  # 더 이상 진행하지 않음

    # 조회 기간 입력 (전체 폭 대비 1/4)
    col_start, col_end, col_dummy = st.columns([1, 1, 6]) 
    with col_start:
        start_date_input = st.date_input("시작일", value=datetime(2023, 1, 1), key="start_date")
    with col_end:
        end_date_input = st.date_input("종료일", value=datetime.today(), key="end_date")

    # ------------------------------
    # API 요청용 헤더
    # ------------------------------
    headers = {
        "cookie": f"access_token={access_token}; session_id={session_id}"
    }

    try:
        # ------------------------------
        # 1️⃣ 총 매출 (From 2023-01-01)
        # ------------------------------
        total_payload = {
            "procedure_name": "get_sales_summary",
            "params": ["2023-01-01", datetime.today().strftime("%Y-%m-%d")]
        }
        total_resp = requests.post(API_URL, json=total_payload, headers=headers)
        total_resp.raise_for_status()
        total_data = total_resp.json()["data"]
        total_df = pd.DataFrame(total_data)
        total_sales = total_df[total_df["period_type"] == "total"]["total_amount_sum"].sum()

        # ------------------------------
        # 2️⃣ 연 매출 (올해)
        # ------------------------------
        current_year = datetime.today().year
        year_payload = {
            "procedure_name": "get_sales_summary",
            "params": [f"{current_year}-01-01", datetime.today().strftime("%Y-%m-%d")]
        }
        year_resp = requests.post(API_URL, json=year_payload, headers=headers)
        year_resp.raise_for_status()
        year_data = year_resp.json()["data"]
        year_df = pd.DataFrame(year_data)
        year_sales = year_df[year_df["period_type"] == "year"]["total_amount_sum"].sum()

        # ------------------------------
        # 3️⃣ 선택 기간 데이터 (월별 매출만 합산)
        # ------------------------------
        period_payload = {
            "procedure_name": "get_sales_summary",
            "params": [start_date_input.strftime("%Y-%m-%d"), end_date_input.strftime("%Y-%m-%d")]
        }
        period_resp = requests.post(API_URL, json=period_payload, headers=headers)
        period_resp.raise_for_status()
        period_data = period_resp.json()["data"]
        period_df = pd.DataFrame(period_data)

        # month 데이터만 합산
        month_df_only = period_df[period_df["period_type"] == "month"]
        period_total_sales = month_df_only["total_amount_sum"].sum()

        # ------------------------------
        # 메트릭 표시
        # ------------------------------
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 매출 (from 2023)", f"{total_sales:,.0f} 원")
        with col2:
            st.metric(f"연 매출 ({current_year})", f"{year_sales:,.0f} 원")
        with col3:
            st.metric(f"선택 기간 총 매출 ({start_date_input} ~ {end_date_input})", f"{period_total_sales:,.0f} 원")
        with col4:
            st.metric("빈값", "0%", "0%")

        # ------------------------------
        # 월별 매출 차트 (Altair 사용)
        # ------------------------------
        st.subheader("📊 매출 추이(월별)")
        
        # 월별 데이터 필터
        month_df = period_df[period_df["period_type"] == "month"].copy()

        if not month_df.empty:
            # '해당 월' datetime
            month_df['해당 월'] = pd.to_datetime(month_df['period_label'])
            # '월 매출액' 문자열 포맷
            month_df['월 매출액'] = month_df['total_amount_sum'].apply(lambda x: f"{x:,.0f}원")

            # 라인 + 도트
            line_chart = alt.Chart(month_df).mark_line(point=True).encode(
                x=alt.X('해당 월', axis=alt.Axis(title='해당 월', format='%Y년 %m월', tickCount=len(month_df)//3, labelAngle=-45)),
                y=alt.Y('total_amount_sum', title='월 매출액'),
                tooltip=[
                    alt.Tooltip('해당 월:T', title='해당 월', format='%Y년 %m월'),
                    alt.Tooltip('월 매출액:N', title='월 매출액')
                ]
            )

            # 도트 위 텍스트
            text_chart = alt.Chart(month_df).mark_text(
                dy=-10,
                color='black',
                fontSize=11
            ).encode(
                x='해당 월',
                y='total_amount_sum',
                text='월 매출액'
            )

            st.altair_chart(line_chart + text_chart, use_container_width=True)
        else:
            st.info("월별 매출 데이터가 없습니다.")
            
        # ------------------------------
        # 추가 분석
        # ------------------------------
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

    except requests.HTTPError as http_err:
        logger.error(f"HTTP error: {http_err}")
        st.error(f"API 호출 실패: {http_err}")
    except Exception as e:
        logger.exception(f"대시보드 처리 중 오류 발생: {e}")
        st.error(f"오류가 발생했습니다: {e}")

# ------------------------------
# 초기 랜더링
# ------------------------------
show_management_dashboard()