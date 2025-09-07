# services/business/frontend/app.py
import streamlit as st
import requests

st.title("Business Dashboard")

st.write("Hello from Business Frontend!")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")

# Backend API 호출 샘플
if ENVIRONMENT == "prod":
    # 도커 compose 상에서 backend 서비스명 사용
    backend_url = st.secrets.get("BACKEND_URL", "http://business_backend:8000")
else:
    backend_url = st.secrets.get("BACKEND_URL", "http://localhost:8000")

try:
    resp = requests.get(f"{backend_url}/api/health")
    status = resp.json().get("status", "unknown")
    st.write(f"Backend Health: {status}")
except Exception as e:
    st.write(f"Error connecting to backend: {e}")