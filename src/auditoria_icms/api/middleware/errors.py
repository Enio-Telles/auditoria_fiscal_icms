"""
Classes de erro personalizadas para a API.
"""

from typing import Any, Optional, Dict
from fastapi import HTTPException, status


class APIError(Exception):
    """
    Classe base para erros da API.
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(APIError):
    """Erro de validação de dados."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class AuthenticationError(APIError):
    """Erro de autenticação."""
    
    def __init__(self, message: str = "Credenciais inválidas"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(APIError):
    """Erro de autorização/permissão."""
    
    def __init__(self, message: str = "Acesso negado"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundError(APIError):
    """Recurso não encontrado."""
    
    def __init__(self, message: str = "Recurso não encontrado"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )


class ConflictError(APIError):
    """Conflito de dados."""
    
    def __init__(self, message: str = "Conflito de dados"):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT
        )


class DatabaseError(APIError):
    """Erro de banco de dados."""
    
    def __init__(self, message: str = "Erro interno do banco de dados"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class WorkflowError(APIError):
    """Erro no processamento de workflow."""
    
    def __init__(self, message: str = "Erro no processamento"):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class ExternalServiceError(APIError):
    """Erro em serviço externo."""
    
    def __init__(self, message: str = "Serviço externo indisponível"):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class RateLimitError(APIError):
    """Limite de taxa excedido."""
    
    def __init__(self, message: str = "Muitas requisições"):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


# Mapeamento de exceções para HTTPException
def api_error_to_http_exception(error: APIError) -> HTTPException:
    """
    Converte APIError para HTTPException do FastAPI.
    
    Args:
        error: Erro da API
        
    Returns:
        HTTPException correspondente
    """
    return HTTPException(
        status_code=error.status_code,
        detail={
            "message": error.message,
            "details": error.details,
            "type": type(error).__name__
        }
    )
