"""
코호트 Task 정의
- DatabaseTask 기반으로 MySQL/Sheets 작업 수행
- 공통 파이프라인 재사용
"""
import logging
import asyncio
from datetime import datetime

from backend.app.celery_app.celery_config import celery_app, get_mysql_pool_stats
from backend.app.celery_app.config import CohortTaskConfig
from backend.app.celery_app.tasks.base import DatabaseTask
from backend.app.celery_app.tasks.utils.data_processor import (
    DataProcessor,
    get_next_business_date
)
from backend.app.celery_app.tasks.utils.sheets_updater import SheetsUpdater
from backend.app.core.database.mysql_client import mysql_client


logger = logging.getLogger(__name__)


# =============================================================================
# 공통 파이프라인
# =============================================================================

def run_cohort_pipeline(
    task_instance: DatabaseTask,
    config: dict,
    target: str = None,
    start_date: str = None,
    end_date: str = None
) -> dict:
    """
    공통 파이프라인: Extract → Transform → Load
    
    Args:
        task_instance: DatabaseTask 인스턴스 (self)
        config: Task 설정 딕셔너리
        target: 타겟 날짜 or 제목 (옵션)
        start_date: 시작 날짜 (옵션)
        end_date: 종료 날짜 (옵션)
        
    Returns:
        실행 결과 딕셔너리
    """
    try:
        # 1. Extract: MySQL 데이터 추출
        # 파라미터 결정
        if config.get("needs_period", False):
            # 기간 조회 모드
            if not start_date or not end_date:
                raise ValueError("needs_period=True requires both start_date and end_date")
            params = (start_date, end_date)
            logger.info(f"📅 Period mode: {start_date} ~ {end_date}")
            
        elif config.get("needs_target_date", False):
            # 단일 날짜 조회 모드
            if not target:
                raise ValueError("needs_target_date=True requires target parameter")
            params = (target,)
            logger.info(f"📅 Single date mode: {target}")
                        
        else:
            # 파라미터 없음
            params = ()
            logger.info(f"📅 No parameter mode")
        
        # MySQL 프로시저 실행
        raw_data = task_instance.run_async(
            task_instance.mysql.execute_procedure(
                config["procedure_name"], 
                params
            )
        )
        
        if not raw_data:
            logger.warning(f"⚠️ No data returned: {config['worksheet_name']}")
            return {"status": "no_data", "count": 0}
        
        logger.info(f"📥 Extracted {len(raw_data)} records from MySQL")
        
        # 2. Transform: 데이터 변환
        sheet_data = DataProcessor.to_sheets_format(raw_data)
        
        # 3. Load: Google Sheets 업데이트
        updater = SheetsUpdater(task_instance.sheets, task_instance.run_async)
        
        # 기존 데이터 초기화
        updater.clear_data_range(
            config["spreadsheet_id"],
            config["worksheet_name"]
        )
        
        # 헤더 업데이트 (필요시)
        if config.get("needs_date_header", False):
            header_range = config.get("header_range", "A2")
            merge_cells = config.get("header_merge_cells", 1)
            
            # 헤더 텍스트 결정
            if config.get("needs_period", False):
                # 기간 모드: "2024-01-01 ~ 2024-01-31" 형식
                header_text = f"{start_date} ~ {end_date}"
            elif config.get("needs_target_date", False):
                # 단일 날짜 모드
                header_text = target
            else:
                # 기타: 현재 날짜
                header_text = datetime.now().strftime("%Y-%m-%d")
            
            updater.update_header(
                config["spreadsheet_id"],
                config["worksheet_name"],
                header_text,
                header_range=header_range,
                merge_cells=merge_cells
            )
        
        # 데이터 삽입
        start_cell = config["start_cell"]
        logger.info(f"📤 Inserting {len(sheet_data)} rows to Sheets")
        
        updater.insert_data(
            config["spreadsheet_id"],
            config["worksheet_name"],
            sheet_data,
            start_cell
        )
        
        logger.info(f"✅ {config['worksheet_name']}: {len(raw_data)} rows updated")
        
        return {
            "status": "success",
            "count": len(raw_data),
            "target": target,
            "start_date": start_date,
            "end_date": end_date,
            "worksheet": config["worksheet_name"],
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed for {config.get('worksheet_name', 'unknown')}: {e}", exc_info=True)
        raise


# =============================================================================
# Cohort Task 정의
# =============================================================================

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
        return run_cohort_pipeline(self, CohortTaskConfig.NOT_ORDERED, target_date)
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
        return run_cohort_pipeline(self, CohortTaskConfig.PENDING_NOT_ORDERED, target_date)
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
        return run_cohort_pipeline(self, CohortTaskConfig.END_OF_USE)
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
        return run_cohort_pipeline(self, CohortTaskConfig.ACTIVE_ACCOUNTS)
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
        return run_cohort_pipeline(self, CohortTaskConfig.INCOMING_LEADS, target)
    except Exception as e:
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="cohort_tasks.update_now_active_accounts_cohort",
    max_retries=3,
    default_retry_delay=300
)    
def update_now_active_accounts_cohort(self, start_date=None, end_date=None):
    """현재 활성 고객 데이터 업데이트"""
    try:
        if start_date is None:
            start_date = "2022-12-01"
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        return run_cohort_pipeline(
            self,
            CohortTaskConfig.NOW_ACTIVE_ACCOUNTS,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as e:
        raise self.retry(exc=e)

@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="cohort_tasks.update_product_sales_summary_cohort",
    max_retries=3,
    default_retry_delay=300
)    
def update_product_sales_summary_cohort(self):
    """일별 상품별 주문 수량 데이터 업데이트"""
    try:
        return run_cohort_pipeline(self, CohortTaskConfig.PRODUCT_SALES_SUMMARY)
    except Exception as e:
        raise self.retry(exc=e)

@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="cohort_tasks.update_account_orders_summary_cohort",
    max_retries=3,
    default_retry_delay=300
)    
def update_account_orders_summary_cohort(self):
    """고객사별 주문 현황 데이터 업데이트"""
    try:
        return run_cohort_pipeline(self, CohortTaskConfig.ACCOUNT_ORDERS_SUMMARY)
    except Exception as e:
        raise self.retry(exc=e)
    
    
@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="cohort_tasks.update_trial_accounts_cohort",
    max_retries=3,
    default_retry_delay=300
)    
def update_trial_accounts_cohort(self):
    """체험 고객사 데이터 업데이트"""
    try:
        return run_cohort_pipeline(self, CohortTaskConfig.TRIAL_ACCOUNTS)
    except Exception as e:
        raise self.retry(exc=e)
    
@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="cohort_tasks.update_lead_applications_cohort",
    max_retries=3,
    default_retry_delay=300
)    
def update_lead_applications_cohort(self):
    """고객유입리드 데이터 업데이트"""
    try:
        return run_cohort_pipeline(self, CohortTaskConfig.LEAD_APPLICATIONS)
    except Exception as e:
        raise self.retry(exc=e)
    
@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="cohort_tasks.update_active_accounts_history_cohort",
    max_retries=3,
    default_retry_delay=300
)    
def update_active_accounts_history_cohort(self, start_date=None, end_date=None):
    """활성 고객 히스토리 데이터 업데이트"""
    try:
        if start_date is None:
            start_date = "2022-12-01"
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
            
        return run_cohort_pipeline(
            self, 
            CohortTaskConfig.ACTIVE_ACCOUNTS_HISTORY,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as e:
        raise self.retry(exc=e)
    
@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="cohort_tasks.update_latest_trial_orders_cohort",
    max_retries=3,
    default_retry_delay=300
)      
def update_latest_trial_orders_cohort(self):
    """체험 주문 수량 현황 업데이트"""
    try:
        return run_cohort_pipeline(self, CohortTaskConfig.LATEST_TRIAL_ORDERS)
    except Exception as e:
        raise self.retry(exc=e)
   
   
# JANDI ALERT TASKS
@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="cohort_tasks.update_jandi_alert_data",
    max_retries=3,
    default_retry_delay=300
)
def update_jandi_alert_data(self):
    """잔디 알림용 데이터 일괄 업데이트 (신규유입/체험/구독전환/이탈)"""
    try:
        results = []

        for config in CohortTaskConfig.JANDI_ALERT_GROUP:
            result = run_cohort_pipeline(self, config)
            results.append({
                "worksheet": config["worksheet_name"],
                "status": result.get("status"),
                "count": result.get("count", 0)
            })
            logger.info(
                f"✅ {config['worksheet_name']}: "
                f"{result.get('count', 0)}건 업데이트"
            )

        total = sum(r["count"] for r in results)
        logger.info(f"✅ 잔디 알림 데이터 일괄 업데이트 완료 (총 {total}건)")

        return {
            "status": "success",
            "results": results,
            "total_count": total,
            "updated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ 잔디 알림 데이터 업데이트 실패: {e}", exc_info=True)
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



# =============================================================================
# MySQL 연결 모니터링 Task
# =============================================================================

@celery_app.task(
    bind=True,
    name="cohort_tasks.monitor_mysql_health",
    max_retries=0
)
def monitor_mysql_health(self):
    """
    MySQL 연결 상태 및 Pool 사용률 모니터링
    - SSH Tunnel 상태 확인
    - Connection Pool 사용률 확인
    - 80% 이상 사용 시 경고
    """
    
    async def _async_monitor():
        """비동기 모니터링 로직"""
        try:
            # 1. Pool 통계 수집
            stats = get_mysql_pool_stats()
            
            # 2. SSH 터널 상태 확인
            ssh_status = stats.get("ssh_tunnel", {})
            if not ssh_status.get("active"):
                logger.error("❌ SSH Tunnel is NOT active!")
                return {"status": "error", "message": "SSH tunnel inactive"}
            
            logger.info(f"✅ SSH Tunnel active on port {ssh_status.get('local_port')}")
            
            # 3. 각 Pool 상태 확인
            pool_warnings = []
            pools_data = stats.get("pools", {})
            
            for db_name, pool_stats in pools_data.items():
                usage = pool_stats.get("usage_percent", 0)
                logger.info(
                    f"📊 Pool [{db_name}] - "
                    f"Size: {pool_stats['size']}/{pool_stats['maxsize']}, "
                    f"Free: {pool_stats['freesize']}, "
                    f"In-use: {pool_stats['in_use']}, "
                    f"Usage: {usage}%"
                )
                
                # 사용률 80% 이상 시 경고
                if usage >= 80:
                    warning_msg = (
                        f"High connection usage for {db_name}: {usage}%! "
                        f"Consider increasing maxsize or checking for connection leaks."
                    )
                    logger.warning(f"⚠️ {warning_msg}")
                    pool_warnings.append(warning_msg)
            
            # 4. Health check 수행
            is_healthy = await mysql_client.health_check()
            
            if not is_healthy:
                logger.error("❌ MySQL health check failed!")
                return {
                    "status": "unhealthy",
                    "ssh_tunnel": ssh_status,
                    "pools": pools_data,
                    "warnings": pool_warnings
                }
            
            logger.info("✅ MySQL health check passed")
            return {
                "status": "healthy",
                "ssh_tunnel": ssh_status,
                "pools": pools_data,
                "warnings": pool_warnings
            }
        
        except Exception as e:
            logger.error(f"❌ Error in MySQL monitoring: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
    
    # 메인 실행 로직
    try:
        # Event loop 안전하게 가져오기
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 비동기 모니터링 실행
        result = loop.run_until_complete(_async_monitor())
        return result
    
    except Exception as e:
        logger.error(f"❌ Failed to execute monitoring task: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}