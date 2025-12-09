"""
모든 Task의 베이스 클래스
DB 클라이언트 초기화 및 비동기 실행 지원
"""
from celery import Task
import logging
import asyncio
from typing import Any, Coroutine

from backend.app.core.database.mysql_client import mysql_client
from backend.app.core.database.google_sheets_client import GoogleSheetsClient
from backend.app.core.config import settings


logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """
    MySQL + Google Sheets 작업을 위한 베이스 Task
    
    특징:
    - MySQL 클라이언트는 전역 인스턴스 사용 (worker_process_init에서 초기화됨)
    - Google Sheets 클라이언트는 Task 인스턴스별로 lazy 초기화
    - 안전한 비동기 실행 지원
    """
    
    # Google Sheets 클라이언트만 인스턴스별 관리
    _sheets_client = None
    
    @property
    def mysql(self):
        """
        MySQL 클라이언트 (전역 싱글톤 사용)
        
        이미 worker_process_init에서 초기화되었으므로
        여기서는 전역 인스턴스를 그대로 반환
        """
        # 연결 상태 확인 (선택적)
        if not mysql_client._initialized:
            logger.warning("⚠️ MySQL client not initialized, this should not happen!")
            # Task prerun signal에서 자동 재연결 시도할 것
        
        return mysql_client
    
    @property
    def sheets(self):
        """
        Google Sheets 클라이언트 (인스턴스별 Lazy 초기화)
        
        각 Task 인스턴스마다 독립적인 Sheets 클라이언트 생성
        """
        if self._sheets_client is None:
            try:
                self._sheets_client = GoogleSheetsClient(
                    credentials_json=settings.google_sheets_credentials_sales
                )
                logger.debug("✅ Google Sheets client initialized for task")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Sheets client: {e}")
                raise
        
        return self._sheets_client
    
    def run_async(self, coro: Coroutine) -> Any:
        """
        동기 환경에서 비동기 코루틴 안전하게 실행
        
        Args:
            coro: 실행할 코루틴 객체
            
        Returns:
            코루틴 실행 결과
            
        Raises:
            Exception: 코루틴 실행 중 발생한 예외
        """
        try:
            # 기존 event loop 가져오기 시도
            loop = asyncio.get_event_loop()
            
            # Loop가 닫혀있으면 새로 생성
            if loop.is_closed():
                logger.debug("Event loop is closed, creating new loop")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
        except RuntimeError as e:
            # Event loop가 없는 경우 (드문 케이스)
            logger.debug(f"No event loop found ({e}), creating new loop")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            # 코루틴 실행
            return loop.run_until_complete(coro)
            
        except Exception as e:
            logger.error(f"❌ Error executing async coroutine: {e}", exc_info=True)
            raise
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Task 실패 시 정리 작업
        
        Sheets 클라이언트 리소스 정리 (있다면)
        MySQL은 전역 관리되므로 여기서 처리하지 않음
        """
        try:
            if self._sheets_client:
                logger.debug("Cleaning up Sheets client after task failure")
                self._sheets_client = None
        except Exception as e:
            logger.error(f"Error in on_failure cleanup: {e}")
        
        # 부모 클래스의 on_failure 호출
        super().on_failure(exc, task_id, args, kwargs, einfo)
    
    def on_success(self, retval, task_id, args, kwargs):
        """
        Task 성공 시 정리 작업 (선택적)
        """
        # Sheets 클라이언트는 재사용 가능하므로 유지
        # 필요시 여기서 정리 가능
        super().on_success(retval, task_id, args, kwargs)
    
    def __call__(self, *args, **kwargs):
        """
        Task 실행 전 추가 검증 (선택적)
        """
        try:
            # MySQL 연결 상태 간단 체크 (task_prerun signal에서도 체크하지만 이중 안전장치)
            if not mysql_client._initialized:
                logger.warning("⚠️ MySQL client not initialized at task call time")
            
            # Task 실행
            return super().__call__(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"❌ Error in task call: {e}", exc_info=True)
            raise


# # =============================================================================
# # 선택적: MySQL 연결 보장 데코레이터
# # =============================================================================

# def ensure_mysql_connection(func):
#     """
#     데코레이터: Task 함수 실행 전 MySQL 연결 보장
    
#     Usage:
#         @celery_app.task(bind=True, base=DatabaseTask)
#         @ensure_mysql_connection
#         def my_task(self):
#             ...
#     """
#     async def _check_and_reconnect():
#         """연결 확인 및 재연결"""
#         if not mysql_client._initialized or not await mysql_client.health_check():
#             logger.warning("MySQL not healthy, attempting reconnection...")
#             await mysql_client._ensure_connection()
    
#     def wrapper(self, *args, **kwargs):
#         try:
#             # 연결 확인 및 재연결 시도
#             loop = asyncio.get_event_loop()
#             loop.run_until_complete(_check_and_reconnect())
            
#             # 원래 함수 실행
#             return func(self, *args, **kwargs)
            
#         except Exception as e:
#             logger.error(f"❌ Error in ensure_mysql_connection: {e}")
#             raise
    
#     return wrapper


# # =============================================================================
# # 선택적: 재시도 가능한 DatabaseTask
# # =============================================================================

# class RetryableDatabaseTask(DatabaseTask):
#     """
#     자동 재시도 기능이 강화된 DatabaseTask
    
#     MySQL 연결 에러 발생 시 자동으로 재시도
#     """
    
#     autoretry_for = (ConnectionError, TimeoutError)
#     retry_kwargs = {'max_retries': 3, 'countdown': 5}
#     retry_backoff = True
#     retry_backoff_max = 600  # 10분
#     retry_jitter = True
    
#     def on_retry(self, exc, task_id, args, kwargs, einfo):
#         """재시도 시 로깅"""
#         logger.warning(
#             f"🔄 Task {self.name} retrying due to {exc.__class__.__name__}: {exc}"
#         )
#         super().on_retry(exc, task_id, args, kwargs, einfo)