from fastapi import APIRouter
from ..core.security import redis_client, supabase_client
import logging

router = APIRouter(tags=["health"])
logger = logging.getLogger("healthcheck")


def check_redis() -> dict:
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


def check_supabase() -> dict:
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
async def health_check():
    """헬스 체크 엔드포인트"""
    redis_result = check_redis()
    supabase_result = check_supabase()

    overall_status = "healthy" if all(r["status"] == "ok" for r in [redis_result, supabase_result]) else "degraded"

    return {
        "status": overall_status,
        "services": {
            "redis": redis_result,
            "supabase": supabase_result
        }
    }