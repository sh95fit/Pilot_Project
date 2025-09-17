import streamlit as st
from components.auth.login_form import render_login_form

def show_login_page():
    st.set_page_config(
        page_title="로그인 - Business Dashboard",
        page_icon="🔐",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    # 기본 사이드바 완전히 숨기기
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True
    )

    render_login_form()