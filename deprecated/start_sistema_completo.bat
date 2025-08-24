@echo off
echo ========================================
echo   Sistema Auditoria Fiscal ICMS v2.1
echo   Iniciando API + Frontend React
echo ========================================

REM Criar diretório de logs se não existir
if not exist logs mkdir logs

echo.
echo [1/4] Verificando se a API ja esta rodando...
powershell -Command "try { Invoke-RestMethod -Uri 'http://127.0.0.1:8003/health' -TimeoutSec 3 | Out-Null; Write-Host '✅ API ja esta rodando na porta 8003' } catch { Write-Host '❌ API nao encontrada, iniciando...' }"

REM Verificar se a API está rodando
powershell -Command "try { Invoke-RestMethod -Uri 'http://127.0.0.1:8003/health' -TimeoutSec 3 | Out-Null } catch { exit 1 }" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [2/4] Iniciando API estavel...
    echo Comando: start /B python api_estavel.py
    start /B python api_estavel.py > logs\api.log 2>&1

    REM Aguardar API inicializar
    echo Aguardando API inicializar...
    timeout /t 5 >nul

    REM Verificar se API iniciou
    powershell -Command "for ($i=1; $i -le 10; $i++) { try { $response = Invoke-RestMethod -Uri 'http://127.0.0.1:8003/health' -TimeoutSec 2; Write-Host \"✅ API iniciada com sucesso! Status: $($response.status)\"; break } catch { Write-Host \"⏳ Tentativa $i/10...\"; Start-Sleep 2 } }"

) else (
    echo ✅ API ja esta funcionando!
)

echo.
echo [3/4] Verificando status da API...
powershell -Command "try { $response = Invoke-RestMethod -Uri 'http://127.0.0.1:8003/health' -TimeoutSec 5; Write-Host \"Status: $($response.status)\"; Write-Host \"Versao: $($response.version)\" } catch { Write-Host '❌ Erro ao conectar com API' }"

echo.
echo [4/4] Iniciando Frontend React...
cd frontend

REM Verificar se node_modules existe
if not exist node_modules (
    echo ⚠️  node_modules nao encontrado, instalando dependencias...
    call npm install
)

echo Comando: npm start
echo.
echo ========================================
echo   🚀 SISTEMA COMPLETO INICIANDO!
echo ========================================
echo   API Backend: http://127.0.0.1:8003
echo   Docs API:    http://127.0.0.1:8003/docs
echo   Frontend:    http://localhost:3000
echo ========================================
echo.

REM Iniciar o frontend (esta linha bloqueia o terminal)
call npm start

echo.
echo ========================================
echo   Sistema finalizado
echo ========================================
