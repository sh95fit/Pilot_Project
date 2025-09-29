from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from contextlib import asynccontextmanager

from backend.app.api import auth, health
from backend.app.api.v1.router import api_router as api_v1_router
from backend.app.middleware.auth_middleware import AuthMiddleware
from backend.app.core.config import settings
from backend.app.core.database import database_manager

from backend.app.core.exceptions import (
    BaseAPIException,
    DatabaseConnectionError,
    SSHTunnelError,
    DataValidationError
)
from .middleware.error_handler import (
    base_exception_handler,
    database_exception_handler,
    ssh_tunnel_exception_handler,
    validation_exception_handler
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 실행
    print(f"🚀 Starting FastAPI application in {settings.environment} mode")
    print(f"🔧 Debug: {settings.debug}")
    print(f"📊 Log level: {settings.log_level}")

    # ✅ 모든 DB 초기화
    try:
        await database_manager.initialize()
        print("✅ All database clients initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database clients: {e}")
        raise

    try:
        yield
    finally:
        # 종료 시 연결 종료
        try:
            await database_manager.close()
            print("🛑 Database manager closed")
        except Exception as e:
            print(f"⚠️ Failed to close database manager: {e}")


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
        allow_origins=["http://localhost:8501", "http://frontend:8501", "http://127.0.0.1:8501", "https://prototype.lunchlab.me"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # 예외 핸들러 등록
    app.add_exception_handler(BaseAPIException, base_exception_handler)
    app.add_exception_handler(DatabaseConnectionError, database_exception_handler)
    app.add_exception_handler(SSHTunnelError, ssh_tunnel_exception_handler)
    app.add_exception_handler(DataValidationError, validation_exception_handler)

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
    app.include_router(api_v1_router, prefix="/api/v1")

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
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "message": str(exc),
                        "type": exc.__class__.__name__,
                        "traceback": traceback.format_exc()
                    }
                }
            )
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "message": "Internal server error",
                    "type": "InternalError"
                }
            }
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