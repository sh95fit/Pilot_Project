from fastapi import APIRouter
from .endpoints import data

api_router = APIRouter()

# 모든 v1 엔드포인트 등록
api_router.include_router(data.router)