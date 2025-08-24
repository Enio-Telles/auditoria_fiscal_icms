"""
Gerenciamento de conexões com banco de dados
Implementa pooling de conexões e sessões SQLAlchemy
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import logging

from ..core.config import get_settings
from ..database.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gerenciador de conexões com banco de dados"""

    def __init__(self):
        self.settings = get_settings()
        self.engine = None
        self.SessionLocal = None
        self._initialize()

    def _initialize(self):
        """Inicializa engine e session factory"""
        try:
            # Configurar engine com pool de conexões
            self.engine = create_engine(
                self.settings.database.get_url(),
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=self.settings.debug,
                echo_pool=self.settings.debug,
            )

            # Configurar session factory
            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )

            # Event listeners para logging
            if self.settings.debug:
                event.listen(self.engine, "connect", self._on_connect)
                event.listen(self.engine, "checkout", self._on_checkout)
                event.listen(self.engine, "checkin", self._on_checkin)

            logger.info("✅ Database engine inicializado com sucesso")

        except Exception as e:
            logger.error(f"❌ Erro ao inicializar database engine: {e}")
            raise

    def _on_connect(self, dbapi_connection, connection_record):
        """Callback executado em novas conexões"""
        logger.debug("Nova conexão estabelecida")

    def _on_checkout(self, dbapi_connection, connection_record, connection_proxy):
        """Callback executado ao fazer checkout de conexão do pool"""
        logger.debug("Conexão retirada do pool")

    def _on_checkin(self, dbapi_connection, connection_record):
        """Callback executado ao retornar conexão para o pool"""
        logger.debug("Conexão retornada para o pool")

    def create_tables(self):
        """Cria todas as tabelas do banco"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Tabelas criadas/verificadas com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao criar tabelas: {e}")
            raise

    def get_session(self) -> Session:
        """Retorna nova sessão do banco"""
        if self.SessionLocal is None:
            raise RuntimeError("Database não foi inicializado")
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Context manager para sessões com commit/rollback automático"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def health_check(self) -> bool:
        """Verifica se o banco está acessível"""
        try:
            with self.session_scope() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Health check falhou: {e}")
            return False

    def close(self):
        """Fecha todas as conexões"""
        if self.engine:
            self.engine.dispose()
            logger.info("🛑 Conexões de banco fechadas")


# Instância global do gerenciador
db_manager = DatabaseManager()


# Funções de conveniência para FastAPI
def get_db_session() -> Generator[Session, None, None]:
    """Dependency para injeção de sessão nas rotas FastAPI"""
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


def get_db() -> Session:
    """Retorna sessão de banco (para uso direto)"""
    return db_manager.get_session()


# Funções de inicialização
def init_database():
    """Inicializa o banco de dados"""
    db_manager.create_tables()


def close_database():
    """Fecha conexões do banco"""
    db_manager.close()


# Context manager para transações
@contextmanager
def transaction() -> Generator[Session, None, None]:
    """Context manager para transações manuais"""
    with db_manager.session_scope() as session:
        yield session
