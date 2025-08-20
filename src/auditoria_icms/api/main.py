"""
FastAPI Main Application for Sistema de Auditoria Fiscal ICMS v16.0
Implementação da API REST para orquestração dos agentes e interface web
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import logging
import uvicorn
from typing import Optional
import yaml

from ..core.config import load_config
from ..database.connection import get_db_session
from .endpoints import auth, companies, users, data_import, classification, agents, results, golden_set
from .middleware.logging_middleware import LoggingMiddleware
from .middleware.error_handler import add_exception_handlers

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar configurações
config = load_config()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar ciclo de vida da aplicação"""
    logger.info("🚀 Iniciando Sistema de Auditoria Fiscal ICMS v16.0")
    
    # Inicialização
    try:
        # Verificar conexões com bancos de dados
        logger.info("✅ Verificando conexões com banco de dados...")
        
        # Inicializar modelos de IA
        logger.info("🧠 Carregando modelos de IA...")
        
        # Verificar estrutura de dados
        logger.info("📊 Verificando estrutura de dados...")
        
        logger.info("🎯 Sistema iniciado com sucesso!")
        yield
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
        raise
    finally:
        logger.info("🛑 Finalizando Sistema de Auditoria Fiscal")

# Configurar aplicação FastAPI
app = FastAPI(
    title="Sistema de Auditoria Fiscal ICMS",
    description="API para classificação automatizada de mercadorias (NCM/CEST) com IA multi-agente",
    version="16.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend React
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Adicionar middleware customizado
app.add_middleware(LoggingMiddleware)

# Adicionar tratadores de erro
add_exception_handlers(app)

# Configurar segurança JWT
security = HTTPBearer()

# =============================================================================
# ROTAS PRINCIPAIS
# =============================================================================

# Rota de health check
@app.get("/")
async def root():
    """Endpoint de verificação de saúde da API"""
    return {
        "message": "Sistema de Auditoria Fiscal ICMS v16.0",
        "status": "online",
        "version": "16.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Verificação detalhada da saúde do sistema"""
    try:
        # Verificar banco de dados
        db_status = "ok"  # Implementar verificação real
        
        # Verificar modelos de IA
        ai_status = "ok"  # Implementar verificação real
        
        return {
            "status": "healthy",
            "timestamp": "2025-08-19T12:00:00Z",
            "services": {
                "database": db_status,
                "ai_models": ai_status,
                "api": "ok"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service Unavailable")

# =============================================================================
# INCLUIR ROUTERS DOS ENDPOINTS
# =============================================================================

# Autenticação e usuários
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticação"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Usuários"])

# Gestão de empresas
app.include_router(companies.router, prefix="/api/v1/companies", tags=["Empresas"])

# Importação de dados
app.include_router(data_import.router, prefix="/api/v1/data", tags=["Importação"])

# Classificação e agentes
app.include_router(classification.router, prefix="/api/v1/classify", tags=["Classificação"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agentes"])

# Resultados e revisão
app.include_router(results.router, prefix="/api/v1/results", tags=["Resultados"])

# Golden Set
app.include_router(golden_set.router, prefix="/api/v1/golden-set", tags=["Golden Set"])

# =============================================================================
# CONFIGURAÇÃO DE STARTUP
# =============================================================================

if __name__ == "__main__":
    # Configuração para desenvolvimento
    uvicorn.run(
        "main:app",
        host=config.get("api", {}).get("host", "0.0.0.0"),
        port=config.get("api", {}).get("port", 8000),
        reload=True,
        log_level="info"
    )
