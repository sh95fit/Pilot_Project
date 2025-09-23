import asyncio
import logging
from typing import Dict, Any, List, Optional
from .mysql_client import mysql_client
from .supabase_data_client import supabase_data_client

logger = logging.getLogger(__name__)

class DatabaseManager:
    """통합 데이터베이스 매니저"""
    
    def __init__(self):
        self.mysql = mysql_client
        self.supabase_data = supabase_data_client
        self._initialized = False
    
    async def initialize(self) -> None:
        """모든 데이터베이스 클라이언트 초기화"""
        if self._initialized:
            logger.info("Database manager already initialized")
            return
            
        try:
            await asyncio.gather(
                self.mysql.initialize(),
                self.supabase_data.initialize(),
                return_exceptions=True
            )
            
            self._initialized = True
            logger.info("✅ Database manager initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database manager: {e}")
            raise
    
    async def health_check(self) -> Dict[str, bool]:
        """모든 데이터베이스 연결 상태 확인"""
        results = {}
        
        try:
            results["mysql"] = await self.mysql.health_check()
        except Exception as e:
            logger.error(f"MySQL health check failed: {e}")
            results["mysql"] = False
        
        try:
            results["supabase_data"] = await self.supabase_data.health_check()
        except Exception as e:
            logger.error(f"Supabase data health check failed: {e}")
            results["supabase_data"] = False
        
        return results

    async def close(self) -> None:
        """모든 연결 종료"""
        await self.mysql.close()
        self._initialized = False
        logger.info("Database manager closed")

# 전역 인스턴스
database_manager = DatabaseManager()