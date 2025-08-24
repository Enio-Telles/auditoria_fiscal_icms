"""
ConfiguraÃ§Ã£o de desenvolvimento para o Sistema de Auditoria Fiscal ICMS
Este arquivo contÃ©m configuraÃ§Ãµes especÃ­ficas para ambiente de desenvolvimento
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

# DiretÃ³rio base do projeto
BASE_DIR = Path(__file__).parent

# ConfiguraÃ§Ãµes de ambiente
class DevelopmentConfig:
    """ConfiguraÃ§Ãµes para ambiente de desenvolvimento"""
    
    # Ambiente
    ENVIRONMENT = "development"
    DEBUG = True
    TESTING = False
    
    # Banco de dados
    DATABASE_URL = "postgresql://postgres:admin@localhost:5432/auditoria_fiscal_icms"
    DATABASE_ECHO = True  # Log SQL queries
    
    # Cache
    REDIS_URL = "redis://localhost:6379/0"
    CACHE_ENABLED = True
    CACHE_TTL = 300  # 5 minutos em desenvolvimento
    
    # IA e LLM
    AI_PROVIDERS = {
        "ollama": {
            "enabled": True,
            "base_url": "http://localhost:11434",
            "default_model": "llama3",
            "timeout": 60
        },
        "openai": {
            "enabled": False,  # Desabilitado por padrÃ£o em dev
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "default_model": "gpt-3.5-turbo",
            "max_tokens": 1000
        },
        "anthropic": {
            "enabled": False,  # Desabilitado por padrÃ£o em dev
            "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
            "default_model": "claude-3-haiku"
        }
    }
    
    # ConfiguraÃ§Ãµes RAG
    RAG_CONFIG = {
        "chroma_persist_directory": str(BASE_DIR / "data" / "chroma_dev"),
        "embeddings_model": "sentence-transformers/all-MiniLM-L6-v2",
        "chunk_size": 500,  # Menor para desenvolvimento
        "chunk_overlap": 100,
        "max_retrieval_docs": 3
    }
    
    # Logging
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
                "style": "{",
            },
            "simple": {
                "format": "{levelname} {message}",
                "style": "{",
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "verbose"
            },
            "file": {
                "level": "INFO",
                "class": "logging.FileHandler",
                "filename": str(BASE_DIR / "logs" / "development.log"),
                "formatter": "verbose"
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    
    # DiretÃ³rios
    DATA_DIR = BASE_DIR / "data"
    UPLOAD_DIR = DATA_DIR / "uploads"
    REPORTS_DIR = DATA_DIR / "reports"
    TEMP_DIR = DATA_DIR / "temp"
    BACKUP_DIR = DATA_DIR / "backups"
    LOGS_DIR = BASE_DIR / "logs"
    
    # SeguranÃ§a (desenvolvimento)
    SECRET_KEY = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Mais tempo em dev
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    
    # Performance
    MAX_CONCURRENT_REQUESTS = 3  # Limitado em desenvolvimento
    BATCH_SIZE = 5  # Menor em desenvolvimento
    
    # ConfiguraÃ§Ãµes de classificaÃ§Ã£o
    CLASSIFICATION_CONFIG = {
        "auto_threshold": 0.8,
        "review_threshold": 0.6,
        "max_retries": 2,
        "timeout": 30
    }

class ProductionConfig:
    """ConfiguraÃ§Ãµes para ambiente de produÃ§Ã£o"""
    
    # Ambiente
    ENVIRONMENT = "production"
    DEBUG = False
    TESTING = False
    
    # Banco de dados
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/prod_db")
    DATABASE_ECHO = False
    
    # Cache
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_ENABLED = True
    CACHE_TTL = 3600  # 1 hora
    
    # IA e LLM (produÃ§Ã£o usa configuraÃ§Ãµes do .env)
    AI_PROVIDERS = {
        "ollama": {
            "enabled": True,
            "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            "default_model": os.getenv("OLLAMA_DEFAULT_MODEL", "llama3"),
            "timeout": 120
        },
        "openai": {
            "enabled": bool(os.getenv("OPENAI_API_KEY")),
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "default_model": os.getenv("OPENAI_DEFAULT_MODEL", "gpt-3.5-turbo"),
            "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
        },
        "anthropic": {
            "enabled": bool(os.getenv("ANTHROPIC_API_KEY")),
            "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
            "default_model": os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-3-haiku")
        }
    }
    
    # Logging
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "production": {
                "format": "{asctime} [{levelname}] {name}: {message}",
                "style": "{",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
        },
        "handlers": {
            "file": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/production.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "production"
            },
        },
        "loggers": {
            "": {
                "handlers": ["file"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    
    # SeguranÃ§a
    SECRET_KEY = os.getenv("SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")
    
    # Performance
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))

def get_config() -> Dict[str, Any]:
    """
    Retorna configuraÃ§Ã£o baseada no ambiente
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionConfig.__dict__
    elif env == "testing":
        # ConfiguraÃ§Ã£o de teste pode ser adicionada aqui
        return DevelopmentConfig.__dict__
    else:
        return DevelopmentConfig.__dict__

def setup_directories():
    """
    Cria diretÃ³rios necessÃ¡rios se nÃ£o existirem
    """
    config = get_config()
    
    directories = [
        config.get('DATA_DIR'),
        config.get('UPLOAD_DIR'),
        config.get('REPORTS_DIR'),
        config.get('TEMP_DIR'),
        config.get('BACKUP_DIR'),
        config.get('LOGS_DIR'),
    ]
    
    for directory in directories:
        if directory:
            Path(directory).mkdir(parents=True, exist_ok=True)

def validate_config() -> bool:
    """
    Valida configuraÃ§Ãµes essenciais
    """
    config = get_config()
    
    # Verifica se variÃ¡veis essenciais estÃ£o definidas
    required_vars = [
        'DATABASE_URL',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not config.get(var) or config.get(var) == "your-secret-key-change-this-in-production":
            missing_vars.append(var)
    
    if missing_vars:
        print(f"âš ï¸  ConfiguraÃ§Ãµes obrigatÃ³rias nÃ£o definidas: {', '.join(missing_vars)}")
        print("Configure o arquivo .env com as variÃ¡veis necessÃ¡rias.")
        return False
    
    return True

if __name__ == "__main__":
    # Executar validaÃ§Ã£o de configuraÃ§Ã£o
    print("ðŸ”§ Validando configuraÃ§Ãµes...")
    
    setup_directories()
    print("âœ“ DiretÃ³rios criados/verificados")
    
    if validate_config():
        print("âœ“ ConfiguraÃ§Ãµes vÃ¡lidas")
        print(f"âœ“ Ambiente: {get_config()['ENVIRONMENT']}")
    else:
        print("âŒ Problemas na configuraÃ§Ã£o encontrados")
        exit(1)
    
    print("ðŸš€ Sistema pronto para execuÃ§Ã£o!")


# Configuracao de Agentes
USE_REAL_AGENTS = True
MOCK_AGENTS = False

