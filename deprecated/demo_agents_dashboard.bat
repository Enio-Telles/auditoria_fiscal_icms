@echo off
echo ========================================
echo 🖥️ DEMO - INTERFACE DE AGENTES
echo ========================================
echo.
echo Este script demonstra a interface de agentes
echo Dashboard completo para monitoramento e controle
echo.

echo ⚡ Iniciando servidor mock da API de agentes...
echo.

cd /d "%~dp0"

:: Verificar se estamos no diretório correto
if not exist "frontend\src\services\mock\mock_agents_api.py" (
    echo ❌ ERRO: Arquivo mock_agents_api.py não encontrado!
    echo    Certifique-se de estar na raiz do projeto
    pause
    exit /b 1
)

:: Verificar se Python está disponível
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERRO: Python não encontrado!
    echo    Instale Python ou ative o ambiente conda
    pause
    exit /b 1
)

:: Verificar se o ambiente conda está ativo
where conda >nul 2>&1
if %errorlevel% equ 0 (
    echo 🐍 Ativando ambiente conda...
    call conda activate auditoria-fiscal-icms
)

echo.
echo 📦 Verificando dependências...
python -c "import flask, flask_cors" 2>nul
if %errorlevel% neq 0 (
    echo 📦 Instalando dependências do servidor mock...
    pip install flask flask-cors
)

echo.
echo 🚀 Iniciando servidor mock da API de agentes...
echo    URL: http://127.0.0.1:5001
echo    Endpoints: /api/agents, /api/tasks, /api/workflows
echo.

start cmd /k "cd /d frontend\src\services\mock && python mock_agents_api.py"

timeout /t 3 /nobreak >nul

echo.
echo 🌐 Verificando se o servidor está respondendo...
curl -s http://127.0.0.1:5001/api/agents/status >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Servidor mock funcionando!
) else (
    echo ⏳ Servidor ainda iniciando... (normal)
)

echo.
echo 📱 Agora inicie o frontend React:
echo.
echo    cd frontend
echo    npm start
echo.
echo 🖥️ Acesse o dashboard em:
echo    http://localhost:3000/agents
echo.
echo 🎛️ Funcionalidades disponíveis:
echo    ✅ Monitoramento em tempo real
echo    ✅ Controle de agentes (start/stop/restart)
echo    ✅ Execução de tarefas
echo    ✅ Métricas de sistema
echo    ✅ Classificação rápida
echo    ✅ Histórico de execuções
echo.

set /p choice="🚀 Deseja abrir o frontend automaticamente? (s/n): "
if /i "%choice%"=="s" (
    echo.
    echo 🚀 Iniciando frontend React...
    cd frontend
    start cmd /k "npm start"
    
    echo.
    echo ⏳ Aguardando frontend inicializar...
    timeout /t 10 /nobreak >nul
    
    echo 🌐 Abrindo navegador...
    start http://localhost:3000/agents
)

echo.
echo ========================================
echo ✅ SETUP COMPLETO!
echo ========================================
echo.
echo 📊 Mock API: http://127.0.0.1:5001
echo 🖥️ Dashboard: http://localhost:3000/agents
echo.
echo Para parar os serviços:
echo - Feche as janelas de terminal abertas
echo - Ou pressione Ctrl+C em cada uma
echo.
pause
