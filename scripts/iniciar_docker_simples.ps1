# Diagnostico e Inicializacao Docker - Windows 11
# Sistema de Auditoria Fiscal ICMS v4.0

Write-Host "Diagnostico Docker Windows 11..." -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""

# Verificar se Docker Desktop esta instalado
$dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
if (Test-Path $dockerPath) {
    Write-Host "Docker Desktop instalado" -ForegroundColor Green
} else {
    Write-Host "Docker Desktop nao encontrado!" -ForegroundColor Red
    Write-Host "Baixe em: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

# Verificar se Docker esta rodando
try {
    docker info | Out-Null
    Write-Host "Docker esta respondendo" -ForegroundColor Green
    $dockerReady = $true
} catch {
    Write-Host "Docker nao esta respondendo" -ForegroundColor Red
    $dockerReady = $false
}

# Iniciar Docker se necessario
if (-not $dockerReady) {
    Write-Host "Iniciando Docker Desktop..." -ForegroundColor Yellow
    Start-Process -FilePath $dockerPath -WindowStyle Minimized

    Write-Host "Aguardando Docker inicializar..." -ForegroundColor Yellow
    $maxWait = 24  # 120 segundos
    $count = 0

    do {
        Start-Sleep -Seconds 5
        $count++
        Write-Host "Tentativa $count de $maxWait..." -ForegroundColor Gray

        try {
            docker info | Out-Null
            $dockerReady = $true
            Write-Host "Docker esta pronto!" -ForegroundColor Green
            break
        } catch {
            # Continua tentando
        }
    } while ($count -lt $maxWait)

    if (-not $dockerReady) {
        Write-Host "Docker nao ficou pronto em 2 minutos" -ForegroundColor Red
        Write-Host "Verifique se Docker Desktop inicializou corretamente" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "Configurando containers locais..." -ForegroundColor Cyan
Write-Host "---------------------------------"

# Criar network
Write-Host "Criando network..." -ForegroundColor Yellow
docker network create auditoria-local-network 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Network criada com sucesso" -ForegroundColor Green
} else {
    Write-Host "Network ja existe ou erro ao criar" -ForegroundColor Yellow
}

# Configurar PostgreSQL
Write-Host "Configurando PostgreSQL..." -ForegroundColor Yellow
$pgExists = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq "auditoria-postgres-local" }
if ($pgExists) {
    Write-Host "Container PostgreSQL ja existe, iniciando..." -ForegroundColor Yellow
    docker start auditoria-postgres-local | Out-Null
} else {
    Write-Host "Criando container PostgreSQL..." -ForegroundColor Yellow
    docker run -d --name auditoria-postgres-local --network auditoria-local-network -e POSTGRES_DB=auditoria_fiscal_local -e POSTGRES_USER=auditoria_user -e POSTGRES_PASSWORD=auditoria123 -p 5432:5432 postgres:15 | Out-Null
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "PostgreSQL configurado" -ForegroundColor Green
} else {
    Write-Host "Erro ao configurar PostgreSQL" -ForegroundColor Red
}

# Configurar Redis
Write-Host "Configurando Redis..." -ForegroundColor Yellow
$redisExists = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq "auditoria-redis-local" }
if ($redisExists) {
    Write-Host "Container Redis ja existe, iniciando..." -ForegroundColor Yellow
    docker start auditoria-redis-local | Out-Null
} else {
    Write-Host "Criando container Redis..." -ForegroundColor Yellow
    docker run -d --name auditoria-redis-local --network auditoria-local-network -p 6379:6379 redis:7-alpine | Out-Null
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "Redis configurado" -ForegroundColor Green
} else {
    Write-Host "Erro ao configurar Redis" -ForegroundColor Red
}

# Configurar Ollama
Write-Host "Configurando Ollama..." -ForegroundColor Yellow
$ollamaExists = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq "auditoria-ollama-local" }
if ($ollamaExists) {
    Write-Host "Container Ollama ja existe, iniciando..." -ForegroundColor Yellow
    docker start auditoria-ollama-local | Out-Null
} else {
    Write-Host "Criando container Ollama..." -ForegroundColor Yellow
    docker run -d --name auditoria-ollama-local --network auditoria-local-network -p 11434:11434 ollama/ollama | Out-Null
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "Ollama configurado" -ForegroundColor Green
} else {
    Write-Host "Erro ao configurar Ollama" -ForegroundColor Red
}

Write-Host ""
Write-Host "Aguardando containers inicializarem..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "Status dos containers:" -ForegroundColor Cyan
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Where-Object { $_ -like "*auditoria*" }

Write-Host ""
Write-Host "=================================" -ForegroundColor Green
Write-Host "Docker configurado com sucesso!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""
Write-Host "Proximos passos:" -ForegroundColor Cyan
Write-Host "1. Execute: .\start_sistema_local.ps1" -ForegroundColor White
Write-Host "2. Ou inicie manualmente o backend e frontend" -ForegroundColor White
Write-Host ""
Write-Host "Containers rodando em:" -ForegroundColor Cyan
Write-Host "- PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host "- Redis: localhost:6379" -ForegroundColor White
Write-Host "- Ollama: localhost:11434" -ForegroundColor White
Write-Host ""
Write-Host "Sistema Docker pronto!" -ForegroundColor Green
