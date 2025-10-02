import streamlit as st
import pandas as pd
import requests
import datetime
import altair as alt
from config.settings import settings

API_URL = f"{settings.BACKEND_URL}"

# -------------------------------------------
# API 호출 함수
# -------------------------------------------
def fetch_metric_dashboard(base_url: str, start_period: str, end_period: str):
    """기간별 Metric Dashboard 데이터를 가져오는 함수"""
    access_token = st.session_state.get("access_token")
    session_id = st.session_state.get("session_id")
    
    headers = {
        "cookie": f"access_token={access_token}; session_id={session_id}"
    }
    url = f"{base_url}/api/v1/google-sheets/metric-dashboard/period"
    payload = {
        "worksheet_name": "Metric_Dashboard",
        "start_period": start_period,
        "end_period": end_period
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return []
    


def fetch_active_accounts(base_url: str, start_date: str, end_date: str):
    """활성 계정 데이터를 가져오는 함수"""
    access_token = st.session_state.get("access_token")
    session_id = st.session_state.get("session_id")
    
    headers = {
        "cookie": f"access_token={access_token}; session_id={session_id}"
    }
    url = f"{base_url}/api/v1/data/get_active_accounts"
    payload = {
        "start_date": start_date,
        "end_date": end_date
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        st.error(f"활성 계정 데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return []


# -------------------------------------------
# 메인 페이지 함수
# -------------------------------------------
def show_operations_dashboard():
    """운영 대시보드"""
    st.header("⚙️ 운영 대시보드")

    today = datetime.date.today()
    current_year = today.year
    current_month = today.month
    year_options = list(range(current_year - 5, current_year + 1))
    month_options = list(range(1, 13))

    # ==========================================
    # 1. KPI 영역 (년월 필터)
    # ==========================================
    
    # 제목과 필터를 한 줄에 배치
    col_title, col_filter = st.columns([1.6, 10.4])
    
    with col_title:
        st.markdown("<h3 style='margin-top:0.5rem;'>📆 영업 지표</h3>", unsafe_allow_html=True)
    
    with col_filter:
        # 셀렉트박스 스타일 - 이 페이지에만 적용
        st.markdown("""
        <style>
        /* 운영 대시보드 필터 영역에만 적용 */
        div[data-testid="stHorizontalBlock"] div[data-baseweb="select"] > div {
            background-color: white;
            border-radius: 6px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
            border: 1px solid #e0e0e0;
            min-height: 38px;
            font-size: 0.88rem;
            padding: 0.5rem 0.6rem !important;
        }
        div[data-testid="stHorizontalBlock"] div[data-baseweb="select"] svg {
            width: 14px;
            height: 14px;
        }
        div[data-testid="stHorizontalBlock"] div[data-baseweb="select"] > div > div {
            padding-top: 0.15rem;
            padding-bottom: 0.15rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 우측 정렬 - 월 드롭다운 너비 증가
        filter_col1, filter_col2, filter_col3 = st.columns([7, 2.3, 2.3])
        
        with filter_col1:
            st.write("")  # 빈 공간
        
        with filter_col2:
            sub_col1, sub_col2 = st.columns([1.5, 1])
            with sub_col1:
                start_year = st.selectbox("시작 연도", year_options, index=len(year_options)-1, key="start_year")
            with sub_col2:
                start_month = st.selectbox("월", month_options, index=current_month - 1, key="start_month")
        
        with filter_col3:
            sub_col3, sub_col4 = st.columns([1.5, 1])
            with sub_col3:
                end_year = st.selectbox("종료 연도", year_options, index=len(year_options)-1, key="end_year")
            with sub_col4:
                end_month = st.selectbox("월", month_options, index=current_month - 1, key="end_month")

    # YYYY-MM 문자열 생성
    start_period = f"{start_year}-{start_month:02d}"
    end_period = f"{end_year}-{end_month:02d}"

    with st.spinner(""):
        kpi_data = fetch_metric_dashboard(API_URL, start_period, end_period)
        active_accounts_data = fetch_active_accounts(API_URL, "2023-01-01", today.strftime("%Y-%m-%d"))
        active_accounts = active_accounts_data[-1]["cumulative_active_accounts"] if active_accounts_data else 0

    if kpi_data:
        df_kpi = pd.DataFrame(kpi_data)

        # KPI 카드 스타일 - 간격 조정
        st.markdown("""
        <style>
        .kpi-card {
            background: white;
            padding: 1rem 1.3rem;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            margin-bottom: 0.8rem;
        }
        .kpi-card-title {
            font-size: 0.85rem;
            font-weight: 500;
            color: #666;
            margin-bottom: 0.7rem;
            text-align: left;
        }
        .kpi-card-value {
            font-size: 2.2rem;
            font-weight: 700;
            color: #333;
            margin: 0;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)

        # KPI 카드 - 간격 추가
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns([1, 1, 1, 1], gap="medium")
        
        with kpi_col1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-card-title">유입 리드 수</div>
                <div class="kpi-card-value">{df_kpi['lead_count'].sum():,}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi_col2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-card-title">체험 전환 수</div>
                <div class="kpi-card-value">{df_kpi['trial_conversion'].sum():,}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi_col3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-card-title">구독 전환 수</div>
                <div class="kpi-card-value">{df_kpi['subscription_conversion'].sum():,}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi_col4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-card-title">활성 계정 수</div>
                <div class="kpi-card-value">{active_accounts:,}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("KPI 데이터를 불러오지 못했습니다.")

    st.markdown("<div style='margin: 0.8rem 0;'></div>", unsafe_allow_html=True)

    # ==========================================
    # 2. 탭으로 차트 분리
    # ==========================================
    
    # 탭 생성
    tab1, tab2 = st.tabs(["📊 월별 현황", "👥 활성 계정 수 현황"])
    
    # ==========================================
    # 탭 1: 월별 현황 차트 (연도 필터)
    # ==========================================
    with tab1:
        # 세션 상태 초기화
        if "selected_year" not in st.session_state:
            st.session_state.selected_year = current_year
            
        # 제목과 연도 선택을 한 줄에
        col_title, col_year_nav = st.columns([4, 1])
        
        with col_title:
            st.markdown("<h3 style='margin-top:0.5rem;'>월별 영업 지표 추이</h3>", unsafe_allow_html=True)
        
        with col_year_nav:
            # 연도 네비게이션 - 컴팩트하게
            st.markdown("""
            <style>
            .stButton > button {
                padding: 0.3rem 0.6rem;
                min-height: 36px;
                font-size: 0.88rem;
            }
            </style>
            """, unsafe_allow_html=True)
            
            nav_cols = st.columns([1, 2, 1])
            with nav_cols[0]:
                if st.button("◀", key="prev_year_btn", width='stretch'):
                    if st.session_state.selected_year > year_options[0]:
                        st.session_state.selected_year -= 1
                        st.rerun()
            
            with nav_cols[1]:
                st.markdown(
                    f"<div style='text-align:center; padding-top:6px; font-size:14px; font-weight:bold;'>{st.session_state.selected_year}년</div>",
                    unsafe_allow_html=True
                )
            
            with nav_cols[2]:
                if st.button("▶", key="next_year_btn", width='stretch', 
                            disabled=(st.session_state.selected_year >= current_year)):
                    if st.session_state.selected_year < current_year:
                        st.session_state.selected_year += 1
                        st.rerun()

        selected_year = st.session_state.selected_year

        # 선택한 연도 데이터 조회
        start_year_period = f"{selected_year}-01"
        end_year_period = f"{selected_year}-12"

        with st.spinner(""):
            chart_data = fetch_metric_dashboard(API_URL, start_year_period, end_year_period)

        if chart_data:
            df_chart = pd.DataFrame(chart_data).sort_values(by="period")
            
            # 유효한 데이터만 필터링 - period 길이 체크 추가
            df_chart = df_chart[df_chart["period"].notna()]
            df_chart = df_chart[df_chart["period"].astype(str).str.len() == 7]  # YYYY-MM 형식만
            df_chart = df_chart.reset_index(drop=True)
            
            df_chart["month"] = df_chart["period"].str[-2:].astype(int)

            # 컬럼명 한글 매핑 - 순서 지정
            column_map = {
                "lead_count": "유입 리드 수",
                "trial_conversion": "체험 전환 수",
                "subscription_conversion": "구독 전환 수"
            }

            # 막대 그래프용 데이터 변환
            melted_df = df_chart.melt(
                id_vars=["period", "month"],
                value_vars=list(column_map.keys()),
                var_name="지표",
                value_name="값"
            )

            # 한글 지표명으로 매핑
            melted_df["지표"] = melted_df["지표"].map(column_map)
            
            # 지표 순서 고정 (카테고리 순서 지정)
            melted_df["지표"] = pd.Categorical(
                melted_df["지표"],
                categories=["유입 리드 수", "체험 전환 수", "구독 전환 수"],
                ordered=True
            )

            # 나란히 막대 그래프 - 순서 적용
            bars = (
                alt.Chart(melted_df)
                .mark_bar()
                .encode(
                    x=alt.X("month:O", title="월", axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("값:Q", title="수"),
                    color=alt.Color("지표:N", title="지표", sort=["유입 리드 수", "체험 전환 수", "구독 전환 수"]),
                    xOffset=alt.XOffset("지표:N", sort=["유입 리드 수", "체험 전환 수", "구독 전환 수"]),
                    tooltip=["period", "지표", "값"]
                )
            )
            
            # 막대 위에 값 표시 - xOffset 명시적으로 동일하게 설정
            text = (
                alt.Chart(melted_df)
                .mark_text(
                    align='center',
                    baseline='bottom',
                    dy=-5,
                    fontSize=12,
                    fontWeight='bold'
                )
                .encode(
                    x=alt.X("month:O"),
                    y=alt.Y("값:Q"),
                    text=alt.Text("값:Q"),
                    xOffset=alt.XOffset("지표:N", sort=["유입 리드 수", "체험 전환 수", "구독 전환 수"])
                )
            )
            
            chart = (bars + text).properties(
                height=280,
                title=f"{selected_year}년 월별 유입 리드 / 체험 전환 / 구독 전환 추이"
            )

            st.altair_chart(chart, use_container_width=True)

            # 데이터 테이블 (토글)
            with st.expander("📋 상세 데이터 보기", expanded=False):
                # 이미 필터링된 df_chart 사용
                display_df = df_chart[["period", "lead_count", "trial_conversion", "subscription_conversion"]].copy()
                
                # 컬럼명 변경
                display_df.columns = ["기간", "유입 리드 수", "체험 전환 수", "구독 전환 수"]
                
                # 기간 포맷 변경
                display_df["기간"] = pd.to_datetime(display_df["기간"]).dt.strftime('%Y-%m')
                
                st.dataframe(
                    display_df,
                    hide_index=True,
                    width='stretch',
                    height=180
                )
        else:
            st.info(f"{selected_year}년 데이터가 없습니다.")
    
    # ==========================================
    # 탭 2: 활성 계정 수 현황
    # ==========================================
    with tab2:
        st.markdown("<h3 style='margin-top:0.5rem;'>누적 활성 계정 수 추이</h3>", unsafe_allow_html=True)
        
        if active_accounts_data:
            df_active = pd.DataFrame(active_accounts_data)
            
            # 날짜 형식 변환
            df_active["created_date"] = pd.to_datetime(df_active["created_date"])
            df_active = df_active.sort_values(by="created_date")
            
            # 라인 차트 생성
            line_chart = (
                alt.Chart(df_active)
                .mark_line(point=True, strokeWidth=2)
                .encode(
                    x=alt.X("created_date:T", title="날짜", axis=alt.Axis(format="%Y-%m-%d")),
                    y=alt.Y("cumulative_active_accounts:Q", title="누적 활성 계정 수"),
                    tooltip=[
                        alt.Tooltip("created_date:T", title="날짜", format="%Y-%m-%d"),
                        alt.Tooltip("daily_active_accounts:Q", title="일일 활성 계정 수"),
                        alt.Tooltip("cumulative_active_accounts:Q", title="누적 활성 계정 수")
                    ]
                )
                .properties(
                    height=300,
                    title="누적 활성 계정 수 추이"
                )
            )
            
            st.altair_chart(line_chart, use_container_width=True)
            
            # 데이터 테이블
            with st.expander("📋 상세 데이터 보기", expanded=False):
                display_df_active = df_active[["created_date", "daily_active_accounts", "cumulative_active_accounts"]].copy()
                display_df_active.columns = ["날짜", "일일 활성 계정 수", "누적 활성 계정 수"]
                display_df_active["날짜"] = display_df_active["날짜"].dt.strftime('%Y-%m-%d')
                
                st.dataframe(
                    display_df_active,
                    hide_index=True,
                    width='stretch',
                    height=300
                )
        else:
            st.info("활성 계정 데이터가 없습니다.")