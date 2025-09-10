import os
import streamlit as st
import requests

st.set_page_config(page_title="Cognito Login Demo", page_icon="🔐")
st.title("🔐 Cognito Login Demo")
st.write("Hello from Business Frontend!")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")

# Backend API 호출 샘플
backend_url = os.environ.get("BACKEND_URL", "http://business_backend:8000")

try:
    resp = requests.get(f"{backend_url}/health")
    status = resp.json().get("status", "unknown")
    st.write(f"Backend Health: {status}")
except Exception as e:
    st.write(f"Error connecting to backend: {e}")


# Login 테스트
username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    try :
        # Cognito Auth API 대신 FastAPI에 로그인 요청
        # FastAPI에서 boto3를 이용해 Cognito로 인증 처리하도록 구성
        resp = requests.post(f"{backend_url}/auth/login", json={
            "username": username,
            "password": password
        })
        
        if resp.status_code == 200:
            tokens = resp.json()
            
            st.success("Login Successful!")
            st.session_state["access_token"] = tokens["access_token"]
            
        else :
            st.error(f"Login failed: {resp.text}")
    except Exception as e :
        st.error(f"Error : {e}")

# 보호된 API 호출 버튼
if "access_token" in st.session_state:
    if st.button("Call Protected API"):
        token = st.session_state["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{backend_url}/protected", headers=headers)
        
        if resp.status_code == 200:
            st.json(resp.json())
        else:
            st.error(f"Protected API call failed: {resp.text}")