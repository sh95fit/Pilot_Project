# services/business/frontend/app.py
import streamlit as st
import requests

st.title("Business Dashboard")

st.write("Hello from Business Frontend!")

# Backend API 호출 샘플
backend_url = st.secrets.get("BACKEND_URL", "http://localhost:8000")

try:
    resp = requests.get(f"{backend_url}/health")
    status = resp.json().get("status", "unknown")
    st.write(f"Backend Health: {status}")
except Exception as e:
    st.write(f"Error connecting to backend: {e}")