@echo off
echo Iniciando Sistema de IA para Classificacao NCM/CEST
echo.

REM Ativar ambiente virtual se existir
if exist venv\Scripts\activate.bat (
    echo Ativando ambiente virtual...
    call venv\Scripts\activate.bat
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
