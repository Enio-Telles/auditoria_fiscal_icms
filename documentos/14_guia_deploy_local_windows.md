# 🚀 GUIA DE DEPLOY LOCAL - WINDOWS 11
## Sistema de Auditoria Fiscal ICMS v4.0

**Data:** 23 de Agosto de 2025
**Status:** Pronto para Deploy Local
**Versão:** 1.0.0 Local Windows 11
**Ambiente:** 100% Local

---

## 📋 PRÉ-REQUISITOS WINDOWS 11

### 🖥️ Sistema Recomendado
- **OS**: Windows 11 (qualquer edição)
- **CPU**: Mínimo 4 cores (recomendado 8 cores)
- **RAM**: Mínimo 8GB (recomendado 16GB)
- **Storage**: Mínimo 50GB livres (recomendado 100GB)
- **GPU**: NVIDIA opcional (para melhor performance IA)
- **Internet**: Para download inicial das dependências

### 🛠️ Software Necessário (Windows)
- **Docker Desktop for Windows** 4.0+
- **Git for Windows**
- **Python 3.10+** (Anaconda recomendado)
- **Node.js 18+** com npm
- **VSCode** (opcional, mas recomendado)

---

## 🚀 INSTALAÇÃO RÁPIDA WINDOWS 11

### 1. Instalar Docker Desktop

```powershell
# Download do Docker Desktop
# https://www.docker.com/products/docker-desktop/

# Após instalação, verificar
docker --version
docker-compose --version

# Configurar Docker para usar WSL2 (recomendado)
```

### 2. Verificar Python/Anaconda

```powershell
# Verificar se Anaconda está instalado
conda --version

# Se não estiver, baixar de: https://www.anaconda.com/
# Ou usar Python padrão:
python --version
```

### 3. Verificar Node.js

```powershell
# Verificar Node.js
node --version
npm --version

# Se não estiver, baixar de: https://nodejs.org/
```

---

## 🏠 DEPLOY 100% LOCAL

### 📁 Preparar Ambiente Local

```powershell
# 1. Navegar para o projeto
cd C:\Users\eniot\OneDrive\Desenvolvimento\Projetos_IA_RAG\auditoria_fiscal_icms

# 2. Criar ambiente conda
conda create -n auditoria-fiscal python=3.10 -y
conda activate auditoria-fiscal

# 3. Instalar dependências Python
pip install -r requirements.txt

# 4. Preparar frontend
cd frontend
npm install
cd ..

# 5. Criar diretórios necessários
md data\logs 2>$null
# Seção corrigida no guia:

# 5. Criar diretórios necessários (COMANDO CORRETO)
New-Item -ItemType Directory -Path "data\logs" -Force
New-Item -ItemType Directory -Path "data\uploads" -Force
New-Item -ItemType Directory -Path "data\backups" -Force
New-Item -ItemType Directory -Path "data\chroma" -Force
New-Item -ItemType Directory -Path "data\postgres" -Force
New-Item -ItemType Directory -Path "data\ollama" -Force

```
# Verificar estrutura criada
Get-ChildItem data\ -Directory


### 🐳 Configurar Docker Local

```powershell
# IMPORTANTE: Verificar containers existentes primeiro!
# Listar containers existentes
docker ps -a

# Opção 1: Se containers já existem (RECOMENDADO)
# Usar containers existentes (auditoria_postgres, auditoria_redis)
docker start auditoria_postgres auditoria_redis

# Verificar status
docker ps | findstr -E "(postgres|redis)"

# Opção 2: Se precisar criar novos containers
# Criar network local (apenas se não existir)
docker network create auditoria-local-network 2>$null

# PostgreSQL (apenas se não existir auditoria_postgres)
docker run -d --name auditoria-postgres-new `
  --network auditoria-local-network `
  -e POSTGRES_DB=auditoria_fiscal_local `
  -e POSTGRES_USER=auditoria_user `
  -e POSTGRES_PASSWORD=auditoria123 `
  -p 5433:5432 `
  -v ${PWD}\data\postgres:/var/lib/postgresql/data `
  postgres:15-alpine

# Redis (apenas se não existir auditoria_redis)
docker run -d --name auditoria-redis-new `
  --network auditoria-local-network `
  -p 6380:6379 `
  redis:7-alpine

# OLLAMA: Usar instalação nativa do Windows (mais eficiente)
# Download: https://ollama.ai/download
# Ollama já roda nativamente na porta 11434
```

---

## 🤖 CONFIGURAR IA LOCAL

### Instalar Modelos Ollama (Windows)

```powershell
# Com Ollama nativo instalado no Windows:

# Instalar modelos essenciais para classificação
ollama pull llama3.1:8b
ollama pull codellama:7b
ollama pull mistral:7b
ollama pull gemma2:9b

# Verificar modelos instalados
ollama list

# Testar modelo
ollama run llama3.1:8b "Hello, how are you?"
```

---

## 🌐 EXECUTAR SISTEMA LOCAL

### 🚀 Iniciar Backend (Terminal 1)

```powershell
# Ativar ambiente
conda activate auditoria-fiscal

# Configurar variáveis de ambiente
$env:DATABASE_URL="postgresql://auditoria_user:auditoria123@localhost:5432/auditoria_fiscal_local"
$env:REDIS_URL="redis://localhost:6379"
$env:OLLAMA_URL="http://localhost:11434"
$env:ENVIRONMENT="local"

# Iniciar API Gateway
cd microservices\gateway
python main.py
```

### 🎨 Iniciar Frontend (Terminal 2)

```powershell
# Em novo terminal
cd C:\Users\eniot\OneDrive\Desenvolvimento\Projetos_IA_RAG\auditoria_fiscal_icms\frontend

# Configurar variável de ambiente
$env:REACT_APP_API_URL="http://localhost:8000"

# Iniciar React
npm start
```

### 🔧 Iniciar Microserviços (Terminal 3)

```powershell
# Em novo terminal
conda activate auditoria-fiscal

# Definir variáveis
$env:DATABASE_URL="postgresql://auditoria_user:auditoria123@localhost:5432/auditoria_fiscal_local"
$env:REDIS_URL="redis://localhost:6379"
$env:OLLAMA_URL="http://localhost:11434"

# Iniciar serviços em background
Start-Process powershell -ArgumentList "-Command", "cd microservices\auth-service; python main.py"
Start-Process powershell -ArgumentList "-Command", "cd microservices\tenant-service; python main.py"
Start-Process powershell -ArgumentList "-Command", "cd microservices\product-service; python main.py"
Start-Process powershell -ArgumentList "-Command", "cd microservices\classification-service; python main.py"
Start-Process powershell -ArgumentList "-Command", "cd microservices\import-service; python main.py"
Start-Process powershell -ArgumentList "-Command", "cd microservices\ai-service; python main.py"
```

---

## 🏗️ ARQUITETURA LOCAL WINDOWS

### 🌐 URLs do Sistema Local

| Serviço | URL Local | Porta |
|---------|-----------|-------|
| **Frontend React** | http://localhost:3000 | 3000 |
| **API Gateway** | http://localhost:8000 | 8000 |
| **Auth Service** | http://localhost:8001 | 8001 |
| **Tenant Service** | http://localhost:8002 | 8002 |
| **Product Service** | http://localhost:8003 | 8003 |
| **Classification** | http://localhost:8004 | 8004 |
| **Import Service** | http://localhost:8005 | 8005 |
| **AI Service** | http://localhost:8006 | 8006 |
| **PostgreSQL** | localhost:5432 | 5432 |
| **Redis** | localhost:6379 | 6379 |
| **Ollama** | http://localhost:11434 | 11434 |

### 🔄 Fluxo Local

```
Browser → React (3000) → API Gateway (8000) → Microserviços (8001-8006)
                                            ↓
                                     PostgreSQL (5432)
                                     Redis (6379)
                                     Ollama (11434)
```

---

## 📊 SCRIPTS DE AUTOMAÇÃO WINDOWS

### 🚀 Script de Inicialização Completa

```powershell
# Salvar como: start_sistema_local.ps1

Write-Host "🚀 Iniciando Sistema de Auditoria Fiscal Local..." -ForegroundColor Green

# Verificar Docker
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker não encontrado. Instale Docker Desktop." -ForegroundColor Red
    exit 1
}

# Verificar se containers estão rodando
$containers = @("auditoria_postgres", "auditoria_redis")

foreach ($container in $containers) {
    $status = docker inspect --format='{{.State.Status}}' $container 2>$null
    if ($status -ne "running") {
        Write-Host "🔄 Iniciando $container..." -ForegroundColor Yellow
        docker start $container
    } else {
        Write-Host "✅ $container já rodando" -ForegroundColor Green
    }
}

# Aguardar serviços
Write-Host "⏳ Aguardando serviços inicializarem..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Ativar ambiente conda
& C:\ProgramData\Anaconda3\shell\condabin\conda-hook.ps1
conda activate auditoria-fiscal

# Configurar variáveis de ambiente
$env:DATABASE_URL="postgresql://auditoria_user:auditoria123@localhost:5432/auditoria_fiscal_local"
$env:REDIS_URL="redis://localhost:6379"
$env:OLLAMA_URL="http://localhost:11434"
$env:ENVIRONMENT="local"

Write-Host "🎯 Sistema pronto! Acesse:" -ForegroundColor Cyan
Write-Host "• Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "• API: http://localhost:8000" -ForegroundColor White
Write-Host "• Docs: http://localhost:8000/docs" -ForegroundColor White

Write-Host "🚀 Para iniciar completamente, execute:" -ForegroundColor Magenta
Write-Host "1. .\start_backend.ps1" -ForegroundColor White
Write-Host "2. .\start_frontend.ps1" -ForegroundColor White
```

### 🔧 Script Backend

```powershell
# Salvar como: start_backend.ps1

Write-Host "🔧 Iniciando Backend..." -ForegroundColor Green

# Ativar ambiente
& C:\ProgramData\Anaconda3\shell\condabin\conda-hook.ps1
conda activate auditoria-fiscal

# Variáveis de ambiente
$env:DATABASE_URL="postgresql://auditoria_user:auditoria123@localhost:5432/auditoria_fiscal_local"
$env:REDIS_URL="redis://localhost:6379"
$env:OLLAMA_URL="http://localhost:11434"
$env:ENVIRONMENT="local"

# Executar migrações se necessário
Write-Host "📊 Configurando banco de dados..." -ForegroundColor Yellow

# Iniciar API Gateway
Write-Host "🚀 Iniciando API Gateway em http://localhost:8000" -ForegroundColor Cyan
cd microservices\gateway
python main.py
```

### 🎨 Script Frontend

```powershell
# Salvar como: start_frontend.ps1

Write-Host "🎨 Iniciando Frontend..." -ForegroundColor Green

cd frontend

# Configurar API URL
$env:REACT_APP_API_URL="http://localhost:8000"

# Verificar se node_modules existe
if (!(Test-Path "node_modules")) {
    Write-Host "📦 Instalando dependências..." -ForegroundColor Yellow
    npm install
}

# Iniciar React
Write-Host "🚀 Iniciando React em http://localhost:3000" -ForegroundColor Cyan
npm start
```

---

## 🔧 CONFIGURAÇÃO ESPECÍFICA WINDOWS

### 🐳 Docker Desktop Settings

1. **Abrir Docker Desktop**
2. **Settings → Resources → Advanced:**
   - CPU: 4+ cores
   - Memory: 8GB+
   - Swap: 2GB

3. **Settings → General:**
   - ✅ Use WSL 2 based engine
   - ✅ Start Docker Desktop when you log in

### 🔥 Windows Firewall

```powershell
# Permitir portas do sistema (executar como Admin)
New-NetFirewallRule -DisplayName "Auditoria Frontend" -Direction Inbound -Port 3000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Auditoria Backend" -Direction Inbound -Port 8000-8006 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Auditoria Database" -Direction Inbound -Port 5432 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Auditoria Redis" -Direction Inbound -Port 6379 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Auditoria Ollama" -Direction Inbound -Port 11434 -Protocol TCP -Action Allow
```

### 🎯 Variáveis de Ambiente Windows

```powershell
# Adicionar ao perfil PowerShell (opcional)
# $PROFILE para ver localização

# Adicionar ao final do arquivo:
function Start-AuditoriaFiscal {
    cd "C:\Users\eniot\OneDrive\Desenvolvimento\Projetos_IA_RAG\auditoria_fiscal_icms"
    & C:\ProgramData\Anaconda3\shell\condabin\conda-hook.ps1
    conda activate auditoria-fiscal
    $env:DATABASE_URL="postgresql://auditoria_user:auditoria123@localhost:5432/auditoria_fiscal_local"
    $env:REDIS_URL="redis://localhost:6379"
    $env:OLLAMA_URL="http://localhost:11434"
    $env:ENVIRONMENT="local"
    Write-Host "🚀 Ambiente Auditoria Fiscal configurado!" -ForegroundColor Green
}

# Uso: Start-AuditoriaFiscal
```

---

## 🧪 TESTES LOCAIS

### ✅ Checklist de Verificação Local

```powershell
# Script de teste local: test_local.ps1

Write-Host "🧪 Testando Sistema Local..." -ForegroundColor Green

# 1. Testar Docker
Write-Host "🐳 Testando containers..."
docker ps | findstr auditoria

# 2. Testar conectividade
Write-Host "🌐 Testando APIs..."
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "✅ API Gateway: OK" -ForegroundColor Green
} catch {
    Write-Host "❌ API Gateway: ERRO" -ForegroundColor Red
}

# 3. Testar banco
Write-Host "💾 Testando PostgreSQL..."
try {
    docker exec auditoria_postgres pg_isready -U auditoria_user
    Write-Host "✅ PostgreSQL: OK" -ForegroundColor Green
} catch {
    Write-Host "❌ PostgreSQL: ERRO" -ForegroundColor Red
}

# 4. Testar Ollama
Write-Host "🤖 Testando Ollama..."
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/version" -TimeoutSec 5
    Write-Host "✅ Ollama: OK" -ForegroundColor Green
} catch {
    Write-Host "❌ Ollama: ERRO" -ForegroundColor Red
}

# 5. Testar Frontend
Write-Host "🎨 Testando Frontend..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Frontend: OK" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Frontend: ERRO" -ForegroundColor Red
}

Write-Host "🎯 Teste concluído!" -ForegroundColor Cyan
```

---

## 🚨 TROUBLESHOOTING WINDOWS

### ❌ Problemas Comuns Windows

#### 🔴 Docker não inicia
```powershell
# Reiniciar Docker Desktop
Stop-Process -Name "Docker Desktop" -Force
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# Verificar WSL2
wsl --list --verbose
wsl --set-default-version 2
```

#### 🔴 Porta em uso
```powershell
# Verificar quem está usando a porta
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# Matar processo se necessário
taskkill /PID <PID> /F
```

#### 🔴 Conda não encontrado
```powershell
# Reconfigurar PATH
$env:PATH += ";C:\ProgramData\Anaconda3\Scripts"
$env:PATH += ";C:\ProgramData\Anaconda3"

# Ou reinstalar: https://www.anaconda.com/
```

#### 🔴 Permissões PowerShell
```powershell
# Permitir execução de scripts (executar como Admin)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 📞 Logs e Debug Windows

```powershell
# Ver logs dos containers
docker logs auditoria_postgres --tail 50
docker logs auditoria_redis --tail 50

# Ver processos Python
Get-Process python

# Verificar portas abertas
netstat -an | findstr LISTENING

# Ver logs do Ollama nativo (se necessário)
# Ollama roda como serviço nativo do Windows
```

---

## 🎉 INICIALIZAÇÃO RÁPIDA

### 🚀 **Comandos Para Iniciar TUDO (Windows)**

```powershell
# 1. Abrir PowerShell como Administrador
# 2. Navegar para o projeto
cd "C:\Users\eniot\OneDrive\Desenvolvimento\Projetos_IA_RAG\auditoria_fiscal_icms"

# 3. Executar setup inicial (apenas primeira vez)
.\scripts\setup_local_windows.ps1

# 4. Iniciar sistema completo
.\scripts\start_sistema_completo_local.ps1

# 5. Acessar o sistema
# Frontend: http://localhost:3000
# API: http://localhost:8000/docs
```

---

## 🎯 **RESUMO - SISTEMA LOCAL WINDOWS 11**

✅ **100% Local** - Sem necessidade de internet após setup
✅ **Windows 11** - Otimizado para o sistema operacional
✅ **Docker** - Containers locais para PostgreSQL, Redis, Ollama
✅ **Frontend React** - http://localhost:3000
✅ **7 Microserviços** - APIs locais (8000-8006)
✅ **IA Local** - 4+ modelos Ollama
✅ **Banco Local** - PostgreSQL em container
✅ **Cache Local** - Redis em container
✅ **Scripts Automação** - PowerShell para Windows

### 🚀 **O sistema está 100% pronto para rodar localmente no Windows 11!**

---

*Guia gerado em 23/08/2025 - Sistema v4.0 Local Windows 11*
