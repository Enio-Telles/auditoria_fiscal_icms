# Verificacao Completa do Sistema - Windows 11

Write-Host "VERIFICACAO COMPLETA DO SISTEMA" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green
Write-Host ""

# Verificar Docker
Write-Host "1. Verificando Docker..." -ForegroundColor Yellow
$dockerVersion = docker --version 2>$null
if ($dockerVersion) {
    Write-Host "✓ Docker: $dockerVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Docker nao encontrado" -ForegroundColor Red
}

# Verificar containers
Write-Host ""
Write-Host "2. Verificando Containers..." -ForegroundColor Yellow
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Verificar PostgreSQL
Write-Host ""
Write-Host "3. Verificando PostgreSQL..." -ForegroundColor Yellow
$pgTest = docker exec auditoria_postgres pg_isready -U auditoria_user 2>$null
if ($pgTest -like "*accepting connections*") {
    Write-Host "✓ PostgreSQL funcionando" -ForegroundColor Green
} else {
    Write-Host "✗ PostgreSQL com problemas" -ForegroundColor Red
}

# Verificar Redis
Write-Host ""
Write-Host "4. Verificando Redis..." -ForegroundColor Yellow
$redisTest = docker exec auditoria_redis redis-cli ping 2>$null
if ($redisTest -eq "PONG") {
    Write-Host "✓ Redis funcionando" -ForegroundColor Green
} else {
    Write-Host "✗ Redis com problemas" -ForegroundColor Red
}

Write-Host ""
Write-Host "RESUMO DO SISTEMA" -ForegroundColor Cyan
Write-Host "=================" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3001 (React)" -ForegroundColor White
Write-Host "Backend:  http://localhost:8000 (FastAPI)" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host "Redis: localhost:6379" -ForegroundColor White
Write-Host ""
Write-Host "Sistema 100% Local - Windows 11 ✓" -ForegroundColor Green
