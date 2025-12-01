"""
코호트 Task 정의
각 Task는 설정을 가져와 파이프라인을 조립하는 역할만 수행
"""
import logging
from datetime import datetime

from backend.app.celery_app.celery_config import celery_app
from backend.app.celery_app.config import CohortTaskConfig
from backend.app.celery_app.tasks.base import DatabaseTask
from backend.app.celery_app.tasks.utils.data_processor import (
    DataProcessor,
    get_next_business_date
)
from backend.app.celery_app.tasks.utils.sheets_updater import SheetsUpdater

logger = logging.getLogger(__name__)


def run_cohort_pipeline(
    task_instance: DatabaseTask,
    config: dict,
    target: str = None
) -> dict:
    """
    공통 파이프라인: Extract → Transform → Load
    
    Args:
        task_instance: Task 인스턴스 (self)
        config: Task 설정 딕셔너리
        target: 타겟 날짜 or 제목 (옵션)
        
    Returns:
        실행 결과 딕셔너리
    """
    try:
        # 1. Extract: MySQL 데이터 추출
        params = (target,) if config["needs_target_date"] and target else ()
        raw_data = task_instance.run_async(
            task_instance.mysql.execute_procedure(
                config["procedure_name"], params
            )
        )
        
        if not raw_data:
            logger.warning(f"⚠️ No data: {config['worksheet_name']}")
            return {"status": "no_data", "count": 0}
        
        logger.info(f"📥 Extracted {len(raw_data)} records from MySQL")
        
        # 2. Transform: 데이터 변환
        sheet_data = DataProcessor.to_sheets_format(raw_data)
        
        # 3. Load: Sheets 업데이트
        updater = SheetsUpdater(task_instance.sheets, task_instance.run_async)
        
        # 기존 데이터 초기화
        updater.clear_data_range(
            config["spreadsheet_id"],
            config["worksheet_name"]
        )
        
        # 날짜 행 포함 업데이트 (필요시)
        if config["needs_date_header"] and target:
            header_range = config.get("header_range", "A2")
            merge_cells = config.get("header_merge_cells", 1)
            
            updater.update_header(
                config["spreadsheet_id"],
                config["worksheet_name"],
                target,
                header_range=header_range,
                merge_cells=merge_cells
            )
        
        # 데이터 삽입
        start_cell = config["start_cell"]
        
        logger.info(f"📤 Inserting {len(sheet_data)} rows (header + {len(sheet_data)-1} data rows)")
        updater.insert_data(
            config["spreadsheet_id"],
            config["worksheet_name"],
            sheet_data,
            start_cell
        )
        
        logger.info(f"✅ {config['worksheet_name']}: {len(raw_data)} rows")
        
        return {
            "status": "success",
            "count": len(raw_data),
            "target": target,
            "worksheet": config["worksheet_name"],
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
        raise


# ============================================
# Task 정의 (설정만 조립)
# ============================================

@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="cohort_tasks.update_not_ordered_cohort",
    max_retries=3,
    default_retry_delay=300
)
def update_not_ordered_cohort(self):
    """미주문 고객사 업데이트"""
    try:
        target_date = get_next_business_date()
        return run_cohort_pipeline(
            self, 
            CohortTaskConfig.NOT_ORDERED, 
            target_date
        )
    except Exception as e:
        raise self.retry(exc=e)

@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="cohort_tasks.update_pending_not_ordered_cohort",
    max_retries=3,
    default_retry_delay=300
)
def update_pending_not_ordered_cohort(self):
    """오후 2시 미주문 고객사 업데이트"""
    try:
        target_date = get_next_business_date()
        return run_cohort_pipeline(
            self, 
            CohortTaskConfig.PENDING_NOT_ORDERED, 
            target_date
        )
    except Exception as e:
        raise self.retry(exc=e)
    
@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="cohort_tasks.update_end_of_use_cohort",
    max_retries=3,
    default_retry_delay=300
)    
def update_end_of_use_cohort(self):
    """서비스 이용 종료(이탈) 고객사 업데이트"""
    try:
        return run_cohort_pipeline(
            self,
            CohortTaskConfig.END_OF_USE,
        )
    except Exception as e:
        raise self.retry(exc=e)    

@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="cohort_tasks.update_active_accounts_cohort",
    max_retries=3,
    default_retry_delay=300
)    
def update_active_accounts_cohort(self):
    """활성 고객 데이터 업데이트"""
    try:
        return run_cohort_pipeline(
            self,
            CohortTaskConfig.ACTIVE_ACCOUNTS,
        )
    except Exception as e:
        raise self.retry(exc=e)        
    
@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="cohort_tasks.update_incoming_leads_cohort",
    max_retries=3,
    default_retry_delay=300
)    
def update_incoming_leads_cohort(self):
    """어드민 유입 리드 업데이트"""
    try:
        target = "어드민 유입 수"
        return run_cohort_pipeline(
            self,
            CohortTaskConfig.INCOMING_LEADS,
            target
        )
    except Exception as e:
        raise self.retry(exc=e)        
        

    
    
# ============================================
# 새 Task 추가 가이드
# ============================================
"""
1. config.py에 설정 추가:
   class CohortTaskConfig:
       NEW_TASK = {
           "spreadsheet_id": ...,
           "worksheet_name": ...,
           "procedure_name": ...,
           "needs_target_date": True/False,
           "needs_date_header": True/False,
       }

2. cohort_tasks.py에 Task 함수 추가:
   @celery_app.task(bind=True, base=DatabaseTask, name="cohort_tasks.new_task")
   def update_new_cohort(self):
       try:
           target_date = get_next_business_date()  # 필요시
           return run_cohort_pipeline(self, CohortTaskConfig.NEW_TASK, target_date)
       except Exception as e:
           raise self.retry(exc=e)

3. celery_config.py에 스케줄 추가:
   beat_schedule = {
       "update-new-cohort": {
           "task": "cohort_tasks.update_new_cohort",
           "schedule": crontab(...),
           "options": {"queue": "cohort"}
       }
   }

끝! 파이프라인 로직은 재사용
"""