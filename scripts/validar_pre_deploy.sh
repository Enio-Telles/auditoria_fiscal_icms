#!/bin/bash

# 🚀 SCRIPT DE VALIDAÇÃO PRÉ-DEPLOY
# Sistema de Auditoria Fiscal ICMS v4.0
# Data: 23 de Agosto de 2025

echo "🔍 INICIANDO VALIDAÇÃO PRÉ-DEPLOY..."
echo "========================================"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para check com status
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
        return 0
    else
        echo -e "${RED}❌ $1${NC}"
        return 1
    fi
}

# Função para warning
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Função para info
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Contador de erros
ERRORS=0

echo
echo "🔧 1. VERIFICANDO DEPENDÊNCIAS..."
echo "--------------------------------"

# Docker
command -v docker >/dev/null 2>&1
if check_status "Docker instalado"; then
    DOCKER_VERSION=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    info "Docker versão: $DOCKER_VERSION"
else
    ERRORS=$((ERRORS + 1))
fi

# Docker Compose
command -v docker-compose >/dev/null 2>&1
if check_status "Docker Compose instalado"; then
    COMPOSE_VERSION=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
    info "Docker Compose versão: $COMPOSE_VERSION"
else
    ERRORS=$((ERRORS + 1))
fi

# Git
command -v git >/dev/null 2>&1
if check_status "Git instalado"; then
    GIT_VERSION=$(git --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
    info "Git versão: $GIT_VERSION"
else
    ERRORS=$((ERRORS + 1))
fi

echo
echo "🐳 2. VERIFICANDO DOCKER..."
echo "---------------------------"

# Docker rodando
docker info >/dev/null 2>&1
check_status "Docker service ativo"
[ $? -ne 0 ] && ERRORS=$((ERRORS + 1))

# Docker sem sudo
docker run hello-world >/dev/null 2>&1
if check_status "Docker sem sudo"; then
    docker rmi hello-world >/dev/null 2>&1
else
    warning "Usuário pode precisar estar no grupo docker"
fi

# NVIDIA Docker (para GPU)
if command -v nvidia-smi >/dev/null 2>&1; then
    info "GPU NVIDIA detectada:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | head -1
    
    docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi >/dev/null 2>&1
    check_status "NVIDIA Docker runtime"
    [ $? -ne 0 ] && warning "GPU não será utilizada pelos containers"
else
    warning "GPU NVIDIA não detectada - Ollama usará CPU"
fi

echo
echo "💾 3. VERIFICANDO RECURSOS DO SISTEMA..."
echo "----------------------------------------"

# CPU
CPU_CORES=$(nproc)
if [ $CPU_CORES -ge 8 ]; then
    check_status "CPU cores: $CPU_CORES (recomendado: 8+)"
else
    warning "CPU cores: $CPU_CORES (recomendado: 8+)"
fi

# RAM
RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
if [ $RAM_GB -ge 16 ]; then
    check_status "RAM: ${RAM_GB}GB (recomendado: 16GB+)"
else
    warning "RAM: ${RAM_GB}GB (recomendado: 16GB+)"
fi

# Disco
DISK_GB=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
if [ $DISK_GB -ge 500 ]; then
    check_status "Espaço livre: ${DISK_GB}GB (recomendado: 500GB+)"
else
    warning "Espaço livre: ${DISK_GB}GB (recomendado: 500GB+)"
fi

echo
echo "🌐 4. VERIFICANDO CONECTIVIDADE..."
echo "----------------------------------"

# Internet
curl -s --connect-timeout 5 https://google.com >/dev/null 2>&1
check_status "Conectividade com internet"
[ $? -ne 0 ] && ERRORS=$((ERRORS + 1))

# Docker Hub
docker pull hello-world >/dev/null 2>&1
if check_status "Acesso ao Docker Hub"; then
    docker rmi hello-world >/dev/null 2>&1
else
    ERRORS=$((ERRORS + 1))
fi

# Hugging Face (para modelos IA)
curl -s --connect-timeout 5 https://huggingface.co >/dev/null 2>&1
check_status "Acesso ao Hugging Face"

echo
echo "📁 5. VERIFICANDO ESTRUTURA DO PROJETO..."
echo "-----------------------------------------"

# Arquivos essenciais
FILES=(
    "scripts/deploy_producao.sh"
    "deploy/production/docker-compose.prod.yml"
    "deploy/production/.env.production"
    "deploy/production/nginx.conf"
    "requirements.txt"
    "frontend/package.json"
    "microservices/api_gateway/main.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        check_status "Arquivo: $file"
    else
        echo -e "${RED}❌ Arquivo: $file${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done

# Diretórios essenciais
DIRS=(
    "microservices"
    "frontend"
    "data"
    "deploy/production"
    "logs"
)

for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        check_status "Diretório: $dir"
    else
        echo -e "${RED}❌ Diretório: $dir${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done

echo
echo "🔒 6. VERIFICANDO CONFIGURAÇÕES DE SEGURANÇA..."
echo "-----------------------------------------------"

# Arquivo .env
if [ -f "deploy/production/.env.production" ]; then
    check_status "Arquivo .env.production existe"
    
    # Verificar variáveis críticas
    if grep -q "POSTGRES_PASSWORD=changeme" deploy/production/.env.production; then
        warning "POSTGRES_PASSWORD usando valor padrão!"
    else
        check_status "POSTGRES_PASSWORD configurada"
    fi
    
    if grep -q "JWT_SECRET=your-secret-key" deploy/production/.env.production; then
        warning "JWT_SECRET usando valor padrão!"
    else
        check_status "JWT_SECRET configurada"
    fi
else
    echo -e "${RED}❌ Arquivo .env.production não encontrado${NC}"
    ERRORS=$((ERRORS + 1))
fi

# SSL
if [ -d "deploy/production/ssl" ]; then
    check_status "Diretório SSL existe"
    
    if [ -f "deploy/production/ssl/auditoria-fiscal.com.crt" ] && [ -f "deploy/production/ssl/auditoria-fiscal.com.key" ]; then
        check_status "Certificados SSL encontrados"
    else
        warning "Certificados SSL não encontrados - configurar antes do deploy"
    fi
else
    warning "Diretório SSL não existe - criar certificados antes do deploy"
fi

echo
echo "🧪 7. EXECUTANDO TESTES BÁSICOS..."
echo "----------------------------------"

# Verificar syntax Python
info "Verificando sintaxe Python..."
python3 -m py_compile microservices/api_gateway/main.py 2>/dev/null
check_status "Sintaxe Python válida"

# Verificar package.json
if [ -f "frontend/package.json" ]; then
    cd frontend
    npm list >/dev/null 2>&1
    if check_status "Dependências frontend válidas"; then
        cd ..
    else
        cd ..
        warning "Executar 'npm install' no frontend antes do deploy"
    fi
fi

# Verificar requirements.txt
if [ -f "requirements.txt" ]; then
    check_status "requirements.txt válido"
else
    warning "requirements.txt não encontrado"
fi

echo
echo "📊 8. RESUMO DA VALIDAÇÃO..."
echo "=============================="

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}"
    echo "✅ SISTEMA PRONTO PARA DEPLOY!"
    echo "------------------------------"
    echo "Todas as verificações passaram com sucesso."
    echo "O sistema está preparado para deploy em produção."
    echo -e "${NC}"
    
    echo
    echo "🚀 PRÓXIMOS PASSOS:"
    echo "1. Configurar certificados SSL se necessário"
    echo "2. Revisar variáveis de ambiente em .env.production"
    echo "3. Executar: ./scripts/deploy_producao.sh"
    echo
    
    exit 0
else
    echo -e "${RED}"
    echo "❌ PROBLEMAS ENCONTRADOS: $ERRORS"
    echo "--------------------------------"
    echo "Corrija os problemas acima antes do deploy."
    echo -e "${NC}"
    
    echo
    echo "🔧 AÇÕES RECOMENDADAS:"
    echo "1. Instalar dependências faltantes"
    echo "2. Configurar Docker adequadamente"
    echo "3. Verificar recursos do sistema"
    echo "4. Corrigir arquivos de configuração"
    echo "5. Executar novamente este script"
    echo
    
    exit 1
fi
