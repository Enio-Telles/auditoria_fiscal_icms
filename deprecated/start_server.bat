@echo off
REM Startup script for Sistema de Auditoria Fiscal ICMS
REM Ativa o ambiente conda e executa o servidor

echo 🚀 Iniciando Sistema de Auditoria Fiscal ICMS...
echo ================================================

REM Ativar ambiente conda
call C:\ProgramData\Anaconda3\Scripts\activate.bat auditoria-fiscal

REM Verificar se ambiente foi ativado
if "%CONDA_DEFAULT_ENV%"=="auditoria-fiscal" (
    echo ✅ Ambiente conda ativado: %CONDA_DEFAULT_ENV%
    echo 📍 Iniciando servidor na porta 8000...
    echo 📚 Documentação: http://localhost:8000/docs
    echo ================================================

    REM Executar servidor
    python run_server.py
) else (
    echo ❌ Erro: Não foi possível ativar o ambiente conda
    echo 🔄 Tentando modo simples...
    python run_simple_server.py
)

pause
