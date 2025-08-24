@echo off
echo ==============================================
echo 🚀 INICIANDO SISTEMA COMPLETO DE AUDITORIA FISCAL
echo ==============================================
echo.

echo 📋 Verificando dependencias...
echo.

REM Ativar ambiente conda
echo 🔧 Ativando ambiente conda...
call conda activate auditoria-fiscal
if errorlevel 1 (
    echo ❌ Erro ao ativar ambiente conda
    pause
    exit /b 1
)

echo.
echo 📦 Verificando instalação do Ollama...
ollama list >nul 2>&1
if errorlevel 1 (
    echo ❌ Ollama não está instalado ou não está rodando
    echo 💡 Execute: ollama serve
    pause
    exit /b 1
)

echo ✅ Ollama está funcionando
echo.

echo 🤖 Iniciando Mock Agents API...
start "Mock Agents API" cmd /k "conda activate auditoria-fiscal && python frontend\src\services\mock\mock_agents_api.py"

echo ⏳ Aguardando Mock API inicializar...
timeout /t 3 /nobreak >nul

echo.
echo ⚛️ Iniciando React Frontend...
start "React Frontend" cmd /k "cd frontend && npm start"

echo ⏳ Aguardando React inicializar...
timeout /t 5 /nobreak >nul

echo.
echo 🧠 Testando sistema completo...
timeout /t 2 /nobreak >nul
python test_sistema_completo.py

echo.
echo ==============================================
echo 🎉 SISTEMA INICIADO COM SUCESSO!
echo ==============================================
echo.
echo 📋 SERVIÇOS DISPONÍVEIS:
echo   🤖 Mock Agents API: http://localhost:8007
echo   ⚛️ React Frontend: http://localhost:3000
echo   🧠 Ollama AI: http://localhost:11434
echo.
echo 🔐 CREDENCIAIS DE DEMO:
echo   Email: admin@demo.com
echo   Senha: admin123
echo.
echo 📖 ENDPOINTS MOCK API:
echo   GET  /agents/status       - Status do sistema
echo   GET  /agents             - Lista de agentes
echo   POST /agents/quick-classify - Classificação NCM
echo   GET  /agents/metrics     - Métricas do sistema
echo.
echo 🔗 Para acessar o sistema:
echo   1. Abra http://localhost:3000
echo   2. Faça login com as credenciais acima
echo   3. Teste a classificação de produtos
echo.
echo Pressione qualquer tecla para continuar...
pause >nul
