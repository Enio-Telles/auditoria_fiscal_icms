"""
Sistema de Conectores para Sistemas Externos
Implementa integração com ERP, sistemas contábeis e outras fontes de dados
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Protocol
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import aiohttp
import pandas as pd
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)


class ConnectorType(str, Enum):
    ERP_SAP = "erp_sap"
    ERP_TOTVS = "erp_totvs"
    ERP_SENIOR = "erp_senior"
    CONTABIL_DOMINIO = "contabil_dominio"
    CONTABIL_ALTERDATA = "contabil_alterdata"
    DATABASE_POSTGRES = "db_postgres"
    DATABASE_SQLSERVER = "db_sqlserver"
    DATABASE_ORACLE = "db_oracle"
    API_REST = "api_rest"
    FILE_EXCEL = "file_excel"
    FILE_CSV = "file_csv"


@dataclass
class ConnectionConfig:
    """Configuração de conexão para sistemas externos"""

    connector_type: ConnectorType
    name: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    file_path: Optional[str] = None
    additional_params: Dict[str, Any] = None


@dataclass
class ImportConfig:
    """Configuração de importação de dados"""

    table_name: Optional[str] = None
    query: Optional[str] = None
    sheet_name: Optional[str] = None
    columns_mapping: Dict[str, str] = None
    filters: Dict[str, Any] = None
    batch_size: int = 1000


class DataConnector(Protocol):
    """Interface para conectores de dados"""

    async def test_connection(self) -> bool:
        """Testa conectividade com o sistema"""
        ...

    async def get_data(self, config: ImportConfig) -> List[Dict[str, Any]]:
        """Extrai dados do sistema"""
        ...

    async def get_schema(self) -> Dict[str, Any]:
        """Retorna esquema/estrutura dos dados"""
        ...


class DatabaseConnector:
    """Conector para bancos de dados relacionais"""

    def __init__(self, connection_config: ConnectionConfig):
        self.config = connection_config
        self.engine = None
        self.session_maker = None

    async def test_connection(self) -> bool:
        """Testa conexão com o banco de dados"""
        try:
            connection_string = self._build_connection_string()
            engine = create_engine(connection_string)

            # Testar conexão
            with engine.connect() as conn:
                conn.execute("SELECT 1")

            logger.info(f"✅ Conexão testada com sucesso: {self.config.name}")
            return True

        except Exception as e:
            logger.error(f"❌ Falha na conexão {self.config.name}: {e}")
            return False

    async def get_data(self, config: ImportConfig) -> List[Dict[str, Any]]:
        """Extrai dados do banco"""
        try:
            connection_string = self._build_connection_string()
            engine = create_engine(connection_string)

            # Construir query
            if config.query:
                query = config.query
            else:
                query = f"SELECT * FROM {config.table_name}"
                if config.filters:
                    conditions = [f"{k} = '{v}'" for k, v in config.filters.items()]
                    query += f" WHERE {' AND '.join(conditions)}"

            # Executar query em batches
            df = pd.read_sql(query, engine, chunksize=config.batch_size)

            all_data = []
            for chunk in df:
                # Aplicar mapeamento de colunas se fornecido
                if config.columns_mapping:
                    chunk = chunk.rename(columns=config.columns_mapping)

                all_data.extend(chunk.to_dict("records"))

            logger.info(f"✅ {len(all_data)} registros extraídos de {self.config.name}")
            return all_data

        except Exception as e:
            logger.error(f"❌ Erro na extração de dados: {e}")
            raise

    async def get_schema(self) -> Dict[str, Any]:
        """Retorna esquema do banco"""
        try:
            connection_string = self._build_connection_string()
            engine = create_engine(connection_string)

            with engine.connect() as conn:
                # Query para listar tabelas (específica por DB type)
                if self.config.connector_type == ConnectorType.DATABASE_POSTGRES:
                    tables_query = """
                        SELECT table_name, column_name, data_type
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                        ORDER BY table_name, ordinal_position
                    """
                elif self.config.connector_type == ConnectorType.DATABASE_SQLSERVER:
                    tables_query = """
                        SELECT t.name as table_name, c.name as column_name, ty.name as data_type
                        FROM sys.tables t
                        JOIN sys.columns c ON t.object_id = c.object_id
                        JOIN sys.types ty ON c.user_type_id = ty.user_type_id
                        ORDER BY t.name, c.column_id
                    """
                else:
                    # Fallback genérico
                    tables_query = "SELECT 'schema' as info"

                result = conn.execute(tables_query)
                schema_data = [dict(row) for row in result]

            return {"tables": schema_data}

        except Exception as e:
            logger.error(f"❌ Erro ao obter schema: {e}")
            return {"error": str(e)}

    def _build_connection_string(self) -> str:
        """Constrói string de conexão baseada no tipo de banco"""

        if self.config.connector_type == ConnectorType.DATABASE_POSTGRES:
            return f"postgresql://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"

        elif self.config.connector_type == ConnectorType.DATABASE_SQLSERVER:
            return f"mssql+pyodbc://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}?driver=ODBC+Driver+17+for+SQL+Server"

        elif self.config.connector_type == ConnectorType.DATABASE_ORACLE:
            return f"oracle+cx_oracle://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"

        else:
            raise ValueError(
                f"Tipo de banco não suportado: {self.config.connector_type}"
            )


class APIConnector:
    """Conector para APIs REST"""

    def __init__(self, connection_config: ConnectionConfig):
        self.config = connection_config

    async def test_connection(self) -> bool:
        """Testa conexão com a API"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.config.api_key:
                    headers["Authorization"] = f"Bearer {self.config.api_key}"

                async with session.get(
                    f"{self.config.api_url}/health", headers=headers
                ) as response:
                    return response.status == 200

        except Exception as e:
            logger.error(f"❌ Falha na conexão API: {e}")
            return False

    async def get_data(self, config: ImportConfig) -> List[Dict[str, Any]]:
        """Extrai dados via API"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.config.api_key:
                    headers["Authorization"] = f"Bearer {self.config.api_key}"

                # Construir URL com filtros
                url = f"{self.config.api_url}/{config.table_name}"
                params = config.filters or {}

                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Aplicar mapeamento de colunas
                        if config.columns_mapping and isinstance(data, list):
                            for item in data:
                                for old_key, new_key in config.columns_mapping.items():
                                    if old_key in item:
                                        item[new_key] = item.pop(old_key)

                        return data if isinstance(data, list) else [data]
                    else:
                        raise Exception(f"API retornou status {response.status}")

        except Exception as e:
            logger.error(f"❌ Erro na extração via API: {e}")
            raise

    async def get_schema(self) -> Dict[str, Any]:
        """Retorna schema da API (se disponível)"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.config.api_key:
                    headers["Authorization"] = f"Bearer {self.config.api_key}"

                # Tentar endpoint de schema/metadata
                endpoints_to_try = ["/schema", "/metadata", "/docs"]

                for endpoint in endpoints_to_try:
                    try:
                        url = f"{self.config.api_url}{endpoint}"
                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                return await response.json()
                    except Exception:
                        continue

                # Fallback: retornar estrutura básica
                return {
                    "api_url": self.config.api_url,
                    "available_endpoints": ["produtos", "empresas", "classificacoes"],
                }

        except Exception as e:
            logger.error(f"❌ Erro ao obter schema da API: {e}")
            return {"error": str(e)}


class FileConnector:
    """Conector para arquivos (Excel, CSV)"""

    def __init__(self, connection_config: ConnectionConfig):
        self.config = connection_config

    async def test_connection(self) -> bool:
        """Verifica se arquivo existe e é acessível"""
        try:
            import os

            return os.path.exists(self.config.file_path)
        except Exception as e:
            logger.error(f"❌ Erro ao verificar arquivo: {e}")
            return False

    async def get_data(self, config: ImportConfig) -> List[Dict[str, Any]]:
        """Extrai dados do arquivo"""
        try:
            if self.config.connector_type == ConnectorType.FILE_EXCEL:
                df = pd.read_excel(
                    self.config.file_path, sheet_name=config.sheet_name or 0
                )
            elif self.config.connector_type == ConnectorType.FILE_CSV:
                df = pd.read_csv(self.config.file_path)
            else:
                raise ValueError(
                    f"Tipo de arquivo não suportado: {self.config.connector_type}"
                )

            # Aplicar filtros
            if config.filters:
                for column, value in config.filters.items():
                    if column in df.columns:
                        df = df[df[column] == value]

            # Aplicar mapeamento de colunas
            if config.columns_mapping:
                df = df.rename(columns=config.columns_mapping)

            return df.to_dict("records")

        except Exception as e:
            logger.error(f"❌ Erro na leitura do arquivo: {e}")
            raise

    async def get_schema(self) -> Dict[str, Any]:
        """Retorna estrutura do arquivo"""
        try:
            if self.config.connector_type == ConnectorType.FILE_EXCEL:
                df = pd.read_excel(self.config.file_path, nrows=0)  # Só cabeçalhos
                sheets = pd.ExcelFile(self.config.file_path).sheet_names
                return {
                    "file_type": "excel",
                    "sheets": sheets,
                    "columns": df.columns.tolist(),
                }
            elif self.config.connector_type == ConnectorType.FILE_CSV:
                df = pd.read_csv(self.config.file_path, nrows=0)  # Só cabeçalhos
                return {"file_type": "csv", "columns": df.columns.tolist()}

        except Exception as e:
            logger.error(f"❌ Erro ao obter schema do arquivo: {e}")
            return {"error": str(e)}


class ConnectorFactory:
    """Factory para criar conectores baseado no tipo"""

    @staticmethod
    def create_connector(connection_config: ConnectionConfig) -> DataConnector:
        """Cria conector apropriado baseado no tipo"""

        if connection_config.connector_type in [
            ConnectorType.DATABASE_POSTGRES,
            ConnectorType.DATABASE_SQLSERVER,
            ConnectorType.DATABASE_ORACLE,
        ]:
            return DatabaseConnector(connection_config)

        elif connection_config.connector_type == ConnectorType.API_REST:
            return APIConnector(connection_config)

        elif connection_config.connector_type in [
            ConnectorType.FILE_EXCEL,
            ConnectorType.FILE_CSV,
        ]:
            return FileConnector(connection_config)

        else:
            raise ValueError(
                f"Tipo de conector não suportado: {connection_config.connector_type}"
            )


class ExternalSystemManager:
    """Gerenciador principal de sistemas externos"""

    def __init__(self):
        self.connections: Dict[str, DataConnector] = {}

    async def register_connection(self, connection_config: ConnectionConfig) -> bool:
        """Registra nova conexão"""
        try:
            connector = ConnectorFactory.create_connector(connection_config)

            # Testar conexão
            if await connector.test_connection():
                self.connections[connection_config.name] = connector
                logger.info(f"✅ Conexão registrada: {connection_config.name}")
                return True
            else:
                logger.error(f"❌ Falha no teste da conexão: {connection_config.name}")
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao registrar conexão: {e}")
            return False

    async def import_data(
        self, connection_name: str, import_config: ImportConfig
    ) -> List[Dict[str, Any]]:
        """Importa dados de sistema externo"""

        if connection_name not in self.connections:
            raise ValueError(f"Conexão não encontrada: {connection_name}")

        connector = self.connections[connection_name]
        return await connector.get_data(import_config)

    async def get_available_connections(self) -> List[Dict[str, Any]]:
        """Lista conexões disponíveis"""
        connections_info = []

        for name, connector in self.connections.items():
            try:
                is_online = await connector.test_connection()
                schema = await connector.get_schema()

                connections_info.append(
                    {
                        "name": name,
                        "status": "online" if is_online else "offline",
                        "schema": schema,
                        "last_tested": datetime.utcnow().isoformat(),
                    }
                )
            except Exception as e:
                connections_info.append(
                    {
                        "name": name,
                        "status": "error",
                        "error": str(e),
                        "last_tested": datetime.utcnow().isoformat(),
                    }
                )

        return connections_info

    async def test_all_connections(self) -> Dict[str, bool]:
        """Testa todas as conexões registradas"""
        results = {}

        for name, connector in self.connections.items():
            try:
                results[name] = await connector.test_connection()
            except Exception as e:
                logger.error(f"Erro ao testar {name}: {e}")
                results[name] = False

        return results


# Exemplo de uso
async def example_usage():
    """Exemplo de como usar o sistema de conectores"""

    manager = ExternalSystemManager()

    # Configurar conexão PostgreSQL
    postgres_config = ConnectionConfig(
        connector_type=ConnectorType.DATABASE_POSTGRES,
        name="postgres_local",
        host="localhost",
        port=5432,
        database="empresa_db",
        username="postgres",
        password="senha123",
    )

    # Registrar conexão
    await manager.register_connection(postgres_config)

    # Configurar importação
    import_config = ImportConfig(
        table_name="produtos",
        columns_mapping={
            "produto_id": "id",
            "descricao_produto": "descricao",
            "codigo_produto": "codigo",
        },
        filters={"ativo": "S"},
        batch_size=500,
    )

    # Importar dados
    data = await manager.import_data("postgres_local", import_config)

    print(f"Importados {len(data)} registros")

    # Testar todas as conexões
    status = await manager.test_all_connections()
    print(f"Status das conexões: {status}")


if __name__ == "__main__":
    asyncio.run(example_usage())
