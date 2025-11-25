from celery import Celery
from celery.schedules import crontab
from kombu import Queue, Exchange
import logging

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
        # 매일 오후 2시 40 - 미주문 고객사 데이터 업데이트
        "update-not-ordered-cohort": {
            "task": "app.celery_app.tasks.cohort_tasks.update_not_ordered_cohort",
            "schedule": crontab(hour=16, minute=3),
            "options": {"queue": "cohort"}
        },
    
        
        # # 매일 오전 9시 10분 - 서비스 이용 종료 고객사 데이터 업데이트
        # "update-end-of-use-cohort": {
        #     "task": "app.celery_app.tasks.cohort_tasks.update_end_of_use_cohort",
        #     "schedule": crontab(hour=9, minute=10),
        #     "options": {"queue": "cohort"}
        # },
        
        # # 매일 오후 23시 30분 - 활성 고객 데이터 업데이트
        # "update-active-customer-cohort": {
        #     "task": "app.celery_app.tasks.cohort_tasks.update_active_customer_cohort",
        #     "schedule": crontab(hour=23, minute=30),
        #     "options": {"queue": "cohort"}
        # },
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