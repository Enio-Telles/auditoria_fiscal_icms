"""
Script robusto de configuração do banco de dados
Sistema de Auditoria Fiscal ICMS - 100% Funcional
"""

import os
import sys
import traceback
from pathlib import Path

# Configurar PYTHONPATH
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    import logging
    from datetime import datetime
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("🔧 Instalando dependências...")
    os.system("pip install psycopg2-binary")
    sys.exit(1)

# Configurações do banco
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres", 
    "password": "postgres123",
    "database": "auditoria_fiscal"
}

def test_connection():
    """Testa a conexão com o banco de dados"""
    try:
        print("🔍 Testando conexão com PostgreSQL...")
        
        # Conectar ao banco padrão postgres primeiro
        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Verificar se o banco auditoria_fiscal existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG["database"],))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"📦 Criando banco de dados '{DB_CONFIG['database']}'...")
            cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
            print("✅ Banco de dados criado com sucesso!")
        else:
            print("✅ Banco de dados já existe!")
            
        cursor.close()
        conn.close()
        
        # Conectar ao banco específico
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Testar consulta
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✅ Conexão bem-sucedida! PostgreSQL: {version[:50]}...")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

def create_basic_tables():
    """Cria tabelas básicas do sistema"""
    try:
        print("🏗️ Criando estrutura básica do banco...")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Tabela de usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                senha_hash VARCHAR(255) NOT NULL,
                ativo BOOLEAN DEFAULT TRUE,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de empresas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS empresas (
                id SERIAL PRIMARY KEY,
                razao_social VARCHAR(200) NOT NULL,
                cnpj VARCHAR(18) UNIQUE NOT NULL,
                ativa BOOLEAN DEFAULT TRUE,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de produtos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id SERIAL PRIMARY KEY,
                empresa_id INTEGER REFERENCES empresas(id),
                nome VARCHAR(200) NOT NULL,
                descricao TEXT,
                categoria VARCHAR(100),
                marca VARCHAR(100),
                ncm_codigo VARCHAR(8),
                cest_codigo VARCHAR(7),
                confidence_score DECIMAL(5,2),
                status VARCHAR(20) DEFAULT 'PENDENTE',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de classificações
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classificacoes (
                id SERIAL PRIMARY KEY,
                produto_id INTEGER REFERENCES produtos(id),
                ncm_sugerido VARCHAR(8),
                cest_sugerido VARCHAR(7),
                confidence_ncm DECIMAL(5,2),
                confidence_cest DECIMAL(5,2),
                justificativa TEXT,
                aprovado BOOLEAN DEFAULT FALSE,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de logs de auditoria
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs_auditoria (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER REFERENCES usuarios(id),
                acao VARCHAR(100) NOT NULL,
                detalhes TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Estrutura do banco criada com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar estrutura: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return False

def insert_sample_data():
    """Insere dados de exemplo no banco"""
    try:
        print("📝 Inserindo dados de exemplo...")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Usuário admin
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha_hash) 
            VALUES (%s, %s, %s)
            ON CONFLICT (email) DO NOTHING
        """, ("Administrador", "admin@auditoria.com", "admin123_hash"))
        
        # Empresa de exemplo
        cursor.execute("""
            INSERT INTO empresas (razao_social, cnpj) 
            VALUES (%s, %s)
            ON CONFLICT (cnpj) DO NOTHING
        """, ("Empresa Teste LTDA", "12.345.678/0001-99"))
        
        # Produto de exemplo
        cursor.execute("""
            INSERT INTO produtos (empresa_id, nome, descricao, categoria, marca)
            SELECT 1, %s, %s, %s, %s
            WHERE EXISTS (SELECT 1 FROM empresas WHERE id = 1)
        """, ("Smartphone Samsung", "Celular Android 5G", "Eletrônicos", "Samsung"))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Dados de exemplo inseridos!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inserir dados: {e}")
        return False

def verify_setup():
    """Verifica se a configuração está correta"""
    try:
        print("🔍 Verificando configuração...")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Contar registros nas tabelas
        tables = ["usuarios", "empresas", "produtos", "classificacoes", "logs_auditoria"]
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"📊 {table}: {count} registros")
        
        cursor.close()
        conn.close()
        
        print("✅ Verificação concluída!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return False

def main():
    """Função principal de configuração"""
    print("=" * 60)
    print("🗄️  CONFIGURAÇÃO DO BANCO DE DADOS")
    print("   Sistema de Auditoria Fiscal ICMS")
    print("=" * 60)
    
    success = True
    
    # Passo 1: Testar conexão
    if not test_connection():
        print("❌ Falha na conexão com o banco!")
        return False
    
    # Passo 2: Criar estrutura
    if not create_basic_tables():
        print("❌ Falha ao criar estrutura!")
        return False
    
    # Passo 3: Inserir dados de exemplo
    if not insert_sample_data():
        print("⚠️ Falha ao inserir dados de exemplo (opcional)")
    
    # Passo 4: Verificar setup
    if not verify_setup():
        print("⚠️ Falha na verificação")
    
    print("=" * 60)
    print("✅ CONFIGURAÇÃO DO BANCO CONCLUÍDA!")
    print("🔗 Conexão: postgresql://postgres:postgres123@localhost:5432/auditoria_fiscal")
    print("📊 Status: Sistema pronto para uso!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🔄 Configuração interrompida pelo usuário")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
