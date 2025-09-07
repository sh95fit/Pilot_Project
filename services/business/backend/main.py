# services/business/backend/main.py
from fastapi import FastAPI

app = FastAPI(title="Marketing Backend")

@app.get("/")
def read_root():
    return {"message": "Hello from Marketing Backend!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}