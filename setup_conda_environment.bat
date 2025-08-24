@echo off
echo ============================================================
echo Setup Conda Environment - Sistema de Auditoria Fiscal ICMS
echo ============================================================

echo.
echo 1. Verificando se o Anaconda/Miniconda está instalado...
where conda >nul 2>&1
if errorlevel 1 (
    echo ERRO: Conda não encontrado. Por favor, instale o Anaconda ou Miniconda.
    echo Download: https://www.anaconda.com/products/distribution
    pause
    exit /b 1
)

echo ✓ Conda encontrado!
echo.

echo 2. Criando ambiente conda 'auditoria-fiscal-icms'...
call conda env create -f environment.yml

if errorlevel 1 (
    echo.
    echo AVISO: Ambiente pode já existir. Tentando atualizar...
    call conda env update -f environment.yml --prune
)

echo.
echo 3. Ativando ambiente...
call conda activate auditoria-fiscal-icms

echo.
echo 4. Verificando instalação...
python --version
pip --version

echo.
echo 5. Instalando dependências adicionais de desenvolvimento...
pip install pre-commit black isort flake8 mypy pytest-cov

echo.
echo 6. Configurando hooks de desenvolvimento (opcional)...
if exist .git (
    pre-commit install
    echo ✓ Hooks de desenvolvimento configurados
) else (
    echo - Git não inicializado, pulando configuração de hooks
)

echo.
echo 7. Criando estrutura de diretórios...
if not exist "data" mkdir data
if not exist "data\uploads" mkdir data\uploads
if not exist "data\reports" mkdir data\reports
if not exist "data\backups" mkdir data\backups
if not exist "data\temp" mkdir data\temp
if not exist "data\chroma" mkdir data\chroma
if not exist "logs" mkdir logs
if not exist "tests" mkdir tests

echo.
echo 8. Verificando conectividade com serviços externos...
echo Testando Ollama (local)...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo - Ollama não está rodando em http://localhost:11434
    echo   Para instalar: https://ollama.ai/
) else (
    echo ✓ Ollama conectado
)

echo.
echo Testando PostgreSQL...
psql --version >nul 2>&1
if errorlevel 1 (
    echo - PostgreSQL não encontrado
    echo   Instale PostgreSQL ou configure connection string no .env
) else (
    echo ✓ PostgreSQL encontrado
)

echo.
echo ============================================================
echo ✓ SETUP CONCLUÍDO COM SUCESSO!
echo ============================================================
echo.
echo Para usar o ambiente:
echo 1. conda activate auditoria-fiscal-icms
echo 2. Copie .env.example para .env e configure suas variáveis
echo 3. Execute: python setup_database.py (se necessário)
echo 4. Inicie o sistema: python main.py ou start_sistema_completo.bat
echo.
echo PRÓXIMOS PASSOS:
echo 1. Configure as APIs keys no arquivo .env
echo 2. Configure conexão com banco de dados
echo 3. Execute testes: pytest
echo 4. Inicie desenvolvimento!
echo.

pause
