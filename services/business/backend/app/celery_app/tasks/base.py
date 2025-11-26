"""
모든 Task의 베이스 클래스
DB 클라이언트 초기화 및 비동기 실행 지원
"""
from celery import Task
import logging
import asyncio

from backend.app.core.database.mysql_client import mysql_client
from backend.app.core.database.google_sheets_client import GoogleSheetsClient
from backend.app.core.config import settings


logger = logging.getLogger(__name__)

class DatabaseTask(Task):
    """
    MySQL + Google Sheets 작업을 위한 베이스 Task
    """
    
    _mysql_client = None
    _sheets_client = None
    
    @property
    def mysql(self):
        """MySQL 클라이언트 (지연 초기화)"""
        if self._mysql_client is None:
            self._mysql_client = mysql_client
            logger.info("✅ MySQL client initialized")
        return self._mysql_client
    
    @property
    def sheets(self):
        """Google Sheets 클라이언트 (지연 초기화)"""
        if self._sheets_client is None:
            self._sheets_client = GoogleSheetsClient(
                credentials_json=settings.google_sheets_credentials_sales
            )
            logger.info("✅ Sheets client initialized")
        return self._sheets_client
    
    def run_async(self, coro):
        """동기 환경에서 비동기 코루틴 실행"""
        try:
            loop = asyncio.get_event_loop()
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    