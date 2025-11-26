"""
Google Sheets 업데이트 로직
시트 초기화 및 데이터 입력 처리
"""
import logging

logger = logging.getLogger(__name__)

class SheetsUpdater:
    """Google Sheets 업데이트 처리"""
    
    def __init__(self, sheets_client, run_async_fn):
        """
        Args:
            sheets_client: GoogleSheetsClient 인스턴스
            run_async_fn: 비동기 함수 실행 헬퍼
        """
        self.sheets = sheets_client
        self.run_async = run_async_fn
        
    def clear_data_range(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        start_row: int = 1
    ):
        """
        기존 데이터 범위 초기화
        
        Arg:
            spreadsheet_id: 스프레드시트 ID
            worksheet_name: 워크시트명
            start_row: 데이터 시작 행 (기본값: 1)
        """
        
        # 워크시트 크기 확인
        info = self.run_async(
            self.sheets.get_worksheet_info(spreadsheet_id, worksheet_name)
        )
        
        # 기존 데이터 조회
        existing = self.run_async(
            self.sheets.get_range_data(
                spreadsheet_id,
                worksheet_name,
                f"A{start_row}:{chr(64 + min(info['col_count'], 26))}{info['row_count']}"
            )
        )
        
        # 데이터 초기화
        if existing and len(existing) > 0 :
            max_cols = max(len(row) for row in existing)
            empty = [[""] * max_cols for _ in range(len(existing))]
            self.run_async(
                self.sheets.update_range(
                    spreadsheet_id,
                    worksheet_name,
                    f"A{start_row}",
                    empty,
                    "USER_ENTERED"
                )
            )
            logger.info(f"🧹 Cleared {len(existing)} rows")
    
    # 병합된 셀에 데이터 삽입 필요시 활용
    def update_header(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        header_value: str,
        header_range: str = "A2",
        merge_cells: int = 1
    ):
        """
        헤더 셀 업데이트 (날짜 등)
        
        Args:
            spreadsheet_id: 스프레드시트 ID
            worksheet_name: 워크시트명
            header_value: 헤더에 입력할 값
            header_range: 헤더 시작 셀 (기본값: A2)
        """
        # 범위가 지정된 경우 (예: "A2:E2")
        if ":" in header_range:
            values = [[header_value]]
        # 단일 셀 + 병합셀 개수 지정
        else:
            values = [[header_value] * merge_cells]
        
        self.run_async(
            self.sheets.update_range(
                spreadsheet_id,
                worksheet_name,
                header_range,
                values,
                "USER_ENTERED"
            )
        )
        logger.info(f"📌 Header updated: {header_value} at {header_range}")    
        
    def insert_data(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        data: list,
        start_cell: str = "A3"
    ):
        """
        데이터 삽입
        
        Args:
            spreadsheet_id: 스프레드시트 ID
            worksheet_name: 워크시트명
            data: 삽입할 2차원 배열
            start_cell: 시작 셀 (기본값: A3)
        """
        self.run_async(
            self.sheets.update_range(
                spreadsheet_id,
                worksheet_name,
                start_cell,
                data,
                "USER_ENTERED"
            )
        )
        logger.info(f"📤 Inserted {len(data)} rows")
