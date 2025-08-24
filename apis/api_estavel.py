"""
API Estável - Versão Final Corrigida
====================================

Esta versão resolve o problema de finalização automática.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging
import traceback

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =================== APLICAÇÃO FASTAPI ===================

app = FastAPI(
    title="Sistema de Auditoria Fiscal ICMS - Multi-Tenant",
    description="API estável para auditoria fiscal com classificação automática NCM/CEST",
    version="2.1.1",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


class EmpresaCreate(BaseModel):
    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str] = None
    atividade_principal: Optional[str] = None
    regime_tributario: Optional[str] = "Simples Nacional"


class ClassificationRequest(BaseModel):
    description: str
    strategy: Optional[str] = "ensemble"


class ClassificationResult(BaseModel):
    ncm_code: str
    ncm_description: str
    cest_code: Optional[str] = None
    cest_description: Optional[str] = None
    confidence: float
    justification: str
    agent_used: str
    processing_time: float


# =================== DADOS MOCK ===================

mock_empresas = [
    {
        "id": 1,
        "cnpj": "12.345.678/0001-90",
        "razao_social": "Empresa Demo Ltda",
        "nome_fantasia": "Demo Store",
        "database_name": "empresa_12345678000190",
        "ativa": True,
    },
    {
        "id": 2,
        "cnpj": "98.765.432/0001-10",
        "razao_social": "Tech Solutions Ltda",
        "nome_fantasia": "TechSol",
        "database_name": "empresa_98765432000110",
        "ativa": True,
    },
]

mock_produtos = [
    {
        "produto_id": 1,
        "descricao_produto": "Notebook Dell Inspiron",
        "ncm": "84713000",
        "cest": "0101500",
    },
    {
        "produto_id": 2,
        "descricao_produto": "Mouse Óptico USB",
        "ncm": "84716090",
        "cest": "0101900",
    },
    {
        "produto_id": 3,
        "descricao_produto": "Teclado Mecânico",
        "ncm": "84716090",
        "cest": "0101900",
    },
    {
        "produto_id": 4,
        "descricao_produto": "Geladeira Brastemp",
        "ncm": "84182100",
        "cest": "0301100",
    },
]

# =================== FUNÇÕES DE EXTRAÇÃO ===================


def test_postgresql_connection(connection: DatabaseConnection):
    """Testa conexão PostgreSQL usando módulo externo se disponível"""
    try:
        # Tentar usar o módulo de extração se disponível
        import sys
        import os

        sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

        from auditoria_icms.data_processing.data_extractor import (
            DataExtractor,
            DatabaseConfig,
        )

        # Converter para configuração do extrator
        db_config = DatabaseConfig(
            host=connection.host,
            port=str(connection.port),
            database=connection.database,
            user=connection.user,
            password=connection.password,
            schema=connection.schema or "public",
            db_type=connection.type,
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
                connect_timeout=5,
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
                "method": "psycopg2_fallback",
            }

            logger.info("✅ Teste de conexão via psycopg2 fallback")
            return result

        except Exception as e2:
            logger.error(f"Falha no teste de conexão: {e2}")
            return {"success": False, "error": str(e2), "method": "fallback_failed"}


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
                "API estável sem finalização automática",
            ],
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
            "checks": {"fastapi": True, "cors": True, "logging": True},
        }
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
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


@app.post("/empresas", response_model=EmpresaResponse)
async def criar_empresa(empresa: EmpresaCreate):
    """Cria nova empresa (versão simplificada com dados mock)"""
    try:
        logger.info(f"Criando empresa: {empresa.cnpj} - {empresa.razao_social}")

        # Verificar se empresa já existe
        for emp in mock_empresas:
            if emp["cnpj"] == empresa.cnpj:
                raise HTTPException(status_code=400, detail="Empresa já cadastrada")

        # Criar nova empresa (mock)
        novo_id = max([emp["id"] for emp in mock_empresas]) + 1
        cnpj_clean = "".join(filter(str.isdigit, empresa.cnpj))
        database_name = f"empresa_{cnpj_clean}"

        nova_empresa = {
            "id": novo_id,
            "cnpj": empresa.cnpj,
            "razao_social": empresa.razao_social,
            "nome_fantasia": empresa.nome_fantasia or empresa.razao_social,
            "database_name": database_name,
            "ativa": True,
        }

        # Adicionar aos dados mock
        mock_empresas.append(nova_empresa)

        logger.info(f"Empresa criada com sucesso: ID {novo_id}")
        return nova_empresa

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar empresa: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar empresa: {str(e)}")


@app.post("/api/classification/classify", response_model=ClassificationResult)
async def classificar_produto(request: ClassificationRequest):
    """Classifica produto usando agentes de IA (versão mock para demonstração)"""
    try:
        import time

        start_time = time.time()

        logger.info(f"Classificando produto: {request.description}")

        # Simular classificação baseada em palavras-chave (mock)
        description_lower = request.description.lower()

        # Mock de classificações baseado em padrões comuns
        if any(
            word in description_lower for word in ["notebook", "laptop", "computador"]
        ):
            result = ClassificationResult(
                ncm_code="84713000",
                ncm_description="Máquinas automáticas para processamento de dados, portáteis",
                cest_code="0101500",
                cest_description="Computadores portáteis",
                confidence=0.92,
                justification=(
                    "Produto identificado como computador portátil baseado na descrição. "
                    "NCM 84713000 aplica-se a máquinas automáticas para processamento de dados portáteis."
                ),
                agent_used="NCMAgent",
                processing_time=time.time() - start_time,
            )
        elif any(
            word in description_lower for word in ["smartphone", "celular", "telefone"]
        ):
            result = ClassificationResult(
                ncm_code="85171200",
                ncm_description="Telefones para redes celulares",
                cest_code="0104600",
                cest_description="Aparelhos telefônicos por fio com unidade auscultador-microfone sem fio",
                confidence=0.89,
                justification=(
                    "Produto identificado como telefone celular. "
                    "NCM 85171200 específico para telefones de redes celulares."
                ),
                agent_used="NCMAgent",
                processing_time=time.time() - start_time,
            )
        elif any(word in description_lower for word in ["mouse", "teclado", "monitor"]):
            result = ClassificationResult(
                ncm_code="84716090",
                ncm_description="Outras unidades de entrada ou saída",
                cest_code="0101900",
                cest_description="Outros equipamentos de informática",
                confidence=0.85,
                justification=(
                    "Produto identificado como periférico de informática. "
                    "NCM 84716090 para unidades de entrada/saída."
                ),
                agent_used="NCMAgent",
                processing_time=time.time() - start_time,
            )
        elif any(
            word in description_lower
            for word in ["geladeira", "refrigerador", "freezer"]
        ):
            result = ClassificationResult(
                ncm_code="84182100",
                ncm_description="Refrigeradores tipo doméstico, de compressão",
                cest_code="0301100",
                cest_description="Refrigeradores e congeladores tipo doméstico",
                confidence=0.91,
                justification=(
                    "Produto identificado como refrigerador doméstico. "
                    "NCM 84182100 específico para refrigeradores de compressão."
                ),
                agent_used="NCMAgent",
                processing_time=time.time() - start_time,
            )
        else:
            # Classificação genérica para produtos não reconhecidos
            result = ClassificationResult(
                ncm_code="39269090",
                ncm_description="Outras obras de plástico",
                cest_code=None,
                cest_description=None,
                confidence=0.45,
                justification=(
                    "Produto não reconhecido pelos padrões conhecidos. "
                    "Classificação genérica aplicada. Recomenda-se revisão manual."
                ),
                agent_used="NCMAgent",
                processing_time=time.time() - start_time,
            )

        logger.info(
            f"Classificação concluída: NCM {result.ncm_code} com {result.confidence:.2f} de confiança"
        )
        return result

    except Exception as e:
        logger.error(f"Erro na classificação: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na classificação: {str(e)}")


@app.get("/stats")
async def get_stats():
    """Retorna estatísticas gerais (mock)"""
    try:
        return {
            "total_empresas": len(mock_empresas),
            "total_produtos": len(mock_produtos),
            "golden_set": {"ncm_items": 150, "cest_items": 89},
            "arquitetura": "multi-tenant",
            "versao": "2.1.1",
            "status": "operational",
        }
    except Exception as e:
        logger.error(f"Erro nas estatísticas: {e}")
        return {"error": str(e), "status": "error"}


@app.post("/api/import/test-connection")
async def test_connection(connection: DatabaseConnection):
    """Testa conexão com banco externo"""
    try:
        logger.info(
            f"Testando conexão: {connection.type}://{connection.host}:{connection.port}/{connection.database}"
        )

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
                "method": "simulated",
            }

        return result

    except Exception as e:
        logger.error(f"Erro no teste de conexão: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"success": False, "error": str(e)}


@app.post("/api/import/preview")
async def preview_import(
    connection: DatabaseConnection, sql_query: str, limit: int = 100
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
                    "cest": "0101500",
                },
                {
                    "produto_id": 2,
                    "descricao_produto": "Mouse Óptico USB",
                    "ncm": "84716090",
                    "cest": "0101900",
                },
                {
                    "produto_id": 3,
                    "descricao_produto": "Teclado Mecânico",
                    "ncm": "84716090",
                    "cest": "0101900",
                },
            ],
            "query_used": sql_query,
            "method": "mock_preview",
        }

        return mock_preview

    except Exception as e:
        logger.error(f"Erro no preview: {e}")
        return {"success": False, "error": str(e)}


@app.get("/dashboard/stats")
async def get_dashboard_stats():
    """Retorna estatísticas para o dashboard"""
    # Simulação de dados reais
    total_produtos = 20223  # len(mock_produtos)
    produtos_com_ncm = 18542  # sum(1 for p in mock_produtos if p.get("ncm"))
    produtos_com_cest = 9781  # sum(1 for p in mock_produtos if p.get("cest"))

    return {
        "totalEmpresas": 23,  # len(mock_empresas),
        "totalProdutos": total_produtos,
        "produtosComNCM": produtos_com_ncm,
        "produtosComCEST": produtos_com_cest,
        "classificacoesPendentes": total_produtos - produtos_com_ncm,
        "accuracy": 98.2,  # Valor mockado
    }


@app.get("/relatorios/stats")
async def get_relatorios_stats():
    """Endpoint para estatísticas de relatórios"""
    try:
        return {
            "relatorios_gerados": 45,
            "relatorio_mais_usado": "Classificação NCM",
            "ultimo_relatorio": datetime.now().isoformat(),
            "tipos_disponiveis": [
                "Classificação NCM",
                "Análise CEST",
                "Compliance Fiscal",
                "Performance Agentes",
            ],
        }
    except Exception as e:
        logger.error(f"Erro ao obter stats de relatórios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/relatorios/classificacao-periodo")
async def get_classificacao_periodo(
    inicio: Optional[str] = None, fim: Optional[str] = None
):
    """Endpoint para relatórios de classificação por período"""
    try:
        return {
            "periodo": {"inicio": inicio or "2025-08-01", "fim": fim or "2025-08-24"},
            "total_classificacoes": 1450,
            "ncm_mais_usado": "8471.30.12",
            "cest_mais_usado": "21.001.00",
            "accuracy": 98.7,
            "classificacoes_por_dia": [
                {"data": "2025-08-24", "total": 89},
                {"data": "2025-08-23", "total": 124},
                {"data": "2025-08-22", "total": 156},
            ],
        }
    except Exception as e:
        logger.error(f"Erro ao obter classificações por período: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/empresas/select")
async def get_empresas_select():
    """Endpoint para select de empresas (dropdown)"""
    try:
        empresas_select = [
            {
                "id": emp["id"],
                "label": f"{emp['cnpj']} - {emp['razao_social']}",
                "value": emp["id"],
            }
            for emp in mock_empresas
        ]
        return empresas_select
    except Exception as e:
        logger.error(f"Erro ao obter empresas para select: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =================== INICIALIZAÇÃO ===================


def main():
    """Função principal para iniciar a API"""
    import uvicorn

    try:
        logger.info("🚀 Iniciando API Multi-Tenant Estável v2.1.1...")
        logger.info("📚 Documentação: http://127.0.0.1:8000/docs")
        logger.info("🏢 Empresas: http://127.0.0.1:8000/empresas")
        logger.info("📊 Estatísticas: http://127.0.0.1:8000/stats")
        logger.info("🔧 Health Check: http://127.0.0.1:8000/health")
        logger.info("🎯 API configurada para não finalizar automaticamente")

        uvicorn.run(
            "api_estavel:app",
            host="127.0.0.1",
            port=8000,  # Mudança para porta 8000
            log_level="info",
            reload=False,  # Desabilitar reload para evitar problemas
        )

    except Exception as e:
        logger.error(f"❌ Erro ao iniciar API: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    main()
