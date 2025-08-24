"""
Módulo de Ingestão de Dados - Fase 2
Adaptador flexível para conectar aos bancos de dados das empresas
Suporta PostgreSQL, SQL Server e Oracle
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
import os
from datetime import datetime

from ..database.models import ProdutoEmpresa

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Configuração de conexão com banco de dados da empresa"""

    db_type: str  # postgresql, sqlserver, oracle
    host: str
    port: int
    database: str
    username: str
    password: str
    schema: Optional[str] = None
    additional_params: Optional[Dict[str, Any]] = None


class DatabaseConnector:
    """Conector genérico para diferentes tipos de banco de dados"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine: Optional[Engine] = None

    def _build_connection_string(self) -> str:
        """Constrói string de conexão baseada no tipo de banco"""

        if self.config.db_type.lower() == "postgresql":
            base_url = f"postgresql://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"

        elif self.config.db_type.lower() == "sqlserver":
            # SQL Server usando pyodbc
            driver = "ODBC+Driver+17+for+SQL+Server"
            base_url = f"mssql+pyodbc://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}?driver={driver}"

        elif self.config.db_type.lower() == "oracle":
            # Oracle usando cx_oracle
            base_url = f"oracle+cx_oracle://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"

        else:
            raise ValueError(f"Tipo de banco não suportado: {self.config.db_type}")

        # Adiciona parâmetros adicionais se fornecidos
        if self.config.additional_params:
            params = "&".join(
                [f"{k}={v}" for k, v in self.config.additional_params.items()]
            )
            base_url += f"&{params}" if "?" in base_url else f"?{params}"

        return base_url

    def connect(self) -> Engine:
        """Estabelece conexão com o banco de dados"""
        try:
            connection_string = self._build_connection_string()
            self.engine = create_engine(
                connection_string, pool_pre_ping=True, pool_recycle=3600, echo=False
            )

            # Testa a conexão
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info(
                f"Conexão estabelecida com {self.config.db_type} em {self.config.host}"
            )
            return self.engine

        except Exception as e:
            logger.error(f"Erro ao conectar ao banco {self.config.db_type}: {str(e)}")
            raise

    def disconnect(self):
        """Fecha conexão com o banco"""
        if self.engine:
            self.engine.dispose()
            self.engine = None


class EmpresaDataIngestion:
    """Classe principal para ingestão de dados de empresas"""

    def __init__(self, empresa_id: int, db_config: Dict[str, Any]):
        self.empresa_id = empresa_id
        self.db_config = DatabaseConfig(**db_config)
        self.connector = DatabaseConnector(self.db_config)

    def extract_produtos(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
        where_clause: Optional[str] = None,
    ) -> List[ProdutoEmpresa]:
        """
        Extrai produtos do banco da empresa usando a consulta base

        Args:
            limit: Número máximo de registros para retornar
            offset: Número de registros para pular
            where_clause: Cláusula WHERE adicional

        Returns:
            Lista de produtos extraídos
        """
        try:
            engine = self.connector.connect()

            # Query base adaptada do plano
            base_query = self._build_extraction_query()

            # Adiciona cláusulas opcionais
            if where_clause:
                base_query += f" AND ({where_clause})"

            if limit:
                base_query += f" LIMIT {limit}"

            if offset:
                base_query += f" OFFSET {offset}"

            # Executa a query
            df = pd.read_sql(base_query, engine)

            # Converte para objetos ProdutoEmpresa
            produtos = []
            for _, row in df.iterrows():
                produto = ProdutoEmpresa(
                    produto_id=str(row["produto_id"]),
                    descricao_produto=row["descricao_produto"],
                    codigo_produto=row.get("codigo_produto"),
                    codigo_barra=row.get("codigo_barra"),
                    ncm=row.get("ncm"),
                    cest=row.get("cest"),
                    id_agregados=row.get("id_agregados"),
                    qtd_mesma_desc=row.get("qtd_mesma_desc"),
                )
                produtos.append(produto)

            logger.info(
                f"Extraídos {len(produtos)} produtos da empresa {self.empresa_id}"
            )
            return produtos

        except Exception as e:
            logger.error(
                f"Erro ao extrair produtos da empresa {self.empresa_id}: {str(e)}"
            )
            raise
        finally:
            self.connector.disconnect()

    def _build_extraction_query(self) -> str:
        """Constrói a query de extração baseada no tipo de banco"""

        # Query base adaptada do exemplo fornecido
        base_query = """
        SELECT
            produto_id,
            descricao_produto,
            codigo_produto,
            codigo_barra,
            ncm,
            cest,
            DENSE_RANK() OVER (ORDER BY descricao_produto) AS id_agregados,
            COUNT(*) OVER (PARTITION BY descricao_produto) AS qtd_mesma_desc
        FROM {schema_prefix}produto
        WHERE descricao_produto IS NOT NULL
        """

        # Ajusta para o schema se necessário
        schema_prefix = ""
        if self.db_config.schema:
            schema_prefix = f"{self.db_config.schema}."
        elif self.db_config.db_type.lower() == "sqlserver":
            schema_prefix = "dbo."

        return base_query.format(schema_prefix=schema_prefix)

    def update_produtos_processados(
        self, produtos_atualizados: List[Dict[str, Any]]
    ) -> bool:
        """
        Atualiza produtos no banco da empresa com os resultados do processamento

        Args:
            produtos_atualizados: Lista de produtos com campos atualizados

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            engine = self.connector.connect()

            # Verifica se as colunas de resultado existem, se não, cria
            self._ensure_result_columns(engine)

            # Atualiza produtos em lote
            with engine.begin() as conn:
                for produto in produtos_atualizados:
                    update_query = self._build_update_query()

                    conn.execute(
                        text(update_query),
                        {
                            "produto_id": produto["produto_id"],
                            "descricao_enriquecida": produto.get(
                                "descricao_enriquecida"
                            ),
                            "ncm_sugerido": produto.get("ncm_sugerido"),
                            "cest_sugerido": produto.get("cest_sugerido"),
                            "status_processamento": produto.get(
                                "status_processamento", "PROCESSADO"
                            ),
                            "confianca_ncm": produto.get("confianca_ncm"),
                            "confianca_cest": produto.get("confianca_cest"),
                            "justificativa_ncm": produto.get("justificativa_ncm"),
                            "justificativa_cest": produto.get("justificativa_cest"),
                            "data_processamento": datetime.utcnow(),
                            "revisao_manual": produto.get("revisao_manual", False),
                        },
                    )

            logger.info(
                f"Atualizados {len(produtos_atualizados)} produtos no banco da empresa {self.empresa_id}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Erro ao atualizar produtos da empresa {self.empresa_id}: {str(e)}"
            )
            return False
        finally:
            self.connector.disconnect()

    def _ensure_result_columns(self, engine: Engine):
        """Garante que as colunas de resultado existem na tabela de produtos"""

        schema_prefix = ""
        if self.db_config.schema:
            schema_prefix = f"{self.db_config.schema}."
        elif self.db_config.db_type.lower() == "sqlserver":
            schema_prefix = "dbo."

        # Colunas que devem existir
        columns_to_add = [
            ("descricao_enriquecida", "TEXT"),
            ("ncm_sugerido", "VARCHAR(10)"),
            ("cest_sugerido", "VARCHAR(10)"),
            ("status_processamento", "VARCHAR(50) DEFAULT 'PENDENTE'"),
            ("confianca_ncm", "FLOAT"),
            ("confianca_cest", "FLOAT"),
            ("justificativa_ncm", "TEXT"),
            ("justificativa_cest", "TEXT"),
            ("data_processamento", "TIMESTAMP"),
            ("revisao_manual", "BOOLEAN DEFAULT FALSE"),
        ]

        with engine.begin() as conn:
            for column_name, column_type in columns_to_add:
                try:
                    # Tenta adicionar a coluna (falhará se já existir)
                    alter_query = f"ALTER TABLE {schema_prefix}produto ADD COLUMN {column_name} {column_type}"
                    conn.execute(text(alter_query))
                    logger.info(f"Coluna {column_name} adicionada à tabela produto")
                except SQLAlchemyError:
                    # Coluna já existe, ignora o erro
                    pass

    def _build_update_query(self) -> str:
        """Constrói query de atualização baseada no tipo de banco"""

        schema_prefix = ""
        if self.db_config.schema:
            schema_prefix = f"{self.db_config.schema}."
        elif self.db_config.db_type.lower() == "sqlserver":
            schema_prefix = "dbo."

        return f"""
        UPDATE {schema_prefix}produto
        SET
            descricao_enriquecida = :descricao_enriquecida,
            ncm_sugerido = :ncm_sugerido,
            cest_sugerido = :cest_sugerido,
            status_processamento = :status_processamento,
            confianca_ncm = :confianca_ncm,
            confianca_cest = :confianca_cest,
            justificativa_ncm = :justificativa_ncm,
            justificativa_cest = :justificativa_cest,
            data_processamento = :data_processamento,
            revisao_manual = :revisao_manual
        WHERE produto_id = :produto_id
        """

    def test_connection(self) -> Dict[str, Any]:
        """Testa a conexão com o banco da empresa"""
        try:
            engine = self.connector.connect()

            # Testa query simples
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) as total FROM produto"))
                total_produtos = result.fetchone()[0]

            self.connector.disconnect()

            return {
                "status": "sucesso",
                "mensagem": "Conexão estabelecida com sucesso",
                "total_produtos": total_produtos,
                "tipo_banco": self.db_config.db_type,
            }

        except Exception as e:
            return {
                "status": "erro",
                "mensagem": f"Erro na conexão: {str(e)}",
                "total_produtos": 0,
                "tipo_banco": self.db_config.db_type,
            }


class DataIngestionManager:
    """Gerenciador principal para ingestão de dados de múltiplas empresas"""

    def __init__(self):
        self.active_connections: Dict[int, EmpresaDataIngestion] = {}

    def get_empresa_ingestion(
        self, empresa_id: int, db_config: Dict[str, Any]
    ) -> EmpresaDataIngestion:
        """Obtém ou cria uma instância de ingestão para uma empresa"""

        if empresa_id not in self.active_connections:
            self.active_connections[empresa_id] = EmpresaDataIngestion(
                empresa_id, db_config
            )

        return self.active_connections[empresa_id]

    def test_all_connections(self) -> Dict[int, Dict[str, Any]]:
        """Testa conexões com todas as empresas ativas"""
        results = {}

        for empresa_id, ingestion in self.active_connections.items():
            results[empresa_id] = ingestion.test_connection()

        return results

    def extract_produtos_bulk(
        self, empresa_configs: List[Dict[str, Any]], batch_size: int = 1000
    ) -> Dict[int, List[ProdutoEmpresa]]:
        """Extrai produtos de múltiplas empresas em lote"""

        results = {}

        for config in empresa_configs:
            empresa_id = config["empresa_id"]
            db_config = config["db_config"]

            try:
                ingestion = self.get_empresa_ingestion(empresa_id, db_config)
                produtos = ingestion.extract_produtos(limit=batch_size)
                results[empresa_id] = produtos

            except Exception as e:
                logger.error(
                    f"Erro ao extrair produtos da empresa {empresa_id}: {str(e)}"
                )
                results[empresa_id] = []

        return results


# Funções utilitárias
def create_database_config_from_env(empresa_id: int) -> Optional[DatabaseConfig]:
    """Cria configuração de banco a partir de variáveis de ambiente"""

    prefix = f"EMPRESA_{empresa_id}"

    try:
        return DatabaseConfig(
            db_type=os.getenv(f"{prefix}_DB_TYPE", "postgresql"),
            host=os.getenv(f"{prefix}_DB_HOST", "localhost"),
            port=int(os.getenv(f"{prefix}_DB_PORT", "5432")),
            database=os.getenv(f"{prefix}_DB_NAME"),
            username=os.getenv(f"{prefix}_DB_USER"),
            password=os.getenv(f"{prefix}_DB_PASSWORD"),
            schema=os.getenv(f"{prefix}_DB_SCHEMA"),
        )
    except (TypeError, ValueError) as e:
        logger.error(f"Erro ao criar configuração para empresa {empresa_id}: {str(e)}")
        return None


def validate_database_config(config: Dict[str, Any]) -> bool:
    """Valida configuração de banco de dados"""

    required_fields = ["db_type", "host", "port", "database", "username", "password"]

    for field in required_fields:
        if field not in config or not config[field]:
            logger.error(f"Campo obrigatório ausente: {field}")
            return False

    # Valida tipo de banco suportado
    supported_types = ["postgresql", "sqlserver", "oracle"]
    if config["db_type"].lower() not in supported_types:
        logger.error(f"Tipo de banco não suportado: {config['db_type']}")
        return False

    return True


# Exemplo de uso
if __name__ == "__main__":
    # Exemplo de configuração
    config_exemplo = {
        "db_type": "postgresql",
        "host": "localhost",
        "port": 5432,
        "database": "db_04565289005297",
        "username": "postgres",
        "password": "sefin",
        "schema": "dbo",
    }

    # Testa a ingestão
    ingestion = EmpresaDataIngestion(empresa_id=1, db_config=config_exemplo)

    # Testa conexão
    result = ingestion.test_connection()
    print(f"Teste de conexão: {result}")

    # Extrai alguns produtos
    if result["status"] == "sucesso":
        produtos = ingestion.extract_produtos(limit=10)
        print(f"Produtos extraídos: {len(produtos)}")

        for produto in produtos[:3]:
            print(f"- {produto.produto_id}: {produto.descricao_produto[:50]}...")
