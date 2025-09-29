from fastapi import Request, status
from fastapi.responses import JSONResponse
from backend.app.core.exceptions import (
    BaseAPIException,
    DatabaseConnectionError,
    SSHTunnelError,
    DataValidationError
)
import logging

logger = logging.getLogger(__name__)

async def base_exception_handler(request: Request, exc: BaseAPIException):
    """기본 API 예외 핸들러"""
    logger.error(f"API Exception: {exc.message}", extra={
        "path": request.url.path,
        "method": request.method
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "message": exc.message,
                "type": exc.__class__.__name__
            }
        }
    )

async def database_exception_handler(request: Request, exc: DatabaseConnectionError):
    """DB 연결 에러 핸들러"""
    logger.critical(f"Database connection error: {exc.message}")
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "error": {
                "message": "Database temporarily unavailable",
                "type": "ServiceUnavailable"
            }
        }
    )

async def ssh_tunnel_exception_handler(request: Request, exc: SSHTunnelError):
    """SSH 터널 에러 핸들러"""
    logger.critical(f"SSH tunnel error: {exc.message}")
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "error": {
                "message": "Service temporarily unavailable",
                "type": "ServiceUnavailable"
            }
        }
    )

async def validation_exception_handler(request: Request, exc: DataValidationError):
    """데이터 검증 에러 핸들러"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "message": exc.message,
                "type": "ValidationError"
            }
        }
    )