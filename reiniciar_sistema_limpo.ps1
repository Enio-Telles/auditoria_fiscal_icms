# Script para reiniciar sistema completo - Versao limpa
# Script para usuario final resolver problemas

Write-Host "REINICIANDO SISTEMA COMPLETO..." -ForegroundColor Green
Write-Host ""

# 1. Parar todos os processos
Write-Host "Parando todos os processos..." -ForegroundColor Yellow

# Parar processos Python
$processosPython = Get-Process -Name python -ErrorAction SilentlyContinue
foreach ($processo in $processosPython) {
    Write-Host "Parando processo Python: $($processo.Id)" -ForegroundColor Gray
    Stop-Process -Id $processo.Id -Force -ErrorAction SilentlyContinue
}

# Parar processos Node.js
$processosNode = Get-Process -Name node -ErrorAction SilentlyContinue
foreach ($processo in $processosNode) {
    Write-Host "Parando processo Node.js: $($processo.Id)" -ForegroundColor Gray
    Stop-Process -Id $processo.Id -Force -ErrorAction SilentlyContinue
}

Write-Host "Processos parados" -ForegroundColor Green
Write-Host ""

# 2. Reiniciar containers Docker
Write-Host "Reiniciando containers Docker..." -ForegroundColor Yellow
try {
    # Parar containers
    docker-compose down
    Write-Host "Containers parados" -ForegroundColor Gray

    # Iniciar containers
    docker-compose up -d
    Write-Host "Containers reiniciados" -ForegroundColor Green
} catch {
    Write-Host "Alguns containers podem nao existir - normal na primeira execucao" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Aguardando containers inicializarem..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# 3. Verificar status
Write-Host "Verificando status dos servicos..." -ForegroundColor Cyan

# Verificar PostgreSQL
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "PostgreSQL: Funcionando" -ForegroundColor Green
    } else {
        Write-Host "PostgreSQL: Ainda inicializando..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "PostgreSQL: Ainda nao disponivel" -ForegroundColor Red
}

# Verificar Ollama
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/" -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "Ollama: Funcionando" -ForegroundColor Green
    } else {
        Write-Host "Ollama: Problema detectado" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Ollama: Nao disponivel" -ForegroundColor Red
}

Write-Host ""

# 4. Iniciar backend
Write-Host "Iniciando backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-Command", "& '.\iniciar_backend.ps1'"

Write-Host "Aguardando backend inicializar..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 5. Iniciar frontend
Write-Host "Iniciando frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-Command", "& '.\iniciar_frontend.ps1'"

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "SISTEMA REINICIADO COM SUCESSO!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "URLs do sistema:" -ForegroundColor White
Write-Host "- Frontend: http://localhost:3001" -ForegroundColor Cyan
Write-Host "- Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "- Docs API: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "- Ollama:   http://localhost:11434" -ForegroundColor Cyan
Write-Host ""
Write-Host "Credenciais de acesso:" -ForegroundColor White
Write-Host "Usuario: admin" -ForegroundColor White
Write-Host "Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "Se ainda houver problemas:" -ForegroundColor Gray
Write-Host "- Verifique se Docker Desktop esta rodando" -ForegroundColor White
Write-Host "- Reinicie o computador" -ForegroundColor White
Write-Host "- Execute: .\verificar_status.ps1" -ForegroundColor White

pause
