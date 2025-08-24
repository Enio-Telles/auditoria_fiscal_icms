"""
Configurações centrais do sistema de auditoria fiscal ICMS
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class DatabaseConfig:
    """Configurações do banco de dados"""

    host: str = "localhost"
    port: int = 5432
    database: str = "auditoria_icms"
    username: str = "postgres"
    password: str = "postgres"

    def get_url(self) -> str:
        """Retorna URL de conexão"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class RedisConfig:
    """Configurações do Redis"""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None


@dataclass
class LLMConfig:
    """Configurações do LLM"""

    provider: str = "openai"  # openai, anthropic, local
    model_name: str = "gpt-4"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 2000


@dataclass
class RAGConfig:
    """Configurações do sistema RAG"""

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_store_type: str = "faiss"  # faiss, chroma, pinecone
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5


@dataclass
class AgentConfig:
    """Configurações dos agentes"""

    max_retries: int = 3
    timeout_seconds: int = 300
    confidence_threshold: float = 0.7
    auto_approve_threshold: float = 0.9
    enable_enrichment: bool = True
    enable_ncm_classification: bool = True
    enable_cest_classification: bool = True
    enable_reconciliation: bool = True


@dataclass
class WorkflowConfig:
    """Configurações dos workflows LangGraph"""

    confidence_threshold: float = 0.7
    auto_approval_threshold: float = 0.9
    enable_parallel_execution: bool = True
    max_retry_attempts: int = 3
    timeout_seconds: int = 600
    version: str = "1.0"

    # Configurações específicas por tipo de workflow
    confirmation_config: Dict[str, Any] = None
    determination_config: Dict[str, Any] = None

    def __post_init__(self):
        if self.confirmation_config is None:
            self.confirmation_config = {
                "enable_ncm_refinement": True,
                "enable_cest_determination": True,
                "require_high_confidence": True,
            }

        if self.determination_config is None:
            self.determination_config = {
                "enable_deep_enrichment": True,
                "enable_ncm_refinement": True,
                "max_ncm_candidates": 5,
                "enable_golden_set_learning": True,
            }


@dataclass
class ProcessingConfig:
    """Configurações de processamento"""

    batch_size: int = 100
    max_concurrent_tasks: int = 10
    enable_async_processing: bool = True
    log_level: str = "INFO"


@dataclass
class Settings:
    """Configurações principais do sistema"""

    database: DatabaseConfig
    redis: RedisConfig
    llm: LLMConfig
    rag: RAGConfig
    agent: AgentConfig
    workflow: WorkflowConfig
    processing: ProcessingConfig

    # Configurações gerais
    debug: bool = False
    environment: str = "development"  # development, staging, production
    secret_key: str = "your-secret-key-here"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


def load_settings_from_env() -> Settings:
    """Carrega configurações das variáveis de ambiente"""

    # Database
    db_config = DatabaseConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "auditoria_icms"),
        username=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )

    # Redis
    redis_config = RedisConfig(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        password=os.getenv("REDIS_PASSWORD"),
    )

    # LLM
    llm_config = LLMConfig(
        provider=os.getenv("LLM_PROVIDER", "openai"),
        model_name=os.getenv("LLM_MODEL", "gpt-4"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
    )

    # RAG
    rag_config = RAGConfig(
        embedding_model=os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        ),
        vector_store_type=os.getenv("VECTOR_STORE_TYPE", "faiss"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
        top_k=int(os.getenv("RAG_TOP_K", "5")),
    )

    # Agent
    agent_config = AgentConfig(
        max_retries=int(os.getenv("AGENT_MAX_RETRIES", "3")),
        timeout_seconds=int(os.getenv("AGENT_TIMEOUT", "300")),
        confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.7")),
        auto_approve_threshold=float(os.getenv("AUTO_APPROVE_THRESHOLD", "0.9")),
        enable_enrichment=os.getenv("ENABLE_ENRICHMENT", "true").lower() == "true",
        enable_ncm_classification=os.getenv("ENABLE_NCM_CLASSIFICATION", "true").lower()
        == "true",
        enable_cest_classification=os.getenv(
            "ENABLE_CEST_CLASSIFICATION", "true"
        ).lower()
        == "true",
        enable_reconciliation=os.getenv("ENABLE_RECONCILIATION", "true").lower()
        == "true",
    )

    # Workflow
    workflow_config = WorkflowConfig(
        confidence_threshold=float(os.getenv("WORKFLOW_CONFIDENCE_THRESHOLD", "0.7")),
        auto_approval_threshold=float(
            os.getenv("WORKFLOW_AUTO_APPROVAL_THRESHOLD", "0.9")
        ),
        enable_parallel_execution=os.getenv("WORKFLOW_ENABLE_PARALLEL", "true").lower()
        == "true",
        max_retry_attempts=int(os.getenv("WORKFLOW_MAX_RETRIES", "3")),
        timeout_seconds=int(os.getenv("WORKFLOW_TIMEOUT", "600")),
        version=os.getenv("WORKFLOW_VERSION", "1.0"),
    )

    # Processing
    processing_config = ProcessingConfig(
        batch_size=int(os.getenv("BATCH_SIZE", "100")),
        max_concurrent_tasks=int(os.getenv("MAX_CONCURRENT_TASKS", "10")),
        enable_async_processing=os.getenv("ENABLE_ASYNC_PROCESSING", "true").lower()
        == "true",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )

    return Settings(
        database=db_config,
        redis=redis_config,
        llm=llm_config,
        rag=rag_config,
        agent=agent_config,
        workflow=workflow_config,
        processing=processing_config,
        debug=os.getenv("DEBUG", "false").lower() == "true",
        environment=os.getenv("ENVIRONMENT", "development"),
        secret_key=os.getenv("SECRET_KEY", "your-secret-key-here"),
    )


def load_settings_from_dict(config_dict: Dict[str, Any]) -> Settings:
    """Carrega configurações de um dicionário"""

    db_config = DatabaseConfig(**config_dict.get("database", {}))
    redis_config = RedisConfig(**config_dict.get("redis", {}))
    llm_config = LLMConfig(**config_dict.get("llm", {}))
    rag_config = RAGConfig(**config_dict.get("rag", {}))
    agent_config = AgentConfig(**config_dict.get("agent", {}))
    workflow_config = WorkflowConfig(**config_dict.get("workflow", {}))
    processing_config = ProcessingConfig(**config_dict.get("processing", {}))

    return Settings(
        database=db_config,
        redis=redis_config,
        llm=llm_config,
        rag=rag_config,
        agent=agent_config,
        workflow=workflow_config,
        processing=processing_config,
        debug=config_dict.get("debug", False),
        environment=config_dict.get("environment", "development"),
        secret_key=config_dict.get("secret_key", "your-secret-key-here"),
    )


# Configurações padrão para desenvolvimento
DEFAULT_SETTINGS = Settings(
    database=DatabaseConfig(),
    redis=RedisConfig(),
    llm=LLMConfig(),
    rag=RAGConfig(),
    agent=AgentConfig(),
    workflow=WorkflowConfig(),
    processing=ProcessingConfig(),
    debug=True,
    environment="development",
    secret_key="dev-secret-key",
)


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna as configurações do sistema (cached)
    Primeiro tenta carregar das variáveis de ambiente,
    senão usa as configurações padrão
    """
    try:
        return load_settings_from_env()
    except Exception:
        return DEFAULT_SETTINGS


def get_database_url() -> str:
    """Retorna URL do banco de dados"""
    settings = get_settings()
    return settings.database.get_url()


def get_workflow_config() -> "WorkflowConfig":
    """Retorna configuração específica dos workflows"""
    settings = get_settings()
    return settings.workflow


def get_company_database_config(empresa_id: int) -> Dict[str, Any]:
    """
    Retorna configuração do banco de dados da empresa
    Em produção, isso viria do banco de dados
    """

    # Configurações de exemplo para teste
    configs = {
        1: {
            "database_type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "empresa_alpha",
            "username": "user_alpha",
            "password": "pass_alpha",
        },
        2: {
            "database_type": "sql_server",
            "host": "servidor-beta.com",
            "port": 1433,
            "database": "ERP_Beta",
            "username": "auditor_beta",
            "password": "senha_beta",
        },
        3: {
            "database_type": "oracle",
            "host": "oracle-gamma.local",
            "port": 1521,
            "database": "GAMMA_PROD",
            "username": "gamma_audit",
            "password": "oracle_123",
        },
    }

    return configs.get(empresa_id, configs[1])  # Default para empresa 1


def update_settings(**kwargs) -> None:
    """Atualiza configurações em runtime"""
    # Limpa o cache das configurações
    get_settings.cache_clear()

    # Em produção, isso atualizaria as configurações persistidas
    # Por enquanto, apenas limpa o cache para forçar recarga


# Configurações específicas por ambiente
ENVIRONMENT_CONFIGS = {
    "development": {
        "debug": True,
        "database": {"host": "localhost", "database": "auditoria_icms_dev"},
        "llm": {"temperature": 0.2, "model_name": "gpt-3.5-turbo"},
    },
    "staging": {
        "debug": False,
        "database": {
            "host": "staging-db.company.com",
            "database": "auditoria_icms_staging",
        },
        "llm": {"temperature": 0.1, "model_name": "gpt-4"},
    },
    "production": {
        "debug": False,
        "database": {"host": "prod-db.company.com", "database": "auditoria_icms_prod"},
        "llm": {"temperature": 0.05, "model_name": "gpt-4"},
        "processing": {"batch_size": 200, "max_concurrent_tasks": 20},
    },
}


def get_environment_config(environment: str) -> Dict[str, Any]:
    """Retorna configuração específica do ambiente"""
    return ENVIRONMENT_CONFIGS.get(environment, {})


def load_config(config_path: Optional[str] = None) -> Settings:
    """
    Carrega configuração da aplicação.

    Args:
        config_path: Caminho para arquivo de configuração (opcional)

    Returns:
        Settings: Configuração carregada
    """
    # Por enquanto, retorna configuração padrão
    # Em versões futuras, pode carregar de arquivo ou variáveis de ambiente
    return get_settings()


## Função duplicada get_database_url removida (mantida definição anterior)


def setup_logging(level: str = "INFO"):
    """Configura logging da aplicação."""
    import logging

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/app.log", mode="a"),
        ],
    )

    # Criar diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)
