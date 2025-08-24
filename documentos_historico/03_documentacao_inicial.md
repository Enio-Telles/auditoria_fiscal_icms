# Sistema de Auditoria Fiscal ICMS v15.0 🧾⚖️

Sistema Multiagente de Auditoria de ICMS com IA 100% Local para classificação automática de produtos na tabela NCM e CEST.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

## 🎯 Visão Geral

Este sistema foi desenvolvido para automatizar e otimizar a classificação fiscal de mercadorias, combinando:

- **🤖 Sistema Multiagente Hierárquico** com Adaptive RAG
- **🧠 IA 100% Local** usando Ollama + Llama 3.1
- **📊 Base de Conhecimento Tri-Híbrida** (Relacional + Vetorial + Grafo)
- **🔍 Auditabilidade Completa** com trilhas de decisão
- **🌐 Interface Web Moderna** em React
- **📈 Golden Set Humano** para aprimoramento contínuo

### Objetivos
- ✅ **Precisão >90%** na classificação NCM/CEST
- ✅ **Redução de 70%** no esforço manual
- ✅ **Execução 100% local** sem dependência de nuvem
- ✅ **Auditabilidade completa** de todas as decisões
- ✅ **Preparado para integração** com sistemas de análise de estoques

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                        │
│  Login │ Cadastros │ Dashboard │ Classificação │ Golden Set │
└─────────────────────┬───────────────────────────────────────┘
                      │ API REST
┌─────────────────────▼───────────────────────────────────────┐
│                  BACKEND (FastAPI)                         │
│              Orquestração + Autenticação                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│               SISTEMA MULTIAGENTE                          │
│  ManagerAgent │ EnrichmentAgent │ NCMAgent │ CESTAgent      │
│              ReconciliationAgent                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│           BASE DE CONHECIMENTO TRI-HÍBRIDA                 │
│  PostgreSQL │ FAISS (Vetorial) │ Neo4j (Grafo)             │
│                  Ollama (LLM Local)                        │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Instalação e Configuração

### Pré-requisitos
- Python 3.10+
- Docker e Docker Compose
- Git
- 16GB RAM (recomendado para modelos LLM)

### 1. Clone o Repositório
```bash
git clone <repository-url>
cd auditoria_fiscal_icms
```

### 2. Configure o Ambiente
```bash
# Criar ambiente virtual
conda create -n auditoria-fiscal python=3.11 -y
conda activate auditoria-fiscal

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configurar Dados
```bash
# Criar estrutura de diretórios
mkdir -p data/raw data/processed

# Colocar arquivos fonte em data/raw:
# - Tabela_NCM.xlsx
# - conv_142_formatado.json
# - CEST_RO.xlsx
# - produtos_selecionados.json
```

### 4. Executar com Docker
```bash
# Inicializar todos os serviços
docker-compose up -d

# Preparar modelos LLM (primeira execução)
docker-compose run model_setup
```

### 5. Configurar Base de Conhecimento
```bash
# Executar carregamento de dados
python src/auditoria_icms/data_processing/structured_loader.py
```

## 📁 Estrutura do Projeto

```
auditoria_fiscal_icms/
│
├── data/                           # Dados do sistema
│   ├── raw/                       # Arquivos fonte (NCM, CEST, etc.)
│   └── processed/                 # Base de conhecimento processada
│
├── configs/                        # Configurações
│   ├── model_config.yml          # Config. de IA/LLM
│   └── protocol_config.yml       # Config. de API/Integração
│
├── src/auditoria_icms/            # Código fonte principal
│   ├── agents/                    # Sistema multiagente
│   │   ├── base_agent.py         # Classe base dos agentes
│   │   ├── manager_agent.py      # Agente gerenciador
│   │   ├── enrichment_agent.py   # Agente de enriquecimento
│   │   ├── ncm_agent.py          # Agente classificador NCM
│   │   ├── cest_agent.py         # Agente classificador CEST
│   │   └── reconciliation_agent.py # Agente de reconciliação
│   │
│   ├── workflows/                 # Workflows LangGraph
│   │   ├── base_workflow.py      # Workflow base
│   │   ├── confirmation_flow.py   # Fluxo de confirmação
│   │   └── determination_flow.py  # Fluxo de determinação
│   │
│   ├── tools/                     # Ferramentas de busca
│   │   ├── retrieval_tools.py    # Busca tri-híbrida
│   │   └── database_tools.py     # Ferramentas de BD
│   │
│   ├── data_processing/           # Processamento de dados
│   │   ├── structured_loader.py  # Carregador de dados estruturados
│   │   ├── document_extractor.py # Extrator de documentos
│   │   ├── data_enrichment.py    # Enriquecimento de dados
│   │   ├── vector_builder.py     # Construtor de índices vetoriais
│   │   └── graph_builder.py      # Construtor de grafos
│   │
│   ├── api/                       # API FastAPI
│   │   ├── endpoints/            # Endpoints da API
│   │   └── main.py               # Aplicação principal
│   │
│   ├── database/                  # Modelos de banco
│   │   └── models.py             # Modelos SQLAlchemy
│   │
│   ├── integrations/             # Integrações externas
│   │   └── stock_analysis/       # Sistema de análise de estoques
│   │       └── stock_adapter.py  # Adaptador para sistemas de estoque
│   │
│   └── core/                     # Utilitários centrais
│
├── frontend/                      # Interface React (futuro)
├── tests/                         # Testes automatizados
├── scripts/                       # Scripts utilitários
├── docs/                          # Documentação
│
├── docker-compose.yml             # Orquestração Docker
├── requirements.txt               # Dependências Python
└── README.md                      # Este arquivo
```

## 🤖 Sistema de Agentes

### Agentes Especializados

1. **ManagerAgent** 🎯
   - Orquestra todo o fluxo de classificação
   - Coordena agentes especialistas
   - Toma decisões de nível superior

2. **EnrichmentAgent** 📝
   - Enriquece descrições de produtos
   - Adiciona contexto técnico e regulamentar
   - Melhora qualidade da classificação

3. **NCMAgent** 🏷️
   - Especialista em classificação NCM
   - Busca hierárquica (Capítulo → Item)
   - Múltiplas estratégias de classificação

4. **CESTAgent** ⚡
   - Especialista em classificação CEST
   - Análise de substituição tributária
   - Correspondência de padrões NCM

5. **ReconciliationAgent** ⚖️
   - Validação cruzada NCM ↔ CEST
   - Resolução de conflitos
   - Análise de consistência final

### Workflows Implementados

- **Confirmation Flow**: Confirma/valida classificações existentes
- **Determination Flow**: Determina classificações do zero
- **Validation Flow**: Valida resultados contra Golden Set

## 📊 Base de Conhecimento

### Fontes de Dados Suportadas
- **Tabela NCM** (Nomenclatura Comum do Mercosul)
- **CEST Convênio 142** (Regras nacionais)
- **CEST Rondônia** (Regras estaduais)
- **Produtos Exemplo** (Golden Set)
- **NESH** (Notas Explicativas - futuro)

### Arquitetura Tri-Híbrida
1. **Relacional (SQLite/PostgreSQL)**: Dados estruturados, regras
2. **Vetorial (FAISS)**: Busca semântica por similaridade
3. **Grafo (Neo4j)**: Relações ontológicas, hierarquias

## 🔗 Integração com Sistemas de Estoques

O sistema está preparado para integração futura com sistemas de análise de estoques:

### Funcionalidades Planejadas (v2.0)
- ✅ Interface padronizada para múltiplos ERPs
- ✅ Adaptadores para sistemas específicos
- ✅ Sincronização automática de classificações
- ✅ Suporte a formatos XML, JSON, CSV
- ✅ API REST para integração externa

### Exemplo de Uso
```python
from src.auditoria_icms.integrations import StockIntegrationManager

# Configurar integração
manager = StockIntegrationManager(config)

# Analisar itens de estoque
results = await manager.analyze_stock_items("sistema_erp")

# Sincronizar classificações
await manager.sync_classifications("sistema_erp", results)
```

## 🎮 Interface Web

### Páginas Implementadas
1. **Login** - Autenticação de usuários
2. **Gestão de Cadastros** - Usuários e empresas
3. **Painel de Controle** - Dashboard principal
4. **Importação de Dados** - Upload de planilhas
5. **Dashboard de Classificação** - Análise em tempo real
6. **Visualização e Revisão** - Resultados detalhados
7. **Gestão do Golden Set** - Curadoria humana

### Tecnologias Frontend
- React 18+ com TypeScript
- Material-UI para componentes
- Recharts para visualizações
- React Query para cache de API

## 📈 Avaliação e Métricas

### Métricas Automáticas
- **Accuracy**: Precisão geral das classificações
- **Precision/Recall**: Por categoria de produto
- **F1-Score**: Harmonia entre precisão e recall
- **Confidence Distribution**: Distribuição de confianças

### Avaliação RAGAS
- **Faithfulness**: Fidelidade às fontes
- **Answer Relevancy**: Relevância das respostas
- **Context Precision**: Precisão do contexto recuperado
- **Context Recall**: Cobertura do contexto

## 🔧 Configuração Avançada

### Configuração de Modelos (model_config.yml)
```yaml
llm:
  provider: "ollama"
  models:
    primary: "llama3.1:8b"
    fallback: "llama3.1:70b"

embeddings:
  model_name: "BAAI/bge-m3"

rag:
  similarity_threshold: 0.7
  top_k_vector: 10
```

### Configuração de Protocolos (protocol_config.yml)
```yaml
api:
  host: "0.0.0.0"
  port: 8000

database:
  postgresql:
    host: "localhost"
    port: 5432
    database: "auditoria_fiscal"

integrations:
  stock_analysis:
    enabled: false  # Habilitar na v2.0
```

## 🧪 Testes e Validação

### Executar Testes
```bash
# Testes unitários
pytest tests/unit/

# Testes de integração
pytest tests/integration/

# Testes end-to-end
pytest tests/e2e/

# Benchmark de agentes
python scripts/benchmark_agents.py
```

### Validação de Dados
```bash
# Validar base de conhecimento
python scripts/validate_knowledge_base.py

# Avaliar com RAGAS
python scripts/evaluate_rag.py
```

## 📚 Documentação Adicional

- [Plano de Implementação Detalhado](docs/plano_implementacao.md)
- [Guia de Desenvolvimento](docs/guia_desenvolvimento.md)
- [API Reference](docs/api_reference.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contribuição

### Roadmap v2.0
- [ ] Integração completa com sistemas de estoque
- [ ] Interface gráfica para visualização de grafos
- [ ] Fine-tuning de modelos locais
- [ ] Suporte a múltiplos estados (além de RO)
- [ ] API pública para terceiros
- [ ] Módulo de relatórios avançados

### Como Contribuir
1. Fork o projeto
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

## 👥 Equipe

- **Desenvolvedor Principal**: [Seu Nome]
- **Especialista Fiscal**: [Nome do Especialista]
- **Arquiteto de IA**: [Nome do Arquiteto]

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/auditoria_fiscal_icms/issues)
- **Discussões**: [GitHub Discussions](https://github.com/seu-usuario/auditoria_fiscal_icms/discussions)
- **Email**: suporte@auditoriafiscal.com

---

**Sistema de Auditoria Fiscal ICMS v15.0** - Automatizando a classificação fiscal com IA 100% local 🤖⚖️
