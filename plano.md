# **Plano de Projeto Mestre: Sistema de Auditoria Fiscal v15.0 (Ecossistema Completo)**

Versão: 15.0 (Unificada e Detalhada com Golden Set Humano)  
Data: 18 de Agosto de 2025

### **1\. Visão Geral e Objetivos**

#### **1.1. Sumário Executivo**

Este documento é o plano mestre unificado para o desenvolvimento de um **Sistema Multiagente de Auditoria de ICMS**, uma aplicação web completa projetada para otimizar a classificação fiscal de mercadorias (NCM e CEST). O sistema combina uma interface de usuário intuitiva com um backend robusto, baseado em uma arquitetura de IA 100% local.

O núcleo da solução é um sistema **Multiagente Hierárquico com Adaptive RAG**, composto por agentes especialistas que realizam tarefas de enriquecimento, classificação e agregação de dados. A aplicação será totalmente auditável, registrando cada decisão dos agentes, e contará com um banco de dados multiempresa e um **Golden Set** curado por humanos, que servirá para realimentar e aprimorar continuamente a precisão do RAG.

#### **1.2. Objetivos do Projeto**

* **Precisão:** Atingir \>90% de acurácia na confirmação/determinação de NCM e CEST.  
* **Auditabilidade:** Geração de trilhas de decisão completas para cada operação dos agentes.  
* **Autonomia:** Execução totalmente local, sem dependência de serviços em nuvem.  
* **Eficiência:** Reduzir em até 70% o esforço humano de classificação manual.  
* **Usabilidade:** Fornecer uma interface web clara e funcional que suporte todo o fluxo de trabalho de auditoria.

### **2\. Arquitetura da Solução e Ecossistema**

#### **2.1. Arquitetura Geral**

O sistema é composto por três camadas principais:

1. **Frontend (Interface Web):** Uma aplicação web single-page (React).  
2. **Backend (API e Orquestração):** Uma API FastAPI que gerencia a lógica de negócio, autenticação e a orquestração dos agentes.  
3. **Core de IA (Agentes e Base de Conhecimento):** O sistema de agentes LangGraph e a base de conhecimento tri-híbrida.

#### **2.2. Infraestrutura e Tecnologias (Stack Local)**

* **Frontend:** React.  
* **Backend & Orquestração:** Python 3.10+, FastAPI, LangChain/LangGraph.  
* **LLM Local:** Ollama servindo Llama 3 8B/70B.  
* **Bancos de Dados:**  
  * **BD da Aplicação (Multiempresa):** PostgreSQL.  
  * **BD de Conhecimento (RAG):** FAISS (Vetorial), Neo4j (Grafo).  
* **Embeddings:** BAAI/bge-m3 (SentenceTransformers).  
* **Execução:** Docker \+ Docker Compose.

### **3\. Estrutura de Código do Projeto (Padrão Agentic)**

/auditoria\_fiscal\_icms  
│  
├── /data/  
│   ├── /raw/  
│   └── /processed/  
│  
├── /configs/  
│   ├── model\_config.yml  
│   └── protocol\_config.yml  
│  
├── /src/auditoria\_icms/  
│   ├── /agents/  
│   │   ├── base\_agent.py  
│   │   ├── manager\_agent.py  
│   │   ├── enrichment\_agent.py  
│   │   ├── ncm\_agent.py  
│   │   ├── cest\_agent.py  
│   │   └── reconciliation\_agent.py  
│   │  
│   ├── /workflows/  
│   │   ├── base\_workflow.py  
│   │   ├── confirmation\_flow.py  
│   │   └── determination\_flow.py  
│   │  
│   ├── /tools/  
│   │   ├── retrieval\_tools.py  
│   │   └── database\_tools.py  
│   │  
│   ├── /data\_processing/  
│   │   ├── structured\_loader.py  
│   │   ├── document\_extractor.py  
│   │   ├── data\_enrichment.py  
│   │   ├── vector\_builder.py  
│   │   └── graph\_builder.py  
│   │  
│   ├── /api/  
│   │   ├── /endpoints/  
│   │   └── main.py  
│   │  
│   ├── /database/  
│   │   └── models.py  
│   │  
│   └── /core/  
│  
├── /tests/  
│  
├── /scripts/  
│   └── benchmark\_agents.py  
│  
├── docker-compose.yml  
└── requirements.txt

### **4\. Frontend e Interface do Usuário (UI)**

* **Página 1: Login**  
* **Página 2: Gestão de Cadastros (Usuários e Empresas)**  
* **Página 3: Painel de Controle**  
* **Página 4: Importação e Gestão de Dados**  
* **Página 5: Dashboard de Classificação**  
* **Página 6: Visualização e Revisão**  
* **Página 7: Gestão do Golden Set**  
  * Interface dedicada para visualizar, editar e criar novas entradas no Golden Set.  
  * Um formulário permitirá que um usuário humano crie uma entrada completa, preenchendo os campos: descrição original, descrição enriquecida, gtin, ncm confirmado e cest confirmado.  
  * Esta interface será a principal ferramenta para a curadoria humana que realimentará o sistema.

### **5\. Banco de Dados da Aplicação (PostgreSQL)**

O banco de dados principal irá armazenar os dados operacionais de forma isolada por empresa.

* **Schema Principal:**  
  * usuarios, empresas, usuario\_empresa\_acesso.  
  * mercadorias\_a\_classificar: (id, **empresa\_id**, produto\_id\_origem, descricao\_original, ...).  
  * classificacoes: (id, **mercadoria\_id**, ncm\_determinado, cest\_determinado, justificativa\_ncm, contexto\_ncm, justificativa\_cest, ...).  
  * agregacoes: (id, **empresa\_id**, produto\_conceitual\_id, mercadoria\_id).  
  * golden\_set: (id, descricao\_produto, **descricao\_enriquecida**, **gtin**, ncm\_correto, cest\_correto, fonte\_usuario, fonte\_empresa, data\_confirmacao).

### **6\. Plano de Execução Detalhado**

#### **Fase 1: Construção da Base de Conhecimento e Estrutura (5 Semanas)**

* **Semana 1: Setup e Estrutura de Dados**  
  * **T1.1:** Configurar ambiente, Git, Docker, requirements.txt.  
  * **T1.2:** Modelar e implementar o schema do **Banco de Dados da Aplicação** (PostgreSQL), incluindo a tabela golden\_set detalhada.  
* **Semana 2: Ingestão de Dados Estruturados e Não-Estruturados**  
  * **T2.1:** Implementar structured\_loader.py para as fontes de conhecimento RAG.  
  * **T2.2:** Implementar document\_extractor.py para NESH e Regras Gerais.  
* **Semana 3: Enriquecimento e Vetorização**  
  * **T3.1:** Criar data\_enrichment.py.  
  * **T3.2:** Criar vector\_builder.py.  
* **Semana 4: Grafo e Ontologias**  
  * **T4.1:** Criar graph\_builder.py para popular Neo4j, incluindo a modelagem das relações **SKOS**.  
* **Semana 5: Validação e Resolução de Entidades**  
  * **T5.1:** Implementar o script de resolução de entidades em batch.  
  * **T5.2:** Criar validate\_data.py e montar a versão inicial do "Golden Set". Executar avaliação baseline com RAGAS.

#### **Fase 2: Desenvolvimento do Backend e Agentes (5 Semanas)**

* **Semanas 6-7:** Implementar os agentes especialistas e o ManagerAgent.  
* **Semanas 8-9:** Implementar o retrieval\_tools.py.  
* **Semana 10:** Desenvolver a **API com FastAPI**.

#### **Fase 3: Orquestração e Desenvolvimento do Frontend (4 Semanas)**

* **Semanas 11-12:** Criar os workflows (confirmation\_flow, determination\_flow) em LangGraph.  
* **Semanas 13-14:** Desenvolver as páginas principais do frontend e integrá-las com a API.

#### **Fase 4: Integração Final, Avaliação e Aprimoramento (3 Semanas)**

* **Semana 15:** Integrar o frontend com os workflows dos agentes, desenvolvendo o dashboard de classificação e a tela de revisão.  
* **Semana 16:** Implementar o pipeline de avaliação contínua. Empacotar a aplicação em contêineres Docker.  
* **Semana 17:** Implementar a interface de feedback e o pipeline para **Aprimoramento Iterativo (RLHF)**. As classificações confirmadas na "Página 7" serão usadas para popular o golden\_set, que por sua vez será usado como fonte prioritária de exemplos para os agentes (few-shot learning) e para o fine-tuning supervisionado.