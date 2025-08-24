# Iniciar Banco de Dados - Sistema de Auditoria Fiscal
# Script para usuário final

Write-Host "💾 INICIANDO BANCO DE DADOS..." -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green

# Verificar se Docker está instalado
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker não encontrado!" -ForegroundColor Red
    Write-Host "📥 Instale em: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    pause
    exit 1
}

# Verificar se Docker está rodando
try {
    docker version | Out-Null
} catch {
    Write-Host "❌ Docker não está rodando!" -ForegroundColor Red
    Write-Host "🔄 Abra o Docker Desktop e aguarde inicializar" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "✅ Docker funcionando" -ForegroundColor Green

# Verificar containers existentes
Write-Host "🔍 Verificando containers existentes..." -ForegroundColor Yellow

$postgresExists = docker ps -a --filter "name=auditoria_postgres" --format "{{.Names}}"
$redisExists = docker ps -a --filter "name=auditoria_redis" --format "{{.Names}}"

# PostgreSQL
if ($postgresExists) {
    Write-Host "📁 Container PostgreSQL encontrado" -ForegroundColor Green
    $postgresStatus = docker inspect --format='{{.State.Status}}' auditoria_postgres
    if ($postgresStatus -eq "running") {
        Write-Host "✅ PostgreSQL já está rodando" -ForegroundColor Green
    } else {
        Write-Host "🔄 Iniciando PostgreSQL..." -ForegroundColor Yellow
        docker start auditoria_postgres
        Write-Host "✅ PostgreSQL iniciado" -ForegroundColor Green
    }
} else {
    Write-Host "📦 Criando container PostgreSQL..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "data\postgres" -Force | Out-Null
    docker run -d --name auditoria_postgres `
        -e POSTGRES_DB=auditoria_fiscal_local `
        -e POSTGRES_USER=auditoria_user `
        -e POSTGRES_PASSWORD=auditoria123 `
        -p 5432:5432 `
        -v ${PWD}\data\postgres:/var/lib/postgresql/data `
        postgres:15-alpine
    Write-Host "✅ PostgreSQL criado e iniciado" -ForegroundColor Green
}

# Redis
if ($redisExists) {
    Write-Host "📁 Container Redis encontrado" -ForegroundColor Green
    $redisStatus = docker inspect --format='{{.State.Status}}' auditoria_redis
    if ($redisStatus -eq "running") {
        Write-Host "✅ Redis já está rodando" -ForegroundColor Green
    } else {
        Write-Host "🔄 Iniciando Redis..." -ForegroundColor Yellow
        docker start auditoria_redis
        Write-Host "✅ Redis iniciado" -ForegroundColor Green
    }
} else {
    Write-Host "📦 Criando container Redis..." -ForegroundColor Yellow
    docker run -d --name auditoria_redis `
        -p 6379:6379 `
        redis:7-alpine
    Write-Host "✅ Redis criado e iniciado" -ForegroundColor Green
}

# Aguardar containers inicializarem
Write-Host "⏳ Aguardando containers inicializarem..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Testar conexões
Write-Host "🧪 Testando conexões..." -ForegroundColor Yellow

try {
    $pgTest = docker exec auditoria_postgres pg_isready -U auditoria_user
    if ($pgTest -like "*accepting connections*") {
        Write-Host "✅ PostgreSQL: Funcionando" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ PostgreSQL: Ainda inicializando..." -ForegroundColor Yellow
}

try {
    $redisTest = docker exec auditoria_redis redis-cli ping
    if ($redisTest -eq "PONG") {
        Write-Host "✅ Redis: Funcionando" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️ Redis: Ainda inicializando..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 BANCO DE DADOS PRONTO!" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
Write-Host "PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host "Redis: localhost:6379" -ForegroundColor White
Write-Host ""
Write-Host "▶️ PRÓXIMO PASSO:" -ForegroundColor Cyan
Write-Host "Execute: .\iniciar_backend.ps1" -ForegroundColor White
Write-Host ""

pause
