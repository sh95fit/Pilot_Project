# services/business/backend/main.py
from fastapi import FastAPI

app = FastAPI(title="Business Backend")

@app.get("/")
def read_root():
    return {"message": "Hello from Marketing Backend!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}


# 로그인 테스트
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer()

AWS_REGION = os.getenv("COGNITO_REGION")
USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")

if not USER_POOL_ID or not CLIENT_ID:
    raise RuntimeError("USER_POOL_ID and CLIENT_ID must be set in .env file")

cognito = boto3.client("cognito-idp", region_name=AWS_REGION)


class LoginRequest(BaseModel):
    username: str
    password: str
    
@app.post("/auth/login")
def login(req: LoginRequest):
    try:
        response = cognito.initiate_auth(
            ClientId = CLIENT_ID,
            AuthFlow = "USER_PASSWORD_AUTH",
            AuthParameters = {
                "USERNAME": req.username,
                "PASSWORD": req.password
            }
        )
        
        return {
            "id_token": response["AuthenticationResult"]["IdToken"],
            "access_token": response["AuthenticationResult"]["AccessToken"],
            "refresh_token": response["AuthenticationResult"]["RefreshToken"],
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    
@app.get("/protected")
def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    
    try:
        # 실제 서비스에서는 JWKS 검증 필요
        payload = jwt.get_unverified_claims(token)
        return {"message": "Protected API success", "claims": payload}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
