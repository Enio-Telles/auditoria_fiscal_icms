"""
API Minimal para Teste - Resolução do Problema de Finalização
==============================================================

Versão extremamente simples para identificar o problema.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =================== APLICAÇÃO FASTAPI ===================

app = FastAPI(
    title="API Minimal - Teste de Estabilidade",
    description="API mínima para teste de problemas de finalização",
    version="1.0.0",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =================== MODELOS BÁSICOS ===================


class DatabaseConnection(BaseModel):
    type: str
    host: str
    port: int
    database: str
    schema: Optional[str] = "dbo"
    user: str
    password: str


# =================== ENDPOINTS BÁSICOS ===================


@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "API Minimal funcionando",
        "version": "1.0.0",
        "status": "online",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health():
    """Health check simples"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


@app.get("/test")
async def test_endpoint():
    """Endpoint de teste simples"""
    return {
        "test": "OK",
        "message": "Endpoint de teste funcionando",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/import/test-connection")
async def test_connection_minimal(connection: DatabaseConnection):
    """Teste de conexão mínimo sem dependências externas"""
    try:
        # Validação básica sem conectar realmente
        if not connection.host or not connection.database:
            return {"success": False, "error": "Host e database são obrigatórios"}

        # Simular teste de conexão
        result = {
            "success": True,
            "database_info": f"Simulado: {connection.type} em {connection.host}:{connection.port}",
            "host": connection.host,
            "database": connection.database,
            "schema": connection.schema,
            "message": "Teste simulado - conexão não realizada",
        }

        logger.info(
            f"Teste de conexão simulado: {connection.host}:{connection.port}/{connection.database}"
        )
        return result

    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        return {"success": False, "error": str(e)}


@app.get("/empresas")
async def listar_empresas():
    """Lista empresas mock"""
    return [
        {
            "id": 1,
            "cnpj": "12.345.678/0001-90",
            "razao_social": "Empresa Teste Ltda",
            "nome_fantasia": "Teste Store",
            "database_name": "empresa_12345678000190",
            "ativa": True,
        }
    ]


@app.get("/stats")
async def estatisticas():
    """Estatísticas básicas"""
    return {
        "total_empresas": 1,
        "total_produtos": 10,
        "versao": "1.0.0",
        "status": "funcionando",
    }


# =================== INICIALIZAÇÃO ===================

if __name__ == "__main__":
    import uvicorn

    print("🚀 Iniciando API Minimal...")
    print("📚 Documentação: http://127.0.0.1:8003/docs")
    print("🔧 Health: http://127.0.0.1:8003/health")
    print("🧪 Teste: http://127.0.0.1:8003/test")

    uvicorn.run(app, host="127.0.0.1", port=8003, log_level="info")
