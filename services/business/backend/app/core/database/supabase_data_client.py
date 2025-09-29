import logging
from typing import Optional, Dict, Any, List, Union
# from supabase import create_client, Client
from supabase import acreate_client, AsyncClient
from postgrest.exceptions import APIError
from ..config import settings

logger = logging.getLogger(__name__)

class SupabaseDataClient:
    """
    Supabase 비동기 데이터 DB 클라이언트 (조회 및 RPC 실행용)
    
    주요 개선사항:
    - acreate_client()로 완전 비동기 처리
    - 동시 초기화 방지 로직 추가
    - 다중 정렬 및 확장된 필터 연산자 지원
    - count() 메서드 추가
    - 컨텍스트 매니저 지원 (async with)
    - 명확한 에러 핸들링
    """
    def __init__(self):
        self.client: Optional[AsyncClient] = None
        self._initialized = False
        self._initializing = False  # 동시 초기화 방지
    
    async def initialize(self) -> None:
        """
        Supabase 비동기 클라이언트 초기화
        """
        if self._initialized:
            logger.info("Supabase data client already initialized")
            return

        # 동시 초기화 방지
        if self._initializing:
            while self._initializing:
                await asyncio.sleep(0.1)
            return
            
        self._initializing = True
            
        try:
            # ✅ acreate_client로 비동기 클라이언트 생성
            self.client = await acreate_client(
                settings.supabase_data_url, 
                settings.supabase_data_service_key
            )
            self._initialized = True
            logger.info("✅ Supabase async client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            raise
        finally:
            self._initializing = False
            
    def _ensure_initialized(self) -> None:
        """초기화 상태 확인"""
        if not self._initialized or not self.client:
            raise RuntimeError(
                "Supabase client not initialized. Call 'await initialize()' first."
            )
            
    async def select(
        self, 
        table: str, 
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[Union[str, List[str]]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        single: bool = False
    ) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
        """
        데이터 조회
        
        Args:
            table: 테이블 명
            columns: 조회할 컬럼 (default: "*")
            filters: 필터 조건 dict
            order_by: 정렬 (str or list, "-"로 내림차순)
            limit: 조회 개수 제한
            offset: 오프셋
            single: True면 단일 객체 반환
        
        Example:
            # 복합 필터 + 다중 정렬
            await client.select(
                "users",
                filters={
                    "age": {"gte": 18},
                    "status": "active",
                    "city": {"in": ["Seoul", "Busan"]}
                },
                order_by=["-created_at", "name"],
                limit=10
            )
        """
        if not self._initialized:
            await self.initialize()
        
        self._ensure_initialized()
        
        try:
            query = self.client.table(table).select(columns)
            
            # 필터 적용
            if filters:
                query = self._apply_filters(query, filters)
            
            # 정렬 (다중 정렬 지원)
            if order_by:
                query = self._apply_ordering(query, order_by)
            
            # 페이징
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
            
            # 단일 결과
            if single:
                query = query.single()
            
            # ✅ 비동기 실행
            response = await query.execute()
            return response.data
            
        except APIError as e:
            logger.error(f"Supabase API error on {table}: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Supabase select error on {table}: {e}")
            raise

    def _apply_filters(self, query, filters: Dict[str, Any]):
        """필터 조건 적용"""
        for column, value in filters.items():
            if isinstance(value, dict):
                # 복합 조건 처리
                for operator, filter_value in value.items():
                    query = self._apply_operator(query, column, operator, filter_value)
            else:
                # 단순 조건 (기본 eq)
                query = query.eq(column, value)
        return query

    def _apply_operator(self, query, column: str, operator: str, value: Any):
        """연산자별 쿼리 적용 (확장된 연산자 지원)"""
        operator_map = {
            "eq": lambda q, c, v: q.eq(c, v),
            "neq": lambda q, c, v: q.neq(c, v),
            "gt": lambda q, c, v: q.gt(c, v),
            "gte": lambda q, c, v: q.gte(c, v),
            "lt": lambda q, c, v: q.lt(c, v),
            "lte": lambda q, c, v: q.lte(c, v),
            "like": lambda q, c, v: q.like(c, v),
            "ilike": lambda q, c, v: q.ilike(c, v),
            "in": lambda q, c, v: q.in_(c, v),
            "is": lambda q, c, v: q.is_(c, v),
            "not": lambda q, c, v: q.not_(c, v),
            "contains": lambda q, c, v: q.contains(c, v),
            "contained_by": lambda q, c, v: q.contained_by(c, v),
        }
        
        if operator not in operator_map:
            logger.warning(f"Unknown operator '{operator}' for column '{column}'")
            return query
        
        return operator_map[operator](query, column, value)

    def _apply_ordering(self, query, order_by: Union[str, List[str]]):
        """정렬 조건 적용 (다중 정렬 지원)"""
        order_list = [order_by] if isinstance(order_by, str) else order_by
        
        for order_col in order_list:
            if order_col.startswith("-"):
                query = query.order(order_col[1:], desc=True)
            else:
                query = query.order(order_col)
        
        return query

    async def count(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        레코드 개수 조회
        
        Returns:
            int: 레코드 개수
        """
        if not self._initialized:
            await self.initialize()
        
        self._ensure_initialized()
        
        try:
            query = self.client.table(table).select("*", count="exact")
            
            if filters:
                query = self._apply_filters(query, filters)
            
            response = await query.execute()
            return response.count
            
        except Exception as e:
            logger.error(f"Supabase count error on {table}: {e}")
            raise

    async def rpc(
        self, 
        function_name: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Supabase RPC 함수 호출 (PostgreSQL Function)
        """
        if not self._initialized:
            await self.initialize()
        
        self._ensure_initialized()
        
        try:
            response = await self.client.rpc(function_name, params or {}).execute()
            return response.data
        except Exception as e:
            logger.error(f"Supabase RPC error ({function_name}): {e}")
            raise

    async def health_check(self) -> bool:
        """연결 상태 확인"""
        try:
            if not self._initialized:
                await self.initialize()
            
            # 단순 연결 확인용 RPC (가장 가벼운 쿼리)
            await self.client.rpc("ping").execute()  
            return True
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return False

    async def close(self) -> None:
        """클라이언트 종료"""
        if self.client:
            await self.client.close()
            self._initialized = False
            logger.info("Supabase client closed")

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.close()

# 전역 인스턴스
supabase_data_client = SupabaseDataClient()







"""
# 1. 기본 초기화
await database_manager.initialize()

# 2. Supabase 조회
users = await database_manager.supabase_data.select(
    "users",
    filters={
        "age": {"gte": 18},
        "status": "active"
    },
    order_by=["-created_at"],
    limit=10
)

# 3. MySQL 조회
orders = await database_manager.mysql.execute_query(
    "SELECT * FROM orders WHERE user_id = %s",
    params=(user_id,)
)

# 4. 헬스체크
status = await database_manager.health_check(detailed=True)

# 5. 컨텍스트 매니저 사용
async with DatabaseManager() as db:
    users = await db.supabase_data.select("users")

# 6. 종료
await database_manager.close()
"""