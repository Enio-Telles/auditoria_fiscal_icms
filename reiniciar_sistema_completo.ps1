# Reiniciar Sistema Completo - Sistema de Auditoria Fiscal
# Script para usuário final resolver problemas

Write-Host "🔄 REINICIANDO SISTEMA COMPLETO..." -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Parar todos os processos
Write-Host "🛑 Parando todos os processos..." -ForegroundColor Yellow

# Parar processos Python relacionados ao sistema
$processosPython = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*auditoria*" -or $_.CommandLine -like "*main.py*"}
foreach ($processo in $processosPython) {
    Write-Host "🔪 Parando processo Python: $($processo.Id)" -ForegroundColor Gray
    Stop-Process -Id $processo.Id -Force -ErrorAction SilentlyContinue
}

# Parar processos Node.js (React)
$processosNode = Get-Process node -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*react-scripts*"}
foreach ($processo in $processosNode) {
    Write-Host "🔪 Parando processo Node.js: $($processo.Id)" -ForegroundColor Gray
    Stop-Process -Id $processo.Id -Force -ErrorAction SilentlyContinue
}

Write-Host "✅ Processos parados" -ForegroundColor Green

# Parar containers Docker
Write-Host ""
Write-Host "🐳 Reiniciando containers Docker..." -ForegroundColor Yellow

try {
    docker stop auditoria_postgres auditoria_redis 2>$null
    Write-Host "🛑 Containers parados" -ForegroundColor Gray

    Start-Sleep -Seconds 3

    docker start auditoria_postgres auditoria_redis 2>$null
    Write-Host "▶️ Containers reiniciados" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Alguns containers podem não existir - normal na primeira execução" -ForegroundColor Yellow
}

# Aguardar containers inicializarem
Write-Host ""
Write-Host "⏳ Aguardando containers inicializarem..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Verificar status dos containers
Write-Host ""
Write-Host "🔍 Verificando status dos serviços..." -ForegroundColor Cyan

# PostgreSQL
try {
    $pgTest = docker exec auditoria_postgres pg_isready -U auditoria_user 2>$null
    if ($pgTest -like "*accepting connections*") {
        Write-Host "✅ PostgreSQL: Funcionando" -ForegroundColor Green
    } else {
        Write-Host "⚠️ PostgreSQL: Ainda inicializando..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ PostgreSQL: Problema" -ForegroundColor Red
}

# Redis
try {
    $redisTest = docker exec auditoria_redis redis-cli ping 2>$null
    if ($redisTest -eq "PONG") {
        Write-Host "✅ Redis: Funcionando" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Redis: Ainda inicializando..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Redis: Problema" -ForegroundColor Red
}

# Ollama
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/version" -TimeoutSec 3
    Write-Host "✅ Ollama: Funcionando (versão $($response.version))" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Ollama: Não está respondendo" -ForegroundColor Yellow
    Write-Host "💡 Se precisar de IA, execute: ollama serve" -ForegroundColor Gray
}

# Limpar cache e arquivos temporários
Write-Host ""
Write-Host "🧹 Limpando arquivos temporários..." -ForegroundColor Yellow

if (Test-Path "data\temp") {
    Remove-Item "data\temp\*" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Cache limpo" -ForegroundColor Green
}

if (Test-Path "__pycache__") {
    Remove-Item "__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Cache Python limpo" -ForegroundColor Green
}

# Verificar espaço em disco
Write-Host ""
Write-Host "💾 Verificando espaço em disco..." -ForegroundColor Yellow
$espacoLivre = Get-WmiObject -Class Win32_LogicalDisk | Where-Object {$_.DeviceID -eq "C:"} | Select-Object @{Name="FreeSpaceGB";Expression={[math]::Round($_.FreeSpace/1GB,2)}}
Write-Host "💾 Espaço livre no disco C: $($espacoLivre.FreeSpaceGB) GB" -ForegroundColor White

if ($espacoLivre.FreeSpaceGB -lt 5) {
    Write-Host "⚠️ ATENÇÃO: Pouco espaço em disco!" -ForegroundColor Red
    Write-Host "💡 Considere fazer limpeza do sistema" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 REINICIALIZAÇÃO CONCLUÍDA!" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green
Write-Host ""
Write-Host "▶️ PRÓXIMOS PASSOS:" -ForegroundColor Cyan
Write-Host "1. Execute: .\iniciar_backend.ps1 (em nova janela)" -ForegroundColor White
Write-Host "2. Execute: .\iniciar_frontend.ps1 (em nova janela)" -ForegroundColor White
Write-Host "3. Acesse: http://localhost:3001" -ForegroundColor White
Write-Host ""
Write-Host "🔑 LOGIN:" -ForegroundColor Yellow
Write-Host "Email: admin@demo.com" -ForegroundColor White
Write-Host "Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "Se ainda houver problemas:" -ForegroundColor Gray
Write-Host "- Verifique se Docker Desktop está rodando" -ForegroundColor White
Write-Host "- Reinicie o computador" -ForegroundColor White
Write-Host "- Execute: .\verificar_status.ps1" -ForegroundColor White

pause
