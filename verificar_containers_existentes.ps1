# Verificar e Usar Containers Existentes - Windows 11

Write-Host "VERIFICANDO CONTAINERS EXISTENTES..." -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Verificar containers existentes
Write-Host "1. Verificando containers..." -ForegroundColor Yellow
$containers = docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
Write-Host $containers

# Iniciar containers necessários se não estiverem rodando
Write-Host ""
Write-Host "2. Iniciando containers necessários..." -ForegroundColor Yellow

$postgresStatus = docker inspect --format='{{.State.Status}}' auditoria_postgres 2>$null
if ($postgresStatus -eq "running") {
    Write-Host "✓ PostgreSQL já rodando" -ForegroundColor Green
} elseif ($postgresStatus -eq "exited") {
    Write-Host "⚡ Iniciando PostgreSQL..." -ForegroundColor Yellow
    docker start auditoria_postgres
    Write-Host "✓ PostgreSQL iniciado" -ForegroundColor Green
} else {
    Write-Host "✗ Container PostgreSQL não encontrado" -ForegroundColor Red
}

$redisStatus = docker inspect --format='{{.State.Status}}' auditoria_redis 2>$null
if ($redisStatus -eq "running") {
    Write-Host "✓ Redis já rodando" -ForegroundColor Green
} elseif ($redisStatus -eq "exited") {
    Write-Host "⚡ Iniciando Redis..." -ForegroundColor Yellow
    docker start auditoria_redis
    Write-Host "✓ Redis iniciado" -ForegroundColor Green
} else {
    Write-Host "✗ Container Redis não encontrado" -ForegroundColor Red
}

# Verificar Ollama nativo
Write-Host ""
Write-Host "3. Verificando Ollama nativo..." -ForegroundColor Yellow
try {
    $ollamaVersion = Invoke-RestMethod -Uri "http://localhost:11434/api/version" -TimeoutSec 5
    Write-Host "✓ Ollama nativo rodando (versão $($ollamaVersion.version))" -ForegroundColor Green
} catch {
    Write-Host "✗ Ollama nativo não está respondendo" -ForegroundColor Red
    Write-Host "  Execute: ollama serve (se instalado)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "STATUS FINAL DOS SERVIÇOS:" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan

# Status PostgreSQL
try {
    $pgTest = docker exec auditoria_postgres pg_isready -U auditoria_user 2>$null
    if ($pgTest -like "*accepting connections*") {
        Write-Host "✓ PostgreSQL: FUNCIONANDO (porta 5432)" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ PostgreSQL: ERRO" -ForegroundColor Red
}

# Status Redis
try {
    $redisTest = docker exec auditoria_redis redis-cli ping 2>$null
    if ($redisTest -eq "PONG") {
        Write-Host "✓ Redis: FUNCIONANDO (porta 6379)" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Redis: ERRO" -ForegroundColor Red
}

Write-Host ""
Write-Host "AMBIENTE PRONTO PARA USO!" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green
Write-Host "PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host "Redis: localhost:6379" -ForegroundColor White
Write-Host "Ollama: localhost:11434" -ForegroundColor White
Write-Host ""
Write-Host "Execute agora:" -ForegroundColor Cyan
Write-Host "1. .\start_backend_simples.ps1" -ForegroundColor White
Write-Host "2. cd frontend; npm start" -ForegroundColor White
