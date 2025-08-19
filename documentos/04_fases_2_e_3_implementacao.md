# **Plano de Implementação Aprimorado: Fases 2 e 3**

## **1\. Análise da Fase 1 e Pontos de Melhoria**

A implementação da Fase 1 no repositório estabeleceu com sucesso a base do projeto. Os módulos em src/auditoria\_icms/data\_processing demonstram a capacidade de carregar, processar e estruturar os dados fiscais. A arquitetura de agentes em src/auditoria\_icms/agents está iniciada.

**Observação Estratégica:** A consulta SQL fornecida é um excelente ponto de partida para a identificação de duplicatas exatas (descricao\_produto), mas a lógica para similaridade e correspondência por codigo\_produto precisa ser implementada por agentes especializados, como proposto abaixo.

## **2\. Visão Geral das Fases 2 e 3**

O foco agora é dar vida aos agentes de IA, orquestrar suas ações e garantir que cada passo seja totalmente auditável. Para isso, o sistema se conectará aos bancos de dados de cada empresa para processar os produtos.

### **Arquitetura Proposta:**

1. **Bancos de Dados Operacionais (Multi-Tenant):** Cada empresa cliente possui seu próprio banco de dados com o cadastro de produtos. O sistema não armazena esses dados, mas se conecta a eles para leitura e atualização.  
2. **Módulo de Ingestão de Dados (Adaptador):** Um componente flexível responsável por se conectar aos diferentes bancos de dados das empresas, executar consultas para extrair os produtos e carregá-los em uma estrutura de trabalho temporária para processamento.  
3. **Banco de Dados do Golden Set (PostgreSQL):** Uma base de dados **separada e centralizada**, servindo como a fonte de verdade para a IA, compartilhada entre todos os tenants.  
4. **Agentes Especialistas:** Cada agente terá uma única responsabilidade (enriquecer, classificar NCM, classificar CEST, identificar duplicatas).  
5. **Agente Gerente (Orquestrador):** O ManagerAgent controlará o fluxo de trabalho.  
6. **RAG (Retrieval-Augmented Generation):** Será a principal ferramenta dos agentes NCMAgent e CESTAgent para consultar a base de conhecimento e fundamentar suas decisões.  
7. **Processamento Isolado por Empresa:** Todo o pipeline, desde a classificação até a identificação de produtos idênticos, é executado no contexto de uma única empresa por vez. A agregação de produtos é contida dentro do banco de dados de cada cliente, garantindo a integridade dos dados para análises subsequentes, como a de estoques.

## **3\. Plano Detalhado da Fase 2: Backend, Banco de Dados e Agentes de IA**

**Objetivo:** Implementar o núcleo lógico do sistema, habilitando os agentes a se conectarem, processarem, classificarem e auditarem os dados dos produtos de diferentes empresas.

### **Tarefa 2.1: Estrutura de Processamento e Auditoria**

Para operar, o sistema precisa de uma estrutura de trabalho e de um local para armazenar os logs de auditoria. Isso pode ser em um banco de dados interno do próprio sistema.

**Ações:**

1. **Criar a tabela auditoria\_agentes\_log (no DB interno do sistema):**  
   * log\_id (SERIAL PRIMARY KEY)  
   * empresa\_id (VARCHAR): Identificador da empresa sendo processada.  
   * produto\_id\_origem (VARCHAR): A chave primária do produto no banco de dados da empresa.  
   * agente\_nome (VARCHAR)  
   * timestamp (TIMESTAMP)  
   * acao\_realizada (VARCHAR)  
   * dados\_entrada (JSONB)  
   * dados\_saida (JSONB)  
   * justificativa\_rag (TEXT)  
   * query\_rag (TEXT)  
2. **Desenvolvimento do Módulo de Ingestão de Dados:**  
   * Criar uma classe ou conjunto de funções (evoluindo o stock\_adapter.py) que:  
     * Recebe as credenciais de conexão de um banco de dados de uma empresa.  
     * Executa a consulta de extração de produtos (a consulta SQL que você forneceu é um exemplo perfeito).  
     * Retorna os dados em um formato padronizado (ex: uma lista de objetos Pydantic ou um DataFrame Pandas) para os agentes processarem.  
   * O sistema irá adicionar/atualizar colunas no banco de dados da **empresa cliente** para armazenar os resultados (descricao\_enriquecida, ncm\_sugerido, status\_processamento, etc.). Isso requer que o script de setup do cliente adicione essas colunas à tabela produto existente.

### **Tarefa 2.2: Implementação e Refinamento dos Agentes**

* **EnrichmentAgent, NCMAgent, CESTAgent:** A lógica permanece a mesma, operando sobre os dados extraídos pelo Módulo de Ingestão e consultando o Golden Set para validações.  
* **ReconciliationAgent (Agente de Identificação de Duplicatas):**  
  * **Escopo de Atuação:** É crucial notar que este agente opera **exclusivamente** dentro do conjunto de dados da empresa que está sendo processada. A busca por duplicatas e a agregação de produtos (definindo o id\_produto\_mestre) não cruzam as fronteiras entre empresas. Isso garante que a análise de estoque posterior seja consistente com o cadastro de cada empresa.  
  * **Lógica:** A lógica de três níveis (Match Exato, Código \+ Similaridade, Similaridade Pura) será aplicada apenas aos produtos pertencentes ao empresa\_id em processamento.

### **Tarefa 2.3: Criação e Manutenção do Golden Set Centralizado**

**(Esta tarefa permanece inalterada, pois o Golden Set é, por definição, um recurso centralizado de conhecimento, e não de dados operacionais)**

## **4\. Plano Detalhado da Fase 3: Orquestração e Workflow**

**Objetivo:** Criar um fluxo de trabalho coeso que processe os produtos de ponta a ponta, gerenciando o estado e permitindo a intervenção humana.

### **Tarefa 3.1: Implementação do ManagerAgent com LangGraph**

O ManagerAgent será o cérebro da operação, implementado como um grafo de estados.

**Grafo de Estados (status\_processamento):**

          \[PENDENTE\]  
              |  
      \[EnrichmentAgent\]  
              |  
         \[ENRIQUECIDO\]  
              |  
          \[NCMAgent\]  
              |  
      \[NCM\_CLASSIFICADO\]  
              |  
         \[CESTAgent\]  
              |  
      \[CEST\_CLASSIFICADO\]  
              |  
   \[ReconciliationAgent\]  
              |  
         \[CONCLUIDO\]

**Ações:**

1. **Definir os Nós do Grafo:** Cada nó corresponde a uma chamada de um agente especialista.  
2. **Definir as Arestas Condicionais:** A transição entre os nós dependerá do resultado.  
   * Se NCMAgent retornar baixa confiança (\< 0.7), o estado pode mudar para REVISAO\_MANUAL.  
   * Se ocorrer um erro, o estado muda para ERRO.  
3. **Implementar o ManagerAgent:**  
   * Recebe um lote de produtos **extraídos pelo Módulo de Ingestão de uma única empresa**.  
   * Para cada produto, invoca o grafo do LangGraph.  
   * Ao final, consolida os resultados para atualização em lote no banco de dados da empresa correspondente.

### **Tarefa 3.2: Criação de um Script de Processamento em Lote**

Criar um script principal (ex: run\_batch\_processing.py) que:

1. **Aceita parâmetros de entrada:** empresa\_id e as credenciais de conexão para o banco de dados da empresa.  
2. Usa o **Módulo de Ingestão** para buscar um lote de produtos com status PENDENTE do banco de dados do cliente.  
3. Instancia o ManagerAgent.  
4. Inicia o processamento do lote.  
5. Ao final, atualiza os registros processados no banco de dados do cliente com os novos status e dados.