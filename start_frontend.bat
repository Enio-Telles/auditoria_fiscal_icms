@echo off
echo ====================================
echo  Sistema de Auditoria Fiscal ICMS
echo  Frontend React - Inicializacao
echo ====================================
echo.

echo [1/4] Verificando ambiente...
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ERRO: Node.js nao encontrado! Instale o Node.js primeiro.
    pause
    exit /b 1
)

echo [2/4] Navegando para pasta frontend...
cd /d "%~dp0frontend"
if %errorlevel% neq 0 (
    echo ERRO: Pasta frontend nao encontrada!
    pause
    exit /b 1
)

echo [3/4] Instalando dependencias...
call npm install
if %errorlevel% neq 0 (
    echo ERRO: Falha na instalacao das dependencias!
    pause
    exit /b 1
)

echo [4/4] Iniciando servidor React...
echo.
echo O frontend sera aberto em: http://localhost:3000
echo Certifique-se de que a API esteja rodando em: http://127.0.0.1:8003
echo.
echo Pressione Ctrl+C para parar o servidor
echo.

call npm start

pause
