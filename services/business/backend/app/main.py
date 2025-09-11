from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from contextlib import asynccontextmanager

from .api import auth, health
from .middleware.auth_middleware import AuthMiddleware
from .core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 실행
    print(f"🚀 Starting FastAPI application in {settings.environment} mode")
    print(f"🔧 Debug: {settings.debug}")
    print(f"📊 Log level: {settings.log_level}")
    
    yield
    
    # 종료 시 실행
    print("🛑 Shutting down FastAPI application")


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 팩토리"""
    
    app = FastAPI(
        title="Pilot Auth API",
        description="Cognito + FastAPI + Streamlit Authentication System",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8501", "http://frontend:8501"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # 커스텀 인증 미들웨어 추가
    app.add_middleware(
        AuthMiddleware,
        excluded_paths=[
            "/health", 
            "/health/detailed",
            "/docs", 
            "/redoc", 
            "/openapi.json",
            "/auth/login",
            "/auth/check"
        ]
    )

    # 라우터 등록
    app.include_router(health.router)
    app.include_router(auth.router)

    # 보호된 API 예시
    @app.get("/api/dashboard")
    async def protected_dashboard(request: Request):
        """보호된 대시보드 API"""
        user = getattr(request.state, 'user', None)
        if not user:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        
        return {
            "message": "Welcome to the protected dashboard!",
            "user_id": user.get("sub"),
            "roles": user.get("roles", [])
        }

    # 글로벌 예외 핸들러
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        if settings.debug:
            import traceback
            print(f"Global exception: {exc}")
            print(traceback.format_exc())
        
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

    return app

# 애플리케이션 인스턴스 생성
app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )