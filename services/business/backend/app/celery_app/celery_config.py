from celery import Celery
from celery.schedules import crontab
from kombu import Queue, Exchange
import logging
from datetime import timedelta

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# Celery 앱 생성
celery_app = Celery(
    "business_tasks",
    broker=settings.celery_broker_url,
    backend=None,
    include=[
        "app.celery_app.tasks.cohort_tasks",
    ]
)

# Celery 설정
celery_app.conf.update(
    # 타임존 설정
    timezone="Asia/Seoul",
    enable_utc=True,
    
    # 태스크 설정
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_expires=3600,  # 1시간 후 결과 삭제

    # Worker 설정
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # 재시도 설정
    task_default_retry_delay=60,  # 60초
    task_max_retries=3,
    
    
    # Beat 스케줄러 설정
    beat_schedule={
        # 매일 오후 2시 35 - 미주문 고객사 데이터 업데이트
        "update-not-ordered-cohort": {
            "task": "cohort_tasks.update_not_ordered_cohort",
            "schedule": crontab(hour=14, minute=35, day_of_week="1-5"),
            "options": {"queue": "cohort"}
        },
        
        # 매일 오전 9시 ~ 오후 13시 30분 사이 30분마다 - 미주문 고객사 데이터 업데이트
        "update-pending-not-ordered-cohort": {
            "task": "cohort_tasks.update_pending_not_ordered_cohort",
            'schedule': crontab(minute='0,30', hour='9-14', day_of_week="1-5"),
            "options": {"queue": "cohort"}
        },
    
        # 정각 마다 실행(9시~20시 사이) - 서비스 이용 종료 고객사 데이터 업데이트
        "update-end-of-use-cohort": {
            "task": "cohort_tasks.update_end_of_use_cohort",
            "schedule": crontab(minute=0, hour="9-20"),
            "options": {"queue": "cohort"}
        },
        
        # 매일 오후 23시 40분 - 활성 고객 데이터 업데이트
        "update-active-customer-cohort": {
            "task": "cohort_tasks.update_active_accounts_cohort",
            "schedule": crontab(hour=23, minute=40),
            "options": {"queue": "cohort"}
        },
        
        # 정각 마다 실행(9시~20시 사이) - 어드민 유입 고객 데이터 업데이트
        "update-incoming-leads-cohort": {
            "task": "cohort_tasks.update_incoming_leads_cohort",
            "schedule": crontab(minute=0, hour="9-20"),
            "options": {"queue": "cohort"}
        },
        
        # 정각 마다 실행(9시~20시 사이) - 현재 활성 고객 데이터 업데이트
        "update-now-active-accounts-cohort": {
            "task": "cohort_tasks.update_now_active_accounts_cohort",
            'schedule': crontab(minute='0,30', hour='9-20', day_of_week="1-5"),
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