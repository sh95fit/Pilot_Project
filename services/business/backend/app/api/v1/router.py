from fastapi import APIRouter
from .endpoints import data, google_sheets

api_router = APIRouter()

# 모든 v1 엔드포인트 등록
api_router.include_router(data.router)
api_router.include_router(google_sheets.router)