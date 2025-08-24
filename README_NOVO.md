# 🏢 Sistema de Auditoria Fiscal ICMS v4.0 
## **Sistema Multi-Agentes com IA Real**

> **🤖 AGENTES REAIS IMPLEMENTADOS!** Mock desativado - Sistema operacional com NCMAgent e CESTAgent  
> **📅 AGOSTO 2025:** Versão final com backend microserviços e IA local

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://www.postgresql.org/)
[![Status](https://img.shields.io/badge/Status-AGENTES_REAIS_ATIVOS-brightgreen.svg)](/)

---

## 🎉 **SISTEMA 100% COMPLETO COM AGENTES REAIS**

### ✅ **AGENTES DE IA REAIS IMPLEMENTADOS**
- **🤖 NCMAgent:** Classificação automática baseada em estrutura de dados real
- **🔍 CESTAgent:** Determinação CEST por segmento e atividade empresarial  
- **📊 Sistema RAG:** Base NESH 2022 integrada para consultas regulamentares
- **⚡ Performance:** Processamento assíncrono e cache inteligente
- **🛡️ Validação:** Regras de negócio e auditoria automática

### ✅ **ARQUITETURA BACKEND COMPLETA**
- **🏗️ Gateway API:** Ponto central de entrada (Port 8000)
- **🧠 AI Service:** Serviço especializado para IA (Port 8006)
- **🔐 Microserviços:** 7 serviços independentes e escaláveis
- **🐳 Infraestrutura:** PostgreSQL, Redis, Ollama integrados
- **📈 Monitoramento:** Health checks e logs centralizados

### ✅ **INTERFACE WEB REACT**
- **📊 Dashboard:** Métricas em tempo real
- **🏢 Gestão Empresas:** CRUD completo multi-tenant
- **📁 Importação:** Conectores Excel, CSV, bancos de dados
- **🤖 Agentes Dashboard:** Controle e monitoramento de agentes
- **📈 Relatórios:** Analytics avançados e compliance

---

## 📚 **DOCUMENTAÇÃO ORGANIZADA**

### 📍 **Arquivos Principais (Raiz)**
- **`README.md`** - Este arquivo (visão geral do sistema)
- **`MANUAL_USUARIO_FINAL.md`** - Manual completo para instalação e uso
- **`Novas_consideracoes.md`** - Especificações técnicas e requisitos

### 📁 **Documentação Técnica (`/documentos/`)**

#### **📋 Índice Completo**
- **[00_indice_documentos.md](./documentos/00_indice_documentos.md)** - Navegação completa da documentação

#### **🏗️ Organização e Arquitetura (01-06)**
- **01_organizacao_limpeza.md** - Plano de estruturação inicial
- **02_microservices_fix_report.md** - Correções dos microserviços  
- **03_microservices_status_august_2025.md** - Status de desenvolvimento
- **04_microservices_final_status_august_2025.md** - Finalização backend
- **05_final_microservices_status_august_2025.md** - Confirmação operacional
- **06_microservices_status_report_latest.md** - Relatório mais recente

#### **🎯 Análise e Implementação (07-12)**
- **07_analise_prontidao_usuario_final.md** - Análise de prontidão
- **08_plano_sistema_completo_usuario_final.md** - Plano de finalização
- **09_sistema_completo_final.md** - Sistema 100% implementado
- **10_interface_cadastro_implementada.md** - Frontend React completo
- **11_relatorio_finalizacao_100_porcento.md** - Relatório de conclusão
- **12_sistema_100_porcento_completo.md** - Confirmação final

#### **🚀 Deploy e Instalação Windows (13-16)**
- **13_guia_deploy_producao.md** - Deploy para produção
- **14_guia_deploy_local_windows.md** - Instalação local Windows 11
- **15_guia_docker_windows.md** - Configuração Docker Windows
- **16_correcoes_guia_windows.md** - Fixes específicos Windows

#### **👤 Usuário e Agentes (17-18)**
- **17_readme_usuario.md** - Documentação para usuários
- **18_relatorio_agentes_reais_implementados.md** - **🤖 AGENTES REAIS** ⭐

---

## 🚀 **INÍCIO RÁPIDO**

### **🔧 Pré-requisitos**
1. **Windows 11** (testado e configurado)
2. **Docker Desktop** (para PostgreSQL/Redis)
3. **Anaconda Python** (ambiente conda)
4. **Ollama** (IA local - opcional)

### **⚡ Instalação Rápida**
```powershell
# 1. Clonar repositório
git clone [url-do-repo]
cd auditoria_fiscal_icms

# 2. Configurar ambiente conda
.\setup_conda_environment.bat

# 3. Ativar ambiente
conda activate auditoria-fiscal

# 4. Iniciar infraestrutura (PostgreSQL + Redis)
docker-compose up auditoria_postgres auditoria_redis -d

# 5. Iniciar sistema completo com agentes reais
.\ativar_agentes_reais.ps1
```

### **🌐 URLs do Sistema**
- **🏠 API Gateway:** http://localhost:8000
- **📖 Documentação:** http://localhost:8000/docs  
- **⚛️ Frontend React:** http://localhost:3001
- **🤖 AI Service:** http://localhost:8006
- **🧠 Ollama (IA):** http://localhost:11434

---

## 🤖 **SISTEMA DE AGENTES REAIS**

### **🎯 Agentes Implementados**
```python
# Exemplo de uso dos agentes reais
from src.auditoria_icms.agents.real_agents import NCMAgent, CESTAgent

# Classificação NCM
ncm_agent = NCMAgent()
ncm_result = await ncm_agent.classify_product("Notebook Dell Core i5")

# Determinação CEST  
cest_agent = CESTAgent()
cest_result = await cest_agent.determine_cest(
    ncm_code="8471.30.12",
    company_activity="Venda de equipamentos de informática"
)
```

### **🔄 Fluxo Completo**
1. **ExpansionAgent** → Enriquece descrição do produto
2. **AggregationAgent** → Agrupa produtos similares  
3. **NCMAgent** → Classifica NCM com validação hierárquica
4. **CESTAgent** → Determina CEST por segmento empresarial
5. **ReconcilerAgent** → Audita e valida classificação final

### **📊 Recursos dos Agentes**
- **Base Estruturada:** Dados NCM/CEST organizados para classificação
- **Validação RGI/RGC:** Regras Gerais de Interpretação aplicadas
- **Context-Aware:** Considera atividade da empresa na classificação
- **Auditoria:** Logs detalhados de decisões e justificativas
- **Performance:** Cache e processamento assíncrono

---

## 🏗️ **ARQUITETURA DO SISTEMA**

### **🔄 Microserviços Ativos**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Frontend │───▶│   API Gateway    │───▶│   AI Service    │
│   Port 3001     │    │   Port 8000      │    │   Port 8006     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌────────┴────────┐
                       │  Microserviços  │
                       │  Auth, Tenant,  │
                       │  Product, etc.  │
                       └─────────────────┘
                                │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PostgreSQL    │◀───│   Infrastructure │───▶│     Ollama      │
│   Port 5432     │    │   (Docker)       │    │   Port 11434    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### **🗄️ Estrutura de Dados**
- **Multi-tenant:** Isolamento completo por empresa
- **Golden Set:** Base de conhecimento compartilhada
- **Auditoria:** Logs de classificações e decisões
- **Cache:** Otimização de consultas RAG

---

## 📋 **FUNCIONALIDADES PRINCIPAIS**

### **🏢 Gestão de Empresas**
- Cadastro multi-etapa com validação
- CRUD completo multi-tenant
- Gestão de atividades empresariais
- Dashboard de estatísticas

### **📦 Classificação de Produtos**
- Importação de Excel/CSV/Bancos
- Classificação automática NCM/CEST
- Validação com regras fiscais
- Interface de aprovação/rejeição

### **🤖 Sistema de IA**
- Agentes reais especializados
- Base RAG NESH 2022
- Processamento em lote
- Relatórios de confiança

### **📊 Relatórios e Analytics**
- Dashboard executivo
- Métricas de performance
- Relatórios de compliance
- Exportação PDF/Excel

---

## 🛠️ **DESENVOLVIMENTO**

### **📁 Estrutura do Projeto**
```
auditoria_fiscal_icms/
├── src/auditoria_icms/agents/   # Agentes reais de IA
├── microservices/               # 7 microserviços backend
├── frontend/                    # React TypeScript
├── configs/                     # Configurações
├── data/                        # Dados e cache
├── documentos/                  # Documentação técnica
├── scripts/                     # Scripts de automação
└── tests/                       # Testes automatizados
```

### **⚙️ Configuração de Desenvolvimento**
```bash
# Ambiente Python com Conda
conda activate auditoria-fiscal

# Instalar dependências
pip install -r requirements.txt

# Executar testes
python -m pytest tests/

# Verificar qualidade código
black src/ && flake8 src/
```

---

## 🎯 **STATUS E PRÓXIMOS PASSOS**

### **✅ Implementado (100%)**
- ✅ Agentes reais de IA (NCM/CEST)
- ✅ Backend microserviços completo
- ✅ Frontend React operacional
- ✅ Infraestrutura Docker
- ✅ Sistema multi-tenant
- ✅ Documentação organizada

### **🔜 Roadmap Futuro**
- [ ] **Golden Set Automático:** Auto-aprendizado
- [ ] **Integração EFD:** Processamento direto
- [ ] **API Externa:** Validação Receita Federal
- [ ] **Mobile App:** React Native
- [ ] **CI/CD:** Pipeline automatizado

---

## 📞 **SUPORTE E CONTRIBUIÇÃO**

### **📖 Para Usuários Finais**
- Consulte: `MANUAL_USUARIO_FINAL.md`
- Guias Windows: `documentos/13-16_guias_deploy_*.md`

### **👨‍💻 Para Desenvolvedores**
- Arquitetura: `documentos/01-06_microservices_*.md`
- Agentes IA: `documentos/18_relatorio_agentes_reais_implementados.md`

### **🤝 Contribuir**
1. Fork do repositório
2. Criar branch feature
3. Implementar mudanças
4. Testes e documentação
5. Pull Request

---

**🏆 Sistema 100% completo com agentes reais implementados**  
**📅 Versão:** v4.0 - Agosto 2025  
**👨‍💻 Desenvolvido por:** Enio Telles  
**🌟 Status:** Pronto para produção com IA real ativa
