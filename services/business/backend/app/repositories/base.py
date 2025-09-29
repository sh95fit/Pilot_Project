from typing import Generic, TypeVar, Optional, List
from abc import ABC, abstractmethod

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """
    기본 Repository 패턴
    
    장점:
    - 데이터 접근 로직 캡슐화
    - 테스트 용이 (Mock 가능)
    - DB 교체 시 유연성
    """
    def __init__(self, db_manager):
        self.db = db_manager
    
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[T]:
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        pass
    
    @abstractmethod
    async def create(self, obj: T) -> T:
        pass
    
    @abstractmethod
    async def update(self, id: int, obj: T) -> Optional[T]:
        pass
    
    @abstractmethod
    async def delete(self, id: int) -> bool:
        pass