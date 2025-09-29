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