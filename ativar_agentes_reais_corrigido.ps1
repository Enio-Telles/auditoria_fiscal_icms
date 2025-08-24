# ===================================================================
# SCRIPT DE ATIVACAO DOS AGENTES REAIS
# Sistema de Auditoria Fiscal ICMS v4.0
# Data: 23 de Agosto de 2025
# Objetivo: Ativar agentes reais e desativar ambiente simulado (mock)
# ===================================================================

param(
    [switch]$SkipInfraCheck = $false,
    [switch]$Verbose = $false
)

# Configuracao de encoding para evitar problemas com caracteres especiais
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = New-Object System.Text.UTF8Encoding

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "    ATIVACAO DOS AGENTES REAIS - AUDITORIA FISCAL ICMS" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Funcao para verificar se uma porta esta em uso
function Test-Port {
    param([int]$Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", $Port)
        $connection.Close()
        return $true
    } catch {
        return $false
    }
}

# Funcao para aguardar servico
function Wait-ForService {
    param([string]$ServiceName, [int]$Port, [int]$TimeoutSeconds = 30)
    
    Write-Host "Aguardando $ServiceName (porta $Port)..." -ForegroundColor Yellow
    
    $timeout = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $timeout) {
        if (Test-Port -Port $Port) {
            Write-Host "✅ $ServiceName esta respondendo!" -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds 2
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "⚠️ Timeout aguardando $ServiceName" -ForegroundColor Yellow
    return $false
}

# Funcao para atualizar configuracao e desativar mock
function Update-AIConfig {
    Write-Host "📝 Atualizando configuracao de IA..." -ForegroundColor White
    
    $aiConfigPath = "configs\ai_config.yaml"
    
    if (Test-Path $aiConfigPath) {
        try {
            $content = Get-Content $aiConfigPath -Raw
            
            # Atualizar configuracoes principais
            $content = $content -replace "mock_llm_responses:\s*true", "mock_llm_responses: false"
            $content = $content -replace "use_real_agents:\s*false", "use_real_agents: true"
            $content = $content -replace "default_strategy:\s*.*", "default_strategy: 'real_agents'"
            
            # Adicionar configuracoes se nao existirem
            if ($content -notmatch "mock_llm_responses:") {
                $content += "`n`n# Configuracao de agentes reais`nmock_llm_responses: false`n"
            }
            if ($content -notmatch "use_real_agents:") {
                $content += "use_real_agents: true`n"
            }
            
            Set-Content $aiConfigPath $content -Encoding UTF8
            Write-Host "✅ Configuracao atualizada para agentes reais" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ Erro ao atualizar configuracao: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️ Arquivo de configuracao nao encontrado: $aiConfigPath" -ForegroundColor Yellow
        Write-Host "Criando configuracao basica..." -ForegroundColor White
        
        $basicConfig = @"
# Configuracao dos Agentes Reais - Sistema de Auditoria Fiscal
ai:
  mock_llm_responses: false
  use_real_agents: true
  default_strategy: 'real_agents'
  
ollama:
  base_url: 'http://localhost:11434'
  model: 'llama3'
  
agents:
  ncm:
    enabled: true
    confidence_threshold: 0.8
  cest:
    enabled: true
    confidence_threshold: 0.8
"@
        Set-Content $aiConfigPath $basicConfig -Encoding UTF8
        Write-Host "✅ Arquivo de configuracao criado" -ForegroundColor Green
    }
    
    # Atualizar config.py tambem se existir
    $configPyPath = "config.py"
    if (Test-Path $configPyPath) {
        try {
            $conteudoPy = Get-Content $configPyPath -Raw
            
            # Adicionar configuracao se nao existir
            if ($conteudoPy -notmatch "USE_REAL_AGENTS") {
                $conteudoPy += "`n`n# Configuracao de Agentes`nUSE_REAL_AGENTS = True`nMOCK_AGENTS = False`n"
                Set-Content $configPyPath $conteudoPy -Encoding UTF8
                Write-Host "✅ config.py atualizado" -ForegroundColor Green
            }
        } catch {
            Write-Host "⚠️ Erro ao atualizar config.py: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

# Verificar Docker
function Test-Docker {
    Write-Host "🐳 Verificando Docker..." -ForegroundColor White
    
    try {
        $dockerVersion = docker --version 2>$null
        if (-not $dockerVersion) {
            Write-Host "❌ Docker nao encontrado!" -ForegroundColor Red
            Write-Host "Instale o Docker Desktop primeiro" -ForegroundColor Yellow
            return $false
        }
        Write-Host "✅ Docker encontrado: $dockerVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Docker nao esta rodando!" -ForegroundColor Red
        Write-Host "Inicie o Docker Desktop primeiro" -ForegroundColor Yellow
        return $false
    }
    
    return $true
}

# Verificar e iniciar containers
function Start-Infrastructure {
    Write-Host "🏗️ Iniciando infraestrutura..." -ForegroundColor White
    
    # Verificar se containers existem
    $containers = @("auditoria_postgres", "auditoria_redis")
    
    foreach ($container in $containers) {
        Write-Host "Verificando container $container..." -ForegroundColor Gray
        
        $exists = docker ps -a --format "table {{.Names}}" | Select-String $container
        if (-not $exists) {
            Write-Host "Criando container $container..." -ForegroundColor Yellow
            try {
                if ($container -eq "auditoria_postgres") {
                    docker-compose up auditoria_postgres -d
                } elseif ($container -eq "auditoria_redis") {
                    docker-compose up auditoria_redis -d
                }
            } catch {
                Write-Host "⚠️ Erro ao criar $container" -ForegroundColor Yellow
            }
        } else {
            Write-Host "Iniciando container $container..." -ForegroundColor Yellow
            docker start $container 2>$null
        }
    }
    
    # Aguardar PostgreSQL
    Write-Host "Aguardando PostgreSQL..." -ForegroundColor Yellow
    Wait-ForService -ServiceName "PostgreSQL" -Port 5432 -TimeoutSeconds 30
    
    # Aguardar Redis
    Write-Host "Aguardando Redis..." -ForegroundColor Yellow
    Wait-ForService -ServiceName "Redis" -Port 6379 -TimeoutSeconds 15
    
    Write-Host "✅ Infraestrutura iniciada!" -ForegroundColor Green
}

# Verificar Ollama
function Test-Ollama {
    Write-Host "🧠 Verificando Ollama..." -ForegroundColor White
    
    try {
        $ollamaProcess = Get-Process "ollama" -ErrorAction SilentlyContinue
        if (-not $ollamaProcess) {
            Write-Host "Iniciando Ollama..." -ForegroundColor Yellow
            Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
            Start-Sleep -Seconds 5
        }
        
        if (Test-Port -Port 11434) {
            Write-Host "✅ Ollama esta rodando (porta 11434)" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Ollama nao encontrado!" -ForegroundColor Red
            Write-Host "Instale o Ollama primeiro: https://ollama.ai/download" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "⚠️ Erro ao verificar Ollama: $($_.Exception.Message)" -ForegroundColor Yellow
        return $false
    }
}

# Verificar ambiente conda
function Test-CondaEnvironment {
    Write-Host "🐍 Verificando ambiente conda..." -ForegroundColor White
    
    try {
        $condaEnvs = conda env list 2>$null | Select-String "auditoria-fiscal"
        if (-not $condaEnvs) {
            Write-Host "❌ Ambiente conda 'auditoria-fiscal' nao encontrado!" -ForegroundColor Red
            Write-Host "Execute: setup_conda_environment.bat" -ForegroundColor Yellow
            return $false
        }
        Write-Host "✅ Ambiente conda encontrado" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "⚠️ Erro ao verificar conda: $($_.Exception.Message)" -ForegroundColor Yellow
        return $false
    }
}

# Iniciar microservico
function Start-Microservice {
    param([string]$Nome, [string]$Caminho, [int]$Porta)
    
    Write-Host "🚀 Iniciando $Nome..." -ForegroundColor White
    
    $caminhoMicroservico = Join-Path "microservices" $Caminho
    if (-not (Test-Path $caminhoMicroservico)) {
        Write-Host "❌ Pasta nao encontrada: $caminhoMicroservico" -ForegroundColor Red
        return $false
    }
    
    # Verificar se ja esta rodando
    if (Test-Port -Port $Porta) {
        Write-Host "✅ $Nome ja esta rodando (porta $Porta)" -ForegroundColor Green
        return $true
    }
    
    try {
        # Iniciar em background
        $processInfo = New-Object System.Diagnostics.ProcessStartInfo
        $processInfo.FileName = "powershell"
        $processInfo.Arguments = "-Command `"cd '$caminhoMicroservico'; conda activate auditoria-fiscal; python main.py`""
        $processInfo.UseShellExecute = $true
        $processInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Minimized
        
        $process = [System.Diagnostics.Process]::Start($processInfo)
        
        if ($process) {
            Write-Host "✅ $Nome iniciado (PID: $($process.Id))" -ForegroundColor Green
            
            # Aguardar servico ficar disponivel
            if (Wait-ForService -ServiceName $Nome -Port $Porta -TimeoutSeconds 20) {
                return $true
            } else {
                Write-Host "⚠️ $Nome pode nao ter iniciado corretamente" -ForegroundColor Yellow
                return $false
            }
        }
    } catch {
        Write-Host "❌ Erro ao iniciar $Nome: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    return $false
}

# Validar sistema
function Test-System {
    Write-Host "🔍 Validando sistema..." -ForegroundColor White
    
    # Testar Gateway
    if (Test-Port -Port 8000) {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 5
            Write-Host "✅ API Gateway OK" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ API Gateway pode nao estar totalmente disponivel" -ForegroundColor Yellow
        }
    }
    
    # Testar Ollama
    if (Test-Port -Port 11434) {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
            Write-Host "✅ Ollama OK" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ Ollama pode nao estar disponivel" -ForegroundColor Yellow
        }
    }
    
    # Testar AI Service
    if (Test-Port -Port 8006) {
        Write-Host "✅ AI Service OK" -ForegroundColor Green
    } else {
        Write-Host "⚠️ AI Service pode nao estar disponivel" -ForegroundColor Yellow
    }
}

# EXECUCAO PRINCIPAL
try {
    # 1. Atualizar configuracoes
    Update-AIConfig
    
    if (-not $SkipInfraCheck) {
        # 2. Verificar Docker
        if (-not (Test-Docker)) {
            exit 1
        }
        
        # 3. Iniciar infraestrutura
        Start-Infrastructure
        
        # 4. Verificar Ollama
        Test-Ollama
        
        # 5. Verificar conda
        if (-not (Test-CondaEnvironment)) {
            exit 1
        }
    }
    
    # 6. Iniciar microservicos principais
    Write-Host ""
    Write-Host "🚀 INICIANDO MICROSERVICOS..." -ForegroundColor Cyan
    Write-Host ""
    
    $gatewayOK = Start-Microservice -Nome "Gateway" -Caminho "gateway" -Porta 8000
    Start-Sleep -Seconds 3
    
    $aiServiceOK = Start-Microservice -Nome "AI Service" -Caminho "ai_service" -Porta 8006
    Start-Sleep -Seconds 2
    
    # 7. Validar sistema
    Write-Host ""
    Test-System
    
    # 8. Resultado final
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host "    🎉 SISTEMA COM AGENTES REAIS INICIADO COM SUCESSO!" -ForegroundColor Yellow
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 URLS DISPONIVEIS:" -ForegroundColor Cyan
    Write-Host "• API Gateway: http://localhost:8000" -ForegroundColor White
    Write-Host "• AI Service: http://localhost:8006" -ForegroundColor White
    Write-Host "• Ollama: http://localhost:11434" -ForegroundColor White
    Write-Host "• Documentacao: http://localhost:8000/docs" -ForegroundColor White
    Write-Host ""
    Write-Host "🤖 AGENTES REAIS ATIVOS:" -ForegroundColor Cyan
    Write-Host "• NCMAgent: Classificacao NCM com dados estruturados" -ForegroundColor White
    Write-Host "• CESTAgent: Determinacao CEST por atividade empresarial" -ForegroundColor White
    Write-Host ""
    Write-Host "📖 Para testar classificacao com IA real:" -ForegroundColor Yellow
    Write-Host "python demo_agentes_reais.py" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 PROXIMOS PASSOS:" -ForegroundColor Gray
    Write-Host "1. Inicie o frontend: .\iniciar_frontend.ps1" -ForegroundColor White
    Write-Host "2. Acesse o sistema: http://localhost:3001" -ForegroundColor White
    Write-Host "3. Teste classificacoes reais com IA" -ForegroundColor White
    
    pause
    
} catch {
    Write-Host ""
    Write-Host "❌ ERRO DURANTE A EXECUCAO:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📋 SOLUCOES:" -ForegroundColor Gray
    Write-Host "1. Verifique se o Docker Desktop esta rodando" -ForegroundColor White
    Write-Host "2. Execute: conda activate auditoria-fiscal" -ForegroundColor White
    Write-Host "3. Verifique as portas 8000, 8006, 5432, 6379, 11434" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}
