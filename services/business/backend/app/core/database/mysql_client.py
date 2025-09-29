import asyncio
import aiomysql
import logging
import threading
from typing import Optional, Dict, Any, List, Tuple
from contextlib import asynccontextmanager
from sshtunnel import SSHTunnelForwarder
from ..config import settings

logger = logging.getLogger(__name__)

class MySQLClient:
    """
    SSH 터널링을 통한 MySQL 연결 클라이언트
    - 기본 DB: mysql_main_database
    - 필요 시 다른 DB 지정 가능
    - Lazy Pool 방식 적용: 실제 사용 시 풀 생성
    """
    def __init__(self):
        self.pools: Dict[str, aiomysql.Pool] = {}
        self.ssh_tunnel: Optional[SSHTunnelForwarder] = None
        self.local_port: Optional[int] = None
        self._lock = asyncio.Lock()
        self._initialized = False
        self._reconnecting = False
        self.default_db = settings.mysql_main_database
        self.max_reconnect_attempts = 3
        self.reconnect_delay = 2  # 초기 대기 시간 (초)

    async def initialize(self) -> None:
        """
        SSH 터널 초기화 (DB 풀은 필요할 때 Lazy 생성)
        """
        if self._initialized:
            logger.info("MySQL client already initialized")
            return

        async with self._lock:
            try:
                await self._setup_ssh_tunnel()
                self._initialized = True
                logger.info("✅ MySQL SSH client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize MySQL SSH client: {e}")
                await self.close()
                raise

    async def _setup_ssh_tunnel(self) -> None:
        """SSH 터널 설정"""
        if self.ssh_tunnel and self.ssh_tunnel.is_active:
            logger.warning("SSH tunnel already active")
            return
        
        try:
            # SSH 터널 생성 (blocking이므로 executor 사용)
            loop = asyncio.get_event_loop()
            self.ssh_tunnel = await loop.run_in_executor(
                None,
                self._create_ssh_tunnel
            )
            
            self.local_port = self.ssh_tunnel.local_bind_port
            logger.info(f"✅ SSH tunnel established on port {self.local_port}")
            
        except Exception as e:
            logger.error(f"Failed to setup SSH tunnel: {e}")
            raise

    def _create_ssh_tunnel(self) -> SSHTunnelForwarder:
        """SSH 터널 객체 생성 (동기 작업)"""
        tunnel = SSHTunnelForwarder(
            (settings.ssh_host, settings.ssh_port),
            ssh_username=settings.ssh_user,
            ssh_pkey=settings.ssh_key_path,
            remote_bind_address=(settings.mysql_host, settings.mysql_port),
            local_bind_address=("127.0.0.1", 0)
        )
        tunnel.start()
        return tunnel

    async def _reconnect_ssh_tunnel(self) -> bool:
        """
        SSH 터널 재연결 (Exponential Backoff)
        
        Returns:
            bool: 재연결 성공 여부
        """
        if self._reconnecting:
            logger.warning("Reconnection already in progress, waiting...")
            # 다른 태스크가 재연결 중이면 대기
            while self._reconnecting:
                await asyncio.sleep(0.5)
            return self._initialized
        
        async with self._lock:
            self._reconnecting = True
            
            try:
                logger.warning("🔄 Attempting to reconnect SSH tunnel...")
                
                # 기존 터널 정리
                if self.ssh_tunnel:
                    try:
                        self.ssh_tunnel.stop()
                    except Exception as e:
                        logger.warning(f"Error stopping old tunnel: {e}")
                    self.ssh_tunnel = None
                
                # 기존 풀 정리
                await self._close_all_pools()
                
                # 재연결 시도 (Exponential Backoff)
                for attempt in range(self.max_reconnect_attempts):
                    try:
                        await self._setup_ssh_tunnel()
                        self._initialized = True
                        logger.info(f"✅ SSH tunnel reconnected on attempt {attempt + 1}")
                        return True
                        
                    except Exception as e:
                        delay = self.reconnect_delay * (2 ** attempt)
                        logger.warning(
                            f"⚠️ Reconnection attempt {attempt + 1}/{self.max_reconnect_attempts} failed: {e}"
                        )
                        if attempt < self.max_reconnect_attempts - 1:
                            logger.info(f"Retrying in {delay}s...")
                            await asyncio.sleep(delay)
                
                logger.error("❌ Failed to reconnect SSH tunnel after all attempts")
                self._initialized = False
                return False
                
            finally:
                self._reconnecting = False

    async def _close_all_pools(self) -> None:
        """모든 Connection Pool 닫기"""
        for db_name, pool in list(self.pools.items()):
            try:
                pool.close()
                await pool.wait_closed()
                logger.info(f"Pool closed for DB: {db_name}")
            except Exception as e:
                logger.error(f"Error closing pool for {db_name}: {e}")
        
        self.pools.clear()

    async def _create_pool(self, db_name: str) -> None:
        """DB별 풀 생성 (Lazy 생성용, SSH 터널 통해 접속)"""
        if db_name in self.pools:
            return  # 이미 풀 생성됨

        if not self.ssh_tunnel or not self.ssh_tunnel.is_active:
            raise RuntimeError("SSH tunnel is not active. Call initialize() before creating pool.")

        try:
            pool = await aiomysql.create_pool(
                host="127.0.0.1",          # SSH 터널 로컬 포트
                port=self.local_port,       # SSH 터널 바인딩 포트
                user=settings.mysql_user,
                password=settings.mysql_password,
                db=db_name,
                charset="utf8mb4",
                autocommit=True,
                minsize=5,
                maxsize=20,
                echo=getattr(settings, "debug", False),
                pool_recycle=3600
            )
            self.pools[db_name] = pool
            logger.info(f"MySQL connection pool created for DB via SSH tunnel: {db_name}")
            
        except Exception as e:
            logger.error(f"Failed to create MySQL pool for {db_name} via SSH tunnel: {e}")
            raise

    async def _ensure_connection(self) -> None:
        """
        연결 상태 확인 및 재연결
        
        SSH 터널이 끊어진 경우 자동 재연결 시도
        """
        if not self._initialized or not self.ssh_tunnel or not self.ssh_tunnel.is_active:
            logger.warning("SSH tunnel not active, attempting reconnection...")
            success = await self._reconnect_ssh_tunnel()
            if not success:
                raise ConnectionError("Failed to establish SSH tunnel connection")

    @asynccontextmanager
    async def get_connection(self, db_name: str = None):
        """
        DB 연결 컨텍스트 매니저 (자동 재연결 포함)
        
        Usage:
            async with client.get_connection("mydb") as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
        """
        db_name = db_name or self.default_db
        
        # 연결 확인 및 재연결
        await self._ensure_connection()
        
        # 풀이 없으면 생성
        if db_name not in self.pools:
            await self._create_pool(db_name)
        
        # 풀에서 연결 획득
        try:
            async with self.pools[db_name].acquire() as conn:
                yield conn
                
        except Exception as e:
            logger.error(f"Database connection error on {db_name}: {e}")
            
            # SSH 터널 문제인지 확인
            if self._is_connection_error(e):
                logger.warning("Connection lost detected, triggering reconnection...")
                await self._reconnect_ssh_tunnel()
            
            raise

    def _is_connection_error(self, error: Exception) -> bool:
        """연결 에러인지 판단"""
        error_msg = str(error).lower()
        connection_errors = [
            "lost connection",
            "can't connect",
            "connection refused",
            "broken pipe",
            "connection reset",
            "timeout"
        ]
        return any(err in error_msg for err in connection_errors)

    async def execute_query(
        self, 
        query: str, 
        params: Tuple = None, 
        db_name: str = None,
        retry: bool = True
    ) -> List[Dict[str, Any]]:
        """
        SELECT 쿼리 실행 (자동 재시도)
        
        Args:
            query: SQL 쿼리
            params: 파라미터
            db_name: DB 이름
            retry: 실패 시 재시도 여부
        
        Returns:
            List[Dict[str, Any]]: 쿼리 결과
        """
        try:
            async with self.get_connection(db_name) as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query, params)
                    return await cursor.fetchall()
                    
        except Exception as e:
            if retry and self._is_connection_error(e):
                logger.warning(f"Query failed due to connection error, retrying once... ({e})")
                await self._reconnect_ssh_tunnel()
                return await self.execute_query(query, params, db_name, retry=False)
            raise

    async def execute_procedure(
        self, 
        proc_name: str, 
        params: Tuple = None, 
        db_name: str = None,
        retry: bool = True
    ) -> List[Dict[str, Any]]:
        """
        저장 프로시저 실행 (자동 재시도)
        
        Args:
            proc_name: 프로시저 이름
            params: 파라미터
            db_name: DB 이름
            retry: 실패 시 재시도 여부
        
        Returns:
            List[Dict[str, Any]]: 프로시저 결과
        """
        try:
            async with self.get_connection(db_name) as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.callproc(proc_name, params)
                    return await cursor.fetchall()
                    
        except Exception as e:
            if retry and self._is_connection_error(e):
                logger.warning(f"Procedure failed due to connection error, retrying once... ({e})")
                await self._reconnect_ssh_tunnel()
                return await self.execute_procedure(proc_name, params, db_name, retry=False)
            raise

    async def execute_non_query(
        self, 
        query: str, 
        params: Tuple = None, 
        db_name: str = None
    ) -> int:
        """
        INSERT/UPDATE/DELETE 실행
        
        Returns:
            int: 영향받은 행 수
        """
        async with self.get_connection(db_name) as conn:
            async with conn.cursor() as cursor:
                affected = await cursor.execute(query, params)
                await conn.commit()
                return affected

    async def execute_transaction(
        self, 
        queries: List[Tuple[str, Tuple]], 
        db_name: str = None
    ) -> bool:
        """
        여러 쿼리를 트랜잭션으로 실행
        
        Args:
            queries: [(query, params), ...] 리스트
            db_name: DB 이름
        
        Returns:
            bool: 성공 여부
        """
        async with self.get_connection(db_name) as conn:
            async with conn.cursor() as cursor:
                try:
                    await conn.begin()
                    for query, params in queries:
                        await cursor.execute(query, params)
                    await conn.commit()
                    logger.info(f"Transaction committed: {len(queries)} queries")
                    return True
                except Exception as e:
                    await conn.rollback()
                    logger.error(f"Transaction failed and rolled back: {e}")
                    raise

    async def health_check(self, db_name: str = None) -> bool:
        """
        DB 연결 상태 확인 (SSH 터널 포함)
        
        Returns:
            bool: 정상 연결 여부
        """
        try:
            # SSH 터널 확인
            if not self.ssh_tunnel or not self.ssh_tunnel.is_active:
                logger.warning("SSH tunnel not active during health check")
                return False
            
            # DB 쿼리 확인
            result = await self.execute_query("SELECT 1 as health", db_name=db_name, retry=False)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def close(self) -> None:
        """모든 연결 종료 (Graceful Shutdown)"""
        logger.info("Closing MySQL client...")
        
        # 모든 풀 종료
        await self._close_all_pools()
        
        # SSH 터널 종료
        if self.ssh_tunnel:
            try:
                if self.ssh_tunnel.is_active:
                    self.ssh_tunnel.stop()
                    logger.info("✅ SSH tunnel closed")
            except Exception as e:
                logger.error(f"Error closing SSH tunnel: {e}")
            finally:
                self.ssh_tunnel = None
        
        self._initialized = False
        logger.info("✅ MySQL client closed")


# 전역 인스턴스
mysql_client = MySQLClient()


"""
# 1. 초기화
await mysql_client.initialize()

# 2. 일반 쿼리 (자동 재연결)
users = await mysql_client.execute_query(
    "SELECT * FROM users WHERE status = %s",
    params=("active",)
)

# 3. 프로시저 호출 (자동 재연결)
sales = await mysql_client.execute_procedure(
    "get_sales_summary",
    params=("2025-01-01", "2025-09-29")
)

# 4. 트랜잭션
await mysql_client.execute_transaction([
    ("INSERT INTO orders (user_id) VALUES (%s)", (123,)),
    ("UPDATE users SET order_count = order_count + 1 WHERE id = %s", (123,))
])

# 5. 헬스체크
is_healthy = await mysql_client.health_check()

# 6. 종료
await mysql_client.close()


# SSH 터널이 끊겼을 때 자동으로 처리되는 시나리오:
# 1. 쿼리 실행 중 "Lost connection" 에러 발생
# 2. _is_connection_error()로 연결 에러 감지
# 3. _reconnect_ssh_tunnel() 자동 호출 (최대 3번 재시도, Exponential Backoff)
# 4. 터널 재연결 성공 시 쿼리 자동 재실행
# 5. 실패 시 원본 에러 raise
"""