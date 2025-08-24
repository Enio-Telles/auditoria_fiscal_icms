# 🩺 DIAGNÓSTICO E INICIALIZAÇÃO DOCKER - WINDOWS 11
# Sistema de Auditoria Fiscal ICMS v4.0

Write-Host "🩺 DIAGNÓSTICO DOCKER WINDOWS 11..." -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

# Função para verificar se processo está rodando
function Test-ProcessRunning($processName) {
    return (Get-Process -Name $processName -ErrorAction SilentlyContinue) -ne $null
}

# Função para aguardar Docker ficar pronto
function Wait-DockerReady {
    param([int]$MaxWaitSeconds = 120)
    
    $elapsed = 0
    $interval = 5
    
    Write-Host "⏳ Aguardando Docker ficar pronto..." -ForegroundColor Yellow
    
    while ($elapsed -lt $MaxWaitSeconds) {
        try {
            docker info | Out-Null
            Write-Host "✅ Docker está pronto!" -ForegroundColor Green
            return $true
        } catch {
            Write-Host "   Aguardando... ($elapsed/$MaxWaitSeconds segundos)" -ForegroundColor Gray
            Start-Sleep -Seconds $interval
            $elapsed += $interval
        }
    }
    
    Write-Host "❌ Docker não ficou pronto em $MaxWaitSeconds segundos" -ForegroundColor Red
    return $false
}

Write-Host "🔍 1. VERIFICANDO STATUS DO DOCKER..." -ForegroundColor Cyan
Write-Host "-------------------------------------"

# Verificar se Docker Desktop está instalado
$dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
if (Test-Path $dockerPath) {
    Write-Host "✅ Docker Desktop instalado" -ForegroundColor Green
    Write-Host "   Localização: $dockerPath" -ForegroundColor Gray
} else {
    Write-Host "❌ Docker Desktop não encontrado!" -ForegroundColor Red
    Write-Host "   📥 Baixe em: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    Write-Host "   Instale e reinicie este script" -ForegroundColor Yellow
    exit 1
}

# Verificar se Docker Desktop está rodando
$dockerDesktopRunning = Test-ProcessRunning "Docker Desktop"
$dockerServiceRunning = Test-ProcessRunning "com.docker.service"

Write-Host ""
Write-Host "📊 STATUS DOS PROCESSOS:" -ForegroundColor Cyan
if ($dockerDesktopRunning) {
    Write-Host "✅ Docker Desktop (Interface) - Rodando" -ForegroundColor Green
} else {
    Write-Host "❌ Docker Desktop (Interface) - Parado" -ForegroundColor Red
}

if ($dockerServiceRunning) {
    Write-Host "✅ Docker Service (Motor) - Rodando" -ForegroundColor Green
} else {
    Write-Host "❌ Docker Service (Motor) - Parado" -ForegroundColor Red
}

# Verificar conectividade Docker
Write-Host ""
Write-Host "🔌 TESTANDO CONECTIVIDADE..." -ForegroundColor Cyan
try {
    docker info | Out-Null
    Write-Host "✅ Docker respondendo aos comandos" -ForegroundColor Green
    $dockerReady = $true
} catch {
    Write-Host "❌ Docker não está respondendo" -ForegroundColor Red
    $dockerReady = $false
}

Write-Host ""
Write-Host "🚀 2. INICIANDO DOCKER SE NECESSÁRIO..." -ForegroundColor Cyan
Write-Host "----------------------------------------"

if (-not $dockerReady) {
    if (-not $dockerDesktopRunning) {
        Write-Host "🔄 Iniciando Docker Desktop..." -ForegroundColor Yellow
        
        try {
            Start-Process -FilePath $dockerPath -WindowStyle Minimized
            Write-Host "✅ Docker Desktop iniciado" -ForegroundColor Green
            
            # Aguardar Docker ficar pronto
            if (Wait-DockerReady -MaxWaitSeconds 120) {
                $dockerReady = $true
            }
        } catch {
            Write-Host "❌ Erro ao iniciar Docker Desktop: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "⚠️  Docker Desktop está rodando mas não responde" -ForegroundColor Yellow
        Write-Host "   Pode estar inicializando ainda..." -ForegroundColor Yellow
        
        if (Wait-DockerReady -MaxWaitSeconds 60) {
            $dockerReady = $true
        }
    }
}

if (-not $dockerReady) {
    Write-Host ""
    Write-Host "❌ DOCKER NÃO ESTÁ FUNCIONANDO!" -ForegroundColor Red
    Write-Host "================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 SOLUÇÕES MANUAIS:" -ForegroundColor Yellow
    Write-Host "1. Feche Docker Desktop completamente" -ForegroundColor White
    Write-Host "2. Reinicie como Administrador" -ForegroundColor White
    Write-Host "3. Verifique WSL2 está habilitado:" -ForegroundColor White
    Write-Host "   wsl --install" -ForegroundColor Gray
    Write-Host "   wsl --set-default-version 2" -ForegroundColor Gray
    Write-Host "4. Reinicie o Windows" -ForegroundColor White
    Write-Host ""
    Write-Host "📞 TROUBLESHOOTING ADICIONAL:" -ForegroundColor Yellow
    Write-Host "• Verifique se Hyper-V está habilitado" -ForegroundColor White
    Write-Host "• Verifique se virtualização está habilitada na BIOS" -ForegroundColor White
    Write-Host "• Tente executar como Administrador" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "🐳 3. CONFIGURANDO CONTAINERS LOCAIS..." -ForegroundColor Cyan
Write-Host "---------------------------------------"

# Criar network se não existir
try {
    docker network inspect auditoria-local-network | Out-Null
    Write-Host "✅ Network 'auditoria-local-network' já existe" -ForegroundColor Green
} catch {
    Write-Host "🔄 Criando network 'auditoria-local-network'..." -ForegroundColor Yellow
    docker network create auditoria-local-network
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Network criada com sucesso" -ForegroundColor Green
    } else {
        Write-Host "❌ Erro ao criar network" -ForegroundColor Red
    }
}

# Verificar/iniciar containers essenciais
$containers = @(
    @{
        Name = "auditoria-postgres-local"
        Image = "postgres:15"
        Port = "5432:5432"
        Env = @(
            "POSTGRES_DB=auditoria_fiscal_local",
            "POSTGRES_USER=auditoria_user", 
            "POSTGRES_PASSWORD=auditoria123"
        )
        Volume = "${PWD}\data\postgres:/var/lib/postgresql/data"
    },
    @{
        Name = "auditoria-redis-local"
        Image = "redis:7-alpine"
        Port = "6379:6379"
        Env = @()
        Volume = ""
    },
    @{
        Name = "auditoria-ollama-local"
        Image = "ollama/ollama"
        Port = "11434:11434"
        Env = @()
        Volume = "${PWD}\data\ollama:/root/.ollama"
    }
)

foreach ($container in $containers) {
    Write-Host ""
    Write-Host "🐳 Configurando $($container.Name)..." -ForegroundColor Yellow
    
    # Verificar se container existe
    $existingContainer = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq $container.Name }
    
    if ($existingContainer) {
        # Container existe, verificar status
        $status = docker inspect --format='{{.State.Status}}' $container.Name
        
        if ($status -eq "running") {
            Write-Host "✅ $($container.Name) já está rodando" -ForegroundColor Green
        } elseif ($status -eq "exited") {
            Write-Host "🔄 Iniciando $($container.Name)..." -ForegroundColor Yellow
            docker start $container.Name | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ $($container.Name) iniciado" -ForegroundColor Green
            } else {
                Write-Host "❌ Erro ao iniciar $($container.Name)" -ForegroundColor Red
            }
        } else {
            Write-Host "⚠️  $($container.Name) em status: $status" -ForegroundColor Yellow
        }
    } else {
        # Container não existe, criar
        Write-Host "🔄 Criando $($container.Name)..." -ForegroundColor Yellow
        
        # Construir comando docker run
        $cmd = @("docker", "run", "-d", "--name", $container.Name, "--network", "auditoria-local-network", "-p", $container.Port)
        
        # Adicionar variáveis de ambiente
        foreach ($env in $container.Env) {
            $cmd += @("-e", $env)
        }
        
        # Adicionar volume se especificado
        if ($container.Volume) {
            $cmd += @("-v", $container.Volume)
        }
        
        # Adicionar imagem
        $cmd += $container.Image
        
        # Executar comando
        & $cmd[0] $cmd[1..($cmd.Length-1)] | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $($container.Name) criado e iniciado" -ForegroundColor Green
        } else {
            Write-Host "❌ Erro ao criar $($container.Name)" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "⏳ 4. AGUARDANDO CONTAINERS INICIALIZAREM..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"
Start-Sleep -Seconds 15

# Verificar saúde dos containers
Write-Host ""
Write-Host "🩺 5. VERIFICANDO SAÚDE DOS CONTAINERS..." -ForegroundColor Cyan
Write-Host "-----------------------------------------"

# PostgreSQL
try {
    docker exec auditoria-postgres-local pg_isready -U auditoria_user | Out-Null
    Write-Host "✅ PostgreSQL está aceitando conexões" -ForegroundColor Green
} catch {
    Write-Host "⚠️  PostgreSQL ainda inicializando..." -ForegroundColor Yellow
}

# Redis
try {
    $redisResponse = docker exec auditoria-redis-local redis-cli ping
    if ($redisResponse -eq "PONG") {
        Write-Host "✅ Redis está respondendo" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Redis ainda inicializando..." -ForegroundColor Yellow
}

# Ollama
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/version" -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response) {
        Write-Host "✅ Ollama está respondendo" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Ollama ainda inicializando..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📊 STATUS FINAL DOS CONTAINERS:" -ForegroundColor Cyan
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Where-Object { $_ -like "*auditoria*" }

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "🎉 DOCKER CONFIGURADO COM SUCESSO!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "✅ PRÓXIMOS PASSOS:" -ForegroundColor Cyan
Write-Host "1. Execute: .\start_sistema_local.ps1" -ForegroundColor White
Write-Host "2. Ou inicie manualmente:" -ForegroundColor White
Write-Host "   • Backend: cd microservices\api_gateway && python main.py" -ForegroundColor Gray
Write-Host "   • Frontend: cd frontend && npm start" -ForegroundColor Gray
Write-Host ""
Write-Host "🌐 CONTAINERS RODANDO EM:" -ForegroundColor Cyan
Write-Host "• PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host "• Redis: localhost:6379" -ForegroundColor White
Write-Host "• Ollama: localhost:11434" -ForegroundColor White
Write-Host ""
Write-Host "🎊 Sistema Docker pronto para o Windows 11!" -ForegroundColor Green
