# import streamlit as st
# from utils.auth_utils import login_user, logout_user

# def show_login_form():
#     st.title("🔐 Login")
    
#     with st.form("login_form"):
#         email = st.text_input(
#             "Email",
#             placeholder="Enter your email address"
#         )
#         password = st.text_input(
#             "Password",
#             type="password",
#             placeholder="Enter your password"
#         )
        
#         submit_button = st.form_submit_button("Login", use_container_width=True)
#         if submit_button:
#             if not email or not password:
#                 st.error("Please fill in all fields")
#                 return
#             with st.spinner("Logging in ..."):
#                 success, message = login_user(email, password)
#                 if success:
#                     st.success(message)
#                     st.rerun()
#                 else:
#                     st.error(message)

# def show_user_info(user_info: dict):
#     st.sidebar.markdown("---")
#     st.sidebar.markdown("### 👤 User Info")
#     st.sidebar.markdown(f"**Email:** {user_info.get('email', 'N/A')}")
#     st.sidebar.markdown(f"**Name:** {user_info.get('display_name', 'N/A')}")
#     st.sidebar.markdown(f"**Role:** {user_info.get('role', 'N/A')}")
    
#     st.sidebar.markdown("---")
#     if st.sidebar.button("🚪 Logout"):
#         with st.spinner("Logging out..."):
#             success, message = logout_user()
#             if success:
#                 st.success(message)
#                 st.rerun()
#             else:
#                 st.error(message)


###############################################################################

# import streamlit as st
# import time
# from utils.auth_utils import login_user, logout_user, get_auth_status_info


# def show_login_form():
#     """로그인 폼 컴포넌트"""
#     st.title("🔐 로그인")
    
#     # 로그인 상태 디버깅 정보 (개발 모드에서만)
#     if st.checkbox("🔍 디버그 정보 표시"):
#         status_info = get_auth_status_info()
#         st.json(status_info)
    
#     with st.form("login_form"):
#         email = st.text_input(
#             "이메일",
#             placeholder="이메일 주소를 입력하세요",
#             help="AWS Cognito 계정 이메일을 사용하세요"
#         )
#         password = st.text_input(
#             "비밀번호",
#             type="password",
#             placeholder="비밀번호를 입력하세요"
#         )
        
#         submit_button = st.form_submit_button("로그인", use_container_width=True)
        
#         if submit_button:
#             if not email or not password:
#                 st.error("모든 필드를 입력해주세요")
#                 return
            
#             with st.spinner("로그인 중..."):
#                 success, message = login_user(email, password)
                
#                 if success:
#                     st.success(message)
#                     # 로그인 성공 후 잠시 대기 후 페이지 새로고침
#                     time.sleep(1)
#                     st.rerun()
#                 else:
#                     st.error(message)


# def show_logout_button():
#     """로그아웃 버튼 컴포넌트"""
#     col1, col2, col3 = st.columns([1, 1, 1])
    
#     with col2:
#         if st.button("🚪 로그아웃", use_container_width=True):
#             with st.spinner("로그아웃 중..."):
#                 success, message = logout_user()
                
#                 if success:
#                     st.success(message)
#                     st.rerun()
#                 else:
#                     st.error(message)


# def show_user_info(user_info: dict):
#     """사용자 정보 표시 컴포넌트"""
#     st.sidebar.markdown("---")
#     st.sidebar.markdown("### 👤 사용자 정보")
#     st.sidebar.markdown(f"**이메일:** {user_info.get('email', 'N/A')}")
#     st.sidebar.markdown(f"**이름:** {user_info.get('display_name', 'N/A')}")
#     st.sidebar.markdown(f"**역할:** {user_info.get('role', 'N/A')}")
    
#     # 로그아웃 버튼을 사이드바에 표시
#     st.sidebar.markdown("---")
#     if st.sidebar.button("🚪 로그아웃"):
#         with st.spinner("로그아웃 중..."):
#             success, message = logout_user()
#             if success:
#                 st.success(message)
#                 st.rerun()
#             else:
#                 st.error(message)


#################################################################################

# import streamlit as st
# from utils.auth_utils import login_user, logout_user, get_auth_status_info

# def show_login_form():
#     """로그인 폼 컴포넌트"""
    
#     st.title("🔐 로그인")
    
#     with st.form("login_form"):
#         email = st.text_input("이메일", placeholder="이메일 주소를 입력하세요")
#         password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
#         submit_button = st.form_submit_button("로그인", use_container_width=True)
        
#         if submit_button:
#             if not email or not password:
#                 st.error("모든 필드를 입력해주세요")
#                 return
#             with st.spinner("로그인 중..."):
#                 success, message = login_user(email, password)
#                 if success:
#                     st.success(message)
#                     st.rerun()
#                 else:
#                     st.error(message)

# def show_logout_button():
#     """로그아웃 버튼"""
#     if st.button("🚪 로그아웃", use_container_width=True):
#         with st.spinner("로그아웃 중..."):
#             success, message = logout_user()
#             if success:
#                 st.success(message)
#                 st.rerun()
#             else:
#                 st.error(message)

# def show_user_info(user_info: dict):
#     """사용자 정보 표시 사이드바"""
#     st.sidebar.markdown("---")
#     st.sidebar.markdown("### 👤 사용자 정보")
#     st.sidebar.markdown(f"**이메일:** {user_info.get('email', 'N/A')}")
#     st.sidebar.markdown(f"**이름:** {user_info.get('display_name', 'N/A')}")
#     st.sidebar.markdown(f"**역할:** {user_info.get('role', 'N/A')}")
    
#     st.sidebar.markdown("---")
#     show_logout_button()



import streamlit as st
from utils.auth_utils import login_user, logout_user, get_auth_status_info

def show_login_form():
    """로그인 폼 컴포넌트"""
    
    st.title("🔐 로그인")
    
    with st.form("login_form"):
        email = st.text_input("이메일", placeholder="이메일 주소를 입력하세요")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        submit_button = st.form_submit_button("로그인", use_container_width=True)
        
        if submit_button:
            if not email or not password:
                st.error("모든 필드를 입력해주세요")
                return
            with st.spinner("로그인 중..."):
                success, message = login_user(email, password)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

def show_logout_button():
    """로그아웃 버튼"""
    if st.button("🚪 로그아웃", use_container_width=True):
        with st.spinner("로그아웃 중..."):
            success, message = logout_user()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

def show_user_info(user_info: dict):
    """사용자 정보 표시 사이드바"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👤 사용자 정보")
    st.sidebar.markdown(f"**이메일:** {user_info.get('email', 'N/A')}")
    st.sidebar.markdown(f"**이름:** {user_info.get('display_name', 'N/A')}")
    st.sidebar.markdown(f"**역할:** {user_info.get('role', 'N/A')}")
    
    st.sidebar.markdown("---")
    show_logout_button()