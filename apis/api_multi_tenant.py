"""
API FastAPI Multi-Tenant para Sistema de Auditoria Fiscal ICMS
Versão 2.0 - Suporte a bancos separados por empresa
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import subprocess
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import uuid
import threading
import time
import sqlalchemy
from sqlalchemy import create_engine, text
import sys
import os

# Adicionar src ao path para importar nossos módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from auditoria_icms.data_processing.data_extractor import (
        DataExtractor, 
        DatabaseConfig, 
        ExtractionConfig
    )
    DATA_EXTRACTOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Módulo de extração não disponível: {e}")
    DATA_EXTRACTOR_AVAILABLE = False
try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False
    
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

# Configurações
DB_HOST = "localhost"
DB_PORT = "5432" 
DB_USER = "postgres"
DB_PASSWORD = "postgres123"

# Inicializar FastAPI
app = FastAPI(
    title="Sistema de Auditoria Fiscal ICMS - Multi-Tenant",
    description="API para classificação automática NCM/CEST com isolamento por empresa",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# =================== MODELOS PYDANTIC ===================

class Usuario(BaseModel):
    username: str
    email: str
    nome_completo: Optional[str] = None

class EmpresaCreate(BaseModel):
    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str] = None
    atividade_principal: Optional[str] = None
    regime_tributario: Optional[str] = None

class EmpresaResponse(BaseModel):
    id: int
    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str]
    database_name: str
    ativa: bool

class ProdutoCreate(BaseModel):
    codigo_interno: Optional[str] = None
    ean: Optional[str] = None
    nome: str
    descricao: Optional[str] = None
    categoria: Optional[str] = None
    marca: Optional[str] = None
    preco_venda: Optional[float] = None

class ProdutoResponse(BaseModel):
    id: int
    nome: str
    descricao: Optional[str]
    categoria: Optional[str]
    marca: Optional[str]
    ncm_codigo: Optional[str]
    cest_codigo: Optional[str]
    criado_em: datetime

class ClassificacaoRequest(BaseModel):
    produto_id: int
    forcar_reclassificacao: bool = False

class ClassificacaoResponse(BaseModel):
    produto_id: int
    ncm_sugerido: Optional[str]
    ncm_confianca: Optional[float]
    cest_sugerido: Optional[str]
    cest_confianca: Optional[float]
    justificativa: Optional[str]
    status: str

# Modelos para Importação de Dados
class DatabaseConnection(BaseModel):
    type: str  # sqlserver, postgresql, mysql
    host: str
    port: int
    database: str
    schema: Optional[str] = "dbo"
    user: str
    password: str

class ImportConfig(BaseModel):
    empresa_id: int
    sql_query: str
    connection: DatabaseConnection
    batch_size: int = 1000
    update_existing: bool = False

class PreviewData(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    total_count: int
    sample_size: int

class ImportJob(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed
    total_records: int
    processed_records: int
    error_message: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None

# =================== CONEXÕES DE BANCO ===================

def get_db_connection(database_name: str):
    """Cria conexão com banco específico"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=database_name,
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro de conexão com banco {database_name}: {str(e)}")

def execute_query(database_name: str, query: str, params=None, fetch=True):
    """Executa query em banco específico"""
    conn = None
    try:
        conn = get_db_connection(database_name)
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if fetch:
            result = cursor.fetchall()
            conn.commit()
            return result
        else:
            conn.commit()
            return cursor.rowcount
            
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erro na query: {str(e)}")
    finally:
        if conn:
            conn.close()

# =================== FUNCÕES DE IMPORTAÇÃO ===================

# Armazenar jobs de importação em memória (em produção usar Redis ou banco)
import_jobs = {}

def create_external_connection(connection: DatabaseConnection):
    """Cria conexão com banco externo"""
    try:
        if connection.type == "sqlserver":
            if not PYODBC_AVAILABLE:
                raise HTTPException(status_code=501, detail="SQL Server requer pyodbc. Instale com: pip install pyodbc")
            
            conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={connection.host},{connection.port};DATABASE={connection.database};UID={connection.user};PWD={connection.password}"
            conn = pyodbc.connect(conn_str)
            return conn
        
        elif connection.type == "postgresql":
            conn = psycopg2.connect(
                host=connection.host,
                port=connection.port,
                user=connection.user,
                password=connection.password,
                database=connection.database
            )
            return conn
            
        elif connection.type == "mysql":
            if not MYSQL_AVAILABLE:
                raise HTTPException(status_code=501, detail="MySQL requer mysql-connector-python. Instale com: pip install mysql-connector-python")
            
            conn = mysql.connector.connect(
                host=connection.host,
                port=connection.port,
                user=connection.user,
                password=connection.password,
                database=connection.database
            )
            return conn
        
        else:
            raise HTTPException(status_code=400, detail=f"Tipo de banco não suportado: {connection.type}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar ao banco externo: {str(e)}")

def test_external_connection(connection: DatabaseConnection):
    """Testa conexão com banco externo usando o módulo de extração"""
    try:
        if not DATA_EXTRACTOR_AVAILABLE:
            return {"success": False, "error": "Módulo de extração não disponível"}
        
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
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def preview_external_data(connection: DatabaseConnection, sql_query: str, limit: int = 100):
    """Faz preview dos dados do banco externo"""
    try:
        conn = create_external_connection(connection)
        cursor = conn.cursor()
        
        # Executar query com LIMIT baseado no tipo de banco
        if connection.type == "sqlserver":
            limited_query = f"SELECT TOP {limit} * FROM ({sql_query}) subquery"
        elif connection.type == "mysql":
            limited_query = f"SELECT * FROM ({sql_query}) subquery LIMIT {limit}"
        else:  # PostgreSQL
            limited_query = f"SELECT * FROM ({sql_query}) subquery LIMIT {limit}"
            
        cursor.execute(limited_query)
        rows = cursor.fetchall()
        
        # Obter nomes das colunas
        if rows:
            if connection.type == "postgresql":
                columns = [desc[0] for desc in cursor.description]
                data_rows = [[row[col] for col in columns] for row in rows]
            else:
                columns = [desc[0] for desc in cursor.description]
                data_rows = [list(row) for row in rows]
        else:
            columns = []
            data_rows = []
        
        # Contar total de registros
        count_query = f"SELECT COUNT(*) as total FROM ({sql_query}) subquery"
        cursor.execute(count_query)
        total_result = cursor.fetchone()
        total_count = total_result[0] if total_result else 0
        
        conn.close()
        
        return PreviewData(
            columns=columns,
            rows=data_rows,
            total_count=total_count,
            sample_size=len(data_rows)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no preview: {str(e)}")

def execute_import_job(job_id: str, config: ImportConfig):
    """Executa importação em background"""
    try:
        # Atualizar status para running
        import_jobs[job_id]["status"] = "running"
        import_jobs[job_id]["start_time"] = datetime.now()
        
        # Conectar ao banco externo
        external_conn = create_external_connection(config.connection)
        external_cursor = external_conn.cursor()
        
        # Executar query completa
        external_cursor.execute(config.sql_query)
        
        # Obter nome do banco da empresa
        empresa_db = get_empresa_database(config.empresa_id)
        
        # Processar em lotes
        processed = 0
        batch_size = config.batch_size
        
        while True:
            rows = external_cursor.fetchmany(batch_size)
            if not rows:
                break
                
            # Inserir lote no banco da empresa
            for row in rows:
                try:
                    # Mapear dados do produto
                    produto_data = {
                        'nome': row.get('descricao_produto', ''),
                        'descricao': row.get('descricao_produto', ''),
                        'codigo_produto': row.get('codigo_produto', ''),
                        'codigo_barra': row.get('codigo_barra', ''),
                        'ncm_codigo': row.get('ncm', ''),
                        'cest_codigo': row.get('cest', '')
                    }
                    
                    # Verificar se produto já existe
                    if config.update_existing:
                        # Lógica de update
                        query = """
                        INSERT INTO produtos (nome, descricao, codigo_produto, codigo_barra, ncm_codigo, cest_codigo, criado_em)
                        VALUES (%(nome)s, %(descricao)s, %(codigo_produto)s, %(codigo_barra)s, %(ncm_codigo)s, %(cest_codigo)s, NOW())
                        ON CONFLICT (codigo_produto) DO UPDATE SET
                        descricao = EXCLUDED.descricao,
                        ncm_codigo = EXCLUDED.ncm_codigo,
                        cest_codigo = EXCLUDED.cest_codigo,
                        atualizado_em = NOW()
                        """
                    else:
                        # Apenas inserir novos
                        query = """
                        INSERT INTO produtos (nome, descricao, codigo_produto, codigo_barra, ncm_codigo, cest_codigo, criado_em)
                        VALUES (%(nome)s, %(descricao)s, %(codigo_produto)s, %(codigo_barra)s, %(ncm_codigo)s, %(cest_codigo)s, NOW())
                        ON CONFLICT (codigo_produto) DO NOTHING
                        """
                    
                    execute_query(empresa_db, query, produto_data, fetch=False)
                    processed += 1
                    
                except Exception as e:
                    print(f"Erro ao inserir produto: {e}")
                    continue
            
            # Atualizar progresso
            import_jobs[job_id]["processed_records"] = processed
        
        # Finalizar
        external_conn.close()
        import_jobs[job_id]["status"] = "completed"
        import_jobs[job_id]["end_time"] = datetime.now()
        
    except Exception as e:
        import_jobs[job_id]["status"] = "failed"
        import_jobs[job_id]["error_message"] = str(e)
        import_jobs[job_id]["end_time"] = datetime.now()

def get_empresa_database(empresa_id: int) -> str:
    """Obtém nome do banco da empresa"""
    try:
        query = "SELECT database_name FROM empresas WHERE id = %s"
        result = execute_query("auditoria_central", query, (empresa_id,))
        if not result:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        return result[0]['database_name']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter banco da empresa: {str(e)}")

# =================== ENDPOINTS DE SISTEMA ===================

@app.get("/")
async def root():
    return {
        "message": "Sistema de Auditoria Fiscal ICMS - Multi-Tenant",
        "version": "2.0.0",
        "status": "online",
        "features": [
            "Bancos separados por empresa",
            "Golden Set centralizado",
            "Classificação IA NCM/CEST",
            "Auditoria completa"
        ]
    }

@app.get("/health")
async def health():
    """Endpoint de saúde do sistema"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

# =================== ENDPOINTS DE EMPRESAS ===================

@app.get("/empresas", response_model=List[EmpresaResponse])
async def listar_empresas():
    """Lista todas as empresas cadastradas"""
    query = """
    SELECT id, cnpj, razao_social, nome_fantasia, database_name, ativa
    FROM empresas 
    WHERE ativa = TRUE
    ORDER BY razao_social
    """
    
    result = execute_query("auditoria_central", query)
    return result

@app.post("/empresas", response_model=EmpresaResponse)
async def criar_empresa(empresa: EmpresaCreate):
    """Cria nova empresa com banco dedicado"""
    
    # Sanitizar CNPJ para nome do banco
    cnpj_clean = ''.join(filter(str.isdigit, empresa.cnpj))
    database_name = f"empresa_{cnpj_clean}"
    
    try:
        # 1. Verificar se empresa já existe
        check_query = "SELECT id FROM empresas WHERE cnpj = %s"
        existing = execute_query("auditoria_central", check_query, (empresa.cnpj,))
        
        if existing:
            raise HTTPException(status_code=400, detail="Empresa já cadastrada")
        
        # 2. Criar banco da empresa via subprocess (mesma lógica do script)
        docker_cmd = [
            "docker", "exec", "auditoria_postgresql",
            "psql", "-U", "postgres", "-d", "postgres", 
            "-c", f'CREATE DATABASE "{database_name}"'
        ]
        
        subprocess.run(docker_cmd, check=True, capture_output=True, text=True)
        
        # 3. Criar tabelas no banco da empresa
        produtos_sql = """
        CREATE TABLE IF NOT EXISTS produtos (
            id SERIAL PRIMARY KEY,
            codigo_interno VARCHAR(50),
            ean VARCHAR(20),
            nome TEXT NOT NULL,
            descricao TEXT,
            categoria VARCHAR(100),
            subcategoria VARCHAR(100),
            marca VARCHAR(100),
            modelo VARCHAR(100),
            unidade VARCHAR(10),
            preco_custo NUMERIC(12,2),
            preco_venda NUMERIC(12,2),
            estoque_atual INTEGER,
            ncm_codigo VARCHAR(10),
            cest_codigo VARCHAR(7),
            origem VARCHAR(1),
            cst_icms VARCHAR(3),
            aliquota_icms NUMERIC(5,2),
            ativo BOOLEAN DEFAULT TRUE,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        classificacoes_sql = """
        CREATE TABLE IF NOT EXISTS classificacoes_ia (
            id SERIAL PRIMARY KEY,
            produto_id INTEGER REFERENCES produtos(id),
            ncm_sugerido VARCHAR(10),
            ncm_confianca NUMERIC(5,2),
            cest_sugerido VARCHAR(7),
            cest_confianca NUMERIC(5,2),
            justificativa TEXT,
            agente_usado VARCHAR(50),
            status VARCHAR(20),
            processado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            aprovado_por VARCHAR(100),
            aprovado_em TIMESTAMP
        );
        """
        
        execute_query(database_name, produtos_sql, fetch=False)
        execute_query(database_name, classificacoes_sql, fetch=False)
        
        # 4. Registrar empresa no banco central
        insert_query = """
        INSERT INTO empresas (cnpj, razao_social, nome_fantasia, atividade_principal, regime_tributario, database_name)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, cnpj, razao_social, nome_fantasia, database_name, ativa
        """
        
        result = execute_query("auditoria_central", insert_query, (
            empresa.cnpj,
            empresa.razao_social,
            empresa.nome_fantasia,
            empresa.atividade_principal,
            empresa.regime_tributario,
            database_name
        ))
        
        return result[0]
        
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar banco: {e.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar empresa: {str(e)}")

@app.get("/empresas/{empresa_id}/produtos", response_model=List[ProdutoResponse])
async def listar_produtos_empresa(empresa_id: int):
    """Lista produtos de uma empresa específica"""
    
    # Buscar database_name da empresa
    empresa_query = "SELECT database_name FROM empresas WHERE id = %s AND ativa = TRUE"
    empresa_result = execute_query("auditoria_central", empresa_query, (empresa_id,))
    
    if not empresa_result:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    database_name = empresa_result[0]['database_name']
    
    # Buscar produtos no banco da empresa
    produtos_query = """
    SELECT id, nome, descricao, categoria, marca, ncm_codigo, cest_codigo, criado_em
    FROM produtos 
    WHERE ativo = TRUE
    ORDER BY nome
    """
    
    produtos = execute_query(database_name, produtos_query)
    return produtos

@app.post("/empresas/{empresa_id}/produtos", response_model=ProdutoResponse)
async def criar_produto(empresa_id: int, produto: ProdutoCreate):
    """Cria novo produto para uma empresa"""
    
    # Buscar database_name da empresa
    empresa_query = "SELECT database_name FROM empresas WHERE id = %s AND ativa = TRUE"
    empresa_result = execute_query("auditoria_central", empresa_query, (empresa_id,))
    
    if not empresa_result:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    database_name = empresa_result[0]['database_name']
    
    # Inserir produto no banco da empresa
    insert_query = """
    INSERT INTO produtos (codigo_interno, ean, nome, descricao, categoria, marca, preco_venda)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    RETURNING id, nome, descricao, categoria, marca, ncm_codigo, cest_codigo, criado_em
    """
    
    result = execute_query(database_name, insert_query, (
        produto.codigo_interno,
        produto.ean,
        produto.nome,
        produto.descricao,
        produto.categoria,
        produto.marca,
        produto.preco_venda
    ))
    
    return result[0]

# =================== ENDPOINTS DE CLASSIFICAÇÃO ===================

@app.post("/empresas/{empresa_id}/classificar", response_model=ClassificacaoResponse)
async def classificar_produto(empresa_id: int, request: ClassificacaoRequest):
    """Classifica produto usando IA (simulado)"""
    
    # Buscar database_name da empresa
    empresa_query = "SELECT database_name FROM empresas WHERE id = %s AND ativa = TRUE"
    empresa_result = execute_query("auditoria_central", empresa_query, (empresa_id,))
    
    if not empresa_result:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    database_name = empresa_result[0]['database_name']
    
    # Buscar produto
    produto_query = "SELECT * FROM produtos WHERE id = %s AND ativo = TRUE"
    produto_result = execute_query(database_name, produto_query, (request.produto_id,))
    
    if not produto_result:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    produto = produto_result[0]
    
    # Simulação de classificação IA
    # Em produção, aqui seria chamado o sistema de agentes
    ncm_sugerido = "84713000"  # Notebook genérico
    cest_sugerido = "0101500"  # Equipamentos de informática
    
    if "farmac" in produto['nome'].lower() or "medicamento" in (produto['descricao'] or '').lower():
        ncm_sugerido = "30049099"
        cest_sugerido = "2800100"
    elif "smartphone" in produto['nome'].lower() or "celular" in produto['nome'].lower():
        ncm_sugerido = "85171200"
        cest_sugerido = "0700800"
    
    # Salvar classificação
    classificacao_query = """
    INSERT INTO classificacoes_ia (produto_id, ncm_sugerido, ncm_confianca, cest_sugerido, cest_confianca, justificativa, agente_usado, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING *
    """
    
    classificacao_result = execute_query(database_name, classificacao_query, (
        request.produto_id,
        ncm_sugerido,
        85.5,  # Confiança NCM
        cest_sugerido,
        78.2,  # Confiança CEST
        f"Classificação baseada em análise do nome '{produto['nome']}' e descrição",
        "AgenteMockV2",
        "processado"
    ), fetch=True)
    
    result = classificacao_result[0]
    
    return ClassificacaoResponse(
        produto_id=result['produto_id'],
        ncm_sugerido=result['ncm_sugerido'],
        ncm_confianca=float(result['ncm_confianca']),
        cest_sugerido=result['cest_sugerido'],
        cest_confianca=float(result['cest_confianca']),
        justificativa=result['justificativa'],
        status=result['status']
    )

# =================== ENDPOINTS DO GOLDEN SET ===================

@app.get("/golden-set/ncm")
async def listar_golden_set_ncm():
    """Lista itens do Golden Set NCM"""
    query = """
    SELECT * FROM golden_set_ncm 
    WHERE ativo = TRUE 
    ORDER BY produto_nome
    """
    
    result = execute_query("golden_set", query)
    return result

@app.post("/golden-set/ncm")
async def adicionar_golden_set_ncm(
    produto_nome: str,
    ncm_codigo: str,
    produto_descricao: str = None,
    categoria: str = None
):
    """Adiciona item ao Golden Set NCM"""
    
    insert_query = """
    INSERT INTO golden_set_ncm (produto_nome, produto_descricao, categoria, ncm_codigo, fonte, validado_por)
    VALUES (%s, %s, %s, %s, 'API', 'Sistema')
    RETURNING *
    """
    
    result = execute_query("golden_set", insert_query, (
        produto_nome,
        produto_descricao,
        categoria,
        ncm_codigo
    ))
    
    return result[0]

# =================== ENDPOINTS DE IMPORTAÇÃO ===================

@app.post("/api/import/test-connection")
async def test_connection(connection: DatabaseConnection):
    """Testa conexão com banco externo"""
    return test_external_connection(connection)

@app.post("/api/import/preview")
async def preview_import(
    connection: DatabaseConnection,
    sql_query: str,
    limit: int = 100
):
    """Faz preview dos dados a serem importados"""
    return preview_external_data(connection, sql_query, limit)

@app.post("/api/import/execute")
async def execute_import(config: ImportConfig):
    """Executa importação de dados em background"""
    
    # Gerar ID único para o job
    job_id = str(uuid.uuid4())
    
    # Fazer preview primeiro para obter total de registros
    preview = preview_external_data(config.connection, config.sql_query, limit=1)
    total_records = preview.total_count
    
    # Criar job
    job = {
        "job_id": job_id,
        "status": "pending",
        "total_records": total_records,
        "processed_records": 0,
        "error_message": None,
        "start_time": datetime.now()
    }
    
    import_jobs[job_id] = job
    
    # Executar importação em thread separada
    thread = threading.Thread(target=execute_import_job, args=(job_id, config))
    thread.start()
    
    return ImportJob(**job)

@app.get("/api/import/status/{job_id}")
async def get_import_status(job_id: str):
    """Obtém status da importação"""
    if job_id not in import_jobs:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    job_data = import_jobs[job_id]
    return ImportJob(**job_data)

# =================== ENDPOINTS DE ESTATÍSTICAS ===================

@app.get("/stats")
async def estatisticas_sistema():
    """Estatísticas gerais do sistema"""
    
    # Contar empresas
    empresas_query = "SELECT COUNT(*) as count FROM empresas WHERE ativa = TRUE"
    empresas_result = execute_query("auditoria_central", empresas_query)
    total_empresas = empresas_result[0]['count']
    
    # Contar itens no Golden Set
    golden_ncm_query = "SELECT COUNT(*) as count FROM golden_set_ncm WHERE ativo = TRUE"
    golden_ncm_result = execute_query("golden_set", golden_ncm_query)
    total_golden_ncm = golden_ncm_result[0]['count']
    
    golden_cest_query = "SELECT COUNT(*) as count FROM golden_set_cest WHERE ativo = TRUE"
    golden_cest_result = execute_query("golden_set", golden_cest_query)
    total_golden_cest = golden_cest_result[0]['count']
    
    # Contar produtos por empresa (exemplo da primeira empresa)
    total_produtos = 0
    empresas_query = "SELECT database_name FROM empresas WHERE ativa = TRUE LIMIT 5"
    empresas_result = execute_query("auditoria_central", empresas_query)
    
    for empresa in empresas_result:
        try:
            produtos_query = "SELECT COUNT(*) as count FROM produtos WHERE ativo = TRUE"
            produtos_result = execute_query(empresa['database_name'], produtos_query)
            total_produtos += produtos_result[0]['count']
        except:
            pass  # Empresa pode não ter produtos ainda
    
    return {
        "total_empresas": total_empresas,
        "total_produtos": total_produtos,
        "golden_set": {
            "ncm_items": total_golden_ncm,
            "cest_items": total_golden_cest
        },
        "arquitetura": "multi-tenant",
        "versao": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando API Multi-Tenant...")
    print("📚 Documentação: http://127.0.0.1:8003/docs")
    print("🏢 Empresas: http://127.0.0.1:8003/empresas")
    print("📊 Estatísticas: http://127.0.0.1:8003/stats")
    
    uvicorn.run(app, host="127.0.0.1", port=8003)
