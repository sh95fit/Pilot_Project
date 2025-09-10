# shared/utils/logger.py
import logging
import sys
from pathlib import Path
from loguru import logger
from typing import Optional

class InterceptHandler(logging.Handler):
    """표준 로깅을 loguru로 리다이렉트"""
    
    def emit(self, record):
        # 해당 로그 레벨을 loguru 레벨로 매핑
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        
        # 호출자 정보 가져오기
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logger(name: Optional[str] = None) -> logger:
    """로거 설정"""
    
    # 기존 핸들러 제거
    logger.remove()
    
    # 환경 변수에서 로그 레벨 가져오기
    import os
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # 콘솔 출력 설정
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        colorize=True
    )
    
    # 파일 출력 설정 (프로덕션에서)
    if os.getenv("ENVIRONMENT") == "prod":
        log_dir = Path("/app/logs")
        log_dir.mkdir(exist_ok=True)
        
        logger.add(
            log_dir / "app.log",
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="100 MB",
            retention="30 days",
            compression="zip"
        )
    
    # 표준 logging을 loguru로 리다이렉트
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    return logger