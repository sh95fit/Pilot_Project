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
        'needs_period': False,
        "header_range": "A2:E2",      # 헤더 범위
        "header_merge_cells": 5,   # 병합셀 개수  
        "start_cell": "A3"
    }
    
    PENDING_NOT_ORDERED = {
        'spreadsheet_id': settings.google_sheet_id_cohort,
        'worksheet_name': "주문확정전_미주문 고객사",
        'procedure_name': "get_pending_not_order_accounts",
        'needs_target_date': True,
        'needs_date_header': True,
        'needs_period': False,
        "header_range": "A2:F2",      # 헤더 범위
        "header_merge_cells": 6,   # 병합셀 개수  
        "start_cell": "A3"
    }
    
    
    END_OF_USE = {
        'spreadsheet_id': settings.google_sheet_id_cohort,
        'worksheet_name': "이탈유저관리(서비스 이용 종료)",
        'procedure_name': "get_end_of_use_accounts",
        'needs_target_date': False,
        'needs_date_header': False,    
        'needs_period': False,
        "start_cell": "A1"
    }
    
    ACTIVE_ACCOUNTS = {
        'spreadsheet_id': settings.google_sheet_id_cohort,
        'worksheet_name': "9월_이후_전환_활성고객_DB",
        'procedure_name': "get_available_accounts_cohort",
        'needs_target_date': False,
        'needs_date_header': False,    
        'needs_period': False,
        "start_cell": "A1"
    }
    
    INCOMING_LEADS = {
        'spreadsheet_id': settings.google_sheet_id_cohort,
        'worksheet_name': "어드민_유입_리드_DB",
        'procedure_name': "get_incoming_leads_accounts",
        'needs_target_date': False,
        'needs_date_header': True,    
        'needs_period': False,
        "header_range": "A1",
        "header_merge_cells": 2,
        "start_cell": "A2"
    }
    
    NOW_ACTIVE_ACCOUNTS = {
        'spreadsheet_id': settings.google_sheet_id_cohort,
        'worksheet_name': "활성_고객_DB",
        'procedure_name': "get_active_accounts_stats",
        'needs_target_date': False,
        'needs_date_header': False,    
        'needs_period': True,
        "header_range": "A1",
        "header_merge_cells": 2,
        "start_cell": "A2",
    }
    
    PRODUCT_SALES_SUMMARY = {
        'spreadsheet_id': settings.google_sheet_id_cohort,
        'worksheet_name': "일별_상품별_주문이력_DB",
        'procedure_name': "get_daily_product_sales_summary",
        'needs_target_date': False,
        'needs_date_header': False,    
        'needs_period': False,
        "start_cell": "A1",
    }
    
    ACCOUNT_ORDERS_SUMMARY = {
        'spreadsheet_id': settings.google_sheet_id_cohort,
        'worksheet_name': "고객사별_주문현황_DB",
        'procedure_name': "get_account_orders_summary",
        'needs_target_date': False,
        'needs_date_header': False,    
        'needs_period': False,
        "start_cell": "A1",
    }
    
    TRIAL_ACCOUNTS = {
        'spreadsheet_id': settings.google_sheet_id_cohort,
        'worksheet_name': "체험_고객사_DB",
        'procedure_name': "get_trial_accounts",
        'needs_target_date': False,
        'needs_date_header': False,    
        'needs_period': False,
        "start_cell": "A1",
    }