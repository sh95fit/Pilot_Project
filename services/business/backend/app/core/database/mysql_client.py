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
        self.pools: Dict[str, aiomysql.Pool] = {}  # DB별 풀 관리
        self.ssh_tunnel: Optional[SSHTunnelForwarder] = None
        self.local_port: Optional[int] = None
        self._lock = threading.Lock()
        self._initialized = False
        self.default_db = settings.mysql_main_database

    async def initialize(self) -> None:
        """
        SSH 터널 초기화 (DB 풀은 필요할 때 Lazy 생성)
        """
        if self._initialized:
            logger.info("MySQL client already initialized")
            return

        try:
            await self._setup_ssh_tunnel()
            self._initialized = True
            logger.info(f"✅ MySQL SSH client initialized (Lazy DB pools)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MySQL SSH client: {e}")
            await self.close()
            raise

    async def _setup_ssh_tunnel(self) -> None:
        """SSH 터널 설정"""
        with self._lock:
            if self.ssh_tunnel and self.ssh_tunnel.is_active:
                logger.warning("SSH tunnel already active.")
                return
            try:
                self.ssh_tunnel = SSHTunnelForwarder(
                    (settings.ssh_host, settings.ssh_port),
                    ssh_username=settings.ssh_user,
                    ssh_pkey=settings.ssh_key_path,  # 경로로 설정
                    remote_bind_address=(settings.mysql_host, settings.mysql_port),
                    local_bind_address=("127.0.0.1", 0)  # 자동 포트 할당
                )
                self.ssh_tunnel.start()
                self.local_port = self.ssh_tunnel.local_bind_port
                logger.info(f"SSH tunnel established on port {self.local_port}")
            except Exception as e:
                logger.error(f"Failed to setup SSH tunnel: {e}")
                raise

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

    @asynccontextmanager
    async def get_connection(self, db_name: str = None):
        """DB 지정 연결 컨텍스트 매니저 (default DB 사용 가능)"""
        db_name = db_name or self.default_db
        if db_name not in self.pools:
            await self._create_pool(db_name)  # Lazy Pool 생성
        async with self.pools[db_name].acquire() as conn:
            try:
                yield conn
            except Exception as e:
                await conn.rollback()
                logger.error(f"Database error on {db_name}: {e}")
                raise

    async def execute_query(self, query: str, params: Tuple = None, db_name: str = None) -> List[Dict[str, Any]]:
        """SELECT 쿼리 실행"""
        async with self.get_connection(db_name) as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params)
                return await cursor.fetchall()

    async def execute_procedure(self, proc_name: str, params: Tuple = None, db_name: str = None) -> List[Dict[str, Any]]:
        """저장 프로시저 실행"""
        async with self.get_connection(db_name) as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.callproc(proc_name, params)
                return await cursor.fetchall()

    async def execute_non_query(self, query: str, params: Tuple = None, db_name: str = None) -> int:
        """INSERT/UPDATE/DELETE 실행"""
        async with self.get_connection(db_name) as conn:
            async with conn.cursor() as cursor:
                affected = await cursor.execute(query, params)
                await conn.commit()
                return affected

    async def execute_transaction(self, queries: List[Tuple[str, Tuple]], db_name: str = None) -> bool:
        """여러 쿼리를 트랜잭션으로 실행"""
        async with self.get_connection(db_name) as conn:
            async with conn.cursor() as cursor:
                try:
                    await conn.begin()
                    for query, params in queries:
                        await cursor.execute(query, params)
                    await conn.commit()
                    return True
                except Exception as e:
                    await conn.rollback()
                    logger.error(f"Transaction failed on {db_name or self.default_db}: {e}")
                    raise

    async def health_check(self, db_name: str = None) -> bool:
        """DB 연결 상태 확인"""
        try:
            await self.execute_query("SELECT 1", db_name=db_name)
            return True
        except Exception as e:
            logger.error(f"MySQL health check failed for {db_name or self.default_db}: {e}")
            return False

    async def close(self) -> None:
        """모든 풀과 터널 종료"""
        for db_name, pool in self.pools.items():
            pool.close()
            await pool.wait_closed()
            logger.info(f"MySQL pool closed for DB: {db_name}")
        self.pools.clear()

        if self.ssh_tunnel and self.ssh_tunnel.is_active:
            self.ssh_tunnel.stop()
            self.ssh_tunnel = None
            logger.info("SSH tunnel closed")


# 전역 인스턴스
mysql_client = MySQLClient()
