#!/bin/bash
# Script de Deploy em Produção - Sistema de Auditoria Fiscal ICMS
# Versão: 1.0.0 - Produção
# Data: 23/08/2025

set -e  # Parar em caso de erro

echo "🚀 INICIANDO DEPLOY EM PRODUÇÃO - Sistema de Auditoria Fiscal ICMS v4.0"
echo "=================================================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variáveis de configuração
PROJECT_NAME="auditoria-fiscal-icms"
DOMAIN="${DOMAIN:-auditoria-fiscal.com}"
ENVIRONMENT="${ENVIRONMENT:-production}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(openssl rand -hex 32)}"
JWT_SECRET="${JWT_SECRET:-$(openssl rand -hex 64)}"

echo -e "${BLUE}📋 Configurações do Deploy:${NC}"
echo "- Projeto: $PROJECT_NAME"
echo "- Domínio: $DOMAIN"
echo "- Ambiente: $ENVIRONMENT"
echo ""

# Função para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# 1. Verificar pré-requisitos
log "1️⃣ Verificando pré-requisitos..."

# Verificar Docker
if ! command -v docker &> /dev/null; then
    error "Docker não está instalado. Instale o Docker primeiro."
fi

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose não está instalado. Instale o Docker Compose primeiro."
fi

# Verificar Node.js
if ! command -v node &> /dev/null; then
    error "Node.js não está instalado. Instale o Node.js primeiro."
fi

# Verificar Python
if ! command -v python3 &> /dev/null; then
    error "Python 3 não está instalado. Instale o Python 3 primeiro."
fi

log "✅ Todos os pré-requisitos verificados"

# 2. Preparar ambiente
log "2️⃣ Preparando ambiente de produção..."

# Criar diretórios necessários
mkdir -p deploy/production/{nginx,postgres,redis,logs,backups}
mkdir -p deploy/production/ssl
mkdir -p deploy/production/data/{postgres,redis,uploads,logs}

# Gerar arquivos de configuração
log "📝 Gerando configurações de produção..."

# 3. Configurar PostgreSQL
log "3️⃣ Configurando PostgreSQL..."

cat > deploy/production/postgres/init.sql << EOF
-- Inicialização do banco de dados de produção
CREATE DATABASE auditoria_fiscal_prod;
CREATE USER auditoria_user WITH ENCRYPTED PASSWORD '$POSTGRES_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE auditoria_fiscal_prod TO auditoria_user;

-- Configurações de performance
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

SELECT pg_reload_conf();
EOF

# 4. Configurar Nginx
log "4️⃣ Configurando Nginx..."

cat > deploy/production/nginx/nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logs
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;

    upstream backend {
        least_conn;
        server api-gateway:8000;
    }

    server {
        listen 80;
        server_name $DOMAIN www.$DOMAIN;
        return 301 https://\$server_name\$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name $DOMAIN www.$DOMAIN;

        ssl_certificate /etc/ssl/certs/$DOMAIN.crt;
        ssl_certificate_key /etc/ssl/private/$DOMAIN.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

        # Frontend
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files \$uri \$uri/ /index.html;
        }

        # API
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF

# 5. Criar Docker Compose para produção
log "5️⃣ Criando configuração Docker Compose..."

cat > deploy/production/docker-compose.prod.yml << EOF
version: '3.8'

services:
  # Banco de dados PostgreSQL
  postgres:
    image: postgres:15-alpine
    container_name: auditoria-postgres
    environment:
      POSTGRES_DB: auditoria_fiscal_prod
      POSTGRES_USER: auditoria_user
      POSTGRES_PASSWORD: $POSTGRES_PASSWORD
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --lc-collate=C --lc-ctype=C"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - auditoria-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U auditoria_user -d auditoria_fiscal_prod"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Redis para cache
  redis:
    image: redis:7-alpine
    container_name: auditoria-redis
    command: redis-server --requirepass redis-password-prod
    volumes:
      - ./data/redis:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - auditoria-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

  # API Gateway
  api-gateway:
    build:
      context: ../../microservices/api-gateway
      dockerfile: Dockerfile.prod
    container_name: auditoria-gateway
    environment:
      - ENVIRONMENT=production
      - POSTGRES_URL=postgresql://auditoria_user:$POSTGRES_PASSWORD@postgres:5432/auditoria_fiscal_prod
      - REDIS_URL=redis://:redis-password-prod@redis:6379/0
      - JWT_SECRET=$JWT_SECRET
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - auditoria-network

  # Auth Service
  auth-service:
    build:
      context: ../../microservices/auth-service
      dockerfile: Dockerfile.prod
    container_name: auditoria-auth
    environment:
      - ENVIRONMENT=production
      - POSTGRES_URL=postgresql://auditoria_user:$POSTGRES_PASSWORD@postgres:5432/auditoria_fiscal_prod
      - JWT_SECRET=$JWT_SECRET
    ports:
      - "8001:8001"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - auditoria-network

  # Tenant Service
  tenant-service:
    build:
      context: ../../microservices/tenant-service
      dockerfile: Dockerfile.prod
    container_name: auditoria-tenant
    environment:
      - ENVIRONMENT=production
      - POSTGRES_URL=postgresql://auditoria_user:$POSTGRES_PASSWORD@postgres:5432/auditoria_fiscal_prod
    ports:
      - "8002:8002"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - auditoria-network

  # Product Service
  product-service:
    build:
      context: ../../microservices/product-service
      dockerfile: Dockerfile.prod
    container_name: auditoria-product
    environment:
      - ENVIRONMENT=production
      - POSTGRES_URL=postgresql://auditoria_user:$POSTGRES_PASSWORD@postgres:5432/auditoria_fiscal_prod
    ports:
      - "8003:8003"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - auditoria-network

  # Classification Service
  classification-service:
    build:
      context: ../../microservices/classification-service
      dockerfile: Dockerfile.prod
    container_name: auditoria-classification
    environment:
      - ENVIRONMENT=production
      - POSTGRES_URL=postgresql://auditoria_user:$POSTGRES_PASSWORD@postgres:5432/auditoria_fiscal_prod
    ports:
      - "8004:8004"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - auditoria-network

  # Import Service
  import-service:
    build:
      context: ../../microservices/import-service
      dockerfile: Dockerfile.prod
    container_name: auditoria-import
    environment:
      - ENVIRONMENT=production
      - POSTGRES_URL=postgresql://auditoria_user:$POSTGRES_PASSWORD@postgres:5432/auditoria_fiscal_prod
    ports:
      - "8005:8005"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - auditoria-network
    volumes:
      - ./data/uploads:/app/uploads

  # AI Service (Ollama)
  ai-service:
    build:
      context: ../../microservices/ai-service
      dockerfile: Dockerfile.prod
    container_name: auditoria-ai
    environment:
      - ENVIRONMENT=production
      - OLLAMA_HOST=ollama:11434
    ports:
      - "8006:8006"
    depends_on:
      - ollama
    restart: unless-stopped
    networks:
      - auditoria-network

  # Ollama (IA Local)
  ollama:
    image: ollama/ollama:latest
    container_name: auditoria-ollama
    ports:
      - "11434:11434"
    volumes:
      - ./data/ollama:/root/.ollama
    restart: unless-stopped
    networks:
      - auditoria-network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Frontend (React)
  frontend:
    build:
      context: ../../frontend
      dockerfile: Dockerfile.prod
    container_name: auditoria-frontend
    restart: unless-stopped
    networks:
      - auditoria-network

  # Nginx (Proxy Reverso)
  nginx:
    image: nginx:alpine
    container_name: auditoria-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - api-gateway
      - frontend
    restart: unless-stopped
    networks:
      - auditoria-network

networks:
  auditoria-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  ollama_data:
  uploads_data:
EOF

# 6. Criar Dockerfiles de produção
log "6️⃣ Criando Dockerfiles de produção..."

# Dockerfile para microserviços Python
cat > deploy/production/Dockerfile.microservice << EOF
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Usuário não-root para segurança
RUN useradd --create-home --shell /bin/bash appuser
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Comando padrão
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
EOF

# Dockerfile para frontend React
cat > deploy/production/Dockerfile.frontend << EOF
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copiar arquivos buildados
COPY --from=builder /app/dist /usr/share/nginx/html

# Configuração nginx para SPA
RUN echo 'server { \\
    listen 80; \\
    location / { \\
        root /usr/share/nginx/html; \\
        index index.html; \\
        try_files \$uri \$uri/ /index.html; \\
    } \\
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

# 7. Script de inicialização do Ollama
log "7️⃣ Configurando modelos Ollama..."

cat > deploy/production/init-ollama.sh << EOF
#!/bin/bash
# Script para inicializar modelos Ollama em produção

echo "🤖 Inicializando modelos Ollama..."

# Aguardar Ollama estar pronto
until curl -s http://ollama:11434/api/version; do
    echo "Aguardando Ollama..."
    sleep 5
done

# Baixar modelos necessários
models=(
    "llama3:8b"
    "gemma2:9b"
    "qwen2:7b"
    "mistral:7b"
    "codellama:7b"
    "phi3:3.8b"
    "nomic-embed-text"
    "all-minilm:l6-v2"
)

for model in "\${models[@]}"; do
    echo "📥 Baixando modelo: \$model"
    curl -X POST http://ollama:11434/api/pull -d "{\\"name\\": \\"\$model\\"}"
    echo "✅ Modelo \$model baixado"
done

echo "🎉 Todos os modelos Ollama configurados!"
EOF

chmod +x deploy/production/init-ollama.sh

# 8. Configurar monitoramento
log "8️⃣ Configurando monitoramento..."

cat > deploy/production/docker-compose.monitoring.yml << EOF
version: '3.8'

services:
  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: auditoria-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./data/prometheus:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    restart: unless-stopped
    networks:
      - auditoria-network

  # Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: auditoria-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123prod
    volumes:
      - ./data/grafana:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    restart: unless-stopped
    networks:
      - auditoria-network

networks:
  auditoria-network:
    external: true
EOF

# 9. Script de backup automático
log "9️⃣ Configurando sistema de backup..."

cat > deploy/production/backup.sh << EOF
#!/bin/bash
# Sistema de backup automático

BACKUP_DIR="./backups"
DATE=\$(date +%Y%m%d_%H%M%S)

echo "📦 Iniciando backup - \$DATE"

# Backup do banco de dados
docker exec auditoria-postgres pg_dump -U auditoria_user auditoria_fiscal_prod > "\$BACKUP_DIR/db_backup_\$DATE.sql"

# Backup dos uploads
tar -czf "\$BACKUP_DIR/uploads_backup_\$DATE.tar.gz" ./data/uploads/

# Backup das configurações
tar -czf "\$BACKUP_DIR/config_backup_\$DATE.tar.gz" ./nginx/ ./postgres/

# Limpeza de backups antigos (manter últimos 7 dias)
find \$BACKUP_DIR -name "*.sql" -mtime +7 -delete
find \$BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "✅ Backup concluído: \$DATE"
EOF

chmod +x deploy/production/backup.sh

# 10. Arquivo de configuração de ambiente
log "🔟 Criando arquivo de configuração..."

cat > deploy/production/.env.production << EOF
# Configurações de Produção - Sistema de Auditoria Fiscal ICMS
ENVIRONMENT=production
DEBUG=false

# Banco de Dados
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=auditoria_fiscal_prod
POSTGRES_USER=auditoria_user
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis-password-prod

# Segurança
JWT_SECRET=$JWT_SECRET
SECRET_KEY=$(openssl rand -hex 32)

# APIs Externas
OLLAMA_HOST=ollama
OLLAMA_PORT=11434

# Domínio
DOMAIN=$DOMAIN
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,localhost

# Logs
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log

# Backup
BACKUP_SCHEDULE="0 2 * * *"  # Todo dia às 2h da manhã
EOF

# 11. Script de deploy final
log "1️⃣1️⃣ Criando script de deploy final..."

cat > deploy/production/deploy.sh << EOF
#!/bin/bash
# Deploy final em produção

set -e

echo "🚀 Executando deploy em produção..."

# Parar serviços existentes
docker-compose -f docker-compose.prod.yml down || true

# Build das imagens
echo "🔨 Buildando imagens..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Iniciar banco de dados primeiro
echo "💾 Iniciando banco de dados..."
docker-compose -f docker-compose.prod.yml up -d postgres redis

# Aguardar banco estar pronto
echo "⏳ Aguardando banco de dados..."
sleep 30

# Executar migrações
echo "🔄 Executando migrações..."
docker-compose -f docker-compose.prod.yml run --rm api-gateway python manage.py migrate

# Iniciar todos os serviços
echo "🚀 Iniciando todos os serviços..."
docker-compose -f docker-compose.prod.yml up -d

# Inicializar Ollama
echo "🤖 Inicializando Ollama..."
sleep 60
./init-ollama.sh

# Configurar cron para backup
echo "📅 Configurando backup automático..."
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/deploy/production/backup.sh") | crontab -

echo "✅ Deploy concluído com sucesso!"
echo "🌐 Sistema disponível em: https://$DOMAIN"
echo "📊 Monitoramento: http://$DOMAIN:3000 (Grafana)"
echo "📈 Métricas: http://$DOMAIN:9090 (Prometheus)"

EOF

chmod +x deploy/production/deploy.sh

# 12. Finalização
log "🎉 Configuração de deploy criada com sucesso!"

echo ""
echo -e "${GREEN}=================================================================="
echo -e "✅ DEPLOY EM PRODUÇÃO CONFIGURADO COM SUCESSO!"
echo -e "=================================================================="
echo ""
echo -e "${BLUE}📋 Próximos passos para deploy:${NC}"
echo ""
echo "1. 🔑 Configurar certificados SSL:"
echo "   - Copie os certificados para: deploy/production/ssl/"
echo "   - Arquivos necessários: $DOMAIN.crt e $DOMAIN.key"
echo ""
echo "2. 🚀 Executar o deploy:"
echo "   cd deploy/production"
echo "   ./deploy.sh"
echo ""
echo "3. 🔧 Configurações adicionais:"
echo "   - DNS: Aponte $DOMAIN para o IP do servidor"
echo "   - Firewall: Abrir portas 80, 443"
echo "   - Monitoramento: Configurar alertas no Grafana"
echo ""
echo -e "${BLUE}📊 URLs do sistema após deploy:${NC}"
echo "   🌐 Sistema: https://$DOMAIN"
echo "   📊 Grafana: http://$DOMAIN:3000"
echo "   📈 Prometheus: http://$DOMAIN:9090"
echo ""
echo -e "${BLUE}🔐 Credenciais geradas:${NC}"
echo "   📊 Grafana: admin / admin123prod"
echo "   💾 PostgreSQL: auditoria_user / [gerada automaticamente]"
echo ""
echo -e "${YELLOW}⚠️  Importante:${NC}"
echo "   - Salve as senhas geradas em local seguro"
echo "   - Configure backups externos"
echo "   - Monitore logs de aplicação"
echo "   - Configure alertas de segurança"
echo ""
echo -e "${GREEN}🎊 O sistema está pronto para produção! 🎊${NC}"
echo ""
