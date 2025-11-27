"""
Task별 설정을 코드와 분리하여 관리
설정 변경 시 비즈니스 로직 수정 불필요
"""

from backend.app.core.config import settings

class CohortTaskConfig:
    """코호트 Task 설정"""
    
    NOT_ORDERED = {
        'spreadsheet_id': settings.google_sheet_id_cohort,
        'worksheet_name': "일별_미주문고객사_DB",
        'procedure_name': "get_daily_not_order_accounts",
        'needs_target_date': True,
        'needs_date_header': True,    
        "header_range": "A2:E2",      # 헤더 범위
        "header_merge_cells": 5,   # 병합셀 개수  
        "start_cell": "A3"
    }
    
    END_OF_USE = {
        'spreadsheet_id': settings.google_sheet_id_cohort,
        'worksheet_name': "이탈유저관리(서비스 이용 종료)",
        'procedure_name': "get_end_of_use_accounts",
        'needs_target_date': False,
        'needs_date_header': False,    
        "start_cell": "A1"
    }
    
    ACTIVE_ACCOUNTS = {
        'spreadsheet_id': settings.google_sheet_id_cohort,
        'worksheet_name': "9월_이후_전환_활성고객_DB",
        'procedure_name': "get_available_accounts_cohort",
        'needs_target_date': False,
        'needs_date_header': False,    
        "start_cell": "A1"
    }
    
    INCOMING_LEADS = {
        'spreadsheet_id': settings.google_sheet_id_cohort,
        'worksheet_name': "어드민_유입_리드_DB",
        'procedure_name': "get_incoming_leads_accounts",
        'needs_target_date': False,
        'needs_date_header': True,    
        "header_range": "A1",
        "header_merge_cells": 2,
        "start_cell": "A2"
    }
    