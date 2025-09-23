import logging
from typing import Optional, Dict, Any, List, Union
from supabase import create_client, Client
from ..config import settings

logger = logging.getLogger(__name__)

class SupabaseDataClient:
    """
    Supabase 데이터 DB 클라이언트 (조회용)
    """
    def __init__(self):
        self.client: Optional[Client] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Supabase 클라이언트 초기화
        """
        if self._initialized:
            logger.info("Supabase data client already initialized")
            return
            
        try:
            self.client = create_client(
                settings.supabase_data_url, 
                settings.supabase_data_service_key
            )
            self._initialized = True
            logger.info("✅ Supabase data client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase data client: {e}")
            raise

    def _ensure_initialized(self):
        """
        초기화 상태 확인
        """
        if not self._initialized or not self.client:
            raise RuntimeError("Supabase data client not initialized")

    async def select(
        self, 
        table: str, 
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        데이터 조회
        """
        if not self._initialized:
            await self.initialize()
        
        self._ensure_initialized()
        
        try:
            query = self.client.table(table).select(columns)
            
            # 필터 적용
            if filters:
                for column, value in filters.items():
                    if isinstance(value, dict):
                        # 복합 조건 처리 (예: {"gte": 10}, {"like": "%text%"})
                        for operator, filter_value in value.items():
                            if operator == "eq":
                                query = query.eq(column, filter_value)
                            elif operator == "neq":
                                query = query.neq(column, filter_value)
                            elif operator == "gt":
                                query = query.gt(column, filter_value)
                            elif operator == "gte":
                                query = query.gte(column, filter_value)
                            elif operator == "lt":
                                query = query.lt(column, filter_value)
                            elif operator == "lte":
                                query = query.lte(column, filter_value)
                            elif operator == "like":
                                query = query.like(column, filter_value)
                            elif operator == "ilike":
                                query = query.ilike(column, filter_value)
                            elif operator == "in":
                                query = query.in_(column, filter_value)
                            elif operator == "is":
                                query = query.is_(column, filter_value)
                    else:
                        # 단순 조건 (기본적으로 eq)
                        query = query.eq(column, value)
            
            # 정렬
            if order_by:
                if order_by.startswith("-"):
                    query = query.order(order_by[1:], desc=True)
                else:
                    query = query.order(order_by)
            
            # 페이징
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
            
            response = query.execute()
            return response.data
            
        except Exception as e:
            logger.error(f"Supabase select error: {e}")
            raise

    async def rpc(
        self, 
        function_name: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Supabase RPC 함수 호출
        """
        if not self._initialized:
            await self.initialize()
        
        self._ensure_initialized()
        
        try:
            response = self.client.rpc(function_name, params or {}).execute()
            return response.data
        except Exception as e:
            logger.error(f"Supabase RPC error: {e}")
            raise

    async def health_check(self) -> bool:
        """
        연결 상태 확인
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # 간단한 쿼리로 연결 확인
            self.client.table("information_schema.tables").select("*").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase data health check failed: {e}")
            return False

# 전역 인스턴스
supabase_data_client = SupabaseDataClient()