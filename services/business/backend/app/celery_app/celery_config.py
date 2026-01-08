"""
Celery 설정 및 MySQL 연결 관리
"""
from celery import Celery
from celery.schedules import crontab
from kombu import Queue, Exchange
import logging
from datetime import timedelta

from backend.app.core.config import settings

# 워커 라이프사이클 시그널
from celery.signals import (
    worker_process_init, # Worker 프로세스 최초 시작 시 1회만 수행 (Mysql 초기화, SSH Tunnel 생성)
    worker_process_shutdown, # Worker 종료 시 1회만 수행 (모든 연결 정리, SSH Tunnel 닫기)
    task_prerun, # Task 실행 직전마다 수행 (연결 상태 확인, 필요시 재연결)
    task_postrun, # Task 성공 시 수행 (Pool 사용률 체크)
    task_failure # Task 실패 시 수행 (에러 원인 분석)
)
import asyncio
from backend.app.core.database.mysql_client import mysql_client


logger = logging.getLogger(__name__)

# =============================================================================
# Celery 앱 생성
# =============================================================================

celery_app = Celery(
    "business_tasks",
    broker=settings.celery_broker_url,
    backend=None,
    include=[
        "app.celery_app.tasks.cohort_tasks",
    ]
)

# =============================================================================
# Celery 설정
# =============================================================================

celery_app.conf.update(
    # 타임존 설정
    timezone="Asia/Seoul",
    enable_utc=True,
    
    # 태스크 설정
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_expires=3600,

    # Worker 설정
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,  # 메모리 누수 방지
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # 재시도 설정
    task_default_retry_delay=60,
    task_max_retries=3,
    
    
    # Beat 스케줄러 설정
    beat_schedule={
        # 미주문 고객사 데이터 업데이트
        "update-not-ordered-cohort": {
            "task": "cohort_tasks.update_not_ordered_cohort",
            "schedule": crontab(hour=14, minute=35, day_of_week="1-5"),
            "options": {"queue": "cohort"}
        },
        
        # 미주문 고객사 데이터 업데이트
        "update-pending-not-ordered-cohort": {
            "task": "cohort_tasks.update_pending_not_ordered_cohort",
            'schedule': crontab(minute='0,20,40', hour='9-14', day_of_week="1-5"),
            "options": {"queue": "cohort"}
        },
    
        # 서비스 이용 종료 고객사 데이터 업데이트
        "update-end-of-use-cohort": {
            "task": "cohort_tasks.update_end_of_use_cohort",
            'schedule': crontab(minute='1,21,41', hour='9-20', day_of_week="1-5"),
            "options": {"queue": "cohort"}
        },
        
        # 활성 고객 데이터 업데이트
        "update-active-customer-cohort": {
            "task": "cohort_tasks.update_active_accounts_cohort",
            'schedule': crontab(minute='2,22,44', hour='9-20', day_of_week="1-5"),
            "options": {"queue": "cohort"}
        },
        
        # 어드민 유입 고객 데이터 업데이트
        "update-incoming-leads-cohort": {
            "task": "cohort_tasks.update_incoming_leads_cohort",
            "schedule": crontab(minute='3,23,43', hour="9-20", day_of_week="1-5"),
            "options": {"queue": "cohort"}
        },
        
        # 현재 활성 고객 데이터 업데이트
        "update-now-active-accounts-cohort": {
            "task": "cohort_tasks.update_now_active_accounts_cohort",
            'schedule': crontab(minute='4,24,44', hour='9-20', day_of_week="1-5"),
            "options": {"queue": "cohort"}
        },
        
        # 상품별 주문 수량 데이터 업데이트        
        "update-product-sales-summary": {
            "task": "cohort_tasks.update_product_sales_summary_cohort",
            "schedule": crontab(minute='5,20,35,50'),
            "options": {"queue": "cohort"}
        },
        
        # 고객사 단위 상품별 주문 수량 데이터 업데이트        
        "update-account-orders-summary": {
            "task": "cohort_tasks.update_account_orders_summary_cohort",
            "schedule": crontab(minute='6, 26, 46'),
            "options": {"queue": "cohort"}
        },
        
        # 체험 고객사 데이터 업데이트
        "update-trial-accounts-cohort": {
            "task": "cohort_tasks.update_trial_accounts_cohort",
            "schedule": crontab(minute='7, 27, 47'),
            "options": {"queue": "cohort"}
        },
        
        # 고객유입리드 데이터 업데이트
        "update-lead-applications-cohort": {
            "task": "cohort_tasks.update_lead_applications_cohort",
            "schedule": crontab(minute='*/10'),
            "options": {"queue": "cohort"}
        },
        
        # 활성 고객사 히스토리 데이터 업데이트
        "update-active-accounts-history-cohort": {
            "task": "cohort_tasks.update_active_accounts_history_cohort",
            "schedule": crontab(minute='*/10'),
            "options": {"queue": "cohort"}
        },
        
        
        # MySQL 연결 모니터링 (30분마다)
        "monitor-mysql-health": {
            "task": "cohort_tasks.monitor_mysql_health",
            "schedule": timedelta(minutes=30),
            "options": {"queue": "cohort"}
        },
    },
    
    # 큐 설정
    task_routes={
        "app.celery_app.tasks.cohort_tasks.*": {"queue": "cohort"},
    },
    
    task_queues=(
        Queue("cohort", Exchange("cohort"), routing_key="cohort"),
        Queue("default", Exchange("default"), routing_key="default"),
    ),
    
    # 연결 풀 설정
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_pool_limit=10,
)

logger.info("✅ Celery app configured successfully")    



# =============================================================================
# MySQL 연결 라이프사이클 관리
# =============================================================================

@worker_process_init.connect
def init_mysql_on_worker_start(**kwargs):
    """
    Worker 프로세스 시작 시 MySQL 클라이언트 초기화
    - SSH Tunnel 설정
    - Event Loop 생성
    - Connection Pool은 첫 요청 시 Lazy 생성
    """
    try:
        # 새로운 Event Loop 생성
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # MySQL 클라이언트 초기화 (SSH Tunnel)
        loop.run_until_complete(mysql_client.initialize())
        
        logger.info("✅ Worker started: MySQL client initialized (SSH tunnel active)")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize MySQL client on worker start: {e}", exc_info=True)
        raise


@task_prerun.connect
def ensure_mysql_connection_before_task(task_id, task, *args, **kwargs):
    """
    Task 실행 직전 MySQL 연결 상태 확인
    - Health check 수행
    - 문제 발견 시 자동 재연결
    """
    # 모니터링 Task는 스킵 (무한 루프 방지)
    if task.name == "cohort_tasks.monitor_mysql_health":
        return
    
    try:
        loop = asyncio.get_event_loop()
        
        # Health check
        is_healthy = loop.run_until_complete(mysql_client.health_check())
        
        if not is_healthy:
            logger.warning(
                f"⚠️ MySQL unhealthy before task {task.name} (id: {task_id}), "
                f"attempting reconnection..."
            )
            loop.run_until_complete(mysql_client._ensure_connection())
            logger.info("✅ MySQL reconnected successfully")
        else:
            logger.debug(f"✅ MySQL healthy, starting task {task.name}")
            
    except Exception as e:
        logger.error(
            f"❌ Error checking MySQL before task {task.name}: {e}",
            exc_info=True
        )
        # Task 실행은 계속 진행 (실제 쿼리 시 재시도할 것)


@task_postrun.connect
def monitor_pool_usage_after_task(task_id, task, retval, *args, **kwargs):
    """
    Task 완료 후 Connection Pool 사용률 체크
    - 80% 이상 사용 시 경고 로그
    """
    try:
        if not mysql_client.pools:
            return
        
        for db_name, pool in mysql_client.pools.items():
            in_use = pool.size - pool.freesize
            usage_percent = (in_use / pool.maxsize) * 100 if pool.maxsize > 0 else 0
            
            if usage_percent >= 80:
                logger.warning(
                    f"⚠️ High pool usage after task {task.name}: "
                    f"[{db_name}] {in_use}/{pool.maxsize} ({usage_percent:.1f}%)"
                )
            else:
                logger.debug(
                    f"Pool [{db_name}] usage: {in_use}/{pool.maxsize} ({usage_percent:.1f}%)"
                )
                
    except Exception as e:
        logger.error(f"Error monitoring pool usage: {e}")


@task_failure.connect
def handle_task_failure_with_connection_check(task_id, exception, *args, **kwargs):
    """
    Task 실패 시 MySQL 연결 에러인지 확인
    - 연결 에러면 다음 Task에서 자동 재연결될 것임을 로그
    """
    try:
        error_msg = str(exception).lower()
        
        connection_error_keywords = [
            "lost connection", "can't connect", "connection refused",
            "broken pipe", "connection reset", "timeout", 
            "ssh tunnel", "no connection", "connection closed"
        ]
        
        is_connection_error = any(keyword in error_msg for keyword in connection_error_keywords)
        
        if is_connection_error:
            logger.error(
                f"❌ Task failed due to MySQL CONNECTION error: {exception}",
                exc_info=True
            )
            logger.warning("🔄 Next task will attempt to reconnect MySQL automatically")
        else:
            logger.error(
                f"❌ Task failed (non-connection error): {exception}",
                exc_info=True
            )
            
    except Exception as e:
        logger.error(f"Error in failure handler: {e}")


@worker_process_shutdown.connect
def cleanup_mysql_on_worker_shutdown(sig=None, how=None, exitcode=None, **kwargs):
    """
    Worker 프로세스 종료 시 완전한 정리
    - 모든 Connection Pool 닫기
    - SSH Tunnel 종료
    - Event Loop 정리
    """
    logger.info("🛑 Worker shutdown signal received, cleaning up MySQL resources...")
    
    loop = None
    
    try:
        # Event loop 확보
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            logger.debug("No event loop, creating new one for cleanup")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Loop가 닫혀있으면 새로 생성
        if loop.is_closed():
            logger.debug("Event loop closed, creating new one for cleanup")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # MySQL 클라이언트 정리
        if not loop.is_running():
            # 정상 케이스: loop가 멈춰있음
            loop.run_until_complete(mysql_client.close())
            logger.info("✅ MySQL connection pools and SSH tunnel closed")
        else:
            # 비정상 케이스: loop가 여전히 실행 중
            logger.warning(
                "⚠️ Event loop still running during shutdown, "
                "attempting forced cleanup..."
            )
            try:
                future = asyncio.ensure_future(mysql_client.close(), loop=loop)
                loop.run_until_complete(asyncio.wait_for(future, timeout=5.0))
                logger.info("✅ Forced cleanup completed")
            except asyncio.TimeoutError:
                logger.error("❌ Timeout during forced MySQL cleanup (5s)")
            except Exception as e:
                logger.error(f"❌ Error during forced cleanup: {e}")
    
    except Exception as e:
        logger.error(f"❌ Error during worker shutdown cleanup: {e}", exc_info=True)
    
    finally:
        # Event loop 정리
        if loop and not loop.is_closed():
            try:
                # 남은 태스크 취소
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                
                # Loop 종료
                loop.close()
                logger.info("✅ Event loop closed")
            except Exception as e:
                logger.error(f"Error closing event loop: {e}")


# =============================================================================
# Pool 상태 조회 유틸리티
# =============================================================================

def get_mysql_pool_stats() -> dict:
    """
    MySQL Connection Pool 통계 반환
    
    Returns:
        dict: {
            "pools": {db_name: {size, freesize, maxsize, usage_percent}},
            "ssh_tunnel": {active, local_port, initialized}
        }
    """
    try:
        stats = {"pools": {}}
        
        # 각 DB Pool 통계
        for db_name, pool in mysql_client.pools.items():
            # aiomysql Pool의 실제 속성 확인
            # size()와 freesize()는 메서드입니다
            try:
                size = pool.size  # 현재 생성된 연결 수
                freesize = pool.freesize  # 사용 가능한 연결 수
                maxsize = pool.maxsize  # 최대 연결 수 (속성)
                minsize = pool.minsize  # 최소 연결 수 (속성)
                
                in_use = size - freesize
                usage_percent = round((in_use / maxsize) * 100, 2) if maxsize > 0 else 0
                
                stats["pools"][db_name] = {
                    "size": size,
                    "freesize": freesize,
                    "in_use": in_use,
                    "minsize": minsize,
                    "maxsize": maxsize,
                    "usage_percent": usage_percent
                }
            except AttributeError as ae:
                logger.warning(f"Pool {db_name} attribute error: {ae}")
                # Pool 객체의 실제 속성 로깅 (디버깅용)
                logger.debug(f"Available pool attributes: {dir(pool)}")
                stats["pools"][db_name] = {"error": "Unable to read pool stats"}
        
        # SSH 터널 상태
        stats["ssh_tunnel"] = {
            "active": mysql_client.ssh_tunnel.is_active if mysql_client.ssh_tunnel else False,
            "local_port": mysql_client.local_port,
            "initialized": mysql_client._initialized
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting pool stats: {e}", exc_info=True)
        return {"error": str(e)}
    
    
#########################
# 실제 흐름 예시
#########################
# 1. Worker 시작
# $ celery -A backend.app.celery_app.celery_config worker

# → worker_process_init 실행
#   ✅ SSH Tunnel 생성
#   ✅ Event Loop 설정
#   (로그) "Worker started: MySQL client initialized"

# # 2. Task 1 실행: update_not_ordered_cohort
# → task_prerun 실행
#   ✅ Health check 수행
#   ✅ 연결 정상
#   (로그) "MySQL healthy, starting task"

# → Task 실행
#   📥 MySQL에서 데이터 추출
#   🔄 데이터 변환
#   📤 Google Sheets 업데이트

# → task_postrun 실행
#   ✅ Pool 사용률 체크: 40%
#   (로그) "Pool usage: 2/5 connections"

# # 3. Task 2 실행: update_active_accounts_cohort
# → task_prerun 실행
#   ⚠️ Health check 실패
#   🔄 자동 재연결 시도
#   ✅ 재연결 성공
#   (로그) "MySQL reconnected successfully"

# → Task 실행
#   (성공)

# → task_postrun 실행
#   (정상)

# # 4. Task 3 실행: update_incoming_leads_cohort
# → task_prerun 실행
#   (정상)

# → Task 실행
#   ❌ 예외 발생: ValueError

# → task_failure 실행
#   (로그) "Task failed (non-connection error)"
  
# # 5. Worker 종료
# $ Ctrl+C

# → worker_process_shutdown 실행
#   ✅ 모든 Connection Pool 닫기
#   ✅ SSH Tunnel 종료
#   ✅ Event Loop 정리
#   (로그) "MySQL connection pools and SSH tunnel closed"