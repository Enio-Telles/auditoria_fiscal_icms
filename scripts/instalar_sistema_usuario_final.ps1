# Script de Instalação Automática para Usuário Final
# Sistema de Auditoria Fiscal ICMS v4.0

Write-Host "🚀 INSTALAÇÃO AUTOMÁTICA - SISTEMA DE AUDITORIA FISCAL" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green
Write-Host ""

# Verificar se está executando como administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "❌ ERRO: Execute como Administrador!" -ForegroundColor Red
    Write-Host "Clique com botão direito no PowerShell e escolha 'Executar como Administrador'" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "✅ Executando como Administrador" -ForegroundColor Green
Write-Host ""

# Etapa 1: Verificar programas necessários
Write-Host "🔍 ETAPA 1: Verificando programas necessários..." -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Verificar Docker
$dockerExists = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerExists) {
    Write-Host "✅ Docker encontrado" -ForegroundColor Green
} else {
    Write-Host "❌ Docker não encontrado!" -ForegroundColor Red
    Write-Host "📥 Baixe em: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    Write-Host "❗ Instale o Docker e execute este script novamente" -ForegroundColor Yellow
    pause
    exit 1
}

# Verificar Python/Conda
$condaExists = Get-Command conda -ErrorAction SilentlyContinue
if ($condaExists) {
    Write-Host "✅ Anaconda/Python encontrado" -ForegroundColor Green
} else {
    Write-Host "❌ Anaconda não encontrado!" -ForegroundColor Red
    Write-Host "📥 Baixe em: https://www.anaconda.com/download/" -ForegroundColor Yellow
    Write-Host "❗ Instale o Anaconda e execute este script novamente" -ForegroundColor Yellow
    pause
    exit 1
}

# Verificar Node.js
$nodeExists = Get-Command node -ErrorAction SilentlyContinue
if ($nodeExists) {
    Write-Host "✅ Node.js encontrado" -ForegroundColor Green
} else {
    Write-Host "❌ Node.js não encontrado!" -ForegroundColor Red
    Write-Host "📥 Baixe em: https://nodejs.org/" -ForegroundColor Yellow
    Write-Host "❗ Instale o Node.js e execute este script novamente" -ForegroundColor Yellow
    pause
    exit 1
}

# Verificar Ollama
$ollamaExists = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollamaExists) {
    Write-Host "✅ Ollama encontrado" -ForegroundColor Green
} else {
    Write-Host "⚠️ Ollama não encontrado - será instalado depois" -ForegroundColor Yellow
}

Write-Host ""

# Etapa 2: Configurar ambiente Python
Write-Host "🐍 ETAPA 2: Configurando ambiente Python..." -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

# Criar ambiente conda
Write-Host "📦 Criando ambiente conda..." -ForegroundColor Yellow
conda create -n auditoria-fiscal python=3.10 -y

# Ativar ambiente
Write-Host "🔄 Ativando ambiente..." -ForegroundColor Yellow
& C:\ProgramData\Anaconda3\shell\condabin\conda-hook.ps1
conda activate auditoria-fiscal

# Instalar dependências Python
Write-Host "📚 Instalando bibliotecas Python..." -ForegroundColor Yellow
pip install fastapi uvicorn python-multipart httpx sqlalchemy psycopg2-binary redis python-jose[cryptography] passlib[bcrypt] aiofiles pandas numpy scikit-learn matplotlib seaborn streamlit

Write-Host "✅ Ambiente Python configurado" -ForegroundColor Green
Write-Host ""

# Etapa 3: Configurar frontend
Write-Host "🎨 ETAPA 3: Configurando interface (Frontend)..." -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

if (Test-Path "frontend") {
    cd frontend
    Write-Host "📦 Instalando dependências do frontend..." -ForegroundColor Yellow
    npm install
    cd ..
    Write-Host "✅ Frontend configurado" -ForegroundColor Green
} else {
    Write-Host "⚠️ Pasta frontend não encontrada - ignorando" -ForegroundColor Yellow
}

Write-Host ""

# Etapa 4: Configurar banco de dados
Write-Host "💾 ETAPA 4: Configurando banco de dados..." -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Criar diretórios necessários
Write-Host "📁 Criando diretórios..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "data\logs" -Force | Out-Null
New-Item -ItemType Directory -Path "data\uploads" -Force | Out-Null
New-Item -ItemType Directory -Path "data\backups" -Force | Out-Null
New-Item -ItemType Directory -Path "data\postgres" -Force | Out-Null
New-Item -ItemType Directory -Path "logs" -Force | Out-Null

# Iniciar containers se necessário
Write-Host "🐳 Configurando containers Docker..." -ForegroundColor Yellow

$postgresRunning = docker ps --filter "name=auditoria_postgres" --format "{{.Names}}"
if (-not $postgresRunning) {
    Write-Host "🔄 Iniciando PostgreSQL..." -ForegroundColor Yellow
    docker run -d --name auditoria_postgres `
        -e POSTGRES_DB=auditoria_fiscal_local `
        -e POSTGRES_USER=auditoria_user `
        -e POSTGRES_PASSWORD=auditoria123 `
        -p 5432:5432 `
        -v ${PWD}\data\postgres:/var/lib/postgresql/data `
        postgres:15-alpine
}

$redisRunning = docker ps --filter "name=auditoria_redis" --format "{{.Names}}"
if (-not $redisRunning) {
    Write-Host "🔄 Iniciando Redis..." -ForegroundColor Yellow
    docker run -d --name auditoria_redis `
        -p 6379:6379 `
        redis:7-alpine
}

Write-Host "✅ Banco de dados configurado" -ForegroundColor Green
Write-Host ""

# Etapa 5: Instalar modelos de IA
Write-Host "🤖 ETAPA 5: Configurando Inteligência Artificial..." -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

if ($ollamaExists) {
    Write-Host "📥 Baixando modelos de IA (pode demorar)..." -ForegroundColor Yellow
    ollama pull llama3.1:8b
    ollama pull mistral:7b
    Write-Host "✅ Modelos de IA instalados" -ForegroundColor Green
} else {
    Write-Host "⚠️ Ollama não instalado - instale manualmente se quiser usar IA" -ForegroundColor Yellow
    Write-Host "📥 Download: https://ollama.ai/download" -ForegroundColor Yellow
}

Write-Host ""

# Etapa 6: Criar scripts de uso
Write-Host "📝 ETAPA 6: Criando scripts de uso..." -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

# Script para iniciar sistema completo
$startScript = @"
# Iniciar Sistema Completo - Usuário Final
Write-Host "🚀 INICIANDO SISTEMA DE AUDITORIA FISCAL..." -ForegroundColor Green

# Verificar Docker
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker não encontrado!" -ForegroundColor Red
    exit 1
}

# Iniciar containers
Write-Host "🐳 Iniciando banco de dados..." -ForegroundColor Yellow
docker start auditoria_postgres auditoria_redis 2>```$null

# Aguardar containers
Start-Sleep -Seconds 5

# Ativar ambiente Python
Write-Host "🐍 Ativando ambiente Python..." -ForegroundColor Yellow
& C:\ProgramData\Anaconda3\shell\condabin\conda-hook.ps1
conda activate auditoria-fiscal

# Configurar variáveis
```$env:DATABASE_URL="postgresql://auditoria_user:auditoria123@localhost:5432/auditoria_fiscal_local"
```$env:REDIS_URL="redis://localhost:6379"
```$env:OLLAMA_URL="http://localhost:11434"

Write-Host "✅ Sistema iniciado!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 COMO ACESSAR:" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3001" -ForegroundColor White
Write-Host "Backend:  http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "🔑 LOGIN:" -ForegroundColor Cyan
Write-Host "Email: admin@demo.com" -ForegroundColor White
Write-Host "Senha: admin123" -ForegroundColor White
Write-Host ""
Write-Host "▶️ PRÓXIMO PASSO:" -ForegroundColor Yellow
Write-Host "1. Execute: .\iniciar_backend.ps1" -ForegroundColor White
Write-Host "2. Execute: .\iniciar_frontend.ps1" -ForegroundColor White
"@

$startScript | Out-File -FilePath "iniciar_sistema_completo.ps1" -Encoding UTF8

# Script para verificar status
$statusScript = @"
Write-Host "📊 STATUS DO SISTEMA DE AUDITORIA FISCAL" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green

Write-Host "🐳 Containers Docker:" -ForegroundColor Cyan
docker ps --format "table {{.Names}}\t{{.Status}}" | findstr auditoria

Write-Host ""
Write-Host "💾 Banco de Dados:" -ForegroundColor Cyan
docker exec auditoria_postgres pg_isready -U auditoria_user 2>```$null
if (```$?) { Write-Host "✅ PostgreSQL funcionando" -ForegroundColor Green } else { Write-Host "❌ PostgreSQL com problema" -ForegroundColor Red }

Write-Host ""
Write-Host "🗄️ Cache Redis:" -ForegroundColor Cyan
docker exec auditoria_redis redis-cli ping 2>```$null
if (```$?) { Write-Host "✅ Redis funcionando" -ForegroundColor Green } else { Write-Host "❌ Redis com problema" -ForegroundColor Red }

Write-Host ""
Write-Host "🤖 Inteligência Artificial:" -ForegroundColor Cyan
try {
    ```$response = Invoke-RestMethod -Uri "http://localhost:11434/api/version" -TimeoutSec 3
    Write-Host "✅ Ollama funcionando (versão ```$(`$response.version))" -ForegroundColor Green
} catch {
    Write-Host "❌ Ollama não está respondendo" -ForegroundColor Red
}

Write-Host ""
Write-Host "🌐 URLs do Sistema:" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3001" -ForegroundColor White
Write-Host "Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White
"@

$statusScript | Out-File -FilePath "verificar_status_sistema.ps1" -Encoding UTF8

Write-Host "✅ Scripts criados com sucesso!" -ForegroundColor Green
Write-Host ""

# Finalização
Write-Host "🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 PRÓXIMOS PASSOS:" -ForegroundColor Cyan
Write-Host "1. Execute: .\iniciar_sistema_completo.ps1" -ForegroundColor White
Write-Host "2. Execute: .\iniciar_backend.ps1 (em nova janela)" -ForegroundColor White
Write-Host "3. Execute: .\iniciar_frontend.ps1 (em nova janela)" -ForegroundColor White
Write-Host "4. Acesse: http://localhost:3001" -ForegroundColor White
Write-Host "5. Login: admin@demo.com / admin123" -ForegroundColor White
Write-Host ""
Write-Host "📞 SUPORTE:" -ForegroundColor Yellow
Write-Host "- Para verificar status: .\verificar_status_sistema.ps1" -ForegroundColor White
Write-Host "- Manual completo: MANUAL_USUARIO_FINAL.md" -ForegroundColor White
Write-Host ""
Write-Host "✅ Sistema pronto para uso!" -ForegroundColor Green

pause
