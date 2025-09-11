import streamlit as st
from utils.auth_utils import login_user, logout_user

def show_login_form():
    st.title("🔐 Login")
    
    with st.form("login_form"):
        email = st.text_input(
            "Email",
            placeholder="Enter your email address"
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password"
        )
        
        submit_button = st.form_submit_button("Login", use_container_width=True)
        if submit_button:
            if not email or not password:
                st.error("Please fill in all fields")
                return
            with st.spinner("Logging in ..."):
                success, message = login_user(email, password)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

def show_user_info(user_info: dict):
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👤 User Info")
    st.sidebar.markdown(f"**Email:** {user_info.get('email', 'N/A')}")
    st.sidebar.markdown(f"**Name:** {user_info.get('display_name', 'N/A')}")
    st.sidebar.markdown(f"**Role:** {user_info.get('role', 'N/A')}")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        with st.spinner("Logging out..."):
            success, message = logout_user()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
