#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup do Sistema de IA para Classificação NCM/CEST
==================================================

Este script configura o ambiente completo para o sistema de IA com LLMs.

Funcionalidades:
- Instala dependências necessárias
- Configura provedores LLM (OpenAI, Ollama, etc.)
- Verifica conectividade com APIs
- Cria estrutura de diretórios
- Inicializa base de conhecimento
- Configura logs e auditoria

Uso:
    python setup_ai_system.py
"""

import os
import sys
import json
import subprocess
import asyncio
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AISystemSetup:
    """Configurador do sistema de IA"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.requirements_installed = False
        self.ollama_available = False
        self.openai_available = False
        
    def check_python_version(self) -> bool:
        """Verifica versão do Python"""
        print("🐍 Verificando versão do Python...")
        
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
            return True
        else:
            print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requer Python 3.8+")
            return False
    
    def create_directory_structure(self):
        """Cria estrutura de diretórios"""
        print("📁 Criando estrutura de diretórios...")
        
        directories = [
            "data/raw",
            "data/processed", 
            "data/cache",
            "data/test",
            "logs",
            "configs",
            "src/auditoria_icms",
            "backups"
        ]
        
        for directory in directories:
            dir_path = self.base_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ {directory}")
    
    def install_python_requirements(self) -> bool:
        """Instala dependências Python"""
        print("📦 Instalando dependências Python...")
        
        requirements = [
            # Core
            "aiohttp>=3.9.0",
            "pandas>=2.0.0",
            "numpy>=1.24.0",
            
            # LLM Providers
            "openai>=1.0.0",
            "anthropic>=0.7.0",
            
            # ML/AI (optional)
            "transformers>=4.30.0",
            "torch>=2.0.0",
            
            # Data Processing
            "PyYAML>=6.0",
            "openpyxl>=3.1.0",
            
            # Utilities
            "tqdm>=4.65.0",
            "requests>=2.31.0",
            "python-dotenv>=1.0.0"
        ]
        
        try:
            for requirement in requirements:
                print(f"  📥 Instalando {requirement}...")
                subprocess.run([
                    sys.executable, "-m", "pip", "install", requirement
                ], check=True, capture_output=True)
                
            print("✅ Todas as dependências foram instaladas")
            self.requirements_installed = True
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar dependências: {e}")
            print("💡 Tente instalar manualmente com: pip install -r requirements.txt")
            return False
    
    def create_requirements_file(self):
        """Cria arquivo requirements.txt"""
        print("📝 Criando requirements.txt...")
        
        requirements_content = """# Sistema de IA para Classificação NCM/CEST
# Core dependencies
aiohttp>=3.9.0
pandas>=2.0.0
numpy>=1.24.0
PyYAML>=6.0
openpyxl>=3.1.0
python-dotenv>=1.0.0

# LLM Providers
openai>=1.0.0
anthropic>=0.7.0

# Machine Learning
transformers>=4.30.0
torch>=2.0.0
sentence-transformers>=2.2.0
scikit-learn>=1.3.0

# Vector Search (Optional)
faiss-cpu>=1.7.0

# Utilities
tqdm>=4.65.0
requests>=2.31.0

# Development (Optional)
pytest>=7.0.0
pytest-asyncio>=0.21.0
black>=23.0.0
flake8>=6.0.0
"""
        
        with open(self.base_path / "requirements.txt", "w", encoding="utf-8") as f:
            f.write(requirements_content)
        
        print("✅ requirements.txt criado")
    
    def check_ollama_installation(self) -> bool:
        """Verifica se Ollama está instalado e funcionando"""
        print("🦙 Verificando instalação do Ollama...")
        
        try:
            import requests
            
            # Tentar conectar com Ollama
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            
            if response.status_code == 200:
                print("✅ Ollama está rodando em http://localhost:11434")
                self.ollama_available = True
                return True
            else:
                print("⚠️ Ollama não está rodando")
                print("💡 Para instalar Ollama:")
                print("   1. Acesse: https://ollama.ai")
                print("   2. Baixe e instale o Ollama")
                print("   3. Execute: ollama pull llama3.1:8b")
                return False
                
        except Exception as e:
            print(f"⚠️ Ollama não disponível: {e}")
            print("💡 Para instalar Ollama:")
            print("   1. Acesse: https://ollama.ai")
            print("   2. Baixe e instale o Ollama")
            print("   3. Execute: ollama pull llama3.1:8b")
            return False
    
    def check_openai_configuration(self) -> bool:
        """Verifica configuração da OpenAI"""
        print("🤖 Verificando configuração da OpenAI...")
        
        api_key = os.getenv("OPENAI_API_KEY")
        
        if api_key:
            print("✅ OPENAI_API_KEY encontrada")
            
            # Testar conexão (opcional)
            try:
                import openai
                client = openai.OpenAI(api_key=api_key)
                
                # Teste simples
                response = client.models.list()
                print("✅ Conexão com OpenAI testada com sucesso")
                self.openai_available = True
                return True
                
            except ImportError:
                print("⚠️ Biblioteca openai não instalada")
                return False
            except Exception as e:
                print(f"⚠️ Erro ao testar OpenAI: {e}")
                return False
        else:
            print("⚠️ OPENAI_API_KEY não configurada")
            print("💡 Configure com: export OPENAI_API_KEY='sua-chave-aqui'")
            return False
    
    def create_environment_file(self):
        """Cria arquivo .env de exemplo"""
        print("🔐 Criando arquivo .env de exemplo...")
        
        env_content = """# Configurações do Sistema de IA para Classificação NCM/CEST

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# Anthropic Configuration (Optional)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Database Configuration
DATABASE_URL=sqlite:///data/cache/auditoria.sqlite

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/ai_classification.log

# Performance Configuration
ENABLE_CACHE=true
CACHE_TTL_HOURS=24
MAX_CONCURRENT_REQUESTS=10

# Cost Optimization
MAX_DAILY_COST_USD=50.0
PREFER_LOCAL_MODELS=true
"""
        
        env_path = self.base_path / ".env.example"
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_content)
        
        print("✅ .env.example criado")
        print("💡 Copie para .env e configure suas chaves de API")
    
    def initialize_database(self):
        """Inicializa banco de dados SQLite"""
        print("🗄️ Inicializando banco de dados...")
        
        db_path = self.base_path / "data" / "cache" / "auditoria.sqlite"
        
        try:
            with sqlite3.connect(str(db_path)) as conn:
                # Tabela de auditoria
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS classification_audit (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        produto_id TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        strategy TEXT,
                        models_used TEXT,
                        ncm_result TEXT,
                        cest_result TEXT,
                        confidence_score REAL,
                        processing_time REAL,
                        cost REAL,
                        user_id TEXT,
                        metadata TEXT
                    )
                """)
                
                # Índices
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_produto_timestamp 
                    ON classification_audit(produto_id, timestamp)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_timestamp 
                    ON classification_audit(user_id, timestamp)
                """)
                
                # Tabela de cache
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS result_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cache_key TEXT UNIQUE NOT NULL,
                        request_data TEXT,
                        result_data TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        expires_at DATETIME,
                        hit_count INTEGER DEFAULT 0
                    )
                """)
                
                # Tabela de métricas
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        provider TEXT,
                        strategy TEXT,
                        response_time REAL,
                        cost REAL,
                        success BOOLEAN,
                        error_message TEXT
                    )
                """)
                
                conn.commit()
                
            print("✅ Banco de dados inicializado")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar banco: {e}")
    
    def create_sample_data(self):
        """Cria dados de exemplo para teste"""
        print("🎯 Criando dados de exemplo...")
        
        # Dados de teste
        test_data = {
            "test_products": [
                {
                    "id": "TEST001",
                    "descricao": "Smartphone Samsung Galaxy A54 5G 128GB",
                    "categoria": "Eletrônicos",
                    "marca": "Samsung",
                    "ncm_esperado": "85171211",
                    "cest_esperado": "2100100"
                },
                {
                    "id": "TEST002", 
                    "descricao": "Notebook Dell Inspiron 15 Intel Core i5",
                    "categoria": "Informática",
                    "marca": "Dell",
                    "ncm_esperado": "84713000",
                    "cest_esperado": "2100700"
                },
                {
                    "id": "TEST003",
                    "descricao": "Cerveja Skol Pilsen 350ml",
                    "categoria": "Bebidas",
                    "marca": "Skol",
                    "ncm_esperado": "22030000",
                    "cest_esperado": "1700300"
                }
            ]
        }
        
        test_file = self.base_path / "data" / "test" / "sample_products.json"
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        print("✅ Dados de exemplo criados")
    
    def create_startup_scripts(self):
        """Cria scripts de inicialização"""
        print("🚀 Criando scripts de inicialização...")
        
        # Script Windows
        batch_content = """@echo off
echo Iniciando Sistema de IA para Classificacao NCM/CEST
echo.

REM Ativar ambiente virtual se existir
if exist venv\\Scripts\\activate.bat (
    echo Ativando ambiente virtual...
    call venv\\Scripts\\activate.bat
)

REM Verificar Ollama
echo Verificando Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo AVISO: Ollama nao esta rodando
    echo Execute: ollama serve
    echo.
)

REM Executar demonstração
echo Iniciando demonstracao...
python demo_ai_classification.py

pause
"""
        
        with open(self.base_path / "start_ai_demo.bat", "w", encoding="utf-8") as f:
            f.write(batch_content)
        
        # Script Linux/Mac
        bash_content = """#!/bin/bash
echo "Iniciando Sistema de IA para Classificação NCM/CEST"
echo

# Ativar ambiente virtual se existir
if [ -f "venv/bin/activate" ]; then
    echo "Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Verificar Ollama
echo "Verificando Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "AVISO: Ollama não está rodando"
    echo "Execute: ollama serve"
    echo
fi

# Executar demonstração
echo "Iniciando demonstração..."
python demo_ai_classification.py
"""
        
        script_path = self.base_path / "start_ai_demo.sh"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(bash_content)
        
        # Tornar executável no Linux/Mac
        try:
            os.chmod(script_path, 0o755)
        except:
            pass
        
        print("✅ Scripts de inicialização criados")
    
    def display_summary(self):
        """Exibe resumo da configuração"""
        print(f"\n{'='*60}")
        print(f"{'📋 RESUMO DA CONFIGURAÇÃO':^60}")
        print(f"{'='*60}")
        
        print(f"✅ Estrutura de diretórios: Criada")
        print(f"{'✅' if self.requirements_installed else '⚠️'} Dependências Python: {'Instaladas' if self.requirements_installed else 'Verifique manualmente'}")
        print(f"{'✅' if self.ollama_available else '⚠️'} Ollama: {'Disponível' if self.ollama_available else 'Não configurado'}")
        print(f"{'✅' if self.openai_available else '⚠️'} OpenAI: {'Configurada' if self.openai_available else 'Não configurada'}")
        print(f"✅ Banco de dados: Inicializado")
        print(f"✅ Dados de exemplo: Criados")
        print(f"✅ Scripts de inicialização: Criados")
        
        print(f"\n{'🚀 PRÓXIMOS PASSOS':^60}")
        print("1. Configure suas chaves de API no arquivo .env")
        print("2. Para usar Ollama localmente:")
        print("   - Instale: https://ollama.ai")
        print("   - Execute: ollama pull llama3.1:8b")
        print("   - Inicie: ollama serve")
        print("3. Execute a demonstração:")
        print("   - Windows: start_ai_demo.bat")
        print("   - Linux/Mac: ./start_ai_demo.sh")
        print("   - Ou diretamente: python demo_ai_classification.py")
        
        print(f"\n{'📚 DOCUMENTAÇÃO':^60}")
        print("- configs/ai_config.yaml: Configurações detalhadas")
        print("- data/test/: Dados de exemplo")
        print("- logs/: Logs do sistema")
        print("- README.md: Documentação completa")
        
        print(f"\n{'💡 DICAS':^60}")
        print("- Use Ollama para desenvolvimento (gratuito)")
        print("- OpenAI para produção (melhor qualidade)")
        print("- Monitore custos via dashboard")
        print("- Configure cache para otimizar performance")
    
    def run_setup(self):
        """Executa configuração completa"""
        print(f"{'🤖 CONFIGURAÇÃO DO SISTEMA DE IA NCM/CEST':^60}")
        print(f"{'='*60}")
        
        try:
            # Verificações básicas
            if not self.check_python_version():
                return False
            
            # Criação da estrutura
            self.create_directory_structure()
            self.create_requirements_file()
            self.create_environment_file()
            
            # Instalação de dependências (opcional)
            install_deps = input("\n📦 Instalar dependências Python automaticamente? (s/n): ").lower().strip()
            if install_deps in ['s', 'sim', 'y', 'yes']:
                self.install_python_requirements()
            
            # Verificações de conectividade
            self.check_ollama_installation()
            self.check_openai_configuration()
            
            # Inicialização
            self.initialize_database()
            self.create_sample_data()
            self.create_startup_scripts()
            
            # Resumo
            self.display_summary()
            
            print(f"\n✅ Configuração concluída com sucesso!")
            return True
            
        except KeyboardInterrupt:
            print(f"\n\n👋 Configuração cancelada pelo usuário.")
            return False
        except Exception as e:
            print(f"\n❌ Erro durante a configuração: {e}")
            return False

def main():
    """Função principal"""
    setup = AISystemSetup()
    success = setup.run_setup()
    
    if success:
        print("\n🎉 Sistema pronto para uso!")
    else:
        print("\n⚠️ Configuração incompleta. Verifique os erros acima.")
        sys.exit(1)

if __name__ == "__main__":
    main()
