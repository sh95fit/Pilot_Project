# import streamlit as st
# from utils.auth_utils import login_user, get_auth_status_info
# from components.auth_components import show_login_form

# def show_login_page():
#     """로그인 페이지"""
    
#     # 페이지 설정 (한 번만)
#     st.set_page_config(
#         page_title="Login - Pilot Auth",
#         page_icon="🔐",
#         layout="centered",
#         initial_sidebar_state="collapsed"
#     )
    
#     # 사이드바 숨기기
#     hide_sidebar_style = """
#         <style>
#         [data-testid="stSidebar"] {display: none !important;}
#         </style>
#     """
#     st.markdown(hide_sidebar_style, unsafe_allow_html=True)
    
#     # 중앙 정렬 컨테이너
#     col1, col2, col3 = st.columns([1, 2, 1])
#     with col2:
#         show_login_form()
    
#     # 하단 정보
#     st.markdown("---")
#     st.markdown(
#         """
#         <div style="text-align: center; color: #666;">
#             <p>🔒 Secure authentication powered by AWS Cognito</p>
#             <p>Demo credentials: contact your administrator</p>
#         </div>
#         """, 
#         unsafe_allow_html=True
#     )
    
#     # 개발용 디버그 정보
#     if st.checkbox("🔍 디버그 정보 표시"):
#         st.json(get_auth_status_info())

#######################################################################

# import streamlit as st
# from streamlit_cookies_controller import CookieController
# import requests

# BACKEND_URL = "http://localhost:8000"  # FastAPI API URL
# cookies = CookieController()

# st.set_page_config(page_title="Login", page_icon="🔐")

# st.title("Login")

# # 로그인 폼
# with st.form("login_form"):
#     email = st.text_input("Email")
#     password = st.text_input("Password", type="password")
#     submitted = st.form_submit_button("Login")

# if submitted:
#     try:
#         response = requests.post(
#             f"{BACKEND_URL}/auth/login",
#             json={"email": email, "password": password},
#         )
#         response.raise_for_status()
#         data = response.json()

#         # access_token, session_id 쿠키 저장
#         cookies.set("access_token", response.cookies.get("access_token"))
#         cookies.set("session_id", response.cookies.get("session_id"))

#         st.success("Login successful! Redirecting...")
#         st.experimental_set_query_params(page="dashboard")  # 리다이렉트
#         st.experimental_rerun()

#     except requests.HTTPError as e:
#         st.error(f"Login failed: {e.response.json().get('detail')}")

#######################################################################


# import streamlit as st
# from app.components.auth_components import show_login_form
# from app.components.auth_components import show_user_info
# from app.utils.auth_utils import get_auth_status_info

# st.set_page_config(page_title="Login", page_icon="🔐", layout="centered")

# auth_info = get_auth_status_info()

# if auth_info["authenticated"]:
#     st.success("이미 로그인되어 있습니다.")
#     show_user_info(auth_info["user_info"])
# else:
#     show_login_form()


import streamlit as st
from components.auth_components import show_login_form
from components.auth_components import show_user_info
from utils.auth_utils import get_auth_status_info

st.set_page_config(page_title="Login", page_icon="🔐", layout="centered")

auth_info = get_auth_status_info()

if auth_info["authenticated"]:
    st.success("이미 로그인되어 있습니다.")
    show_user_info(auth_info["user_info"])
else:
    show_login_form()
