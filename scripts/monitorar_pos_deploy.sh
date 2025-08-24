#!/bin/bash

# 🎯 SCRIPT DE MONITORAMENTO PÓS-DEPLOY
# Sistema de Auditoria Fiscal ICMS v4.0
# Data: 23 de Agosto de 2025

echo "📊 INICIANDO MONITORAMENTO PÓS-DEPLOY..."
echo "========================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
DOMAIN="auditoria-fiscal.com"
API_BASE="https://$DOMAIN/api"
MONITORING_INTERVAL=30
MAX_CHECKS=20

# Função para status com cores
status_ok() {
    echo -e "${GREEN}✅ $1${NC}"
}

status_error() {
    echo -e "${RED}❌ $1${NC}"
}

status_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

status_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Função para testar endpoint
test_endpoint() {
    local url=$1
    local description=$2
    local expected_code=${3:-200}

    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 30 "$url")

    if [ "$response" = "$expected_code" ]; then
        status_ok "$description (HTTP $response)"
        return 0
    else
        status_error "$description (HTTP $response)"
        return 1
    fi
}

# Função para verificar container
check_container() {
    local container_name=$1
    local description=$2

    if docker ps --format "table {{.Names}}" | grep -q "^$container_name$"; then
        local status=$(docker inspect --format='{{.State.Status}}' "$container_name" 2>/dev/null)
        if [ "$status" = "running" ]; then
            status_ok "$description ($container_name)"
            return 0
        else
            status_error "$description - Status: $status"
            return 1
        fi
    else
        status_error "$description - Container não encontrado"
        return 1
    fi
}

# Função para verificar logs de erro
check_logs() {
    local container_name=$1
    local description=$2

    local errors=$(docker logs "$container_name" --since="5m" 2>&1 | grep -i "error\|exception\|failed" | wc -l)

    if [ "$errors" -eq 0 ]; then
        status_ok "$description - Sem erros recentes"
        return 0
    else
        status_warning "$description - $errors erros nos últimos 5min"
        return 1
    fi
}

echo
echo "🐳 1. VERIFICANDO STATUS DOS CONTAINERS..."
echo "------------------------------------------"

# Lista de containers para verificar
CONTAINERS=(
    "auditoria-nginx:Nginx (Proxy)"
    "auditoria-frontend:Frontend React"
    "auditoria-gateway:API Gateway"
    "auditoria-auth:Auth Service"
    "auditoria-tenant:Tenant Service"
    "auditoria-product:Product Service"
    "auditoria-classification:Classification Service"
    "auditoria-import:Import Service"
    "auditoria-ai:AI Service"
    "auditoria-postgres:PostgreSQL"
    "auditoria-redis:Redis Cache"
    "auditoria-ollama:Ollama AI"
)

CONTAINER_ERRORS=0

for container_info in "${CONTAINERS[@]}"; do
    IFS=':' read -r container_name description <<< "$container_info"
    check_container "$container_name" "$description"
    [ $? -ne 0 ] && CONTAINER_ERRORS=$((CONTAINER_ERRORS + 1))
done

echo
echo "🌐 2. TESTANDO CONECTIVIDADE WEB..."
echo "-----------------------------------"

# Testes de conectividade básica
WEB_ERRORS=0

test_endpoint "https://$DOMAIN" "Frontend Principal"
[ $? -ne 0 ] && WEB_ERRORS=$((WEB_ERRORS + 1))

test_endpoint "https://$DOMAIN/health" "Health Check Geral"
[ $? -ne 0 ] && WEB_ERRORS=$((WEB_ERRORS + 1))

test_endpoint "$API_BASE/health" "API Gateway Health"
[ $? -ne 0 ] && WEB_ERRORS=$((WEB_ERRORS + 1))

echo
echo "🔌 3. TESTANDO APIS DOS MICROSERVIÇOS..."
echo "----------------------------------------"

# Testes de APIs específicas
API_ERRORS=0

test_endpoint "$API_BASE/auth/health" "Auth Service"
[ $? -ne 0 ] && API_ERRORS=$((API_ERRORS + 1))

test_endpoint "$API_BASE/tenants/" "Tenant Service" 401  # Esperamos 401 sem auth
[ $? -ne 0 ] && API_ERRORS=$((API_ERRORS + 1))

test_endpoint "$API_BASE/products/" "Product Service" 401
[ $? -ne 0 ] && API_ERRORS=$((API_ERRORS + 1))

test_endpoint "$API_BASE/classification/health" "Classification Service"
[ $? -ne 0 ] && API_ERRORS=$((API_ERRORS + 1))

test_endpoint "$API_BASE/import/health" "Import Service"
[ $? -ne 0 ] && API_ERRORS=$((API_ERRORS + 1))

test_endpoint "$API_BASE/ai/health" "AI Service"
[ $? -ne 0 ] && API_ERRORS=$((API_ERRORS + 1))

echo
echo "💾 4. VERIFICANDO SERVIÇOS DE DADOS..."
echo "--------------------------------------"

DB_ERRORS=0

# PostgreSQL
if check_container "auditoria-postgres" "PostgreSQL Database"; then
    # Teste de conexão ao banco
    docker exec auditoria-postgres pg_isready -U auditoria_user >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        status_ok "PostgreSQL aceitando conexões"
    else
        status_error "PostgreSQL não aceitando conexões"
        DB_ERRORS=$((DB_ERRORS + 1))
    fi
else
    DB_ERRORS=$((DB_ERRORS + 1))
fi

# Redis
if check_container "auditoria-redis" "Redis Cache"; then
    # Teste de conexão ao Redis
    docker exec auditoria-redis redis-cli ping >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        status_ok "Redis respondendo a ping"
    else
        status_error "Redis não respondendo"
        DB_ERRORS=$((DB_ERRORS + 1))
    fi
else
    DB_ERRORS=$((DB_ERRORS + 1))
fi

echo
echo "🤖 5. VERIFICANDO SISTEMA DE IA..."
echo "----------------------------------"

AI_ERRORS=0

# Ollama
if check_container "auditoria-ollama" "Ollama AI Engine"; then
    # Verificar se Ollama está respondendo
    OLLAMA_RESPONSE=$(curl -s --connect-timeout 10 http://localhost:11434/api/version 2>/dev/null)
    if [ $? -eq 0 ] && [[ $OLLAMA_RESPONSE == *"version"* ]]; then
        status_ok "Ollama API respondendo"

        # Verificar modelos carregados
        MODELS=$(curl -s http://localhost:11434/api/tags 2>/dev/null | grep -o '"name"' | wc -l)
        if [ "$MODELS" -gt 0 ]; then
            status_ok "Modelos IA carregados: $MODELS"
        else
            status_warning "Nenhum modelo IA carregado"
            AI_ERRORS=$((AI_ERRORS + 1))
        fi
    else
        status_error "Ollama API não respondendo"
        AI_ERRORS=$((AI_ERRORS + 1))
    fi
else
    AI_ERRORS=$((AI_ERRORS + 1))
fi

# Teste de classificação básica
status_info "Testando classificação IA..."
CLASSIFICATION_TEST=$(curl -s -X POST "$API_BASE/classification/test" \
    -H "Content-Type: application/json" \
    -d '{"description": "Notebook Dell i7"}' 2>/dev/null)

if [ $? -eq 0 ] && [[ $CLASSIFICATION_TEST == *"success"* ]]; then
    status_ok "Sistema de classificação funcionando"
else
    status_warning "Sistema de classificação com problemas"
fi

echo
echo "📊 6. VERIFICANDO MONITORAMENTO..."
echo "----------------------------------"

MONITORING_ERRORS=0

# Prometheus
test_endpoint "http://$DOMAIN:9090/-/healthy" "Prometheus"
[ $? -ne 0 ] && MONITORING_ERRORS=$((MONITORING_ERRORS + 1))

# Grafana
test_endpoint "http://$DOMAIN:3000/api/health" "Grafana"
[ $? -ne 0 ] && MONITORING_ERRORS=$((MONITORING_ERRORS + 1))

echo
echo "🔍 7. VERIFICANDO LOGS DE ERRO..."
echo "---------------------------------"

LOG_ISSUES=0

# Verificar logs dos containers críticos
CRITICAL_CONTAINERS=("auditoria-gateway" "auditoria-postgres" "auditoria-ollama")

for container in "${CRITICAL_CONTAINERS[@]}"; do
    check_logs "$container" "Logs $container"
    [ $? -ne 0 ] && LOG_ISSUES=$((LOG_ISSUES + 1))
done

echo
echo "📈 8. MÉTRICAS DE PERFORMANCE..."
echo "--------------------------------"

# CPU e Memória dos containers
status_info "Uso de recursos dos containers:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -10

echo
echo "💾 Uso do disco:"
df -h / | tail -1 | awk '{print "Disco: " $3 "/" $2 " usado (" $5 ")"}'

echo
echo "🌐 Conectividade de rede:"
ping -c 3 8.8.8.8 >/dev/null 2>&1
if [ $? -eq 0 ]; then
    status_ok "Conectividade externa OK"
else
    status_error "Problemas de conectividade externa"
fi

echo
echo "======================================"
echo "📋 RESUMO DO MONITORAMENTO"
echo "======================================"

TOTAL_ERRORS=$((CONTAINER_ERRORS + WEB_ERRORS + API_ERRORS + DB_ERRORS + AI_ERRORS + MONITORING_ERRORS))

if [ $TOTAL_ERRORS -eq 0 ]; then
    echo -e "${GREEN}"
    echo "🎉 SISTEMA FUNCIONANDO PERFEITAMENTE!"
    echo "====================================="
    echo "✅ Todos os containers ativos"
    echo "✅ APIs respondendo corretamente"
    echo "✅ Banco de dados operacional"
    echo "✅ Sistema de IA funcionando"
    echo "✅ Monitoramento ativo"
    echo -e "${NC}"

    echo
    echo "🔗 LINKS ÚTEIS:"
    echo "• Frontend: https://$DOMAIN"
    echo "• API Docs: https://$DOMAIN/api/docs"
    echo "• Grafana: http://$DOMAIN:3000 (admin/admin)"
    echo "• Prometheus: http://$DOMAIN:9090"
    echo

else
    echo -e "${RED}"
    echo "⚠️  PROBLEMAS DETECTADOS: $TOTAL_ERRORS"
    echo "======================================"
    echo "• Containers com problema: $CONTAINER_ERRORS"
    echo "• Erros de conectividade: $WEB_ERRORS"
    echo "• APIs com problema: $API_ERRORS"
    echo "• Problemas de dados: $DB_ERRORS"
    echo "• Problemas de IA: $AI_ERRORS"
    echo "• Problemas de monitoramento: $MONITORING_ERRORS"
    echo -e "${NC}"

    echo
    echo "🔧 AÇÕES RECOMENDADAS:"
    echo "1. Verificar logs dos containers com problema"
    echo "2. Reiniciar serviços se necessário"
    echo "3. Verificar conectividade de rede"
    echo "4. Consultar documentação de troubleshooting"
    echo

    if [ $LOG_ISSUES -gt 0 ]; then
        echo "📋 VERIFICAR LOGS DETALHADOS:"
        for container in "${CRITICAL_CONTAINERS[@]}"; do
            echo "docker logs $container --tail 50"
        done
        echo
    fi
fi

echo "⏰ Monitoramento executado em: $(date)"
echo "🔄 Para monitoramento contínuo, execute este script periodicamente"

exit $TOTAL_ERRORS
