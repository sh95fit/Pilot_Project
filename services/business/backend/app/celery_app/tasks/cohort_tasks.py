import asyncio
from celery import Task
from typing import List, Dict, Any
import logging
from datetime import datetime, date, timedelta

from backend.app.celery_app.celery_config import celery_app
from backend.app.core.database.mysql_client import mysql_client
from backend.app.core.database.google_sheets_client import GoogleSheetsClient
from backend.app.core.config import settings


logger = logging.getLogger(__name__)

class DatabaseTask(Task):
    """데이터베이스 연결을 관리하는 기본 태스크"""
    _mysql_initialized = False
    _sheets_client = None
    
    def __call__(self, *args, **kwargs):
        """태스크 실행 전 DB 초기화"""
        if not self._mysql_initialized:
            import asyncio
            loop = asyncio.get_event_loop()
            loop.run_until_complete(mysql_client.initialize())
            self._mysql_initialized = True
            logger.info("MySQL client initialized for Celery task")
        
        if not self._sheets_client:
            self._sheets_client = GoogleSheetsClient(
                credentials_json=settings.google_sheets_credentials_sales
            )
            logger.info("Google Sheets client initialized for Celery task")
        
        return self.run(*args, **kwargs)    
    
    @staticmethod
    def process_mysql_data(raw_data: List[Dict[str, Any]]) -> List[List[Any]]:
        """
        MySQL 데이터를 Google Sheets 형식으로 변환
        - datetime/date 타입은 문자열로 변환
        
        Args:
            raw_data: MySQL에서 가져온 원본 데이터
        
        Returns:
            List[List[Any]]: Google Sheets에 삽입할 2차원 배열
        """
        if not raw_data:
            return []
        
        # 헤더 생성 (첫 번째 행)
        headers = list(raw_data[0].keys())
        
        # 데이터 행 생성
        rows = [headers]
        for record in raw_data:
            row = []
            for key in headers:
                value = record.get(key, "")
                # date/datetime 타입 직렬화
                if isinstance(value, (date, datetime)):
                    value = value.strftime("%Y-%m-%d")
                row.append(value)
            rows.append(row)
        
        return rows


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.celery_app.tasks.cohort_tasks.update_not_ordered_cohort",
    max_retries=3,
    default_retry_delay=300  # 5분
)
def update_not_ordered_cohort(self):
    """미주문 고객사 코호트 데이터 업데이트"""
    
    try:
        logger.info("Starting NOT ORDERED cohort update task")
        
        loop = asyncio.get_event_loop()
        
        now = datetime.now()
        
        # 금요일(weekday=4) -> +3일(월요일), 토요일(weekday=5) -> +2일(월요일), 그 외는 +1일
        if now.weekday() == 4:  # 금요일
            days_to_add = 3
            logger.info("Friday detected - targeting Monday")
        elif now.weekday() == 5:  # 토요일
            days_to_add = 2
            logger.info("Saturday detected - targeting Monday")
        else:
            days_to_add = 1
            logger.info("Weekday detected - targeting next day")
        
        # 스케줄러 기준 익일 날짜
        target_date = (now + timedelta(days=days_to_add)).strftime("%Y-%m-%d")
        
        raw_data = loop.run_until_complete(
            mysql_client.execute_procedure(
                proc_name="get_daily_not_order_accounts",
                params=(target_date,)
            )
        )
        
        if not raw_data:
            logger.warning("No data found for NOT ORDERED cohort")
            return {"status": "no_data", "count": 0}
        
        # 데이터 가공 (date 직렬화 적용)
        sheet_data = self.process_mysql_data(raw_data)
        
        # Google Sheets 업데이트
        worksheet_name = "자동화_미주문고객사"
        spreadsheet_id = settings.google_sheet_id_cohort
 
        # 1. 워크시트 정보 조회 (전체 행/열 수 확인)
        worksheet_info = loop.run_until_complete(
            self._sheets_client.get_worksheet_info(
                spreadsheet_id=spreadsheet_id,
                worksheet_name=worksheet_name
            )
        )        
        
        total_rows = worksheet_info['row_count']
        total_cols = worksheet_info['col_count']
        
        logger.info(f"Worksheet info - rows: {total_rows}, cols: {total_cols}")

        # 2. 현재 시트의 데이터 범위 확인
        existing_data = loop.run_until_complete(
            self._sheets_client.get_range_data(
                spreadsheet_id=spreadsheet_id,
                worksheet_name=worksheet_name,
                cell_range=f"A3:{chr(64 + min(total_cols, 26))}{total_rows}"
            )
        )
        
        # 3. 기존 데이터가 있다면 삭제
        if existing_data and len(existing_data) > 0:
            max_rows = len(existing_data)
            # 실제 데이터의 최대 컬럼 수 확인
            max_columns = max(len(row) for row in existing_data) if existing_data else len(sheet_data[0])
            empty_data = [[""] * max_columns for _ in range(max_rows)]
            
            loop.run_until_complete(
                self._sheets_client.update_range(
                    spreadsheet_id=spreadsheet_id,
                    worksheet_name=worksheet_name,
                    cell_range="A3",
                    values=empty_data,
                    value_input_option="USER_ENTERED"
                )
            )
            logger.info(f"Cleared {max_rows} rows x {max_columns} columns from A3")
            
        # 3. A2:E2 병합셀에 target_date 입력
        loop.run_until_complete(
            self._sheets_client.update_range(
                spreadsheet_id=spreadsheet_id,
                worksheet_name=worksheet_name,
                cell_range="A2",
                values=[[target_date]*5],  # A2:E2 병합셀에 동일 값 입력
                value_input_option="USER_ENTERED"
            )
        )
        
        # 4. 새로운 데이터 입력 (A3부터)
        result = loop.run_until_complete(
            self._sheets_client.update_range(
                spreadsheet_id=spreadsheet_id,
                worksheet_name=worksheet_name,
                cell_range="A3",
                values=sheet_data,
                value_input_option="USER_ENTERED"
            )
        )        
        
        logger.info(f"✅ NOT ORDERED cohort updated: {len(raw_data)} rows")
        
        return {
            "status": "success",
            "count": len(raw_data),
            "updated_at": datetime.now().isoformat(),
            "worksheet": worksheet_name
        }
        
    except Exception as e:
        logger.error(f"Failed to update NOT ORDERED cohort: {e}")
        raise self.retry(exc=e)



# @celery_app.task(
#     bind=True,
#     base=DatabaseTask,
#     name="app.celery_app.tasks.cohort_tasks.update_end_of_use_cohort",
#     max_retries=3,
#     default_retry_delay=300
# )
# def update_end_of_use_cohort(self):
#     """서비스 이용 종료 고객사 코호트 데이터 업데이트"""
#     import asyncio
    
#     try:
#         logger.info("Starting END OF USE cohort update task")
        
#         # 프로시저 호출 예시 (실제 프로시저명으로 변경 필요)
#         proc_name = "sp_get_end_of_use_cohort"
#         params = (datetime.now().strftime("%Y-%m-%d"),)
        
#         loop = asyncio.get_event_loop()
#         raw_data = loop.run_until_complete(
#             mysql_client.execute_procedure(proc_name, params)
#         )
        
#         if not raw_data:
#             logger.warning("No data found for END OF USE cohort")
#             return {"status": "no_data", "count": 0}
        
#         # 데이터 가공
#         sheet_data = process_mysql_data(raw_data)
        
#         # Google Sheets 업데이트
#         worksheet_name = "자동화_서비스이용종료"
#         spreadsheet_id = settings.google_sheet_id_sales
        
#         result = loop.run_until_complete(
#             self._sheets_client.update_range(
#                 spreadsheet_id=spreadsheet_id,
#                 worksheet_name=worksheet_name,
#                 cell_range="A1",
#                 values=sheet_data
#             )
#         )
        
#         logger.info(f"✅ END OF USE cohort updated: {len(raw_data)} rows")
        
#         return {
#             "status": "success",
#             "count": len(raw_data),
#             "updated_at": datetime.now().isoformat(),
#             "worksheet": worksheet_name
#         }
        
#     except Exception as e:
#         logger.error(f"Failed to update END OF USE cohort: {e}")
#         raise self.retry(exc=e)
    
    
# @celery_app.task(
#     bind=True,
#     base=DatabaseTask,
#     name="app.celery_app.tasks.cohort_tasks.update_active_customer_cohort",
#     max_retries=3,
#     default_retry_delay=300
# )
# def update_active_customer_cohort(self):
#     """활성 고객 코호트 데이터 업데이트"""
#     import asyncio
    
#     try:
#         logger.info("Starting ACTIVE CUSTOMER cohort update task")
        
#         # 복잡한 쿼리 예시
#         query = """
#             SELECT 
#                 c.company_id,
#                 c.company_name,
#                 c.industry,
#                 c.employee_count,
#                 o.last_order_date,
#                 o.monthly_avg_amount,
#                 o.total_orders,
#                 CASE 
#                     WHEN o.monthly_avg_amount >= 1000000 THEN 'VIP'
#                     WHEN o.monthly_avg_amount >= 500000 THEN 'GOLD'
#                     ELSE 'STANDARD'
#                 END as customer_grade
#             FROM companies c
#             INNER JOIN order_summary o ON c.company_id = o.company_id
#             WHERE c.is_active = TRUE
#             AND o.last_order_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
#             ORDER BY o.monthly_avg_amount DESC
#         """
        
#         loop = asyncio.get_event_loop()
#         raw_data = loop.run_until_complete(
#             mysql_client.execute_query(query)
#         )
        
#         if not raw_data:
#             logger.warning("No data found for ACTIVE CUSTOMER cohort")
#             return {"status": "no_data", "count": 0}
        
#         # 데이터 가공 (추가 계산 포함)
#         sheet_data = process_mysql_data(raw_data)
        
#         # Google Sheets 업데이트
#         worksheet_name = "자동화_활성고객_DB"
#         spreadsheet_id = settings.google_sheet_id_sales
        
#         result = loop.run_until_complete(
#             self._sheets_client.update_range(
#                 spreadsheet_id=spreadsheet_id,
#                 worksheet_name=worksheet_name,
#                 cell_range="A1",
#                 values=sheet_data
#             )
#         )
        
#         logger.info(f"✅ ACTIVE CUSTOMER cohort updated: {len(raw_data)} rows")
        
#         return {
#             "status": "success",
#             "count": len(raw_data),
#             "updated_at": datetime.now().isoformat(),
#             "worksheet": worksheet_name
#         }
        
#     except Exception as e:
#         logger.error(f"Failed to update ACTIVE CUSTOMER cohort: {e}")
#         raise self.retry(exc=e)    