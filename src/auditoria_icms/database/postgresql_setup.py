"""
Configuração PostgreSQL - Fase 6
Scripts de inicialização e configuração do banco de dados
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from ..core.config import get_settings


class PostgreSQLSetup:
    """Configuração e inicialização do PostgreSQL"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.db_config = self._get_db_config()
    
    def _get_db_config(self) -> Dict[str, str]:
        """Obtém configuração do banco de dados"""
        return {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "database": os.getenv("DB_NAME", "auditoria_icms"),
            "username": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "postgres"),
            "admin_database": os.getenv("ADMIN_DB", "postgres")
        }
    
    def setup_database(self) -> bool:
        """Configura o banco de dados completo"""
        try:
            self.logger.info("Iniciando configuração do PostgreSQL...")
            
            # 1. Criar banco de dados se não existir
            if not self._create_database():
                return False
            
            # 2. Executar scripts de inicialização
            if not self._run_init_scripts():
                return False
            
            # 3. Criar tabelas estruturais
            if not self._create_structural_tables():
                return False
            
            # 4. Popular dados de referência
            if not self._populate_reference_data():
                return False
            
            # 5. Configurar índices e otimizações
            if not self._setup_indexes():
                return False
            
            self.logger.info("PostgreSQL configurado com sucesso!")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na configuração do PostgreSQL: {e}")
            return False
    
    def _create_database(self) -> bool:
        """Cria o banco de dados se não existir"""
        try:
            # Conectar ao banco admin
            admin_conn = psycopg2.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                database=self.db_config["admin_database"],
                user=self.db_config["username"],
                password=self.db_config["password"]
            )
            admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = admin_conn.cursor()
            
            # Verificar se banco existe
            cursor.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                (self.db_config["database"],)
            )
            
            if not cursor.fetchone():
                # Criar banco
                cursor.execute(f'CREATE DATABASE "{self.db_config["database"]}"')
                self.logger.info(f"Banco de dados {self.db_config['database']} criado")
            else:
                self.logger.info(f"Banco de dados {self.db_config['database']} já existe")
            
            cursor.close()
            admin_conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao criar banco de dados: {e}")
            return False
    
    def _run_init_scripts(self) -> bool:
        """Executa scripts de inicialização"""
        try:
            engine = self._get_engine()
            
            # Script de inicialização básica
            init_sql = self._get_init_sql()
            
            with engine.connect() as conn:
                # Executar script em blocos
                for sql_block in init_sql.split(';'):
                    sql_block = sql_block.strip()
                    if sql_block:
                        conn.execute(text(sql_block))
                conn.commit()
            
            self.logger.info("Scripts de inicialização executados")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao executar scripts de inicialização: {e}")
            return False
    
    def _create_structural_tables(self) -> bool:
        """Cria tabelas estruturais do sistema"""
        try:
            engine = self._get_engine()
            
            # SQL para tabelas estruturais
            structural_sql = """
            -- Tabela de empresas
            CREATE TABLE IF NOT EXISTS empresas (
                id SERIAL PRIMARY KEY,
                cnpj VARCHAR(14) UNIQUE NOT NULL,
                razao_social VARCHAR(255) NOT NULL,
                nome_fantasia VARCHAR(255),
                atividade_principal VARCHAR(255),
                regime_tributario VARCHAR(50),
                endereco JSONB,
                contato JSONB,
                ativo BOOLEAN DEFAULT TRUE,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Tabela de produtos
            CREATE TABLE IF NOT EXISTS produtos (
                id SERIAL PRIMARY KEY,
                empresa_id INTEGER REFERENCES empresas(id),
                codigo_produto VARCHAR(100) NOT NULL,
                codigo_barras VARCHAR(50),
                descricao TEXT NOT NULL,
                ncm VARCHAR(8),
                cest VARCHAR(9),
                unidade VARCHAR(10),
                categoria VARCHAR(100),
                preco DECIMAL(15,4),
                ativo BOOLEAN DEFAULT TRUE,
                origem_dados VARCHAR(50),
                confianca_ncm DECIMAL(3,2),
                confianca_cest DECIMAL(3,2),
                revisao_manual BOOLEAN DEFAULT FALSE,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(empresa_id, codigo_produto)
            );
            
            -- Tabela de classificações NCM
            CREATE TABLE IF NOT EXISTS ncm_classificacoes (
                id SERIAL PRIMARY KEY,
                codigo VARCHAR(8) UNIQUE NOT NULL,
                descricao TEXT NOT NULL,
                capitulo VARCHAR(2),
                posicao VARCHAR(4),
                subposicao VARCHAR(6),
                unidade_estatistica VARCHAR(10),
                aliquota_ii DECIMAL(5,2),
                aliquota_ipi DECIMAL(5,2),
                ativo BOOLEAN DEFAULT TRUE,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Tabela de classificações CEST
            CREATE TABLE IF NOT EXISTS cest_classificacoes (
                id SERIAL PRIMARY KEY,
                codigo VARCHAR(9) UNIQUE NOT NULL,
                descricao TEXT NOT NULL,
                segmento VARCHAR(2),
                ncm_vinculados TEXT[],
                anexo VARCHAR(10),
                ativo BOOLEAN DEFAULT TRUE,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Tabela de auditoria
            CREATE TABLE IF NOT EXISTS auditoria_classificacoes (
                id SERIAL PRIMARY KEY,
                produto_id INTEGER REFERENCES produtos(id),
                campo_alterado VARCHAR(50) NOT NULL,
                valor_anterior TEXT,
                valor_novo TEXT,
                motivo TEXT,
                usuario VARCHAR(100),
                confianca DECIMAL(3,2),
                origem VARCHAR(50),
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Tabela de workflows
            CREATE TABLE IF NOT EXISTS workflow_execucoes (
                id SERIAL PRIMARY KEY,
                empresa_id INTEGER REFERENCES empresas(id),
                tipo_workflow VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL,
                dados_entrada JSONB,
                dados_saida JSONB,
                metricas JSONB,
                erro TEXT,
                iniciado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finalizado_em TIMESTAMP,
                duracao_segundos INTEGER
            );
            
            -- Tabela de relatórios
            CREATE TABLE IF NOT EXISTS relatorios (
                id SERIAL PRIMARY KEY,
                empresa_id INTEGER REFERENCES empresas(id),
                tipo_relatorio VARCHAR(50) NOT NULL,
                parametros JSONB,
                resultado JSONB,
                criado_por VARCHAR(100),
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            with engine.connect() as conn:
                conn.execute(text(structural_sql))
                conn.commit()
            
            self.logger.info("Tabelas estruturais criadas")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao criar tabelas estruturais: {e}")
            return False
    
    def _populate_reference_data(self) -> bool:
        """Popula dados de referência (NCM, CEST)"""
        try:
            # Popular NCM
            if not self._populate_ncm_data():
                return False
            
            # Popular CEST
            if not self._populate_cest_data():
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao popular dados de referência: {e}")
            return False
    
    def _populate_ncm_data(self) -> bool:
        """Popula dados NCM"""
        try:
            data_path = Path("data/raw")
            
            # Carregar Tabela NCM
            ncm_file = data_path / "Tabela_NCM.xlsx"
            if not ncm_file.exists():
                self.logger.warning("Arquivo Tabela_NCM.xlsx não encontrado")
                return True  # Não é erro crítico
            
            df = pd.read_excel(ncm_file)
            engine = self._get_engine()
            
            # Preparar dados
            ncm_data = []
            for _, row in df.iterrows():
                codigo = str(row.get('Código', '')).replace('.', '')
                if len(codigo) == 8 and codigo.isdigit():
                    ncm_data.append({
                        'codigo': codigo,
                        'descricao': str(row.get('Descrição', '')),
                        'capitulo': codigo[:2],
                        'posicao': codigo[:4],
                        'subposicao': codigo[:6],
                        'unidade_estatistica': str(row.get('Unid. Estat.', '')),
                        'aliquota_ii': float(row.get('Alíq. II (%)', 0)) if pd.notna(row.get('Alíq. II (%)')) else 0,
                        'aliquota_ipi': float(row.get('Alíq. IPI (%)', 0)) if pd.notna(row.get('Alíq. IPI (%)')) else 0
                    })
            
            # Inserir em lotes
            if ncm_data:
                ncm_df = pd.DataFrame(ncm_data)
                ncm_df.to_sql('ncm_classificacoes', engine, if_exists='append', index=False, method='multi')
                self.logger.info(f"Inseridos {len(ncm_data)} códigos NCM")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao popular dados NCM: {e}")
            return False
    
    def _populate_cest_data(self) -> bool:
        """Popula dados CEST"""
        try:
            data_path = Path("data/raw")
            
            # Carregar Convênio 142
            cest_file = data_path / "conv_142_formatado.json"
            if cest_file.exists():
                with open(cest_file, 'r', encoding='utf-8') as f:
                    cest_data = json.load(f)
                
                engine = self._get_engine()
                
                # Preparar dados
                cest_records = []
                for item in cest_data:
                    if item.get('cest'):
                        cest_records.append({
                            'codigo': item['cest'],
                            'descricao': item.get('descricao_oficial_cest', ''),
                            'segmento': item.get('Segmento', ''),
                            'ncm_vinculados': [item.get('ncm', '')] if item.get('ncm') else [],
                            'anexo': item.get('Anexo', '')
                        })
                
                # Inserir em lotes
                if cest_records:
                    cest_df = pd.DataFrame(cest_records)
                    cest_df.to_sql('cest_classificacoes', engine, if_exists='append', index=False, method='multi')
                    self.logger.info(f"Inseridos {len(cest_records)} códigos CEST")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao popular dados CEST: {e}")
            return False
    
    def _setup_indexes(self) -> bool:
        """Configura índices para otimização"""
        try:
            engine = self._get_engine()
            
            indexes_sql = """
            -- Índices para tabela produtos
            CREATE INDEX IF NOT EXISTS idx_produtos_empresa_id ON produtos(empresa_id);
            CREATE INDEX IF NOT EXISTS idx_produtos_ncm ON produtos(ncm);
            CREATE INDEX IF NOT EXISTS idx_produtos_cest ON produtos(cest);
            CREATE INDEX IF NOT EXISTS idx_produtos_codigo ON produtos(codigo_produto);
            
            -- Índices para tabela NCM
            CREATE INDEX IF NOT EXISTS idx_ncm_codigo ON ncm_classificacoes(codigo);
            CREATE INDEX IF NOT EXISTS idx_ncm_capitulo ON ncm_classificacoes(capitulo);
            CREATE INDEX IF NOT EXISTS idx_ncm_descricao ON ncm_classificacoes USING gin(to_tsvector('portuguese', descricao));
            
            -- Índices para tabela CEST
            CREATE INDEX IF NOT EXISTS idx_cest_codigo ON cest_classificacoes(codigo);
            CREATE INDEX IF NOT EXISTS idx_cest_segmento ON cest_classificacoes(segmento);
            CREATE INDEX IF NOT EXISTS idx_cest_ncm_vinculados ON cest_classificacoes USING gin(ncm_vinculados);
            
            -- Índices para auditoria
            CREATE INDEX IF NOT EXISTS idx_auditoria_produto_id ON auditoria_classificacoes(produto_id);
            CREATE INDEX IF NOT EXISTS idx_auditoria_criado_em ON auditoria_classificacoes(criado_em);
            
            -- Índices para workflows
            CREATE INDEX IF NOT EXISTS idx_workflow_empresa_id ON workflow_execucoes(empresa_id);
            CREATE INDEX IF NOT EXISTS idx_workflow_status ON workflow_execucoes(status);
            CREATE INDEX IF NOT EXISTS idx_workflow_tipo ON workflow_execucoes(tipo_workflow);
            """
            
            with engine.connect() as conn:
                for sql_statement in indexes_sql.split(';'):
                    sql_statement = sql_statement.strip()
                    if sql_statement:
                        conn.execute(text(sql_statement))
                conn.commit()
            
            self.logger.info("Índices configurados")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao configurar índices: {e}")
            return False
    
    def _get_engine(self):
        """Cria engine SQLAlchemy"""
        connection_string = (
            f"postgresql://{self.db_config['username']}:{self.db_config['password']}"
            f"@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        )
        return create_engine(connection_string)
    
    def _get_init_sql(self) -> str:
        """Retorna SQL de inicialização"""
        return """
        -- Habilitar extensões necessárias
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        CREATE EXTENSION IF NOT EXISTS "pg_trgm";
        
        -- Configurar timezone
        SET timezone = 'America/Sao_Paulo';
        
        -- Criar schema para auditoria se necessário
        CREATE SCHEMA IF NOT EXISTS auditoria;
        """
    
    def test_connection(self) -> bool:
        """Testa conexão com o banco"""
        try:
            engine = self._get_engine()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                self.logger.info(f"Conexão PostgreSQL OK: {version}")
                return True
        except Exception as e:
            self.logger.error(f"Erro na conexão PostgreSQL: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do banco de dados"""
        try:
            engine = self._get_engine()
            
            stats = {}
            
            with engine.connect() as conn:
                # Contar registros principais
                tables = ['empresas', 'produtos', 'ncm_classificacoes', 'cest_classificacoes']
                
                for table in tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    stats[f"total_{table}"] = result.fetchone()[0]
                
                # Estatísticas de classificação
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_produtos,
                        COUNT(CASE WHEN ncm IS NOT NULL THEN 1 END) as com_ncm,
                        COUNT(CASE WHEN cest IS NOT NULL THEN 1 END) as com_cest,
                        COUNT(CASE WHEN revisao_manual = true THEN 1 END) as requer_revisao
                    FROM produtos
                """))
                
                row = result.fetchone()
                stats.update({
                    "classificacao_stats": {
                        "total_produtos": row[0],
                        "com_ncm": row[1],
                        "com_cest": row[2],
                        "requer_revisao": row[3]
                    }
                })
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {e}")
            return {}


def main():
    """Função principal para execução standalone"""
    import sys
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    setup = PostgreSQLSetup()
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Apenas testar conexão
        if setup.test_connection():
            print("✅ Conexão PostgreSQL OK")
            stats = setup.get_database_stats()
            print("📊 Estatísticas:", json.dumps(stats, indent=2))
        else:
            print("❌ Erro na conexão PostgreSQL")
    else:
        # Configuração completa
        if setup.setup_database():
            print("✅ PostgreSQL configurado com sucesso!")
            stats = setup.get_database_stats()
            print("📊 Estatísticas finais:", json.dumps(stats, indent=2))
        else:
            print("❌ Erro na configuração do PostgreSQL")


if __name__ == "__main__":
    main()
