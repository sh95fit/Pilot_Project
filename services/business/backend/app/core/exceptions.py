class BaseAPIException(Exception):
    """기본 API 예외"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class DatabaseConnectionError(BaseAPIException):
    """DB 연결 에러"""
    def __init__(self, message: str = "Database connection failed"):
        super().__init__(message, status_code=503)

class SSHTunnelError(BaseAPIException):
    """SSH 터널 에러"""
    def __init__(self, message: str = "SSH tunnel connection failed"):
        super().__init__(message, status_code=503)

class DataValidationError(BaseAPIException):
    """데이터 검증 에러"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class AuthenticationError(BaseAPIException):
    """인증 에러"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)

class AuthorizationError(BaseAPIException):
    """권한 에러"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403)

class ResourceNotFoundError(BaseAPIException):
    """리소스 없음"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)