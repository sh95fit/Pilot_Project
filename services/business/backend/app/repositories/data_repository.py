from typing import Optional, List, Dict, Any
from datetime import date
from backend.app.repositories.base import BaseRepository

class DataRepository(BaseRepository[Dict[str, Any]]):
    async def get_sales_summary(
        self, 
        start_date: date, 
        end_date: date
    ) -> List[Dict[str, Any]]:
        rows = await self.db.mysql.execute_procedure(
            "get_sales_summary",
            params=(start_date, end_date)
        )
        rows = rows or []

        # DictCursor를 사용하므로 키 기반 접근으로 변환
        # 결과 키 이름은 프로시저의 SELECT 컬럼 별칭과 일치해야 함
        normalized_results = []
        for r in rows:
            try:
                period_label = r.get("period_label") or r.get("PERIOD_LABEL")
                period_type = r.get("period_type") or r.get("PERIOD_TYPE")
                amount_value = r.get("total_amount_sum") or r.get("TOTAL_AMOUNT_SUM") or r.get("total_amount")

                normalized_results.append({
                    "period_label": period_label,
                    "period_type": period_type,
                    "total_amount_sum": float(amount_value) if amount_value is not None else 0.0
                })
            except Exception:
                # 예기치 않은 스키마의 경우 튜플 형태 방어 (만약 DictCursor 미적용 시)
                if isinstance(r, (list, tuple)) and len(r) >= 3:
                    normalized_results.append({
                        "period_label": r[0],
                        "period_type": r[1],
                        "total_amount_sum": float(r[2]) if r[2] is not None else 0.0
                    })
                else:
                    raise

        return normalized_results


    async def get_active_accounts(
        self, 
        start_date: date, 
        end_date: date
    ) -> List[Dict[str, Any]]:
        rows = await self.db.mysql.execute_procedure(
            "get_active_accounts_stats",
            params=(start_date, end_date)
        )
        rows = rows or []
        
        # DictCursor를 사용하므로 키 기반 접근으로 변환
        normalized_results = []
        for r in rows:
            try:
                subscription_date = r.get("subscription_date") or r.get("SUBSCRIPTION_DATE")
                daily_active = r.get("daily_new_accounts") or r.get("DAILY_NEW_ACCOUNTS")
                cumulative_active = r.get("cumulative_active_accounts") or r.get("CUMULATIVE_ACTIVE_ACCOUNTS")

                normalized_results.append({
                    "subscription_date": str(subscription_date) if subscription_date else None,
                    "daily_new_accounts": int(daily_active) if daily_active is not None else 0,
                    "cumulative_active_accounts": int(cumulative_active) if cumulative_active is not None else 0
                })
            except Exception:
                # 예기치 않은 스키마의 경우 튜플 형태 방어 (만약 DictCursor 미적용 시)
                if isinstance(r, (list, tuple)) and len(r) >= 3:
                    normalized_results.append({
                        "subscription_date": str(r[0]) if r[0] else None,
                        "daily_new_accounts": int(r[1]) if r[1] is not None else 0,
                        "cumulative_active_accounts": int(r[2]) if r[2] is not None else 0
                    })
                else:
                    raise

        return normalized_results
    
    async def get_number_of_product_sold(
        self, 
        start_date: date, 
        end_date: date,
        is_grouped: bool
    ) -> List[Dict[str, Any]]:
        rows = await self.db.mysql.execute_procedure(
            "get_number_of_product_sold",
            params=(start_date, end_date, is_grouped)
        )
        rows = rows or []        
        
        # DictCursor를 사용하므로 키 기반 접근으로 변환
        normalized_results = []

        for r in rows:
            try:
                delivery_date = r.get('delivery_date') or r.get('DELIVERY_DATE')
                product_name = r.get('product_name') or r.get('product') or r.get('PRODUCT_NAME') or r.get('PRODUCT')
                total_quantity = r.get('total_quantity') or r.get('TOTAL_QUANTITY')
                total_amount = r.get('total_amount') or r.get('TOTAL_AMOUNT')
                
                normalized_results.append({
                    "delivery_date": str(delivery_date) if delivery_date else None,
                    "product_name": str(product_name) if product_name else None,
                    "total_quantity": int(total_quantity) if total_quantity is not None else 0,
                    "total_amount": int(total_amount) if total_amount is not None else 0
                })
            except Exception:
                # 예기치 않은 스키마의 경우 튜플 형태 방어 (만약 DictCursor 미적용 시)
                if isinstance(r, (list, tuple)) and len(r) >= 4:
                    normalized_results.append({
                        "created_date": str(r[0]) if r[0] else None,
                        "product_name": str(r[1]) if r[1] is not None else 0,
                        "total_quantity": int(r[2]) if r[2] is not None else 0,
                        "total_amount": int(r[3]) if r[3] is not None else 0
                    })
                else:
                    raise

        return normalized_results        
    
    
    # 추상 메서드 최소 구현
    async def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        raise NotImplementedError

    async def create(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    async def update(self, id: int, obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    async def delete(self, id: int) -> bool:
        raise NotImplementedError    