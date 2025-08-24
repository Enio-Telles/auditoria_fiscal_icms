# Verificação Rápida de Status - Sistema de Auditoria Fiscal
# Script para verificar rapidamente se tudo está funcionando

Write-Host "⚡ VERIFICAÇÃO RÁPIDA DE STATUS" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green
Write-Host ""

# Função para verificar se uma porta está em uso
function Test-Port {
    param($porta)
    $conexao = netstat -an | findstr ":$porta "
    return $conexao -ne $null
}

# Função para verificar se um processo está rodando
function Test-Process {
    param($nomeProcesso)
    $processo = Get-Process -Name $nomeProcesso -ErrorAction SilentlyContinue
    return $processo -ne $null
}

# 1. Verificar Docker
Write-Host "🐳 DOCKER:" -ForegroundColor Cyan
if (Get-Command docker -ErrorAction SilentlyContinue) {
    try {
        docker version | Out-Null
        Write-Host "  ✅ Docker funcionando" -ForegroundColor Green

        # Verificar containers específicos
        $pgContainer = docker ps --filter "name=auditoria_postgres" --format "{{.Status}}"
        $redisContainer = docker ps --filter "name=auditoria_redis" --format "{{.Status}}"

        if ($pgContainer) {
            Write-Host "  ✅ PostgreSQL: $pgContainer" -ForegroundColor Green
        } else {
            Write-Host "  ❌ PostgreSQL: Container não encontrado" -ForegroundColor Red
        }

        if ($redisContainer) {
            Write-Host "  ✅ Redis: $redisContainer" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Redis: Container não encontrado" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ Docker não está funcionando" -ForegroundColor Red
    }
} else {
    Write-Host "  ❌ Docker não encontrado" -ForegroundColor Red
}

Write-Host ""

# 2. Verificar Python/Conda
Write-Host "🐍 PYTHON/CONDA:" -ForegroundColor Cyan
if (Get-Command conda -ErrorAction SilentlyContinue) {
    Write-Host "  ✅ Anaconda disponível" -ForegroundColor Green
    try {
        $envs = conda env list | findstr auditoria-fiscal
        if ($envs) {
            Write-Host "  ✅ Ambiente auditoria-fiscal criado" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️ Ambiente auditoria-fiscal não encontrado" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ⚠️ Erro ao verificar ambientes" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ❌ Anaconda não encontrado" -ForegroundColor Red
}

Write-Host ""

# 3. Verificar Node.js
Write-Host "🟢 NODE.JS:" -ForegroundColor Cyan
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVersion = node --version
    Write-Host "  ✅ Node.js $nodeVersion" -ForegroundColor Green

    if (Test-Path "frontend\package.json") {
        Write-Host "  ✅ Frontend configurado" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ Frontend não encontrado" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ❌ Node.js não encontrado" -ForegroundColor Red
}

Write-Host ""

# 4. Verificar Ollama
Write-Host "🤖 OLLAMA IA:" -ForegroundColor Cyan
if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Write-Host "  ✅ Ollama instalado" -ForegroundColor Green

    # Verificar se está rodando
    if (Test-Port 11434) {
        Write-Host "  ✅ Ollama rodando (porta 11434)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ Ollama não está rodando" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ❌ Ollama não encontrado" -ForegroundColor Red
}

Write-Host ""

# 5. Verificar portas dos serviços
Write-Host "🌐 PORTAS DOS SERVIÇOS:" -ForegroundColor Cyan

$servicos = @(
    @{porta=3001; nome="Frontend (React)"; obrigatorio=$false},
    @{porta=8000; nome="Backend (API)"; obrigatorio=$true},
    @{porta=5432; nome="PostgreSQL"; obrigatorio=$true},
    @{porta=6379; nome="Redis"; obrigatorio=$true},
    @{porta=11434; nome="Ollama IA"; obrigatorio=$true}
)

foreach ($servico in $servicos) {
    if (Test-Port $servico.porta) {
        Write-Host "  ✅ $($servico.nome): Ativo" -ForegroundColor Green
    } else {
        if ($servico.obrigatorio) {
            Write-Host "  ❌ $($servico.nome): Inativo" -ForegroundColor Red
        } else {
            Write-Host "  ⚠️ $($servico.nome): Inativo" -ForegroundColor Yellow
        }
    }
}

Write-Host ""

# 6. Verificar arquivos essenciais
Write-Host "📁 ARQUIVOS ESSENCIAIS:" -ForegroundColor Cyan

$arquivos = @(
    "config.py",
    "requirements.txt",
    "microservices\gateway\main.py",
    "microservices\auth-service\main.py",
    "frontend\package.json",
    "MANUAL_USUARIO_FINAL.md"
)

foreach ($arquivo in $arquivos) {
    if (Test-Path $arquivo) {
        Write-Host "  ✅ $arquivo" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $arquivo: Não encontrado" -ForegroundColor Red
    }
}

Write-Host ""

# 7. Status geral
Write-Host "📊 STATUS GERAL:" -ForegroundColor Cyan

$problemas = 0

# Contar problemas críticos
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { $problemas++ }
if (-not (Test-Port 5432)) { $problemas++ }
if (-not (Test-Port 6379)) { $problemas++ }
if (-not (Test-Port 11434)) { $problemas++ }

if ($problemas -eq 0) {
    Write-Host "  ✅ SISTEMA OPERACIONAL!" -ForegroundColor Green
    Write-Host "  🎉 Todos os serviços essenciais estão funcionando" -ForegroundColor Green
} elseif ($problemas -le 2) {
    Write-Host "  ⚠️ SISTEMA COM PROBLEMAS MENORES" -ForegroundColor Yellow
    Write-Host "  💡 Alguns serviços precisam ser iniciados" -ForegroundColor Yellow
} else {
    Write-Host "  ❌ SISTEMA COM PROBLEMAS GRAVES" -ForegroundColor Red
    Write-Host "  🔧 Vários serviços precisam ser configurados" -ForegroundColor Red
}

Write-Host ""

# 8. Ações recomendadas
Write-Host "💡 AÇÕES RECOMENDADAS:" -ForegroundColor Cyan

if (-not (Test-Port 5432) -or -not (Test-Port 6379)) {
    Write-Host "  • Execute: .\iniciar_banco_dados.ps1" -ForegroundColor Yellow
}

if (-not (Test-Port 11434)) {
    Write-Host "  • Execute: ollama serve" -ForegroundColor Yellow
}

if (-not (Test-Port 8000)) {
    Write-Host "  • Execute: .\iniciar_backend.ps1" -ForegroundColor Yellow
}

if (-not (Test-Port 3001)) {
    Write-Host "  • Execute: .\iniciar_frontend.ps1" -ForegroundColor Yellow
}

Write-Host ""

# 9. Links úteis
Write-Host "🔗 LINKS RÁPIDOS:" -ForegroundColor Cyan
Write-Host "  • Frontend: http://localhost:3001" -ForegroundColor White
Write-Host "  • Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  • Documentação API: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • Status Ollama: http://localhost:11434" -ForegroundColor White

Write-Host ""
Write-Host "⏱️ Verificação concluída em $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Gray
Write-Host "📖 Para mais detalhes, consulte: MANUAL_USUARIO_FINAL.md" -ForegroundColor Gray
Write-Host ""

# Manter a janela aberta por alguns segundos para o usuário ler
Start-Sleep -Seconds 3
