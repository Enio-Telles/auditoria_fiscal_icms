# Verificacao Completa do Sistema - Windows 11

Write-Host "VERIFICACAO COMPLETA DO SISTEMA" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green
Write-Host ""

# Verificar Docker
Write-Host "1. Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker nao encontrado" -ForegroundColor Red
}

# Verificar containers
Write-Host ""
Write-Host "2. Verificando Containers..." -ForegroundColor Yellow
$containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
Write-Host $containers

# Verificar backend
Write-Host ""
Write-Host "3. Verificando Backend (API Gateway)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Backend rodando em http://localhost:8000" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Backend nao esta respondendo" -ForegroundColor Red
}
}

# Verificar frontend
Write-Host ""
Write-Host "4. Verificando Frontend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3001" -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Frontend rodando em http://localhost:3001" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Frontend nao esta respondendo" -ForegroundColor Red
}

# Verificar PostgreSQL
Write-Host ""
Write-Host "5. Verificando PostgreSQL..." -ForegroundColor Yellow
try {
    $pgTest = docker exec auditoria_postgres pg_isready -U auditoria_user
    if ($pgTest -like "*accepting connections*") {
        Write-Host "✓ PostgreSQL funcionando" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ PostgreSQL com problemas" -ForegroundColor Red
}

# Verificar Redis
Write-Host ""
Write-Host "6. Verificando Redis..." -ForegroundColor Yellow
try {
    $redisTest = docker exec auditoria_redis redis-cli ping
    if ($redisTest -eq "PONG") {
        Write-Host "✓ Redis funcionando" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Redis com problemas" -ForegroundColor Red
}
}

Write-Host ""
Write-Host "RESUMO DO SISTEMA" -ForegroundColor Cyan
Write-Host "=================" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3001" -ForegroundColor White
Write-Host "Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host "Redis: localhost:6379" -ForegroundColor White
Write-Host ""
Write-Host "Sistema 100% Local - Windows 11" -ForegroundColor Green
