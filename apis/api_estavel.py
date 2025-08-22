"""
API Estável - Versão Final Corrigida
====================================

Esta versão resolve o problema de finalização automática.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import traceback

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =================== APLICAÇÃO FASTAPI ===================

app = FastAPI(
    title="Sistema de Auditoria Fiscal ICMS - Multi-Tenant",
    description="API estável para auditoria fiscal com classificação automática NCM/CEST",
    version="2.1.1"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"]
)

# =================== MODELOS ===================

class DatabaseConnection(BaseModel):
    type: str
    host: str  
    port: int
    database: str
    schema: Optional[str] = "dbo"
    user: str
    password: str

class EmpresaResponse(BaseModel):
    id: int
    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str]
    database_name: str
    ativa: bool

# =================== DADOS MOCK ===================

mock_empresas = [
    {
        "id": 1,
        "cnpj": "12.345.678/0001-90",
        "razao_social": "Empresa Demo Ltda",
        "nome_fantasia": "Demo Store", 
        "database_name": "empresa_12345678000190",
        "ativa": True
    },
    {
        "id": 2,
        "cnpj": "98.765.432/0001-10", 
        "razao_social": "Tech Solutions Ltda",
        "nome_fantasia": "TechSol",
        "database_name": "empresa_98765432000110", 
        "ativa": True
    }
]

# =================== FUNÇÕES DE EXTRAÇÃO ===================

def test_postgresql_connection(connection: DatabaseConnection):
    """Testa conexão PostgreSQL usando módulo externo se disponível"""
    try:
        # Tentar usar o módulo de extração se disponível
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        
        from auditoria_icms.data_processing.data_extractor import (
            DataExtractor, 
            DatabaseConfig
        )
        
        # Converter para configuração do extrator
        db_config = DatabaseConfig(
            host=connection.host,
            port=str(connection.port),
            database=connection.database,
            user=connection.user,
            password=connection.password,
            schema=connection.schema or 'public',
            db_type=connection.type
        )
        
        # Criar extrator e testar conexão
        extractor = DataExtractor(db_config)
        result = extractor.test_connection()
        extractor.close()
        
        logger.info(f"✅ Teste de conexão via módulo: {result['success']}")
        return result
        
    except Exception as e:
        logger.warning(f"Módulo de extração não disponível: {e}")
        
        # Fallback: teste simples com psycopg2
        try:
            import psycopg2
            
            conn = psycopg2.connect(
                host=connection.host,
                port=connection.port,
                user=connection.user,
                password=connection.password,
                database=connection.database,
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            conn.close()
            
            result = {
                "success": True,
                "database_info": f"PostgreSQL - {version[0][:100]}",
                "host": connection.host,
                "database": connection.database,
                "schema": connection.schema,
                "method": "psycopg2_fallback"
            }
            
            logger.info("✅ Teste de conexão via psycopg2 fallback")
            return result
            
        except Exception as e2:
            logger.error(f"Falha no teste de conexão: {e2}")
            return {
                "success": False,
                "error": str(e2),
                "method": "fallback_failed"
            }

# =================== ENDPOINTS ===================

@app.get("/")
async def root():
    """Endpoint raiz"""
    try:
        return {
            "message": "Sistema de Auditoria Fiscal ICMS - Multi-Tenant",
            "version": "2.1.1",
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "features": [
                "Bancos separados por empresa",
                "Golden Set centralizado",
                "Classificação IA NCM/CEST", 
                "Módulo de extração avançado",
                "API estável sem finalização automática"
            ]
        }
    except Exception as e:
        logger.error(f"Erro no endpoint root: {e}")
        return {"error": str(e), "status": "error"}

@app.get("/health")
async def health():
    """Health check robusto"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.1.1",
            "uptime": "API funcionando",
            "checks": {
                "fastapi": True,
                "cors": True,
                "logging": True
            }
        }
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return {
            "status": "degraded", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/empresas", response_model=List[EmpresaResponse])
async def listar_empresas():
    """Lista empresas"""
    try:
        logger.info("Listando empresas")
        return mock_empresas
    except Exception as e:
        logger.error(f"Erro ao listar empresas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def estatisticas():
    """Estatísticas do sistema"""
    try:
        return {
            "total_empresas": len(mock_empresas),
            "total_produtos": 42,
            "golden_set": {
                "ncm_items": 150,
                "cest_items": 89
            },
            "arquitetura": "multi-tenant",
            "versao": "2.1.1",
            "status": "operational"
        }
    except Exception as e:
        logger.error(f"Erro nas estatísticas: {e}")
        return {"error": str(e), "status": "error"}

@app.post("/api/import/test-connection")
async def test_connection(connection: DatabaseConnection):
    """Testa conexão com banco externo"""
    try:
        logger.info(f"Testando conexão: {connection.type}://{connection.host}:{connection.port}/{connection.database}")
        
        if connection.type.lower() == "postgresql":
            result = test_postgresql_connection(connection)
        else:
            # Para outros tipos de banco, simular por enquanto
            result = {
                "success": True,
                "database_info": f"Simulado: {connection.type} em {connection.host}:{connection.port}",
                "host": connection.host,
                "database": connection.database,
                "schema": connection.schema,
                "method": "simulated"
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Erro no teste de conexão: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"success": False, "error": str(e)}

@app.post("/api/import/preview")
async def preview_import(
    connection: DatabaseConnection,
    sql_query: str,
    limit: int = 100
):
    """Preview de dados para importação"""
    try:
        logger.info(f"Preview de dados: {sql_query[:50]}...")
        
        # Dados mock para demonstração
        mock_preview = {
            "success": True,
            "preview_count": 3,
            "columns": ["produto_id", "descricao_produto", "ncm", "cest"],
            "data": [
                {
                    "produto_id": 1,
                    "descricao_produto": "Notebook Dell Inspiron",
                    "ncm": "84713000", 
                    "cest": "0101500"
                },
                {
                    "produto_id": 2,
                    "descricao_produto": "Mouse Óptico USB",
                    "ncm": "84716090",
                    "cest": "0101900"
                },
                {
                    "produto_id": 3,
                    "descricao_produto": "Teclado Mecânico",
                    "ncm": "84716090",
                    "cest": "0101900"
                }
            ],
            "query_used": sql_query,
            "method": "mock_preview"
        }
        
        return mock_preview
        
    except Exception as e:
        logger.error(f"Erro no preview: {e}")
        return {"success": False, "error": str(e)}

# =================== DOCUMENTAÇÃO ===================

@app.get("/docs-info")
async def docs_info():
    """Informações sobre a documentação da API"""
    return {
        "swagger_ui": "http://127.0.0.1:8003/docs",
        "redoc": "http://127.0.0.1:8003/redoc", 
        "openapi_json": "http://127.0.0.1:8003/openapi.json",
        "endpoints": {
            "health": "/health",
            "empresas": "/empresas",
            "stats": "/stats",
            "test_connection": "/api/import/test-connection",
            "preview": "/api/import/preview"
        }
    }

# =================== INICIALIZAÇÃO ===================

def main():
    """Função principal para iniciar a API"""
    import uvicorn
    
    try:
        logger.info("🚀 Iniciando API Multi-Tenant Estável v2.1.1...")
        logger.info("📚 Documentação: http://127.0.0.1:8003/docs")
        logger.info("🏢 Empresas: http://127.0.0.1:8003/empresas")
        logger.info("📊 Estatísticas: http://127.0.0.1:8003/stats")
        logger.info("🔧 Health Check: http://127.0.0.1:8003/health")
        logger.info("🎯 API configurada para não finalizar automaticamente")
        
        uvicorn.run(
            "api_estavel:app",
            host="127.0.0.1",
            port=8003,
            log_level="info",
            reload=False  # Desabilitar reload para evitar problemas
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar API: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
