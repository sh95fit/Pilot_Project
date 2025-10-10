
import streamlit as st
import pandas as pd
import requests
import datetime
import altair as alt
from config.settings import settings
from dateutil.relativedelta import relativedelta

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

def fetch_product_sold(base_url: str, start_date: str, end_date: str, is_grouped: int):
    """상품 판매 데이터를 가져오는 함수"""
    access_token = st.session_state.get("access_token")
    session_id = st.session_state.get("session_id")
    headers = {
        "cookie": f"access_token={access_token}; session_id={session_id}"
    }
    url = f"{base_url}/api/v1/data/get_number_of_product_sold"
    payload = {
        "start_date": start_date,
        "end_date": end_date,
        "is_grouped": is_grouped
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        st.error(f"품목별 판매 데이터를 불러오는 중 오류가 발생했습니다: {e}")
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
    col_title, col_filter = st.columns([1.8, 10.2])
    
    with col_title:
        st.markdown("<h3 style='margin-top:0.5rem;'>📆 영업 지표</h3>", unsafe_allow_html=True)
    
    # with col_filter:
    #     st.markdown("""
    #     <style>
    #     div[data-testid="stHorizontalBlock"] div[data-baseweb="select"] > div {
    #         background-color: white;
    #         border-radius: 6px;
    #         box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
    #         border: 1px solid #e0e0e0;
    #         min-height: 38px;
    #         font-size: 0.88rem;
    #         padding: 0.5rem 0.6rem !important;
    #     }
    #     div[data-testid="stHorizontalBlock"] div[data-baseweb="select"] svg {
    #         width: 14px;
    #         height: 14px;
    #     }
    #     div[data-testid="stHorizontalBlock"] div[data-baseweb="select"] > div > div {
    #         padding-top: 0.15rem;
    #         padding-bottom: 0.15rem;
    #     }
    #     </style>
    #     """, unsafe_allow_html=True)
        
    #     filter_col1, filter_col2, filter_col3 = st.columns([7, 2.3, 2.3])
        
    #     with filter_col1:
    #         st.write("")
        
    #     with filter_col2:
    #         sub_col1, sub_col2 = st.columns([1.3, 1.1])
    #         with sub_col1:
    #             start_year = st.selectbox("시작 연도", year_options, index=len(year_options)-1, key="start_year")
    #         with sub_col2:
    #             start_month = st.selectbox("월", month_options, index=current_month - 1, key="start_month")
        
    #     with filter_col3:
    #         sub_col3, sub_col4 = st.columns([1.3, 1.1])
    #         with sub_col3:
    #             end_year = st.selectbox("종료 연도", year_options, index=len(year_options)-1, key="end_year")
    #         with sub_col4:
    #             end_month = st.selectbox("월", month_options, index=current_month - 1, key="end_month")
    
    with col_filter:
        st.markdown("""
        <style>
        div[data-testid="stDateInput"] > label {
            font-size: 0.88rem;
            font-weight: 500;
        }
        div[data-testid="stDateInput"] > div > div > input {
            background-color: white !important;
            border-radius: 6px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
            border: 1px solid #e0e0e0 !important;
            min-height: 38px;
            font-size: 0.88rem;
            padding: 0.5rem 0.6rem !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # ✅ 년월일 선택 UI
        filter_col1, filter_col2, filter_col3 = st.columns([7, 2.3, 2.3])
        
        with filter_col1:
            st.write("")
        
        with filter_col2:
            start_date = st.date_input(
                "시작일",
                value=today.replace(day=1),
                key="metric_start_date"
            )
        
        with filter_col3:
            end_date = st.date_input(
                "종료일",
                value=today,
                key="metric_end_date"
            )    
    
    start_period = start_date.strftime("%Y-%m")   # fetch_metric_dashboard용 (년-월)
    end_period = end_date.strftime("%Y-%m")       # fetch_metric_dashboard용 (년-월)
    start_date_str = start_date.strftime("%Y-%m-%d")  # fetch_product_sold용 (년-월-일)
    end_date_str = end_date.strftime("%Y-%m-%d")      # fetch_product_sold용 (년-월-일)
    
    with st.spinner(""):
        kpi_data = fetch_metric_dashboard(API_URL, start_period, end_period)
        active_accounts_data = fetch_active_accounts(API_URL, "2022-12-27", today.strftime("%Y-%m-%d"))
        active_accounts = active_accounts_data[-1]["cumulative_active_accounts"] if active_accounts_data else 0
        product_sales = fetch_product_sold(API_URL, start_date_str, end_date_str, is_grouped=1)
    
    if kpi_data:
        df_kpi = pd.DataFrame(kpi_data)
        
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
        
        kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5, kpi_col6 = st.columns([1, 1, 1, 1,1,1], gap="medium")
        
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
        
    # 판매 데이터가 존재할 때
    if product_sales:
        df_sales = pd.DataFrame(product_sales)
        
        # 가정식 도시락 금액 합산
        home_meal_amount = df_sales[df_sales['product_name'] == "가정식 도시락"]['total_quantity'].sum()

        # 프레시밀 금액 합산
        freshmeal_amount = df_sales[df_sales['product_name'] == "프레시밀"]['total_quantity'].sum()
        
        with kpi_col5:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-card-title">가정식 판매 현황</div>
                <div class="kpi-card-value">{home_meal_amount:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi_col6:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-card-title">프레시밀 판매 현황</div>
                <div class="kpi-card-value">{freshmeal_amount:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("상품 판매 데이터를 불러오지 못했습니다.")
    
    st.markdown("<div style='margin: 0.8rem 0;'></div>", unsafe_allow_html=True)
    
    # ==========================================
    # 2. 탭으로 차트 분리
    # ==========================================
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 월별 현황", 
        "👥 활성 계정 수 현황",
        "🍱 가정식 도시락 판매 현황",
        "🥗 프레시밀 판매 현황",
        "📦 전체 품목별 판매 현황"
    ])
    
    # ==========================================
    # 탭 1: 월별 현황
    # ==========================================
    with tab1:
        if "selected_year" not in st.session_state:
            st.session_state.selected_year = current_year
        
        col_title, col_year_nav = st.columns([4, 1])
        
        with col_title:
            st.markdown("<h3 style='margin-top:0.5rem;'>월별 영업 지표 추이</h3>", unsafe_allow_html=True)
        
        with col_year_nav:
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
                if st.button("▶", key="next_year_btn", width='stretch', disabled=(st.session_state.selected_year >= current_year)):
                    if st.session_state.selected_year < current_year:
                        st.session_state.selected_year += 1
                        st.rerun()
        
        selected_year = st.session_state.selected_year
        start_year_period = f"{selected_year}-01"
        end_year_period = f"{selected_year}-12"
        
        with st.spinner(""):
            chart_data = fetch_metric_dashboard(API_URL, start_year_period, end_year_period)
        
        if chart_data:
            df_chart = pd.DataFrame(chart_data).sort_values(by="period")
            df_chart = df_chart[df_chart["period"].notna()]
            df_chart = df_chart[df_chart["period"].astype(str).str.len() == 7]
            df_chart = df_chart.reset_index(drop=True)
            df_chart["month"] = df_chart["period"].str[-2:].astype(int)
            
            column_map = {
                "lead_count": "유입 리드 수",
                "trial_conversion": "체험 전환 수",
                "subscription_conversion": "구독 전환 수"
            }
            
            melted_df = df_chart.melt(
                id_vars=["period", "month"],
                value_vars=list(column_map.keys()),
                var_name="지표",
                value_name="값"
            )
            
            melted_df["지표"] = melted_df["지표"].map(column_map)
            melted_df["지표"] = pd.Categorical(
                melted_df["지표"],
                categories=["유입 리드 수", "체험 전환 수", "구독 전환 수"],
                ordered=True
            )
            
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
                height=350,
                # title=f"{selected_year}년 월별 유입 리드 / 체험 전환 / 구독 전환 추이"
            )
            
            st.altair_chart(chart, use_container_width=True)
            
            with st.expander("📋 상세 데이터 보기", expanded=False):
                display_df = df_chart[["period", "lead_count", "trial_conversion", "subscription_conversion"]].copy()
                display_df.columns = ["기간", "유입 리드 수", "체험 전환 수", "구독 전환 수"]
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
            df_active["created_date"] = pd.to_datetime(df_active["created_date"])
            df_active = df_active.sort_values(by="created_date")
            
            # 최대값 판별
            max_cumulative = df_active["cumulative_active_accounts"].max()
            df_active["is_max"] = df_active["cumulative_active_accounts"] == max_cumulative
            
            # 라인 차트
            line = (
                alt.Chart(df_active)
                .mark_line(strokeWidth=2)
                .encode(
                    x=alt.X("created_date:T", title="날짜", axis=alt.Axis(format="%Y-%m-%d")),
                    y=alt.Y("cumulative_active_accounts:Q", title="누적 활성 계정 수"),
                    tooltip=[
                        alt.Tooltip("created_date:T", title="날짜", format="%Y-%m-%d"),
                        alt.Tooltip("daily_active_accounts:Q", title="일일 활성 계정 수"),
                        alt.Tooltip("cumulative_active_accounts:Q", title="누적 활성 계정 수")
                    ]
                )
            )
            
            # 일반 포인트
            points = (
                alt.Chart(df_active)
                .mark_point(size=50, filled=True)
                .encode(
                    x=alt.X("created_date:T"),
                    y=alt.Y("cumulative_active_accounts:Q"),
                    color=alt.value("#4C78A8"),
                    tooltip=[
                        alt.Tooltip("created_date:T", title="날짜", format="%Y-%m-%d"),
                        alt.Tooltip("daily_active_accounts:Q", title="일일 활성 계정 수"),
                        alt.Tooltip("cumulative_active_accounts:Q", title="누적 활성 계정 수")
                    ]
                )
            )
            
            # 최대값 포인트 (빨간색 강조)
            max_point = df_active[df_active["is_max"]]
            max_mark = (
                alt.Chart(max_point)
                .mark_point(size=150, filled=True)
                .encode(
                    x=alt.X("created_date:T"),
                    y=alt.Y("cumulative_active_accounts:Q"),
                    color=alt.value("#FF6B6B"),
                    tooltip=[
                        alt.Tooltip("created_date:T", title="날짜", format="%Y-%m-%d"),
                        alt.Tooltip("daily_active_accounts:Q", title="일일 활성 계정 수"),
                        alt.Tooltip("cumulative_active_accounts:Q", title="누적 활성 계정 수")
                    ]
                )
            )
            
            # 최대값에만 텍스트 표시
            text = (
                alt.Chart(max_point)
                .mark_text(
                    align='center',
                    baseline='bottom',
                    dy=-10,
                    fontSize=12,
                    fontWeight='bold',
                    color='#FF6B6B'
                )
                .encode(
                    x=alt.X("created_date:T"),
                    y=alt.Y("cumulative_active_accounts:Q"),
                    text=alt.Text("cumulative_active_accounts:Q", format=",")
                )
            )
            
            line_chart = (line + points + max_mark + text).properties(
                height=350
            )
            
            st.altair_chart(line_chart, use_container_width=True)
            
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
    
    # ==========================================
    # 탭 3: 가정식 도시락 판매 현황
    # ==========================================
    with tab3:
        col_title, col_filter = st.columns([5.5, 6.5])
        
        with col_title:
            st.markdown("<h3 style='margin-top:0.5rem;'>🍱 가정식 도시락 판매 현황</h3>", unsafe_allow_html=True)
        
        # with col_filter:
        #     st.markdown("""
        #     <style>
        #     div[data-testid="stDateInput"] > label {
        #         font-size: 0.88rem;
        #         font-weight: 500;
        #     }
        #     div[data-testid="stDateInput"] > div > div > input {
        #         background-color: white !important;
        #         border-radius: 6px;
        #         box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
        #         border: 1px solid #e0e0e0 !important;
        #         min-height: 38px;
        #         font-size: 0.88rem;
        #         padding: 0.5rem 0.6rem !important;
        #     }
        #     </style>
        #     """, unsafe_allow_html=True)
            
        #     filter_inner_col1, filter_inner_col2, filter_inner_col3 = st.columns([5.7, 2.3, 2.3])
            
        #     with filter_inner_col1:
        #         st.write("")
            
        #     with filter_inner_col2:
        #         home_start_date = st.date_input(
        #             "시작일",
        #             value=today.replace(day=1) - relativedelta(months=2),
        #             key="home_start_date"
        #         )
            
        #     with filter_inner_col3:
        #         home_end_date = st.date_input(
        #             "종료일",
        #             value=today,
        #             key="home_end_date"
        #         )
        
        with st.spinner(""):
            home_data = fetch_product_sold(
                API_URL,
                # home_start_date.strftime("%Y-%m-%d"),
                # home_end_date.strftime("%Y-%m-%d"),
                start_date_str,
                end_date_str,
                1
            )
        
        if home_data:
            df_home = pd.DataFrame(home_data)
            df_home = df_home[df_home["product_name"] == "가정식 도시락"].copy()
            
            if not df_home.empty:
                df_home_agg = df_home.groupby("delivery_date").agg({
                    "total_quantity": "sum",
                    "total_amount": "sum"
                }).reset_index()
                
                df_home_agg["delivery_date"] = pd.to_datetime(df_home_agg["delivery_date"])
                df_home_agg = df_home_agg.sort_values(by="delivery_date")
                
                full_dates = pd.date_range(start=start_date, end=end_date, freq='D')
                df_home_agg = (
                    pd.DataFrame({'delivery_date': full_dates})
                    .merge(df_home_agg, on='delivery_date', how='left')
                    .fillna({'total_quantity': 0, 'total_amount': 0})
                )

                df_home_agg["date_str"] = df_home_agg["delivery_date"].dt.strftime('%Y-%m-%d')                
                
                # 요일 추가
                weekday_map = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금', 5: '토', 6: '일'}
                df_home_agg["weekday"] = df_home_agg["delivery_date"].dt.weekday.map(weekday_map)
                df_home_agg["date_str"] = df_home_agg["delivery_date"].dt.strftime('%Y-%m-%d') + ' (' + df_home_agg["weekday"] + ')'
                
                # 최대값 판별
                max_quantity = df_home_agg["total_quantity"].max()
                df_home_agg["is_max"] = df_home_agg["total_quantity"] == max_quantity

                # ✅ 100일 기준 계산
                max_days = 100
                # period_days = (home_end_date - home_start_date).days
                period_days = (end_date - start_date).days

                # 막대 차트
                bars = (
                    alt.Chart(df_home_agg)
                    .mark_bar()
                    .encode(
                        x=alt.X("date_str:N", title="배송일", axis=alt.Axis(labelAngle=-45)),
                        y=alt.Y("total_quantity:Q", title="판매 식수"),
                        color=alt.condition(
                            alt.datum.is_max,
                            alt.value("#4ECDC4"),  # 최대값 색상 (연한 청록)
                            alt.value("#FF6B6B")   # 일반 색상 (연한 빨강)
                        ),
                        tooltip=[
                            alt.Tooltip("date_str:N", title="배송일"),
                            alt.Tooltip("total_quantity:Q", title="판매 식수", format=","),
                            alt.Tooltip("total_amount:Q", title="판매 금액", format=",")
                        ]
                    )
                )

                # ✅ 6개월 이하일 때만 수치 표시
                if period_days <= max_days:
                    text = (
                        alt.Chart(df_home_agg)
                        .mark_text(
                            align='center',
                            baseline='bottom',
                            dy=-5,
                            fontSize=11,
                            fontWeight='bold'
                        )
                        .encode(
                            x=alt.X("date_str:N"),
                            y=alt.Y("total_quantity:Q"),
                            text=alt.Text("total_quantity:Q", format=",")
                        )
                    )
                    bar_chart = (bars + text)
                else:
                    bar_chart = bars

                # 차트 속성
                bar_chart = bar_chart.properties(
                    height=350,
                ).configure_view(
                    strokeWidth=0
                ).configure_axis(
                    labelLimit=200
                ).configure(
                    padding={"top": 20, "bottom": 80, "left": 10, "right": 10}
                )

                st.altair_chart(bar_chart, use_container_width=True) 

                # line_chart = (
                #     alt.Chart(df_home_agg)
                #     .mark_line(point=True, strokeWidth=2, color="#FF6B6B")
                #     .encode(
                #         x=alt.X("delivery_date:T", title="배송일", axis=alt.Axis(format="%Y-%m-%d")),
                #         y=alt.Y("total_quantity:Q", title="판매 식수"),
                #         tooltip=[
                #             alt.Tooltip("delivery_date:T", title="배송일", format="%Y-%m-%d"),
                #             alt.Tooltip("total_quantity:Q", title="판매 식수", format=","),
                #             alt.Tooltip("total_amount:Q", title="판매 금액", format=",")
                #         ]
                #     )
                #     .properties(
                #         height=300,
                #         title="가정식 도시락 일별 판매 식수"
                #     )
                # )
                
                # st.altair_chart(line_chart, use_container_width=True)
                
                with st.expander("📋 상세 데이터 보기", expanded=False):
                    display_df = df_home_agg[["delivery_date", "total_quantity", "total_amount"]].copy()
                    display_df.columns = ["배송일", "판매 식수", "판매 금액"]
                    display_df["배송일"] = display_df["배송일"].dt.strftime('%Y-%m-%d')
                    display_df["판매 금액"] = display_df["판매 금액"].apply(lambda x: f"{x:,}원")
                    
                    st.dataframe(
                        display_df,
                        hide_index=True,
                        width='stretch',
                        height=300
                    )
            else:
                st.info("선택한 기간에 가정식 도시락 판매 데이터가 없습니다.")
        else:
            st.info("가정식 도시락 판매 데이터를 불러오지 못했습니다.")
    
    # ==========================================
    # 탭 4: 프레시밀 판매 현황
    # ==========================================
    with tab4:
        col_title, col_filter = st.columns([5.5, 6.5])
        
        with col_title:
            st.markdown("<h3 style='margin-top:0.5rem;'>🥗 프레시밀 판매 현황</h3>", unsafe_allow_html=True)
        
        # with col_filter:
        #     st.markdown("""
        #     <style>
        #     div[data-testid="stDateInput"] > label {
        #         font-size: 0.88rem;
        #         font-weight: 500;
        #     }
        #     div[data-testid="stDateInput"] > div > div > input {
        #         background-color: white !important;
        #         border-radius: 6px;
        #         box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
        #         border: 1px solid #e0e0e0 !important;
        #         min-height: 38px;
        #         font-size: 0.88rem;
        #         padding: 0.5rem 0.6rem !important;
        #     }
        #     </style>
        #     """, unsafe_allow_html=True)
            
        #     filter_inner_col1, filter_inner_col2, filter_inner_col3 = st.columns([5.7, 2.3, 2.3])
            
        #     with filter_inner_col1:
        #         st.write("")
            
        #     with filter_inner_col2:
        #         fresh_start_date = st.date_input(
        #             "시작일",
        #             value=today.replace(day=1) - relativedelta(months=2),
        #             key="fresh_start_date"
        #         )
            
        #     with filter_inner_col3:
        #         fresh_end_date = st.date_input(
        #             "종료일",
        #             value=today,
        #             key="fresh_end_date"
        #         )
        
        with st.spinner(""):
            fresh_data = fetch_product_sold(
                API_URL,
                # fresh_start_date.strftime("%Y-%m-%d"),
                # fresh_end_date.strftime("%Y-%m-%d"),
                start_date_str,
                end_date_str,
                1
            )
        
        if fresh_data:
            df_fresh = pd.DataFrame(fresh_data)
            df_fresh = df_fresh[df_fresh["product_name"] == "프레시밀"].copy()
            
            if not df_fresh.empty:
                df_fresh_agg = df_fresh.groupby("delivery_date").agg({
                    "total_quantity": "sum",
                    "total_amount": "sum"
                }).reset_index()
                
                df_fresh_agg["delivery_date"] = pd.to_datetime(df_fresh_agg["delivery_date"])
                df_fresh_agg = df_fresh_agg.sort_values(by="delivery_date")
                
                full_dates = pd.date_range(start=start_date, end=end_date, freq='D')
                df_fresh_agg = (
                    pd.DataFrame({'delivery_date': full_dates})
                    .merge(df_fresh_agg, on='delivery_date', how='left')
                    .fillna({'total_quantity': 0, 'total_amount': 0})
                )

                df_fresh_agg["date_str"] = df_fresh_agg["delivery_date"].dt.strftime('%Y-%m-%d')                
                
                # 요일 추가 (월~일)
                weekday_map = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금', 5: '토', 6: '일'}
                df_fresh_agg["weekday"] = df_fresh_agg["delivery_date"].dt.weekday.map(weekday_map)
                df_fresh_agg["date_str"] = df_fresh_agg["delivery_date"].dt.strftime('%Y-%m-%d') + ' (' + df_fresh_agg["weekday"] + ')'
                
                # 최대값 판별
                max_quantity = df_fresh_agg["total_quantity"].max()
                df_fresh_agg["is_max"] = df_fresh_agg["total_quantity"] == max_quantity

                # ✅ 100일 기준 계산
                max_days = 100
                period_days = (end_date - start_date).days

                # 막대 차트
                bars = (
                    alt.Chart(df_fresh_agg)
                    .mark_bar()
                    .encode(
                        x=alt.X("date_str:N", title="배송일", axis=alt.Axis(labelAngle=-45), sort=None),
                        y=alt.Y("total_quantity:Q", title="판매 식수"),
                        color=alt.condition(
                            alt.datum.is_max,
                            alt.value("#4ECDC4"),  # 최대값 색상
                            alt.value("#FF6B6B")   # 일반 색상
                        ),
                        tooltip=[
                            alt.Tooltip("date_str:N", title="배송일"),
                            alt.Tooltip("total_quantity:Q", title="판매 식수", format=","),
                            alt.Tooltip("total_amount:Q", title="판매 금액", format=",")
                        ]
                    )
                )

                # ✅ 100일 이하일 때만 수치 표시
                if period_days <= max_days:
                    text = (
                        alt.Chart(df_fresh_agg)
                        .mark_text(
                            align='center',
                            baseline='bottom',
                            dy=-5,
                            fontSize=11,
                            fontWeight='bold'
                        )
                        .encode(
                            x=alt.X("date_str:N"),
                            y=alt.Y("total_quantity:Q"),
                            text=alt.Text("total_quantity:Q", format=",")
                        )
                    )
                    bar_chart = (bars + text)
                else:
                    bar_chart = bars

                # 차트 속성
                bar_chart = bar_chart.properties(
                    height=350,
                ).configure_view(
                    strokeWidth=0
                ).configure_axis(
                    labelLimit=200
                ).configure(
                    padding={"top": 20, "bottom": 80, "left": 10, "right": 10}
                )

                st.altair_chart(bar_chart, use_container_width=True)
                    
                # line_chart = (
                #     alt.Chart(df_fresh_agg)
                #     .mark_line(point=True, strokeWidth=2, color="#4ECDC4")
                #     .encode(
                #         x=alt.X("delivery_date:T", title="배송일", axis=alt.Axis(format="%Y-%m-%d")),
                #         y=alt.Y("total_quantity:Q", title="판매 식수"),
                #         tooltip=[
                #             alt.Tooltip("delivery_date:T", title="배송일", format="%Y-%m-%d"),
                #             alt.Tooltip("total_quantity:Q", title="판매 식수", format=","),
                #             alt.Tooltip("total_amount:Q", title="판매 금액", format=",")
                #         ]
                #     )
                #     .properties(
                #         height=300,
                #         title="프레시밀 일별 판매 식수"
                #     )
                # )
                
                # st.altair_chart(line_chart, use_container_width=True)
                
                with st.expander("📋 상세 데이터 보기", expanded=False):
                    display_df = df_fresh_agg[["delivery_date", "total_quantity", "total_amount"]].copy()
                    display_df.columns = ["배송일", "판매 식수", "판매 금액"]
                    display_df["배송일"] = display_df["배송일"].dt.strftime('%Y-%m-%d')
                    display_df["판매 금액"] = display_df["판매 금액"].apply(lambda x: f"{x:,}원")
                    
                    st.dataframe(
                        display_df,
                        hide_index=True,
                        width='stretch',
                        height=300
                    )
            else:
                st.info("선택한 기간에 프레시밀 판매 데이터가 없습니다.")
        else:
            st.info("프레시밀 판매 데이터를 불러오지 못했습니다.")
    
    # ==========================================
    # 탭 5: 전체 제품 판매 현황
    # ==========================================
    with tab5:
        col_title, col_filter_group = st.columns([5, 7])
        
        with col_title:
            st.markdown("<h3 style='margin-top:0.5rem;'>📦 전체 품목별 판매 현황</h3>", unsafe_allow_html=True)
        
        with col_filter_group:
            filter_inner_col1, filter_inner_col2, filter_inner_col3, filter_inner_col4 = st.columns([5.2, 2.3, 2.3, 0.7])
            
            # with filter_inner_col1:
            #     st.write("")
            
            # with filter_inner_col2:
            #     all_start_date = st.date_input(
            #         "시작일",
            #         value=today.replace(day=1) - relativedelta(months=2),
            #         key="all_start_date"
            #     )
            
            # with filter_inner_col3:
            #     all_end_date = st.date_input(
            #         "종료일",
            #         value=today,
            #         key="all_end_date"
            #     )
                
            with filter_inner_col4:
                st.markdown("""
                <style>
                .filter-icon-button {
                    position: relative;
                    top: -0.85rem;
                }
                .filter-icon-button button {
                    width: 38px !important;
                    min-width: 38px !important;
                    height: 38px !important;
                    padding: 0.5rem !important;
                    font-size: 1.2rem !important;
                    border-radius: 6px !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                st.markdown('<div class="filter-icon-button">', unsafe_allow_html=True)
                show_popup = st.button("⚙️", key="toggle_product_filter", help="품목 필터")
                st.markdown('</div>', unsafe_allow_html=True)
        
        with st.spinner(""):
            all_data = fetch_product_sold(
                API_URL,
                # all_start_date.strftime("%Y-%m-%d"),
                # all_end_date.strftime("%Y-%m-%d"),
                start_date_str,
                end_date_str,
                0
            )
        
        if all_data:
            df_all = pd.DataFrame(all_data)
            df_all["delivery_date"] = pd.to_datetime(df_all["delivery_date"])
            df_all = df_all.sort_values(by=["delivery_date", "product_name"])
            
            # 요일 추가 (월, 화, 수, 목, 금, 토, 일)
            weekday_map = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금', 5: '토', 6: '일'}
            df_all["weekday"] = df_all["delivery_date"].dt.weekday.map(weekday_map)
            df_all["date_str"] = df_all["delivery_date"].dt.strftime('%Y-%m-%d') + ' (' + df_all["weekday"] + ')'
            
            all_products = sorted(df_all["product_name"].unique().tolist())
            
            default_products = [
                "가정식 도시락", 
                "가정식 도시락 곱빼기", 
                "가정식 도시락(석식)", 
                "가정식도시락(특)", 
                "프레시밀"
            ]
            
            default_products_filtered = [p for p in default_products if p in all_products]
            
            if "product_filter_applied" not in st.session_state:
                st.session_state.product_filter_applied = default_products_filtered
            
            @st.dialog("🎯 품목 선택", width="large")
            def product_filter_dialog():
                st.markdown("차트에 표시할 품목을 선택하세요")
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
                with col_btn1:
                    if st.button("전체 선택", use_container_width=True):
                        st.session_state.product_filter_temp = all_products
                        st.rerun()
                with col_btn2:
                    if st.button("전체 해제", use_container_width=True):
                        st.session_state.product_filter_temp = []
                        st.rerun()
                
                if "product_filter_temp" not in st.session_state:
                    st.session_state.product_filter_temp = st.session_state.product_filter_applied.copy()
                
                selected_products = st.multiselect(
                    "상품 목록",
                    options=all_products,
                    default=st.session_state.product_filter_temp,
                    key="product_multiselect_popup",
                    label_visibility="collapsed"
                )
                
                st.session_state.product_filter_temp = selected_products
                
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("✅ 적용하기", use_container_width=True, type="primary"):
                        st.session_state.product_filter_applied = st.session_state.product_filter_temp.copy()
                        st.rerun()
            
            if show_popup:
                product_filter_dialog()
            
            selected_products = st.session_state.product_filter_applied
            
            if selected_products:
                df_filtered = df_all[df_all["product_name"].isin(selected_products)].copy()
                
                bar_chart = (
                    alt.Chart(df_filtered)
                    .mark_bar()
                    .encode(
                        x=alt.X("date_str:N", title="배송일", axis=alt.Axis(labelAngle=-45)),
                        y=alt.Y("total_quantity:Q", title="판매 식수"),
                        color=alt.Color("product_name:N", title="상품명"),
                        xOffset=alt.XOffset("product_name:N"),
                        tooltip=[
                            alt.Tooltip("date_str:N", title="배송일"),
                            alt.Tooltip("product_name:N", title="상품명"),
                            alt.Tooltip("total_quantity:Q", title="판매 식수", format=","),
                            alt.Tooltip("total_amount:Q", title="판매 금액", format=",")
                        ]
                    )
                    .properties(
                        height=350,
                        # title="일자별 품목별 판매 식수"
                    )
                )
                
                st.altair_chart(bar_chart, use_container_width=True)
            else:
                st.info("차트에 표시할 품목을 선택해주세요.")
            
            # st.markdown("#### 📊 제품별 판매 요약")
            
            # summary_df = df_all.groupby("product_name").agg({
            #     "total_quantity": "sum",
            #     "total_amount": "sum"
            # }).reset_index()
            
            # summary_df = summary_df.sort_values(by="total_quantity", ascending=False)
            # summary_df.columns = ["제품명", "총 판매 식수", "총 판매 금액"]
            
            # cols = st.columns(min(len(summary_df), 4))
            # for idx, row in summary_df.iterrows():
            #     col_idx = idx % 4
            #     with cols[col_idx]:
            #         st.metric(
            #             label=row["제품명"],
            #             value=f"{row['총 판매 식수']:,}식",
            #             delta=f"{row['총 판매 금액']:,}원"
            #         )
            
            with st.expander("📋 상세 데이터 보기", expanded=False):
                display_df = df_all[["delivery_date", "product_name", "total_quantity", "total_amount"]].copy()
                display_df.columns = ["배송일", "상품명", "판매 식수", "판매 금액"]
                display_df["배송일"] = display_df["배송일"].dt.strftime('%Y-%m-%d')
                display_df["판매 금액"] = display_df["판매 금액"].apply(lambda x: f"{x:,}원")
                
                st.dataframe(
                    display_df,
                    hide_index=True,
                    width='stretch',
                    height=400
                )
        else:
            st.info("전체 품목별 판매 데이터를 불러오지 못했습니다.")