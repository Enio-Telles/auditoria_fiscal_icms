"""
Aplicação principal FastAPI para auditoria fiscal ICMS.
Versão mínima para testes sem dependências de workflows.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
from pathlib import Path

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="API Auditoria Fiscal ICMS",
    description="API para auditoria e classificação fiscal de produtos",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de logging
@app.middleware("http")
async def log_requests(request, call_next):
    """Log de requisições HTTP."""
    start_time = time.time()
    
    # Processar requisição
    response = await call_next(request)
    
    # Calcular tempo de processamento
    process_time = time.time() - start_time
    
    # Log da requisição
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Tempo: {process_time:.3f}s"
    )
    
    # Adicionar header de tempo de processamento
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Handler de erros global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global para exceções não tratadas."""
    logger.error(f"Erro não tratado: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Erro interno do servidor",
            "detail": str(exc) if app.debug else "Erro interno",
            "type": "InternalServerError"
        }
    )

# Rotas básicas
@app.get("/", tags=["Sistema"])
async def root():
    """Endpoint raiz da API."""
    return {
        "message": "API Auditoria Fiscal ICMS",
        "version": "1.0.0",
        "status": "ativo",
        "docs": "/docs"
    }

@app.get("/health", tags=["Sistema"])
async def health_check():
    """Verificação de saúde da API."""
    
    # Verificar componentes básicos
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "components": {
            "api": "healthy",
            "database": "unknown",  # Será verificado quando conectar BD
            "cache": "unknown"      # Será verificado quando conectar Redis
        }
    }
    
    return health_status

@app.get("/info", tags=["Sistema"])
async def api_info():
    """Informações detalhadas da API."""
    
    import platform
    import sys
    
    return {
        "api": {
            "name": "API Auditoria Fiscal ICMS",
            "version": "1.0.0",
            "description": "Sistema de auditoria e classificação fiscal"
        },
        "environment": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "architecture": platform.architecture()[0]
        },
        "features": {
            "authentication": "JWT",
            "database": "PostgreSQL",
            "cache": "Redis",
            "ai_models": ["OpenAI GPT", "Anthropic Claude"],
            "workflows": "LangGraph"
        },
        "endpoints": {
            "auth": "/auth",
            "users": "/users", 
            "companies": "/companies",
            "products": "/products",
            "classification": "/classification",
            "results": "/results"
        }
    }

# Rotas de autenticação básicas (mock para testes)
@app.post("/auth/login", tags=["Autenticação"])
async def login():
    """Login de usuário (mock para testes)."""
    return {
        "access_token": "mock_token_123",
        "token_type": "bearer",
        "expires_in": 3600,
        "user": {
            "id": 1,
            "email": "admin@empresa.com",
            "name": "Administrador"
        }
    }

@app.get("/auth/me", tags=["Autenticação"]) 
async def get_current_user():
    """Obtém usuário atual (mock para testes)."""
    return {
        "id": 1,
        "email": "admin@empresa.com",
        "name": "Administrador",
        "active": True
    }

# Rotas de empresas básicas (mock para testes)
@app.get("/companies", tags=["Empresas"])
async def list_companies():
    """Lista empresas (mock para testes)."""
    return {
        "companies": [
            {
                "id": 1,
                "name": "Empresa Teste Ltda",
                "cnpj": "12345678000195",
                "state": "RO",
                "active": True
            }
        ],
        "total": 1,
        "page": 1,
        "pages": 1
    }

# Rotas de produtos básicas (mock para testes)
@app.get("/products", tags=["Produtos"])
async def list_products():
    """Lista produtos (mock para testes)."""
    return {
        "products": [
            {
                "id": 1,
                "company_id": 1,
                "original_description": "Produto de teste",
                "current_ncm": "12345678",
                "current_cest": "01.001.00",
                "status": "PENDING"
            }
        ],
        "total": 1,
        "page": 1,
        "pages": 1
    }

# Rota de classificação básica (mock para testes)
@app.post("/classification/batch", tags=["Classificação"])
async def batch_classification():
    """Classificação em lote (mock para testes)."""
    return {
        "job_id": "job_123",
        "status": "STARTED",
        "message": "Classificação iniciada",
        "estimated_time": "5 minutos"
    }

# Importações necessárias para o middleware
import time
from datetime import datetime


def create_app() -> FastAPI:
    """Factory function para criar a aplicação FastAPI."""
    return app


# Para desenvolvimento
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_simple:app", host="127.0.0.1", port=8000, reload=True)
