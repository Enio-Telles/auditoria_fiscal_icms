Write-Host "VERIFICANDO CONTAINERS EXISTENTES..." -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

Write-Host "1. Containers existentes:"
docker ps -a --format "table {{.Names}}\t{{.Status}}"

Write-Host ""
Write-Host "2. Iniciando containers necessarios..."

$pgStatus = docker inspect --format='{{.State.Status}}' auditoria_postgres 2>$null
if ($pgStatus -eq "running") {
    Write-Host "PostgreSQL: JA RODANDO" -ForegroundColor Green
} else {
    Write-Host "Iniciando PostgreSQL..." -ForegroundColor Yellow
    docker start auditoria_postgres
}

$redisStatus = docker inspect --format='{{.State.Status}}' auditoria_redis 2>$null
if ($redisStatus -eq "running") {
    Write-Host "Redis: JA RODANDO" -ForegroundColor Green
} else {
    Write-Host "Iniciando Redis..." -ForegroundColor Yellow
    docker start auditoria_redis
}

Write-Host ""
Write-Host "3. Testando servicos..."
Write-Host "PostgreSQL:"
docker exec auditoria_postgres pg_isready -U auditoria_user

Write-Host "Redis:"
docker exec auditoria_redis redis-cli ping

Write-Host "Ollama nativo:"
Invoke-RestMethod -Uri "http://localhost:11434/api/version" -TimeoutSec 3

Write-Host ""
Write-Host "SISTEMA PRONTO!" -ForegroundColor Green
Write-Host "PostgreSQL: localhost:5432"
Write-Host "Redis: localhost:6379"
Write-Host "Ollama: localhost:11434"
