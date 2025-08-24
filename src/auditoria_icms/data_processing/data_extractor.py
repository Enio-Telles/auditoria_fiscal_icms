#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Extração de Dados para Sistema Multi-Tenant
====================================================

Este módulo fornece funcionalidades para extrair dados de diferentes tipos de bancos de dados
e integrá-los ao sistema multi-tenant de auditoria fiscal.

Características:
- Suporte para PostgreSQL, SQL Server e MySQL
- Configuração via arquivo .env ou parâmetros diretos
- Mapeamento automático de colunas
- Validação e limpeza de dados
- Logging detalhado de operações
- Tratamento robusto de erros

Author: Sistema de Auditoria Fiscal ICMS
Date: Agosto 2025
"""

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import logging
from typing import Dict, Optional, List, Any
from dataclasses import dataclass

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Configuração de conexão com banco de dados"""

    host: str
    port: str
    database: str
    user: str
    password: str
    schema: str = "dbo"
    db_type: str = "postgresql"  # postgresql, sqlserver, mysql


@dataclass
class ExtractionConfig:
    """Configuração de extração de dados"""

    table_name: str = "produto"
    columns: List[str] = None
    where_clause: str = ""
    limit: Optional[int] = None
    chunk_size: int = 10000


class DataExtractor:
    """
    Classe principal para extração de dados de bancos externos
    """

    def __init__(self, db_config: DatabaseConfig):
        """
        Inicializa o extrator com configuração do banco

        Args:
            db_config: Configuração de conexão com o banco de dados
        """
        self.db_config = db_config
        self.engine = None

        # Colunas padrão para produtos
        self.default_columns = [
            "produto_id",
            "descricao_produto",
            "codigo_produto",
            "codigo_barra",
            "ncm",
            "cest",
        ]

    def _create_connection_string(self) -> str:
        """
        Cria string de conexão baseada no tipo de banco

        Returns:
            String de conexão formatada
        """
        if self.db_config.db_type == "postgresql":
            return f"postgresql://{self.db_config.user}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}"

        elif self.db_config.db_type == "sqlserver":
            return f"mssql+pyodbc://{self.db_config.user}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}?driver=ODBC+Driver+17+for+SQL+Server"

        elif self.db_config.db_type == "mysql":
            return f"mysql+mysqlconnector://{self.db_config.user}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}"

        else:
            raise ValueError(f"Tipo de banco não suportado: {self.db_config.db_type}")

    def connect(self) -> bool:
        """
        Estabelece conexão com o banco de dados

        Returns:
            True se conexão foi bem-sucedida, False caso contrário
        """
        try:
            connection_string = self._create_connection_string()
            self.engine = create_engine(connection_string)

            # Testar conexão
            with self.engine.connect() as conn:
                if self.db_config.db_type == "postgresql":
                    conn.execute(text("SELECT 1"))
                elif self.db_config.db_type == "sqlserver":
                    conn.execute(text("SELECT 1"))
                elif self.db_config.db_type == "mysql":
                    conn.execute(text("SELECT 1"))

            logger.info(
                f"✅ Conexão estabelecida com {self.db_config.db_type} em {self.db_config.host}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao conectar com o banco: {e}")
            return False

    def test_connection(self) -> Dict[str, Any]:
        """
        Testa conexão e retorna informações do banco

        Returns:
            Dicionário com resultado do teste
        """
        try:
            if not self.connect():
                return {"success": False, "error": "Falha na conexão"}

            with self.engine.connect() as conn:
                if self.db_config.db_type == "postgresql":
                    result = conn.execute(text("SELECT version()"))
                    version = result.fetchone()[0]
                elif self.db_config.db_type == "sqlserver":
                    result = conn.execute(text("SELECT @@VERSION"))
                    version = result.fetchone()[0]
                elif self.db_config.db_type == "mysql":
                    result = conn.execute(text("SELECT VERSION()"))
                    version = result.fetchone()[0]

                return {
                    "success": True,
                    "database_info": f"{self.db_config.db_type.upper()} - {version[:100]}",
                    "host": self.db_config.host,
                    "database": self.db_config.database,
                    "schema": self.db_config.schema,
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Obtém informações sobre uma tabela

        Args:
            table_name: Nome da tabela

        Returns:
            Informações da tabela (colunas, tipos, contagem)
        """
        try:
            if not self.engine:
                if not self.connect():
                    return {
                        "success": False,
                        "error": "Não foi possível conectar ao banco",
                    }

            # Query para obter colunas
            if self.db_config.db_type == "postgresql":
                columns_query = f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                AND table_schema = '{self.db_config.schema}'
                ORDER BY ordinal_position
                """
            elif self.db_config.db_type == "sqlserver":
                columns_query = f"""
                SELECT COLUMN_NAME as column_name, DATA_TYPE as data_type, IS_NULLABLE as is_nullable
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{table_name}'
                AND TABLE_SCHEMA = '{self.db_config.schema}'
                ORDER BY ORDINAL_POSITION
                """
            elif self.db_config.db_type == "mysql":
                columns_query = f"""
                SELECT COLUMN_NAME as column_name, DATA_TYPE as data_type, IS_NULLABLE as is_nullable
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{table_name}'
                AND TABLE_SCHEMA = '{self.db_config.database}'
                ORDER BY ORDINAL_POSITION
                """

            # Obter informações das colunas
            columns_df = pd.read_sql_query(columns_query, self.engine)

            # Contar registros
            count_query = (
                f"SELECT COUNT(*) as total FROM {self.db_config.schema}.{table_name}"
            )
            if self.db_config.db_type == "mysql":
                count_query = f"SELECT COUNT(*) as total FROM {self.db_config.database}.{table_name}"

            count_df = pd.read_sql_query(count_query, self.engine)
            total_records = count_df.iloc[0]["total"]

            return {
                "success": True,
                "table_name": table_name,
                "schema": self.db_config.schema,
                "total_records": int(total_records),
                "columns": columns_df.to_dict("records"),
            }

        except Exception as e:
            logger.error(f"Erro ao obter informações da tabela {table_name}: {e}")
            return {"success": False, "error": str(e)}

    def preview_data(self, config: ExtractionConfig, limit: int = 10) -> Dict[str, Any]:
        """
        Faz preview dos dados a serem extraídos

        Args:
            config: Configuração de extração
            limit: Número máximo de registros para preview

        Returns:
            Preview dos dados
        """
        try:
            if not self.engine:
                if not self.connect():
                    return {
                        "success": False,
                        "error": "Não foi possível conectar ao banco",
                    }

            # Construir query
            columns = config.columns or self.default_columns
            columns_str = ", ".join(columns)

            table_full_name = f"{self.db_config.schema}.{config.table_name}"
            if self.db_config.db_type == "mysql":
                table_full_name = f"{self.db_config.database}.{config.table_name}"

            query = f"SELECT {columns_str} FROM {table_full_name}"

            if config.where_clause:
                query += f" WHERE {config.where_clause}"

            query += f" LIMIT {limit}"

            # Executar query
            df = pd.read_sql_query(query, self.engine)

            return {
                "success": True,
                "preview_count": len(df),
                "columns": list(df.columns),
                "data": df.to_dict("records"),
                "query_used": query,
            }

        except Exception as e:
            logger.error(f"Erro no preview dos dados: {e}")
            return {"success": False, "error": str(e)}

    def extract_data(self, config: ExtractionConfig) -> Optional[pd.DataFrame]:
        """
        Extrai dados do banco de acordo com a configuração

        Args:
            config: Configuração de extração

        Returns:
            DataFrame com os dados extraídos ou None em caso de erro
        """
        try:
            if not self.engine:
                if not self.connect():
                    logger.error("Não foi possível conectar ao banco")
                    return None

            # Construir query
            columns = config.columns or self.default_columns
            columns_str = ", ".join(columns)

            table_full_name = f"{self.db_config.schema}.{config.table_name}"
            if self.db_config.db_type == "mysql":
                table_full_name = f"{self.db_config.database}.{config.table_name}"

            query = f"SELECT {columns_str} FROM {table_full_name}"

            if config.where_clause:
                query += f" WHERE {config.where_clause}"

            if config.limit:
                query += f" LIMIT {config.limit}"

            logger.info("🔄 Iniciando extração de dados...")
            logger.info(f"📋 Query: {query}")

            # Extrair dados
            if config.chunk_size and config.chunk_size > 0:
                # Extração em chunks para tabelas grandes
                chunks = []
                for chunk in pd.read_sql_query(
                    query, self.engine, chunksize=config.chunk_size
                ):
                    chunks.append(chunk)
                    logger.info(f"📦 Chunk processado: {len(chunk)} registros")

                if chunks:
                    df = pd.concat(chunks, ignore_index=True)
                else:
                    df = pd.DataFrame()
            else:
                # Extração completa
                df = pd.read_sql_query(query, self.engine)

            logger.info(f"✅ Extração concluída! {len(df)} registros extraídos.")
            logger.info(f"📊 Colunas: {list(df.columns)}")

            return self._clean_data(df)

        except Exception as e:
            logger.error(f"❌ Erro durante a extração: {e}")
            return None

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpa e padroniza os dados extraídos

        Args:
            df: DataFrame original

        Returns:
            DataFrame limpo
        """
        try:
            # Remover linhas completamente vazias
            df = df.dropna(how="all")

            # Tratar colunas específicas
            if "descricao_produto" in df.columns:
                # Remover registros sem descrição
                df = df[df["descricao_produto"].notna()]
                df = df[df["descricao_produto"].str.strip() != ""]

                # Limpar descrições
                df["descricao_produto"] = (
                    df["descricao_produto"].str.strip().str.upper()
                )

            if "ncm" in df.columns:
                # Limpar NCM (remover caracteres não numéricos)
                df["ncm"] = df["ncm"].astype(str).str.replace(r"\D", "", regex=True)
                df["ncm"] = df["ncm"].replace("", None)

            if "cest" in df.columns:
                # Limpar CEST
                df["cest"] = df["cest"].astype(str).str.replace(r"\D", "", regex=True)
                df["cest"] = df["cest"].replace("", None)

            if "codigo_barra" in df.columns:
                # Limpar código de barras
                df["codigo_barra"] = (
                    df["codigo_barra"].astype(str).str.replace(r"\D", "", regex=True)
                )
                df["codigo_barra"] = df["codigo_barra"].replace("", None)

            logger.info(f"🧹 Dados limpos. Registros válidos: {len(df)}")

            return df

        except Exception as e:
            logger.error(f"Erro na limpeza dos dados: {e}")
            return df

    def close(self):
        """Fecha a conexão com o banco"""
        if self.engine:
            self.engine.dispose()
            logger.info("🔌 Conexão fechada")


def create_extractor_from_env() -> DataExtractor:
    """
    Cria um extrator baseado em variáveis de ambiente

    Returns:
        Instância configurada do DataExtractor
    """
    load_dotenv()

    config = DatabaseConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        schema=os.getenv("DB_SCHEMA", "dbo"),
        db_type=os.getenv("DB_TYPE", "postgresql"),
    )

    # Verificar configurações obrigatórias
    required_configs = ["database", "user", "password"]
    for attr in required_configs:
        if not getattr(config, attr):
            raise ValueError(
                f"Configuração {attr.upper()} não encontrada no arquivo .env"
            )

    return DataExtractor(config)


def extract_produtos_from_env() -> Optional[pd.DataFrame]:
    """
    Função de conveniência para extrair produtos usando configuração do .env

    Returns:
        DataFrame com produtos extraídos ou None em caso de erro
    """
    try:
        extractor = create_extractor_from_env()

        config = ExtractionConfig(
            table_name="produto",
            columns=[
                "produto_id",
                "descricao_produto",
                "codigo_produto",
                "codigo_barra",
                "ncm",
                "cest",
            ],
        )

        df = extractor.extract_data(config)
        extractor.close()

        return df

    except Exception as e:
        logger.error(f"Erro na extração via .env: {e}")
        return None


if __name__ == "__main__":
    # Exemplo de uso direto
    try:
        # Teste usando arquivo .env
        print("🔄 Testando extração via arquivo .env...")
        df = extract_produtos_from_env()

        if df is not None:
            print(f"\n✅ Total de registros extraídos: {len(df)}")
            print("📊 Primeiras 5 linhas:")
            print(df.head())
            print(f"\n📋 Colunas: {list(df.columns)}")
            print("🧮 Tipos de dados:")
            print(df.dtypes)
        else:
            print("❌ Falha na extração")

    except Exception as e:
        print(f"❌ Erro no teste: {e}")
