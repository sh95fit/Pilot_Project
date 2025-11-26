"""
데이터 변환 유틸리티
Mysql -> Google Sheets 형식 변환
"""

from typing import List, Dict, Any
from decimal import Decimal
from datetime import datetime, date, timedelta
import holidays
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    """데이터 변환 처리"""
    
    @staticmethod
    def to_sheets_format(data: List[Dict[str, Any]]) -> List[List[Any]]:
        """
        Mysql 딕셔너리 리스트를 Sheets 2차원 배열로 변환
        
        Args :
            data : MySQL 쿼리 결과
            
        Returns:
            헤더 포함 2차원 배열
        """
        if not data:
            logger.warning("⚠️ No data to convert")
            return []
        
        # 헤더 추출
        headers = list(data[0].keys())
        rows = [headers]
        
        # 데이터 변환
        for record in data:
            row = []
            for key in headers:
                value = record.get(key, "")
                
                # 타입별 직렬화
                if isinstance(value, (date, datetime)):
                    value = value.strftime("%Y-%m-%d")
                elif isinstance(value, Decimal):
                    value = float(value)  # Decimal → float 변환
                elif value is None:
                    value = ""
                    
                row.append(value)
            rows.append(row)
            
        logger.info(f"🔄 Converted {len(data)} records → {len(rows)} rows")
        return rows
    
def get_next_business_date(base_date: datetime = None) -> str:
    """
    다음 업무일 계산 (주말 + 공휴일 제외)
    금/토/일 -> 월요일, 평일 -> 익일
    공휴일이 연속되는 경우도 처리
    """
    now = base_date or datetime.now()
    kr_holidays = holidays.KR()  # 한국 공휴일 (음력 공휴일, 대체공휴일 포함)
    
    # 초기 다음 날짜 계산 (주말 고려)
    if now.weekday() == 4:  # 금요일
        days = 3
    elif now.weekday() == 5:  # 토요일
        days = 2
    else:
        days = 1
        
    next_date = now + timedelta(days=days)
        
    # 주말 또는 공휴일이 아닐 때까지 반복
    max_iterations = 30  # 무한루프 방지
    iterations = 0

    while iterations < max_iterations:
        # 주말 체크 (토요일=5, 일요일=6)
        if next_date.weekday() >= 5:
            next_date += timedelta(days=1)
            iterations += 1
            continue
        
        # 공휴일 체크
        if next_date.date() in kr_holidays:
            holiday_name = kr_holidays.get(next_date.date())
            logger.info(f"🗓️ {next_date.strftime('%Y-%m-%d')} is {holiday_name}, skipping...")
            next_date += timedelta(days=1)
            iterations += 1
            continue
        
        # 평일이면서 공휴일 아님
        break
        
    target_date = next_date.strftime("%Y-%m-%d")
    total_days = (next_date - now).days
    logger.info(f"📅 Next business date: {target_date} (+{total_days} days from {now.strftime('%Y-%m-%d')})")
    return target_date