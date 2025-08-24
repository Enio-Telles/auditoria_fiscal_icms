# 🚀 GUIA DE DEPLOY EM PRODUÇÃO
## Sistema de Auditoria Fiscal ICMS v4.0

**Data:** 23 de Agosto de 2025
**Status:** Pronto para Deploy
**Versão:** 1.0.0 Produção

---

## 📋 PRÉ-REQUISITOS

### 🖥️ Servidor de Produção
- **CPU**: Mínimo 8 cores (recomendado 16 cores)
- **RAM**: Mínimo 16GB (recomendado 32GB)
- **Storage**: Mínimo 500GB SSD (recomendado 1TB)
- **GPU**: NVIDIA com 8GB+ VRAM (para Ollama)
- **OS**: Ubuntu 20.04+ ou CentOS 8+

### 🛠️ Software Necessário
- Docker 24.0+
- Docker Compose 2.20+
- Nginx (opcional, já incluso)
- Certificados SSL válidos
- Domínio configurado

### 🌐 Requisitos de Rede
- **Portas**: 80 (HTTP), 443 (HTTPS), 22 (SSH)
- **Domínio**: DNS apontando para o servidor
- **Certificado SSL**: Let's Encrypt ou certificado válido

---

## 🚀 PROCESSO DE DEPLOY

### 1. Preparação do Servidor

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Instalar NVIDIA Docker (para GPU)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### 2. Configurar Certificados SSL

```bash
# Opção 1: Let's Encrypt (Recomendado)
sudo apt install certbot
sudo certbot certonly --standalone -d auditoria-fiscal.com -d www.auditoria-fiscal.com

# Copiar certificados para o projeto
mkdir -p deploy/production/ssl
sudo cp /etc/letsencrypt/live/auditoria-fiscal.com/fullchain.pem deploy/production/ssl/auditoria-fiscal.com.crt
sudo cp /etc/letsencrypt/live/auditoria-fiscal.com/privkey.pem deploy/production/ssl/auditoria-fiscal.com.key

# Opção 2: Certificado próprio
# Copie seus certificados para deploy/production/ssl/
```

### 3. Executar Script de Deploy

```bash
# Dar permissão de execução
chmod +x scripts/deploy_producao.sh

# Configurar variáveis (opcional)
export DOMAIN="auditoria-fiscal.com"
export ENVIRONMENT="production"

# Executar deploy
./scripts/deploy_producao.sh
```

### 4. Deploy Manual (Passo a Passo)

```bash
# 1. Navegar para diretório de produção
cd deploy/production

# 2. Configurar variáveis de ambiente
cp .env.production .env
# Editar .env com suas configurações

# 3. Iniciar serviços de infraestrutura
docker-compose -f docker-compose.prod.yml up -d postgres redis

# 4. Aguardar serviços estarem prontos
sleep 30

# 5. Executar migrações de banco
docker-compose -f docker-compose.prod.yml run --rm api-gateway python manage.py migrate

# 6. Iniciar todos os serviços
docker-compose -f docker-compose.prod.yml up -d

# 7. Inicializar modelos Ollama
./init-ollama.sh

# 8. Configurar monitoramento
docker-compose -f docker-compose.monitoring.yml up -d

# 9. Configurar backup automático
./backup.sh  # Teste inicial
(crontab -l; echo "0 2 * * * $(pwd)/backup.sh") | crontab -
```

---

## 🏗️ ARQUITETURA DE PRODUÇÃO

### 🐳 Containers em Produção

| Serviço | Container | Porta | Função |
|---------|-----------|-------|---------|
| **Nginx** | auditoria-nginx | 80, 443 | Proxy reverso + SSL |
| **Frontend** | auditoria-frontend | - | Interface React |
| **API Gateway** | auditoria-gateway | 8000 | Gateway central |
| **Auth Service** | auditoria-auth | 8001 | Autenticação |
| **Tenant Service** | auditoria-tenant | 8002 | Gestão empresas |
| **Product Service** | auditoria-product | 8003 | Gestão produtos |
| **Classification** | auditoria-classification | 8004 | Classificação IA |
| **Import Service** | auditoria-import | 8005 | Importação dados |
| **AI Service** | auditoria-ai | 8006 | Serviços IA |
| **PostgreSQL** | auditoria-postgres | 5432 | Banco principal |
| **Redis** | auditoria-redis | 6379 | Cache |
| **Ollama** | auditoria-ollama | 11434 | Modelos IA |
| **Prometheus** | auditoria-prometheus | 9090 | Métricas |
| **Grafana** | auditoria-grafana | 3000 | Dashboards |

### 🔄 Fluxo de Requisições

```
Internet → Nginx (SSL) → API Gateway → Microserviços → PostgreSQL
                      ↓
                   Frontend (React) → API Gateway
```

---

## 🔧 CONFIGURAÇÕES DE PRODUÇÃO

### 🗄️ PostgreSQL
- **Conexões**: 200 simultâneas
- **Shared Buffers**: 256MB
- **Effective Cache**: 1GB
- **Backups**: Diários automáticos

### 🚀 Redis
- **Memória**: 512MB
- **Persistência**: RDB + AOF
- **Password**: Configurada automaticamente

### 🤖 Ollama (IA)
- **Modelos**: 8 modelos pré-carregados
- **GPU**: NVIDIA CUDA support
- **Memória**: 8GB+ VRAM recomendado

### 🔒 Segurança
- **SSL/TLS**: TLS 1.2 e 1.3
- **Headers**: Security headers configurados
- **Rate Limiting**: 10 req/s por IP
- **CORS**: Configurado para domínio específico

---

## 📊 MONITORAMENTO

### 🎯 Métricas Principais
- **CPU/RAM**: Por container
- **Latência**: APIs < 500ms
- **Throughput**: Requisições/segundo
- **Erros**: Taxa < 1%
- **Disponibilidade**: > 99.9%

### 📈 Dashboards Grafana
1. **Sistema Geral**: CPU, RAM, Disk, Network
2. **Aplicação**: Latência, Erros, Throughput
3. **Banco de Dados**: Conexões, Queries, Performance
4. **IA/Ollama**: GPU, Modelos, Classificações

### 🚨 Alertas Configurados
- CPU > 80% por 5 minutos
- RAM > 90% por 2 minutos
- Disk > 85%
- API Error Rate > 5%
- Database connections > 150

---

## 🔄 BACKUP E RECUPERAÇÃO

### 📦 Backup Automático
- **Frequência**: Diário às 2h da manhã
- **Retenção**: 7 dias locais, 30 dias externos
- **Componentes**:
  - Banco PostgreSQL (dump SQL)
  - Uploads de usuários
  - Configurações do sistema

### 🔧 Script de Backup

```bash
# Backup manual
cd deploy/production
./backup.sh

# Verificar backups
ls -la backups/

# Restaurar backup
docker exec -i auditoria-postgres psql -U auditoria_user auditoria_fiscal_prod < backup.sql
```

### 🌐 Backup Externo (Recomendado)

```bash
# Configurar backup para S3/Google Cloud
# Adicionar ao script de backup:
aws s3 sync ./backups/ s3://auditoria-backups/$(date +%Y-%m)/
```

---

## 🚀 DEPLOY E ATUALIZAÇÕES

### 🔄 Deploy Inicial

```bash
# 1. Clonar repositório
git clone https://github.com/usuario/auditoria_fiscal_icms.git
cd auditoria_fiscal_icms

# 2. Executar script de deploy
./scripts/deploy_producao.sh

# 3. Verificar status
docker-compose -f deploy/production/docker-compose.prod.yml ps

# 4. Testar sistema
curl -k https://auditoria-fiscal.com/health
```

### 🔄 Atualizações

```bash
# 1. Backup antes da atualização
./deploy/production/backup.sh

# 2. Atualizar código
git pull origin main

# 3. Rebuild e restart
cd deploy/production
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# 4. Executar migrações se necessário
docker-compose -f docker-compose.prod.yml run --rm api-gateway python manage.py migrate
```

### 🔄 Rollback

```bash
# Em caso de problemas
cd deploy/production

# 1. Parar serviços
docker-compose -f docker-compose.prod.yml down

# 2. Voltar versão anterior
git checkout <version-anterior>

# 3. Restaurar backup se necessário
docker exec -i auditoria-postgres psql -U auditoria_user auditoria_fiscal_prod < backups/backup_anterior.sql

# 4. Restart
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔍 VERIFICAÇÃO PÓS-DEPLOY

### ✅ Checklist de Verificação

#### 🌐 Frontend
- [ ] Site carrega: https://auditoria-fiscal.com
- [ ] Login funciona
- [ ] Dashboard exibe dados
- [ ] Navegação entre páginas
- [ ] Responsividade mobile

#### 🔌 APIs
- [ ] Gateway responde: https://auditoria-fiscal.com/api/health
- [ ] Autenticação: POST /api/auth/login
- [ ] Empresas: GET /api/tenants/
- [ ] Produtos: GET /api/products/
- [ ] Classificação: POST /api/classification/

#### 💾 Banco de Dados
- [ ] PostgreSQL conectando
- [ ] Tabelas criadas
- [ ] Dados de exemplo inseridos
- [ ] Backups funcionando

#### 🤖 IA/Ollama
- [ ] Ollama respondendo: http://localhost:11434/api/version
- [ ] Modelos carregados
- [ ] Classificação funcionando
- [ ] Performance adequada

#### 📊 Monitoramento
- [ ] Grafana: http://auditoria-fiscal.com:3000
- [ ] Prometheus: http://auditoria-fiscal.com:9090
- [ ] Métricas coletadas
- [ ] Alertas configurados

### 🧪 Testes de Produção

```bash
# Script de teste automatizado
cd deploy/production

# 1. Teste de conectividade
curl -f https://auditoria-fiscal.com/health

# 2. Teste de API
curl -X POST https://auditoria-fiscal.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 3. Teste de classificação
curl -X POST https://auditoria-fiscal.com/api/classification/classify \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"description": "Notebook Dell"}'

# 4. Teste de carga (opcional)
ab -n 100 -c 10 https://auditoria-fiscal.com/api/health
```

---

## 🚨 TROUBLESHOOTING

### ❌ Problemas Comuns

#### 🔴 Container não inicia
```bash
# Verificar logs
docker-compose -f docker-compose.prod.yml logs <service-name>

# Verificar recursos
docker stats

# Reiniciar serviço específico
docker-compose -f docker-compose.prod.yml restart <service-name>
```

#### 🔴 Banco de dados não conecta
```bash
# Verificar status PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Verificar logs
docker-compose -f docker-compose.prod.yml logs postgres

# Conectar manualmente
docker-compose -f docker-compose.prod.yml exec postgres psql -U auditoria_user auditoria_fiscal_prod
```

#### 🔴 Ollama sem GPU
```bash
# Verificar NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Verificar configuração Docker
cat /etc/docker/daemon.json

# Restart Docker se necessário
sudo systemctl restart docker
```

#### 🔴 SSL/Certificados
```bash
# Verificar certificados
openssl x509 -in deploy/production/ssl/auditoria-fiscal.com.crt -text -noout

# Renovar Let's Encrypt
sudo certbot renew --dry-run

# Testar SSL
curl -I https://auditoria-fiscal.com
```

### 📞 Suporte
- **Logs**: `deploy/production/logs/`
- **Monitoramento**: Grafana dashboards
- **Documentação**: README.md e arquivos docs/

---

## 🎉 CONCLUSÃO

O Sistema de Auditoria Fiscal ICMS está **100% pronto para produção** com:

- ✅ **7 microserviços** funcionais e escaláveis
- ✅ **Frontend React** responsivo e completo
- ✅ **IA multi-agentes** com 8 modelos Ollama
- ✅ **Sistema RAG** com dados NESH 2022
- ✅ **Monitoramento** completo com Grafana/Prometheus
- ✅ **Backup automático** e sistema de recuperação
- ✅ **Segurança** enterprise com SSL e RBAC
- ✅ **Documentação** completa para operação

### 🚀 **O sistema está pronto para transformar a auditoria fiscal com IA!**

---

*Guia gerado em 23/08/2025 - Sistema v4.0 Produção*
