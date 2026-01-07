from typing import List, Dict, Any, Optional
import pandas as pd
from backend.app.repositories.base import BaseRepository
from backend.app.core.database.google_sheets_client import GoogleSheetsClient
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsRepository(BaseRepository[Dict[str, Any]]):
    """Google Sheets Repository (Pandas 최적화)"""
    
    def __init__(self, google_sheets_client: GoogleSheetsClient):
        self.sheets = google_sheets_client
    
    async def get_metric_dashboard_data(
        self,
        spreadsheet_id: str,
        worksheet_name: str = "Metric_Dashboard",
        start_period: Optional[str] = None,
        end_period: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """메트릭 대시보드 데이터 조회 (Pandas 사용)"""
        try:
            # 전체 데이터 조회
            records = await self.sheets.get_worksheet_data(
                spreadsheet_id=spreadsheet_id,
                worksheet_name=worksheet_name
            )
            
            if not records:
                logger.warning(f"No data found in {worksheet_name}")
                return []
            
            # Pandas DataFrame 생성
            df = pd.DataFrame(records)
            logger.info(f"Retrieved {len(df)} rows from {worksheet_name}")
            
            # 컬럼명 정규화
            df.columns = df.columns.str.lower().str.strip()
            
            # 기간 컬럼 찾기
            period_col = None
            for col in df.columns:
                if col in ['period', '기간', 'date', '날짜', 'ym', '년월']:
                    period_col = col
                    break
            
            if not period_col:
                period_col = df.columns[0]
            
            # 컬럼 매핑
            column_mapping = {period_col: 'period'}
            
            # 리드수 컬럼
            for col in df.columns:
                if col in ['lead', 'lead_count', '리드수', '리드']:
                    column_mapping[col] = 'lead_count'
                    break
            
            # 체험전환 컬럼
            for col in df.columns:
                if col in ['trial', 'trial_conversion', '체험전환', '체험']:
                    column_mapping[col] = 'trial_conversion'
                    break
            
            # 구독전환 컬럼
            for col in df.columns:
                if col in ['subscription', 'subscription_conversion', '구독전환', '구독']:
                    column_mapping[col] = 'subscription_conversion'
                    break
            
            for col in df.columns:
                if col in ['end_of_use', 'end_of_use_count', '이탈수', '이탈']:
                    column_mapping[col] = 'end_of_use_count'
                    break
            
            # 컬럼명 변경
            df = df.rename(columns=column_mapping)
            
            # 필요한 컬럼만 선택
            required_columns = ['period', 'lead_count', 'trial_conversion', 'subscription_conversion', 'end_of_use_count']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = 0
            
            df = df[required_columns]
            
            # period 문자열 변환
            df['period'] = df['period'].astype(str).str.strip()
            
            # YYYY-MM 형식만 필터링
            df = df[df['period'].str.match(r'^\d{4}-\d{2}$', na=False)]
            
            # 숫자 컬럼 변환
            numeric_columns = ['lead_count', 'trial_conversion', 'subscription_conversion', 'end_of_use_count']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            
            # 기간 필터링
            if start_period:
                df = df[df['period'] >= start_period]
            if end_period:
                df = df[df['period'] <= end_period]
            
            # 정렬
            df = df.sort_values('period')
            
            # 딕셔너리 변환
            result = df.to_dict('records')
            
            logger.info(f"Processed {len(result)} metric records")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get metric dashboard data: {e}")
            raise
    
    # BaseRepository 추상 메서드
    async def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("Use get_metric_dashboard_data instead")
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        raise NotImplementedError("Use get_metric_dashboard_data instead")
    
    async def create(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Not implemented")
    
    async def update(self, id: int, obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("Not implemented")
    
    async def delete(self, id: int) -> bool:
        raise NotImplementedError("Not implemented")