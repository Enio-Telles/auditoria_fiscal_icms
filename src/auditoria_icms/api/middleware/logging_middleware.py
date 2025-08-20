"""
Middleware de logging para requests da API
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para log de requests e performance"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Capturar informações do request
        start_time = time.time()
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        
        # Log do início do request
        logger.info(f"🌐 {method} {url} - IP: {client_ip}")
        
        try:
            # Processar request
            response = await call_next(request)
            
            # Calcular tempo de processamento
            process_time = time.time() - start_time
            
            # Log da resposta
            status_code = response.status_code
            log_message = f"✅ {method} {url} - {status_code} - {process_time:.3f}s"
            
            if status_code >= 400:
                logger.warning(log_message)
            else:
                logger.info(log_message)
            
            # Adicionar header com tempo de processamento
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log de erro
            process_time = time.time() - start_time
            logger.error(f"❌ {method} {url} - ERROR: {str(e)} - {process_time:.3f}s")
            raise
