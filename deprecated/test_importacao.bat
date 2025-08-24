@echo off
echo 🚀 Teste de Importacao de Dados PostgreSQL
echo ==========================================

REM Verificar ambiente conda
if "%CONDA_DEFAULT_ENV%"=="" (
    echo ❌ Ambiente conda nao detectado
    echo Execute: conda activate auditoria-fiscal
    pause
    exit /b 1
)

echo ✅ Ambiente conda ativo: %CONDA_DEFAULT_ENV%

REM Verificar se Docker esta rodando
echo 🐳 Verificando Docker...
docker ps >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker nao esta rodando
    echo Inicie o Docker Desktop primeiro
    pause
    exit /b 1
)

echo ✅ Docker OK

REM Iniciar API em background
echo 🚀 Iniciando API FastAPI...
start "API FastAPI" /min python api_multi_tenant.py

echo ⏳ Aguardando API inicializar (10 segundos)...
timeout /t 10 /nobreak >nul

REM Executar teste
echo 🧪 Executando teste de importacao...
python test_importacao_real.py

echo.
echo ==========================================
echo ✅ Teste concluido!
echo.
echo 💡 Para usar a interface web:
echo    1. Mantenha a API rodando
echo    2. Execute: start_frontend.bat
echo    3. Acesse: http://localhost:3000
echo ==========================================

pause
