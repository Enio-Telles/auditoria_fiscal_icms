@echo off
echo 🚀 Iniciando Sistema Completo com Funcionalidade de Importacao
echo ============================================================

REM Verificar se o ambiente conda esta ativo
if "%CONDA_DEFAULT_ENV%"=="" (
    echo ❌ Ambiente conda nao detectado
    echo Execute: conda activate auditoria-fiscal
    pause
    exit /b 1
)

echo ✅ Ambiente conda ativo: %CONDA_DEFAULT_ENV%

REM Instalar dependencias para importacao de dados
echo 📦 Instalando dependencias para importacao de dados...
pip install pyodbc mysql-connector-python

REM Verificar se Docker esta rodando
echo 🐳 Verificando Docker...
docker ps >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker nao esta rodando
    echo Inicie o Docker Desktop primeiro
    pause
    exit /b 1
)

REM Subir containers
echo 🐳 Subindo containers Docker...
docker-compose up -d

echo ⏳ Aguardando containers iniciarem (30 segundos)...
timeout /t 30 /nobreak >nul

REM Verificar se PostgreSQL esta respondendo
echo 🗄️ Verificando PostgreSQL...
docker-compose exec -T postgres pg_isready
if errorlevel 1 (
    echo ❌ PostgreSQL nao esta respondendo
    echo Aguarde mais alguns segundos e tente novamente
    pause
    exit /b 1
)

REM Criar estrutura multi-tenant (apenas na primeira execucao)
echo 🏗️ Criando estrutura multi-tenant...
python scripts\create_multi_tenant_docker.py

REM Iniciar API em background
echo 🚀 Iniciando API FastAPI...
start "API FastAPI" python api_multi_tenant.py

echo ⏳ Aguardando API inicializar (10 segundos)...
timeout /t 10 /nobreak >nul

REM Verificar se API esta respondendo
echo 🔍 Verificando API...
curl -s http://127.0.0.1:8003/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️ API pode ainda estar inicializando...
    echo Aguarde mais alguns segundos
)

REM Iniciar frontend React
echo ⚛️ Iniciando Frontend React...
cd frontend

REM Verificar se node_modules existe
if not exist "node_modules" (
    echo 📦 Instalando dependencias React...
    npm install
)

echo 🌐 Iniciando servidor React...
npm start

echo ============================================================
echo ✅ SISTEMA COMPLETO INICIADO COM SUCESSO!
echo.
echo 🔗 Acessos:
echo    Frontend React:     http://localhost:3000
echo    API Documentation:  http://127.0.0.1:8003/docs
echo    Health Check:       http://127.0.0.1:8003/health
echo    Importacao:         http://localhost:3000/empresas/[ID]/importar
echo.
echo 📋 Funcionalidades Disponiveis:
echo    ✅ Dashboard Executivo
echo    ✅ Gestao Multi-Tenant de Empresas
echo    ✅ Produtos por Empresa
echo    ✅ Sistema de Classificacoes IA
echo    ✅ Golden Set (Base de Conhecimento)
echo    ✅ NOVO: Importacao de Dados Externos
echo.
echo 💾 Suporte a Importacao:
echo    ✅ SQL Server (com pyodbc)
echo    ✅ PostgreSQL
echo    ✅ MySQL (com mysql-connector-python)
echo.
echo ⚠️ Para parar o sistema:
echo    - Feche este terminal (React)
echo    - Feche a janela da API
echo    - Execute: docker-compose down
echo ============================================================

pause
