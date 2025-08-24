"""
Sistema de Importação de Dados - Fase 6
Implementa importação de dados de PostgreSQL externos para o sistema
"""

import logging
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from ..core.config import get_settings
from ..database.models import ProdutoEmpresa


@dataclass
class ExternalDatabaseConfig:
    """Configuração para banco de dados externo"""

    host: str
    port: int
    database: str
    username: str
    password: str
    schema: str = "dbo"

    def get_url(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class DatabaseImporter:
    """Sistema de importação de dados de bancos externos"""

    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.local_engine = None
        self.local_session = None

    async def setup_local_connection(self):
        """Configura conexão com banco local"""
        try:
            database_url = self.settings.database.get_url()
            self.local_engine = create_engine(database_url)
            Session = sessionmaker(bind=self.local_engine)
            self.local_session = Session()
            self.logger.info("Conexão local estabelecida com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao conectar banco local: {e}")
            raise

    async def test_external_connection(self, config: ExternalDatabaseConfig) -> bool:
        """Testa conexão com banco externo"""
        try:
            engine = create_engine(config.get_url())
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                self.logger.info(f"Conexão externa testada: {config.database}")
                return True
        except Exception as e:
            self.logger.error(f"Erro na conexão externa {config.database}: {e}")
            return False

    async def import_products_from_external_db(
        self,
        config: ExternalDatabaseConfig,
        empresa_id: int,
        table_name: str = "produto",
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Importa produtos de banco externo usando a consulta específica das considerações
        """
        try:
            # Consulta conforme especificação nas considerações
            query = f"""
            SELECT
                produto_id,
                descricao_produto,
                codigo_produto,
                codigo_barra,
                ncm,
                cest,
                DENSE_RANK() OVER (ORDER BY descricao_produto) AS id_agregados,
                COUNT(*) OVER (PARTITION BY descricao_produto) AS qtd_mesma_desc
            FROM {config.schema}.{table_name}
            WHERE descricao_produto IS NOT NULL
            """

            if limit:
                query += f" LIMIT {limit}"

            # Conectar ao banco externo
            external_engine = create_engine(config.get_url())

            # Executar consulta
            df = pd.read_sql(query, external_engine)

            self.logger.info(
                f"Consultados {len(df)} produtos do banco {config.database}"
            )

            # Processar e inserir no banco local
            imported_count = await self._process_and_insert_products(df, empresa_id)

            return {
                "success": True,
                "total_consulted": len(df),
                "imported_count": imported_count,
                "empresa_id": empresa_id,
                "source_database": config.database,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Erro na importação: {e}")
            return {
                "success": False,
                "error": str(e),
                "empresa_id": empresa_id,
                "source_database": config.database,
                "timestamp": datetime.now().isoformat(),
            }

    async def _process_and_insert_products(
        self, df: pd.DataFrame, empresa_id: int
    ) -> int:
        """Processa DataFrame e insere produtos no banco local"""
        try:
            imported_count = 0

            for _, row in df.iterrows():
                # Verificar se produto já existe
                existing = (
                    self.local_session.query(ProdutoEmpresa)
                    .filter(
                        ProdutoEmpresa.empresa_id == empresa_id,
                        ProdutoEmpresa.produto_id_original == str(row["produto_id"]),
                    )
                    .first()
                )

                if not existing:
                    # Criar novo produto
                    produto = ProdutoEmpresa(
                        empresa_id=empresa_id,
                        produto_id_original=str(row["produto_id"]),
                        descricao_original=row["descricao_produto"],
                        codigo_produto=row.get("codigo_produto"),
                        codigo_barra=row.get("codigo_barra"),
                        ncm_informado=row.get("ncm"),
                        cest_informado=row.get("cest"),
                        id_agregados=row.get("id_agregados"),
                        qtd_mesma_desc=row.get("qtd_mesma_desc"),
                        status_classificacao="PENDENTE",
                        data_importacao=datetime.now(),
                    )

                    self.local_session.add(produto)
                    imported_count += 1

            # Commit das inserções
            self.local_session.commit()
            self.logger.info(f"Importados {imported_count} novos produtos")

            return imported_count

        except Exception as e:
            self.local_session.rollback()
            self.logger.error(f"Erro ao inserir produtos: {e}")
            raise

    async def get_import_statistics(self, empresa_id: int) -> Dict[str, Any]:
        """Retorna estatísticas de importação para uma empresa"""
        try:
            total_products = (
                self.local_session.query(ProdutoEmpresa)
                .filter(ProdutoEmpresa.empresa_id == empresa_id)
                .count()
            )

            pending_classification = (
                self.local_session.query(ProdutoEmpresa)
                .filter(
                    ProdutoEmpresa.empresa_id == empresa_id,
                    ProdutoEmpresa.status_classificacao == "PENDENTE",
                )
                .count()
            )

            classified = (
                self.local_session.query(ProdutoEmpresa)
                .filter(
                    ProdutoEmpresa.empresa_id == empresa_id,
                    ProdutoEmpresa.status_classificacao.in_(
                        ["CONFIRMADO", "DETERMINADO"]
                    ),
                )
                .count()
            )

            # Agregações
            unique_descriptions = (
                self.local_session.query(ProdutoEmpresa.descricao_original)
                .filter(ProdutoEmpresa.empresa_id == empresa_id)
                .distinct()
                .count()
            )

            return {
                "empresa_id": empresa_id,
                "total_products": total_products,
                "pending_classification": pending_classification,
                "classified": classified,
                "unique_descriptions": unique_descriptions,
                "aggregation_ratio": (
                    round(unique_descriptions / total_products * 100, 2)
                    if total_products > 0
                    else 0
                ),
            }

        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {e}")
            return {"error": str(e)}

    async def cleanup_and_reimport(self, empresa_id: int) -> bool:
        """Remove todos os produtos de uma empresa para reimportação"""
        try:
            deleted_count = (
                self.local_session.query(ProdutoEmpresa)
                .filter(ProdutoEmpresa.empresa_id == empresa_id)
                .delete()
            )

            self.local_session.commit()
            self.logger.info(
                f"Removidos {deleted_count} produtos da empresa {empresa_id}"
            )

            return True

        except Exception as e:
            self.local_session.rollback()
            self.logger.error(f"Erro ao limpar dados: {e}")
            return False

    def close_connections(self):
        """Fecha conexões"""
        if self.local_session:
            self.local_session.close()
        if self.local_engine:
            self.local_engine.dispose()


# Configurações pré-definidas para empresas conhecidas
PREDEFINED_CONFIGS = {
    "db_04565289005297": ExternalDatabaseConfig(
        host="localhost",
        port=5432,
        database="db_04565289005297",
        username="postgres",
        password="sefin",
        schema="dbo",
    )
}


async def get_external_config_by_company(
    empresa_id: int,
) -> Optional[ExternalDatabaseConfig]:
    """Retorna configuração externa baseada na empresa"""
    # Para demonstração, usando configuração fixa
    # Em produção, isso viria do cadastro da empresa
    return PREDEFINED_CONFIGS.get("db_04565289005297")
