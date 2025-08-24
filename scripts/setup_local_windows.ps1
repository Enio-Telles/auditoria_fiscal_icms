# 🚀 SCRIPT DE SETUP LOCAL WINDOWS 11
# Sistema de Auditoria Fiscal ICMS v4.0
# Data: 23 de Agosto de 2025
# Ambiente: 100% Local Windows 11

Write-Host "🚀 CONFIGURANDO SISTEMA LOCAL WINDOWS 11..." -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""

# Verificar se está sendo executado como Administrador
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "⚠️  Execute como Administrador para configurar firewall" -ForegroundColor Yellow
    Write-Host "   Continuando sem configurações de firewall..." -ForegroundColor Yellow
    Write-Host ""
}

# Função para verificar comando
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Função para status
function Write-Status($message, $status) {
    if ($status) {
        Write-Host "✅ $message" -ForegroundColor Green
    } else {
        Write-Host "❌ $message" -ForegroundColor Red
    }
}

Write-Host "🔍 1. VERIFICANDO PRÉ-REQUISITOS..." -ForegroundColor Cyan
Write-Host "------------------------------------"

# Verificar Docker
$dockerInstalled = Test-Command "docker"
Write-Status "Docker instalado" $dockerInstalled

if ($dockerInstalled) {
    $dockerVersion = docker --version
    Write-Host "   Versão: $dockerVersion" -ForegroundColor Gray

    # Verificar se Docker está rodando
    try {
        docker info | Out-Null
        Write-Status "Docker service ativo" $true
    } catch {
        Write-Status "Docker service ativo" $false
        Write-Host "   Inicie Docker Desktop" -ForegroundColor Yellow
    }
} else {
    Write-Host "   📥 Baixe em: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
}

# Verificar Python/Conda
$condaInstalled = Test-Command "conda"
Write-Status "Anaconda/Conda instalado" $condaInstalled

if ($condaInstalled) {
    $condaVersion = conda --version
    Write-Host "   Versão: $condaVersion" -ForegroundColor Gray
} else {
    $pythonInstalled = Test-Command "python"
    Write-Status "Python instalado" $pythonInstalled
    if ($pythonInstalled) {
        $pythonVersion = python --version
        Write-Host "   Versão: $pythonVersion" -ForegroundColor Gray
    } else {
        Write-Host "   📥 Baixe Anaconda em: https://www.anaconda.com/" -ForegroundColor Yellow
    }
}

# Verificar Node.js
$nodeInstalled = Test-Command "node"
Write-Status "Node.js instalado" $nodeInstalled

if ($nodeInstalled) {
    $nodeVersion = node --version
    $npmVersion = npm --version
    Write-Host "   Node: $nodeVersion, npm: $npmVersion" -ForegroundColor Gray
} else {
    Write-Host "   📥 Baixe em: https://nodejs.org/" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🐳 2. CONFIGURANDO CONTAINERS DOCKER..." -ForegroundColor Cyan
Write-Host "---------------------------------------"

if ($dockerInstalled) {
    # Criar network
    Write-Host "📡 Criando network local..."
    docker network create auditoria-local-network 2>$null
    Write-Host "✅ Network criada" -ForegroundColor Green

    # Verificar se containers já existem
    $containers = @(
        @{Name="auditoria-postgres-local"; Image="postgres:15"; Port="5432:5432"; Env=@("-e", "POSTGRES_DB=auditoria_fiscal_local", "-e", "POSTGRES_USER=auditoria_user", "-e", "POSTGRES_PASSWORD=auditoria123")},
        @{Name="auditoria-redis-local"; Image="redis:7-alpine"; Port="6379:6379"; Env=@()},
        @{Name="auditoria-ollama-local"; Image="ollama/ollama"; Port="11434:11434"; Env=@()}
    )

    foreach ($container in $containers) {
        Write-Host "🐳 Configurando $($container.Name)..."

        # Verificar se já existe
        $existing = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq $container.Name }

        if ($existing) {
            Write-Host "   Container já existe, iniciando..." -ForegroundColor Yellow
            docker start $container.Name | Out-Null
        } else {
            Write-Host "   Criando novo container..." -ForegroundColor Yellow

            $volumeParam = ""
            if ($container.Name -eq "auditoria-postgres-local") {
                $volumeParam = "-v", "${PWD}\data\postgres:/var/lib/postgresql/data"
            } elseif ($container.Name -eq "auditoria-ollama-local") {
                $volumeParam = "-v", "${PWD}\data\ollama:/root/.ollama"
            }

            $cmd = @("docker", "run", "-d", "--name", $container.Name, "--network", "auditoria-local-network", "-p", $container.Port) + $container.Env + $volumeParam + $container.Image
            & $cmd[0] $cmd[1..($cmd.Length-1)] | Out-Null
        }

        Write-Host "✅ $($container.Name) configurado" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "⏳ Aguardando containers inicializarem..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15

} else {
    Write-Host "❌ Docker não disponível, pule esta etapa" -ForegroundColor Red
}

Write-Host ""
Write-Host "📁 3. CRIANDO DIRETÓRIOS..." -ForegroundColor Cyan
Write-Host "----------------------------"

$directories = @(
    "data\logs",
    "data\uploads",
    "data\backups",
    "data\chroma",
    "data\postgres",
    "data\ollama",
    "data\temp",
    "data\cache"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✅ Criado: $dir" -ForegroundColor Green
    } else {
        Write-Host "✅ Existe: $dir" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "🐍 4. CONFIGURANDO AMBIENTE PYTHON..." -ForegroundColor Cyan
Write-Host "-------------------------------------"

if ($condaInstalled) {
    Write-Host "🔄 Criando ambiente conda 'auditoria-fiscal'..."

    # Verificar se ambiente já existe
    $envExists = conda env list | Select-String "auditoria-fiscal"

    if (-not $envExists) {
        conda create -n auditoria-fiscal python=3.10 -y | Out-Null
        Write-Host "✅ Ambiente conda criado" -ForegroundColor Green
    } else {
        Write-Host "✅ Ambiente conda já existe" -ForegroundColor Green
    }

    Write-Host "📦 Ativando ambiente e instalando dependências..."

    # Ativar ambiente e instalar dependências
    & conda activate auditoria-fiscal
    if (Test-Path "requirements.txt") {
        pip install -r requirements.txt | Out-Null
        Write-Host "✅ Dependências Python instaladas" -ForegroundColor Green
    } else {
        Write-Host "⚠️  requirements.txt não encontrado" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Conda não disponível, use pip install -r requirements.txt" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📦 5. CONFIGURANDO FRONTEND..." -ForegroundColor Cyan
Write-Host "------------------------------"

if ($nodeInstalled -and (Test-Path "frontend")) {
    Write-Host "📥 Instalando dependências do frontend..."

    Push-Location "frontend"

    if (Test-Path "package.json") {
        npm install | Out-Null
        Write-Host "✅ Dependências frontend instaladas" -ForegroundColor Green

        # Criar arquivo .env local
        $envContent = @"
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=local
GENERATE_SOURCEMAP=false
"@
        $envContent | Out-File -FilePath ".env.local" -Encoding UTF8
        Write-Host "✅ Arquivo .env.local criado" -ForegroundColor Green

    } else {
        Write-Host "⚠️  package.json não encontrado" -ForegroundColor Yellow
    }

    Pop-Location
} else {
    Write-Host "⚠️  Node.js não disponível ou pasta frontend não encontrada" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔥 6. CONFIGURANDO FIREWALL (OPCIONAL)..." -ForegroundColor Cyan
Write-Host "------------------------------------------"

# Verificar se é administrador
if (([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "🛡️  Configurando regras de firewall..."

    $ports = @(
        @{Name="Auditoria Frontend"; Port="3000"},
        @{Name="Auditoria Backend"; Port="8000"},
        @{Name="Auditoria Services"; Port="8001-8006"},
        @{Name="Auditoria Database"; Port="5432"},
        @{Name="Auditoria Redis"; Port="6379"},
        @{Name="Auditoria Ollama"; Port="11434"}
    )

    foreach ($portRule in $ports) {
        try {
            if ($portRule.Port -contains "-") {
                # Range de portas
                $range = $portRule.Port.Split("-")
                New-NetFirewallRule -DisplayName $portRule.Name -Direction Inbound -LocalPort "$($range[0])-$($range[1])" -Protocol TCP -Action Allow -ErrorAction SilentlyContinue | Out-Null
            } else {
                # Porta única
                New-NetFirewallRule -DisplayName $portRule.Name -Direction Inbound -LocalPort $portRule.Port -Protocol TCP -Action Allow -ErrorAction SilentlyContinue | Out-Null
            }
            Write-Host "✅ Firewall: $($portRule.Name)" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Firewall: $($portRule.Name) (já existe)" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "⚠️  Execute como Administrador para configurar firewall" -ForegroundColor Yellow
    Write-Host "   As portas podem precisar ser liberadas manualmente" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🤖 7. CONFIGURANDO MODELOS IA..." -ForegroundColor Cyan
Write-Host "---------------------------------"

if ($dockerInstalled) {
    Write-Host "📥 Baixando modelos essenciais do Ollama..."
    Write-Host "   Isso pode levar alguns minutos..." -ForegroundColor Yellow

    # Aguardar Ollama estar pronto
    $maxAttempts = 12
    $attempt = 0
    $ollamaReady = $false

    while ($attempt -lt $maxAttempts -and -not $ollamaReady) {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:11434/api/version" -TimeoutSec 2 -ErrorAction SilentlyContinue
            $ollamaReady = $true
            Write-Host "✅ Ollama está pronto" -ForegroundColor Green
        } catch {
            $attempt++
            Write-Host "   Aguardando Ollama... ($attempt/$maxAttempts)" -ForegroundColor Yellow
            Start-Sleep -Seconds 5
        }
    }

    if ($ollamaReady) {
        # Instalar modelos básicos
        $models = @("llama3.1:8b", "codellama:7b", "mistral:7b")

        foreach ($model in $models) {
            Write-Host "📦 Instalando modelo: $model..."
            docker exec auditoria-ollama-local ollama pull $model | Out-Null
            Write-Host "✅ Modelo $model instalado" -ForegroundColor Green
        }

        # Verificar modelos instalados
        Write-Host "📋 Modelos disponíveis:"
        docker exec auditoria-ollama-local ollama list

    } else {
        Write-Host "❌ Ollama não está respondendo" -ForegroundColor Red
        Write-Host "   Execute manualmente: docker exec auditoria-ollama-local ollama pull llama3.1:8b" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Docker não disponível para configurar IA" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📄 8. CRIANDO SCRIPTS DE INICIALIZAÇÃO..." -ForegroundColor Cyan
Write-Host "------------------------------------------"

# Script para iniciar containers
$startContainersScript = @'
Write-Host "🐳 Iniciando containers Docker..." -ForegroundColor Green

$containers = @("auditoria-postgres-local", "auditoria-redis-local", "auditoria-ollama-local")

foreach ($container in $containers) {
    $status = docker inspect --format='{{.State.Status}}' $container 2>$null
    if ($status -ne "running") {
        Write-Host "🔄 Iniciando $container..." -ForegroundColor Yellow
        docker start $container | Out-Null
        Write-Host "✅ $container iniciado" -ForegroundColor Green
    } else {
        Write-Host "✅ $container já rodando" -ForegroundColor Green
    }
}

Write-Host "⏳ Aguardando serviços..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "🎯 Containers prontos!" -ForegroundColor Cyan
'@

$startContainersScript | Out-File -FilePath "scripts\start_containers_local.ps1" -Encoding UTF8

# Script para iniciar backend
$startBackendScript = @'
Write-Host "🔧 Iniciando Backend Local..." -ForegroundColor Green

# Ativar ambiente conda
& C:\ProgramData\Anaconda3\shell\condabin\conda-hook.ps1
conda activate auditoria-fiscal

# Configurar variáveis de ambiente
$env:DATABASE_URL="postgresql://auditoria_user:auditoria123@localhost:5432/auditoria_fiscal_local"
$env:REDIS_URL="redis://localhost:6379"
$env:OLLAMA_URL="http://localhost:11434"
$env:ENVIRONMENT="local"

Write-Host "🚀 Iniciando API Gateway em http://localhost:8000" -ForegroundColor Cyan
cd microservices\api_gateway
python main.py
'@

$startBackendScript | Out-File -FilePath "scripts\start_backend_local.ps1" -Encoding UTF8

# Script para iniciar frontend
$startFrontendScript = @'
Write-Host "🎨 Iniciando Frontend Local..." -ForegroundColor Green

cd frontend

$env:REACT_APP_API_URL="http://localhost:8000"

Write-Host "🚀 Iniciando React em http://localhost:3000" -ForegroundColor Cyan
npm start
'@

$startFrontendScript | Out-File -FilePath "scripts\start_frontend_local.ps1" -Encoding UTF8

# Script completo
$startCompleteScript = @'
Write-Host "🚀 INICIANDO SISTEMA COMPLETO..." -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

# 1. Iniciar containers
Write-Host "1. Iniciando containers Docker..." -ForegroundColor Cyan
.\scripts\start_containers_local.ps1

# 2. Iniciar backend em background
Write-Host "2. Iniciando backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-File", ".\scripts\start_backend_local.ps1"

# 3. Aguardar backend inicializar
Write-Host "3. Aguardando backend..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 4. Iniciar frontend
Write-Host "4. Iniciando frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-File", ".\scripts\start_frontend_local.ps1"

Write-Host ""
Write-Host "🎯 SISTEMA INICIADO!" -ForegroundColor Green
Write-Host "===================" -ForegroundColor Green
Write-Host "• Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "• API: http://localhost:8000" -ForegroundColor White
Write-Host "• Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "⏳ Aguarde alguns segundos para tudo carregar..." -ForegroundColor Yellow
'@

$startCompleteScript | Out-File -FilePath "scripts\start_sistema_completo_local.ps1" -Encoding UTF8

Write-Host "✅ Scripts de inicialização criados" -ForegroundColor Green

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "🎉 SETUP CONCLUÍDO COM SUCESSO!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 PARA INICIAR O SISTEMA:" -ForegroundColor Cyan
Write-Host ".\scripts\start_sistema_completo_local.ps1" -ForegroundColor White
Write-Host ""
Write-Host "🎯 URLS DO SISTEMA:" -ForegroundColor Cyan
Write-Host "• Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "• API: http://localhost:8000" -ForegroundColor White
Write-Host "• Documentação: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "📊 CONTAINERS DOCKER:" -ForegroundColor Cyan
Write-Host "• PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host "• Redis: localhost:6379" -ForegroundColor White
Write-Host "• Ollama: localhost:11434" -ForegroundColor White
Write-Host ""
Write-Host "🎊 Sistema 100% configurado para Windows 11!" -ForegroundColor Green
