"""
Tratamento centralizado de erros da API
"""

import logging
from typing import Union
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Exceção base para erros da API"""
    
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class BusinessLogicError(APIError):
    """Erro de lógica de negócio"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, 400, details)

class AgentError(APIError):
    """Erro específico dos agentes"""
    
    def __init__(self, agent_name: str, message: str, details: dict = None):
        super().__init__(
            f"Erro no agente {agent_name}: {message}",
            500,
            {"agent": agent_name, **(details or {})}
        )

class DatabaseError(APIError):
    """Erro de banco de dados"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(f"Erro de banco de dados: {message}", 500, details)

async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handler para erros customizados da API"""
    
    logger.error(f"API Error: {exc.message} - Details: {exc.details}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "details": exc.details,
            "type": type(exc).__name__
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler para HTTPException padrão"""
    
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler para erros de validação"""
    
    logger.warning(f"Validation Error: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Erro de validação dos dados",
            "details": exc.errors()
        }
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler para exceções não tratadas"""
    
    logger.error(f"Unhandled Exception: {str(exc)}\n{traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Erro interno do servidor",
            "details": {"exception": str(exc)} if logger.level <= logging.DEBUG else {}
        }
    )

def add_exception_handlers(app: FastAPI) -> None:
    """Adiciona todos os handlers de exceção à aplicação"""
    
    # Handlers customizados
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(BusinessLogicError, api_error_handler)
    app.add_exception_handler(AgentError, api_error_handler)
    app.add_exception_handler(DatabaseError, api_error_handler)
    
    # Handlers padrão
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
