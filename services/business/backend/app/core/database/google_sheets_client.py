import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Any, Optional
import logging
import json
import os

logger = logging.getLogger(__name__)

class GoogleSheetsClient:
    """Google Sheets 클라이언트"""
    
    def __init__(self, credentials_json: str):
        """
        Args:
            credentials_json: Google Service Account JSON 키 (문자열 또는 파일 경로)
        """
        self.credentials_json = credentials_json
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Google Sheets 클라이언트 초기화"""
        try:
            # # JSON 문자열인 경우와 파일 경로인 경우 모두 처리
            # try:
            #     credentials_dict = json.loads(self.credentials_json)
            # except json.JSONDecodeError:
            #     with open(self.credentials_json, 'r') as f:
            #         credentials_dict = json.load(f)
            
            credentials_dict = None
            
            # 1. 파일 경로인지 먼저 확인 (파일이 실제로 존재하는 경우)
            if os.path.isfile(self.credentials_json):
                logger.info("Loading credentials from file path")
                with open(self.credentials_json, 'r') as f:
                    credentials_dict = json.load(f)
            else:
                # 2. JSON 문자열로 파싱 시도
                try:
                    logger.info("Parsing credentials as JSON string")
                    credentials_dict = json.loads(self.credentials_json)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse credentials as JSON: {e}")
                    raise ValueError(
                        "credentials_json must be either a valid file path or a valid JSON string"
                    )
            
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = Credentials.from_service_account_info(
                credentials_dict,
                scopes=scopes
            )
            
            self.client = gspread.authorize(credentials)
            logger.info("Google Sheets client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            raise
    
    async def get_spreadsheet(self, spreadsheet_id: str):
        """스프레드시트 객체 가져오기"""
        try:
            return self.client.open_by_key(spreadsheet_id)
        except Exception as e:
            logger.error(f"Failed to open spreadsheet {spreadsheet_id}: {e}")
            raise
    
    async def get_worksheet_data(
        self,
        spreadsheet_id: str,
        worksheet_name: str
    ) -> List[Dict[str, Any]]:
        """워크시트 데이터 조회 (딕셔너리 형태)"""
        try:
            spreadsheet = await self.get_spreadsheet(spreadsheet_id)
            worksheet = spreadsheet.worksheet(worksheet_name)
            records = worksheet.get_all_records()
            
            logger.info(f"Retrieved {len(records)} rows from {worksheet_name}")
            return records
            
        except Exception as e:
            logger.error(f"Failed to get worksheet data: {e}")
            raise
    
    async def get_range_data(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        cell_range: str
    ) -> List[List[Any]]:
        """특정 범위의 데이터 조회"""
        try:
            spreadsheet = await self.get_spreadsheet(spreadsheet_id)
            worksheet = spreadsheet.worksheet(worksheet_name)
            values = worksheet.get(cell_range)
            
            logger.info(f"Retrieved range {cell_range} from {worksheet_name}")
            return values
            
        except Exception as e:
            logger.error(f"Failed to get range data: {e}")
            raise
    
    async def append_rows(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        rows: List[List[Any]],
        value_input_option: str = 'USER_ENTERED'
    ) -> Dict[str, Any]:
        """워크시트에 행 추가"""
        try:
            spreadsheet = await self.get_spreadsheet(spreadsheet_id)
            worksheet = spreadsheet.worksheet(worksheet_name)
            
            result = worksheet.append_rows(
                rows,
                value_input_option=value_input_option
            )
            
            logger.info(f"Appended {len(rows)} rows to {worksheet_name}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to append rows: {e}")
            raise
    
    async def update_range(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        cell_range: str,
        values: List[List[Any]],
        value_input_option: str = 'USER_ENTERED'
    ) -> Dict[str, Any]:
        """특정 범위의 데이터 업데이트"""
        try:
            spreadsheet = await self.get_spreadsheet(spreadsheet_id)
            worksheet = spreadsheet.worksheet(worksheet_name)
            
            result = worksheet.update(
                cell_range,
                values,
                value_input_option=value_input_option
            )
            
            logger.info(f"Updated range {cell_range} in {worksheet_name}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to update range: {e}")
            raise
    
    async def get_worksheet_info(
        self,
        spreadsheet_id: str,
        worksheet_name: str
    ) -> Dict[str, Any]:
        """워크시트 정보 조회"""
        try:
            spreadsheet = await self.get_spreadsheet(spreadsheet_id)
            worksheet = spreadsheet.worksheet(worksheet_name)
            
            return {
                "title": worksheet.title,
                "row_count": worksheet.row_count,
                "col_count": worksheet.col_count,
                "spreadsheet_id": spreadsheet_id,
                "worksheet_id": worksheet.id
            }
            
        except Exception as e:
            logger.error(f"Failed to get worksheet info: {e}")
            raise
    
    async def find_records(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        query: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """조건에 맞는 레코드 검색"""
        try:
            records = await self.get_worksheet_data(spreadsheet_id, worksheet_name)
            
            filtered_records = [
                record for record in records
                if all(record.get(k) == v for k, v in query.items())
            ]
            
            logger.info(f"Found {len(filtered_records)} records matching query")
            return filtered_records
            
        except Exception as e:
            logger.error(f"Failed to find records: {e}")
            raise
    
    def health_check(self) -> bool:
        """클라이언트 연결 상태 확인"""
        try:
            return self.client is not None
        except Exception:
            return False