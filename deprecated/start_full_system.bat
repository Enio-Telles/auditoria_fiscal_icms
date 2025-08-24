@echo off
echo ========================================
echo  Sistema de Auditoria Fiscal ICMS
echo  Inicializacao Completa (API + Frontend)
echo ========================================
echo.

echo [1/5] Ativando ambiente Python...
call conda activate auditoria-fiscal
if %errorlevel% neq 0 (
    echo ERRO: Ambiente conda 'auditoria-fiscal' nao encontrado!
    echo Execute: conda create -n auditoria-fiscal python=3.11
    pause
    exit /b 1
)

echo [2/5] Subindo infraestrutura Docker...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ERRO: Falha ao subir containers Docker!
    pause
    exit /b 1
)

echo [3/5] Aguardando containers inicializarem...
timeout /t 30 /nobreak

echo [4/5] Verificando estrutura multi-tenant...
python scripts\create_multi_tenant_docker.py
if %errorlevel% neq 0 (
    echo AVISO: Falha na criacao da estrutura multi-tenant
)

echo [5/5] Iniciando API...
echo.
echo ====================================
echo  SISTEMA PRONTO!
echo ====================================
echo  API Swagger: http://127.0.0.1:8003/docs
echo  Frontend: Execute start_frontend.bat
echo  Health Check: http://127.0.0.1:8003/health
echo ====================================
echo.

python api_multi_tenant.py
