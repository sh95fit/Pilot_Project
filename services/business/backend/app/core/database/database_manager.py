import asyncio
import logging
from typing import Dict, Any, List, Optional
from .mysql_client import mysql_client
from .supabase_data_client import supabase_data_client

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    통합 데이터베이스 매니저
    
    주요 개선사항:
    - 병렬 초기화로 시작 시간 단축
    - 상세한 health_check (각 DB별 상태)
    - Graceful shutdown 지원
    - 재시도 로직 추가 가능
    - 컨텍스트 매니저 지원
    """
    
    def __init__(self):
        self.mysql = mysql_client
        self.supabase_data = supabase_data_client
        self._initialized = False
        self._initializing = False
        self._lock = asyncio.Lock()
    
    async def initialize(self, *, force: bool = False, retry: int = 3) -> None:
        """
        모든 데이터베이스 클라이언트 초기화
        
        Args:
            force: 강제 재초기화
            retry: 재시도 횟수 (default: 3)
        """
        if self._initialized and not force:
            logger.debug("Database manager already initialized")
            return
            
        async with self._lock:
            if self._initializing:
                logger.warning("Initialization already in progress")
                return
            
            self._initializing = True
            
            for attempt in range(retry):
                try:
                    # ✅ 병렬 초기화 (빠른 시작)
                    results = await asyncio.gather(
                        self.mysql.initialize(),
                        self.supabase_data.initialize(),
                        return_exceptions=True
                    )
                    
                    # 실패 확인
                    errors = [r for r in results if isinstance(r, Exception)]
                    if errors:
                        error_msg = "; ".join(str(e) for e in errors)
                        if attempt < retry - 1:
                            logger.warning(f"Initialization attempt {attempt + 1} failed, retrying... ({error_msg})")
                            await asyncio.sleep(2 ** attempt)  # 지수 백오프
                            continue
                        else:
                            raise RuntimeError(f"Database initialization failed after {retry} attempts: {error_msg}")
                    
                    self._initialized = True
                    logger.info("✅ Database manager initialized successfully")
                    break
                    
                except Exception as e:
                    if attempt < retry - 1:
                        logger.warning(f"Initialization attempt {attempt + 1} failed, retrying...")
                        await asyncio.sleep(2 ** attempt)
                    else:
                        logger.error(f"❌ Failed to initialize database manager: {e}")
                        await self._cleanup_on_init_failure()
                        raise
                finally:
                    self._initializing = False

    async def _cleanup_on_init_failure(self) -> None:
        """초기화 실패 시 정리"""
        try:
            await asyncio.gather(
                self.mysql.close(),
                self.supabase_data.close(),
                return_exceptions=True
            )
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def health_check(self, *, detailed: bool = False) -> Dict[str, Any]:
        """
        모든 데이터베이스 연결 상태 확인
        
        Args:
            detailed: 상세 정보 포함 여부
        
        Returns:
            {
                "mysql": True/False,
                "supabase_data": True/False,
                "overall": True/False,
                "timestamp": "2025-09-29 12:00:00"
            }
        """
        if not self._initialized:
            return {
                "mysql": False,
                "supabase_data": False,
                "overall": False,
                "message": "Not initialized"
            }
        
        # ✅ 병렬 헬스체크
        results = await asyncio.gather(
            self.mysql.health_check(),
            self.supabase_data.health_check(),
            return_exceptions=True
        )
        
        mysql_ok = results[0] if not isinstance(results[0], Exception) else False
        supabase_ok = results[1] if not isinstance(results[1], Exception) else False
        
        health_status = {
            "mysql": mysql_ok,
            "supabase_data": supabase_ok,
            "overall": mysql_ok and supabase_ok,
        }
        
        if detailed:
            from datetime import datetime
            health_status["timestamp"] = datetime.now().isoformat()
            health_status["errors"] = {
                "mysql": str(results[0]) if isinstance(results[0], Exception) else None,
                "supabase": str(results[1]) if isinstance(results[1], Exception) else None,
            }
        
        return health_status

    async def close(self) -> None:
        """모든 연결 종료 (Graceful Shutdown)"""
        logger.info("Closing database manager...")
        
        # ✅ 병렬 종료
        await asyncio.gather(
            self.mysql.close(),
            self.supabase_data.close(),
            return_exceptions=True
        )
        
        self._initialized = False
        logger.info("✅ Database manager closed")

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.close()

# 전역 인스턴스
database_manager = DatabaseManager()