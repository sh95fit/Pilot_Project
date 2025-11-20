import pandas as pd
import pymysql
import paramiko
from sshtunnel import SSHTunnelForwarder
from contextlib import contextmanager
import streamlit as st
from config.database import SSHConfig, DBConfig

class DatabaseConnection:
    @staticmethod
    @contextmanager
    # SSH 터널 연결
    def get_tunnel():
        ssh_config = SSHConfig.from_env()
        
        # ssh_key = paramiko.RSAKey.from_private_key_file(ssh_config.key_path)
        ssh_key = ssh_config.key_path
        
        tunnel = SSHTunnelForwarder(
            (ssh_config.host, ssh_config.port),
            ssh_username=ssh_config.user,
            ssh_pkey=ssh_key,
            remote_bind_address=(DBConfig.from_env().host, DBConfig.from_env().port)
        )
        try:
            tunnel.start()
            yield tunnel
        finally:
            tunnel.stop()
            
    @staticmethod
    @contextmanager
    # Mysql DB 커넥션 연결
    def get_connection(tunnel):
        db_config = DBConfig.from_env()
        
        conn = pymysql.connect(
            host='127.0.0.1',
            port=tunnel.local_bind_port,
            user=db_config.user,
            password=db_config.password,
            database=db_config.database,
            charset=db_config.charset
        )
        
        try:
            yield conn
        finally:
            conn.close()    

    @staticmethod
    # 쿼리 실행 및 DataFrame 반환
    def execute_query(query: str, params=None) -> pd.DataFrame:
        with DatabaseConnection.get_tunnel() as tunnel:
            with DatabaseConnection.get_connection(tunnel) as conn:
                try:
                    df = pd.read_sql(query, conn, params=params)
                    
                    # DataFrame이 비어있지만 컬럼이 있는 경우 (INSERT/UPDATE 등)
                    if df.empty and len(df.columns) > 0:
                        with conn.cursor() as cursor:
                            cursor.execute(query, params)
                            rows = cursor.fetchall()
                            if rows:
                                df = pd.DataFrame(
                                    rows, 
                                    columns=[desc[0] for desc in cursor.description]
                                )
                    
                    return df
                except Exception as e:
                    st.error(f"데이터베이스 조회 중 오류 발생: {e}")
                    raise
            
            
class CachedDatabaseConnection:
    @staticmethod
    # streamlit에서 캐시된 결과를 재사용
    @st.cache_data(ttl=600, show_spinner="데이터 로딩 중...")
    def execute_query(query: str, params=None) -> pd.DataFrame:
        return DatabaseConnection.execute_query(query, params)