# **Plano de Implementação Detalhado: Fases 3 & 4**

Versão: 3.0 (Consolidada)  
Data: 19 de Agosto de 2025  
Foco: API, Orquestração com LangGraph, Interface Web (React) e Ciclo de Melhoria Contínua.

## **Fase 3: API, Orquestração e Interface Web (6 Semanas)**

**Objetivo:** Construir a ponte entre o poderoso backend de IA e o usuário final, implementando uma API robusta, orquestrando os agentes de forma inteligente e desenvolvendo as funcionalidades essenciais da interface web.

### **Semana 1-2: Desenvolvimento da API com FastAPI**

O foco é expor todas as funcionalidades dos agentes e da gestão de dados através de endpoints seguros e bem definidos.

* **Tarefa 3.1: Módulo de Autenticação e Gestão**  
  * **Endpoints:**  
    * POST /api/v1/token: Login de usuário (retorna token JWT).  
    * POST /api/v1/users: Cadastro de novos usuários.  
    * POST /api/v1/companies: Cadastro de novas empresas a serem auditadas.  
    * GET /api/v1/companies: Listar empresas cadastradas.  
  * **Detalhes:** Implementar schemas Pydantic para validação de entrada/saída. A segurança será baseada em JWT, conforme protocol\_config.yml.  
* **Tarefa 3.2: Módulo de Ingestão e Classificação**  
  * **Endpoints:**  
    * POST /api/v1/data/import: Endpoint para iniciar a importação de dados de um banco de dados externo (PostgreSQL/SQL Server). O corpo da requisição conterá as credenciais do banco de dados da empresa e o empresa\_id.  
    * POST /api/v1/classify/batch: Inicia o processo de classificação em lote. Recebe empresa\_id e parâmetros (ex: limit, status). Retorna um job\_id para acompanhamento.  
    * GET /api/v1/classify/status/{job\_id}: Retorna o progresso de um lote (ex: { "total": 1000, "processed": 250, "status": "running" }).  
  * **Lógica:** O endpoint de importação utilizará o stock\_adapter.py para executar a consulta SQL \[cite: plano\_enio.docx\] e popular a tabela mercadorias\_a\_classificar.  
* **Tarefa 3.3: Endpoints de Agentes Individuais e Resultados**  
  * **Endpoints:**  
    * GET /api/v1/results/{empresa\_id}: Retorna os produtos classificados com paginação e filtros (por status, NCM, etc.).  
    * GET /api/v1/results/details/{mercadoria\_id}: Retorna a trilha de auditoria completa para um produto, com todas as decisões dos agentes, contextos RAG e justificativas.  
    * POST /api/v1/agents/aggregate: Endpoint para executar apenas o AggregationAgent sobre os dados de uma empresa.  
  * **Objetivo:** Atender à necessidade de executar agentes individualmente e fornecer dados detalhados para a tela de revisão \[cite: plano\_auditoria\_icms.md\].

### **Semana 3-4: Orquestração dos Agentes com LangGraph**

O ManagerAgent usará o LangGraph para executar os fluxos de trabalho de maneira controlada e resiliente.

* **Tarefa 3.4: Implementação dos Workflows ConfirmationFlow e DeterminationFlow**  
  * **Estrutura:** Utilizar o base\_workflow.py para criar dois grafos distintos.  
  * **Lógica Condicional:**  
    1. **Início:** O ManagerAgent classifica a tarefa como "confirmação" (se NCM/CEST presentes) ou "determinação" (se ausentes) \[cite: Plano\_2.md\].  
    2. **Nós:** Cada agente (EnrichmentAgent, NCMAgent, CESTAgent, ReconciliationAgent) será um nó no grafo.  
    3. **Arestas (Edges):** A transição entre os nós será condicional.  
       * Se a confiança do NCMAgent for \< 0.7, o estado do produto na tabela classificacoes muda para REVISAO\_MANUAL e o fluxo para aquele produto é encerrado.  
       * Se ocorrer um erro em qualquer agente, o status muda para ERRO com a respectiva mensagem de log.  
  * **Integração:** O endpoint POST /api/v1/classify/batch irá instanciar o ManagerAgent, que por sua vez invocará o workflow apropriado do LangGraph para cada produto.

### **Semana 5-6: Desenvolvimento do Frontend (React)**

Construir a interface que permitirá ao usuário interagir com o sistema.

* **Tarefa 3.5: Estrutura do App e Páginas Iniciais**  
  * **Tecnologias:** React com TypeScript, Material-UI para componentes, Axios para chamadas de API.  
  * **Páginas:** Implementar as telas de **Login**, **Dashboard Principal** (com botões para as principais funcionalidades), e **Gestão de Empresas/Usuários**.  
* **Tarefa 3.6: Módulo de Importação e Classificação**  
  * **UI:** Criar um formulário para o usuário inserir as credenciais do banco de dados da empresa, selecionar a empresa no sistema e definir a quantidade de produtos a classificar.  
  * **Interação:** Ao submeter, o frontend chamará os endpoints /api/v1/data/import e, em seguida, /api/v1/classify/batch. Uma barra de progresso utilizará o endpoint de status para feedback em tempo real.  
* **Tarefa 3.7: Dashboard de Resultados**  
  * **UI:** Desenvolver uma tabela paginada e com filtros para exibir os dados da tabela classificacoes.  
  * **Colunas:** ID Produto, Descrição Original, NCM Sugerido, CEST Sugerido, Confiança, Status.  
  * **Ações:** Cada linha terá um botão "Revisar", que levará o usuário à tela de revisão detalhada (a ser implementada na Fase 4).

## **Fase 4: Funcionalidades Avançadas e Produção (5 Semanas)**

**Objetivo:** Fechar o ciclo de feedback com a intervenção humana, aprimorar continuamente a IA com o Golden Set e preparar a aplicação para o deploy final.

### **Semana 7-8: Interface de Revisão Humana e Golden Set**

Esta é a funcionalidade central para o ciclo de melhoria contínua.

* **Tarefa 4.1: Desenvolvimento da Página de Revisão Detalhada**  
  * **Layout:** A tela será dividida em três seções principais:  
    1. **Dados do Produto:** Exibição dos dados originais (descricao\_original, ncm\_informado, etc.).  
    2. **Classificação do Agente:** Campos de formulário pré-preenchidos com os resultados dos agentes (ncm\_determinado, cest\_determinado), permitindo a edição pelo usuário.  
    3. **Trilha de Auditoria e Evidências:** Uma visualização em timeline ou em abas que mostra, para cada agente:  
       * A decisão tomada.  
       * A justificativa completa.  
       * **O contexto RAG utilizado**, exibindo os trechos de texto exatos e a referência do arquivo de origem (arquivo, capitulo, chunk\_id) \[cite: plano\_auditoria\_icms.md\].  
  * **Ações do Usuário:**  
    * Botão **"Confirmar Classificação"**: Mantém a sugestão do agente.  
    * Botão **"Corrigir e Enviar para Golden Set"**: Salva as alterações do usuário e envia os dados corrigidos para a tabela golden\_set através de um novo endpoint POST /api/v1/golden-set.  
* **Tarefa 4.2: Página de Gestão do Golden Set**  
  * **UI:** Criar uma interface web para visualizar, editar e remover entradas da tabela golden\_set.  
  * **Funcionalidade:** Permitir que especialistas fiscais façam a curadoria direta da base de conhecimento mais valiosa do sistema \[cite: plano\_enio.docx\].

### **Semana 9: Relatórios e Pipeline de Melhoria Contínua**

* **Tarefa 4.3: Relatório de Agregação**  
  * **UI:** Desenvolver uma nova página no frontend que exibe os resultados do AggregationAgent.  
  * **Conteúdo:** A página mostrará uma lista de "produtos mestre" e, para cada um, os produtos com produto\_id diferentes que foram agrupados, o critério utilizado (ex: "similaridade de descrição \> 95%") e a confiança da agregação.  
* **Tarefa 4.4: Realimentação do RAG com o Golden Set**  
  * **Backend:** Modificar o RetrievalTools para que, antes de realizar a busca vetorial, ele primeiro consulte a tabela golden\_set por similaridade de descrição. Se um resultado de alta confiança for encontrado, ele será usado como contexto prioritário.  
  * **Manutenção:** Criar um script (scripts/retrain\_embeddings.py) que pode ser executado offline para fazer o fine-tuning do modelo de embeddings usando os dados do Golden Set, melhorando a precisão do RAG ao longo do tempo.

### **Semana 10-11: Finalização e Preparação para Produção**

* **Tarefa 4.5: Testes Integrados e End-to-End**  
  * **Ação:** Escrever e executar testes que simulem o fluxo completo do usuário: login, importação, classificação em lote, revisão de um item, correção e verificação de sua inserção no Golden Set.  
* **Tarefa 4.6: Empacotamento Docker e Documentação Final**  
  * **Ação:** Revisar e finalizar o docker-compose.yml, garantindo que todos os serviços (frontend, backend, databases) estão interligados e configurados corretamente para um ambiente de produção.  
  * **Documentação:**  
    * Gerar a documentação da API usando as funcionalidades automáticas do FastAPI (Swagger/OpenAPI).  
    * Escrever um DEPLOYMENT\_GUIDE.md com instruções para configurar e iniciar a aplicação.  
    * Conforme solicitado \[cite: plano\_enio.docx\], criar a pasta documentos/ e organizar todos os arquivos .md do projeto com prefixos numéricos para manter um histórico claro.  
    * Atualizar o README.md principal para ser o sumário consolidado de todo o projeto.