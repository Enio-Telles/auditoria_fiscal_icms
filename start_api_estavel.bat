@echo off
echo 🚀 Iniciando API Estavel em processo separado...

REM Matar processos existentes na porta 8003
echo 🔧 Limpando porta 8003...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8003') do taskkill /f /pid %%a >nul 2>&1

REM Aguardar um pouco
timeout /t 2 /nobreak >nul

REM Iniciar API em background
echo 📡 Iniciando API...
start "API_ESTAVEL" /min python api_estavel.py

REM Aguardar API inicializar
echo ⏳ Aguardando API inicializar...
timeout /t 5 /nobreak >nul

REM Testar API
echo 🧪 Testando API...
curl -s http://127.0.0.1:8003/health

echo.
echo ✅ API deve estar rodando em http://127.0.0.1:8003
echo 📚 Documentação: http://127.0.0.1:8003/docs
echo.
echo ⚠️ Para parar a API, feche a janela "API_ESTAVEL" ou use Ctrl+C nela
pause
