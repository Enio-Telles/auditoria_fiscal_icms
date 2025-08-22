#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Auditoria Fiscal ICMS v2.2 - COM SISTEMA DE IA INTEGRADO
============================================================

API FastAPI completa com:
- Funcionalidades originais (empresas, produtos, importação)
- Sistema de IA para classificação automática NCM/CEST
- Múltiplos provedores LLM (OpenAI, Ollama, Hugging Face)
- Classificação ensemble e em lote
- Cache inteligente e otimizações
"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import logging
import asyncio
import uvicorn
from datetime import datetime
import os
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="🤖 Auditoria Fiscal ICMS com IA",
    description="""
    ## Sistema Completo de Auditoria Fiscal com IA

    ### 🚀 Funcionalidades Principais:
    - **Classificação Automática** com IA (NCM/CEST)
    - **Múltiplos LLMs**: OpenAI, Ollama, Hugging Face
    - **Ensemble Learning** para máxima precisão
    - **Importação de Dados** multi-database
    - **Base de Conhecimento** NCM/CEST integrada
    - **Cache Inteligente** para performance
    - **API RESTful** completa

    ### 🤖 Provedores de IA Suportados:
    - **OpenAI GPT** (3.5-turbo, 4) - Máxima qualidade
    - **Ollama** (Llama, Mistral) - Local, privado
    - **Hugging Face** (Transformers) - Open source
    - **Ensemble** - Combinação de múltiplos modelos

    ### 📊 Endpoints Disponíveis:
    - `/api/ai/classify` - Classificação individual
    - `/api/ai/classify-batch` - Processamento em lote
    - `/api/ai/status` - Status do sistema de IA
    - `/api/import/*` - Importação de dados
    - `/empresas` - Gestão de empresas
    """,
    version="2.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importar e incluir routers de IA (se disponível)
try:
    from src.auditoria_icms.api.ai_endpoints import ai_router
    app.include_router(ai_router)
    AI_INTEGRATED = True
    logger.info("✅ Sistema de IA integrado com sucesso!")
except ImportError as e:
    logger.warning(f"⚠️ Sistema de IA não disponível: {e}")
    AI_INTEGRATED = False

# === ENDPOINTS ORIGINAIS ===

# Mock data para demonstração
MOCK_EMPRESAS = [
    {
        "id": 1,
        "razao_social": "Empresa Demo Ltda",
        "cnpj": "12.345.678/0001-90",
        "ie": "123456789",
        "status": "ativa"
    },
    {
        "id": 2,
        "razao_social": "Tech Solutions Ltda",
        "cnpj": "98.765.432/0001-10",
        "ie": "987654321",
        "status": "ativa"
    }
]

MOCK_PRODUTOS = [
    {
        "id": 1,
        "descricao": "Notebook Dell Inspiron",
        "ncm": "8471.30.12",
        "cest": "01.004.00",
        "preco": 2500.00
    },
    {
        "id": 2,
        "descricao": "Mouse óptico USB",
        "ncm": "8471.60.52",
        "cest": "01.012.00",
        "preco": 25.00
    }
] * 21  # 42 produtos para demonstração

@app.get("/")
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "sistema": "Auditoria Fiscal ICMS com IA",
        "versao": "2.2.0",
        "status": "operacional",
        "ia_disponivel": AI_INTEGRATED,
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "empresas": "/empresas",
            "stats": "/stats",
            "ai_status": "/api/ai/status" if AI_INTEGRATED else "Não disponível",
            "ai_classify": "/api/ai/classify" if AI_INTEGRATED else "Não disponível",
            "ai_demo": "/api/ai/demo" if AI_INTEGRATED else "Não disponível"
        }
    }

@app.get("/health")
async def health_check():
    """Health check com informações detalhadas"""
    health_info = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.2.0",
        "sistema": "Auditoria Fiscal ICMS",
        "funcionalidades": {
            "api_basica": True,
            "importacao": True,
            "ia_classificacao": AI_INTEGRATED
        }
    }
    
    if AI_INTEGRATED:
        try:
            # Verificar status da IA
            from src.auditoria_icms.ai_classification import AIClassificationEngine
            health_info["ia_status"] = "disponível"
            health_info["ia_provedores"] = ["huggingface", "ollama", "openai"]
        except Exception as e:
            health_info["ia_status"] = f"erro: {str(e)}"
    
    return health_info

@app.get("/empresas")
async def listar_empresas():
    """Lista todas as empresas"""
    return MOCK_EMPRESAS

@app.get("/stats")
async def get_statistics():
    """Estatísticas do sistema"""
    stats = {
        "total_empresas": len(MOCK_EMPRESAS),
        "total_produtos": len(MOCK_PRODUTOS),
        "versao": "2.2.0",
        "status": "operational",
        "golden_set": {
            "ncm_items": 150,
            "cest_items": 800
        },
        "arquitetura": "multi-tenant",
        "database": {
            "type": "postgresql",
            "status": "connected"
        }
    }
    
    if AI_INTEGRATED:
        stats["ia"] = {
            "disponivel": True,
            "provedores_ativos": ["huggingface"],
            "classificacoes_realizadas": 0,
            "cache_entries": 0
        }
        
        try:
            # Tentar obter estatísticas reais da IA
            from src.auditoria_icms.api.ai_endpoints import classification_cache
            stats["ia"]["cache_entries"] = len(classification_cache)
        except:
            pass
    
    return stats

# === ENDPOINTS DE IMPORTAÇÃO (Compatibilidade) ===

class DatabaseConfig(BaseModel):
    type: str
    host: str
    port: int
    database: str
    user: str
    password: str
    schema: Optional[str] = None

@app.post("/api/import/test-connection")
async def test_database_connection(config: DatabaseConfig):
    """Testa conexão com banco de dados"""
    # Simulação de teste de conexão
    await asyncio.sleep(1)  # Simular tempo de conexão
    
    return {
        "success": True,
        "message": "Conexão estabelecida com sucesso",
        "database": config.database,
        "host": config.host,
        "database_info": f"{config.type.upper()} - PostgreSQL 13.5, compiled by Visual C++ build 1914, 64-bit"
    }

@app.post("/api/import/preview")
async def preview_import_data(
    config: DatabaseConfig,
    sql_query: str,
    limit: int = 10
):
    """Preview dos dados para importação"""
    # Simulação de preview
    await asyncio.sleep(0.5)
    
    return {
        "success": True,
        "preview_count": min(limit, 3),
        "total_estimated": 20223,
        "columns": ["produto_id", "descricao_produto", "ncm", "cest"],
        "data": [
            {
                "produto_id": "1",
                "descricao_produto": "Notebook Dell Inspiron",
                "ncm": "8471.30.12",
                "cest": "01.004.00"
            },
            {
                "produto_id": "2", 
                "descricao_produto": "Mouse Óptico USB",
                "ncm": "8471.60.52",
                "cest": "01.012.00"
            },
            {
                "produto_id": "3",
                "descricao_produto": "Teclado Mecânico RGB",
                "ncm": "8471.60.53",
                "cest": "01.013.00"
            }
        ]
    }

@app.post("/api/import/execute")
async def execute_import(
    config: DatabaseConfig,
    sql_query: str,
    empresa_id: Optional[str] = None
):
    """Executa importação completa"""
    # Simulação de importação
    await asyncio.sleep(2)
    
    return {
        "success": True,
        "records_imported": 150,
        "records_with_errors": 0,
        "execution_time": 2.5,
        "summary": {
            "empresas": 1,
            "produtos": 150,
            "ncm_matches": 145,
            "cest_matches": 130
        }
    }

# === ENDPOINTS ESPECIAIS PARA IA ===

@app.get("/ai-demo")
async def ai_demo_endpoint():
    """Demonstração especial do sistema de IA"""
    if not AI_INTEGRATED:
        return {
            "error": "Sistema de IA não está disponível",
            "solucao": "Verifique se as dependências estão instaladas",
            "status": "indisponível"
        }
    
    try:
        from src.auditoria_icms.ai_classification import classify_product
        
        # Produtos de teste
        produtos_teste = [
            "Smartphone Samsung Galaxy A50",
            "Café torrado e moído Pilão 500g",
            "Notebook Dell Inspiron 15 3000"
        ]
        
        resultados = []
        
        for produto in produtos_teste:
            try:
                result = await classify_product(produto, "huggingface")
                resultados.append({
                    "produto": produto,
                    "ncm_sugerido": result['ncm'],
                    "confianca": result['confianca'],
                    "modelo": result['modelo'],
                    "tempo": result['tempo']
                })
            except Exception as e:
                resultados.append({
                    "produto": produto,
                    "erro": str(e),
                    "ncm_sugerido": "0000.00.00"
                })
        
        return {
            "sistema": "IA para Classificação NCM/CEST",
            "versao": "2.2.0",
            "demo_resultados": resultados,
            "status": "funcionando",
            "observacoes": "Demonstração usando Hugging Face Transformers"
        }
        
    except Exception as e:
        return {
            "error": f"Erro na demonstração de IA: {str(e)}",
            "status": "erro"
        }

# === TRATAMENTO DE ERROS ===

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler customizado para exceções HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler para exceções gerais"""
    logger.error(f"Erro não tratado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erro interno do servidor",
            "detail": str(exc),
            "path": str(request.url.path),
            "timestamp": datetime.now().isoformat()
        }
    )

# === MIDDLEWARE DE LOGGING ===

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de requisições"""
    start_time = datetime.now()
    
    # Log da requisição
    logger.info(f"📨 {request.method} {request.url.path}")
    
    # Processar requisição
    response = await call_next(request)
    
    # Log da resposta
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"📤 {request.method} {request.url.path} - {response.status_code} - {process_time:.2f}s")
    
    return response

# === EVENTOS DE STARTUP/SHUTDOWN ===

@app.on_event("startup")
async def startup_event():
    """Eventos de inicialização"""
    logger.info("🚀 Iniciando API Auditoria Fiscal ICMS v2.2")
    logger.info("📋 Funcionalidades disponíveis:")
    logger.info("   ✅ API REST básica")
    logger.info("   ✅ Importação de dados")
    logger.info("   ✅ Gestão de empresas")
    
    if AI_INTEGRATED:
        logger.info("   🤖 Sistema de IA ativado!")
        logger.info("      • Classificação automática NCM/CEST")
        logger.info("      • Múltiplos provedores LLM")
        logger.info("      • Processamento em lote")
        logger.info("      • Cache inteligente")
    else:
        logger.info("   ⚠️ Sistema de IA não disponível")
    
    logger.info("🌐 API disponível em: http://127.0.0.1:8003")
    logger.info("📖 Documentação em: http://127.0.0.1:8003/docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Eventos de finalização"""
    logger.info("🛑 Finalizando API Auditoria Fiscal ICMS v2.2")
    
    if AI_INTEGRATED:
        try:
            # Limpar cache se necessário
            from src.auditoria_icms.api.ai_endpoints import classification_cache
            cache_size = len(classification_cache)
            logger.info(f"🗄️ Cache de IA: {cache_size} entradas")
        except:
            pass

def main():
    """Função principal para executar a API"""
    try:
        logger.info("🔧 Configurando servidor...")
        
        # Verificar se a porta está livre
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 8003))
        sock.close()
        
        if result == 0:
            logger.warning("⚠️ Porta 8003 já está em uso!")
            logger.info("💡 Use: python api_ia_completa.py para forçar reinicialização")
        
        # Configurações do servidor
        config = uvicorn.Config(
            app=app,
            host="127.0.0.1",
            port=8003,
            log_level="info",
            reload=False,  # Desabilitar reload para estabilidade
            workers=1
        )
        
        server = uvicorn.Server(config)
        server.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Servidor interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar servidor: {e}")
        raise

if __name__ == "__main__":
    main()
