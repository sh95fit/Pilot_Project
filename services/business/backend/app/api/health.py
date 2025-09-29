from fastapi import APIRouter, Depends
from shared.database.supabase_client import SupabaseClient
from shared.database.redis_client import RedisClient
from backend.app.core.dependencies.auth import get_supabase_client, get_redis_client
import logging

router = APIRouter(tags=["health"])
logger = logging.getLogger("healthcheck")


def check_redis(redis_client: RedisClient) -> dict:
    """Redis 헬스 체크"""
    try:
        exists = redis_client.session_exists("health_check")
        status = "ok" if exists is not None else "error"
        return {
            "status": status,
            "details": {
                "session_exists_test": exists
            }
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}", exc_info=True)
        return {
            "status": "error",
            "details": {"error": str(e)}
        }


def check_supabase(supabase_client: SupabaseClient) -> dict:
    """Supabase 헬스 체크"""
    try:
        response = supabase_client.client.table("users").select("id").limit(1).execute()
        if response.data is None:
            status = "error"
            details = {"message": "Table 'users' not found"}
        elif len(response.data) == 0:
            status = "warning"
            details = {"message": "Table 'users' exists but no data"}
        else:
            status = "ok"
            details = {"rows_found": len(response.data)}
        return {
            "status": status,
            "details": details
        }
    except Exception as e:
        logger.error(f"Supabase health check failed: {e}", exc_info=True)
        return {
            "status": "error",
            "details": {"error": str(e)}
        }


@router.get("/health")
async def health_check(
    redis_client: RedisClient = Depends(get_redis_client),
    supabase_client: SupabaseClient = Depends(get_supabase_client)
):
    """헬스 체크 엔드포인트"""
    redis_result = check_redis(redis_client)
    supabase_result = check_supabase(supabase_client)

    overall_status = "healthy" if all(r["status"] == "ok" for r in [redis_result, supabase_result]) else "degraded"

    return {
        "status": overall_status,
        "services": {
            "redis": redis_result,
            "supabase": supabase_result
        }
    }


# 개별 서비스 헬스 체크 엔드포인트 (선택사항)
@router.get("/health/redis")
async def redis_health_check(redis_client: RedisClient = Depends(get_redis_client)):
    """Redis 헬스 체크만 수행"""
    return check_redis(redis_client)


@router.get("/health/supabase")
async def supabase_health_check(supabase_client: SupabaseClient = Depends(get_supabase_client)):
    """Supabase 헬스 체크만 수행"""
    return check_supabase(supabase_client)