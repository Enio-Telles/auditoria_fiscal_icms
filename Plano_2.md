# **Plano Mestre v10.0: Sistema de Classificação Fiscal (Confirmar e Determinar)**

Versão: 10.0  
Data: 14 de Agosto de 2025

### **1\. Sumário Executivo**

Este documento detalha a arquitetura final e o fluxo operacional do sistema de IA para classificação fiscal. A Versão 10.0 consolida a arquitetura **Adaptive RAG** em um fluxo de trabalho de duplo propósito: **Confirmar ou Determinar**. O sistema foi projetado para primeiro enriquecer a descrição do produto, depois tentar validar uma classificação fiscal fornecida e, se a classificação for inválida ou ausente, pivotar automaticamente para um modo de determinação analítica. A arquitetura também inclui um processo de enriquecimento da base de conhecimento para identificar e agregar produtos idênticos com descrições diferentes, aumentando a precisão e a consistência.

### **2\. Estrutura de Dados de Entrada**

O sistema opera com base em uma entrada JSON bem definida.

{  
  "produto\_id": 12345,  
  "descricao\_produto": "DIPIRONA SODICA 500 MG C/ 10 COMP",  
  "codigo\_barra": "7891234567890",  
  "codigo\_produto": "SKU-XYZ-001",  
  "ncm": "3004.90.69", // Pode ser nulo ou uma string  
  "cest": "13.001.00", // Pode ser nulo ou uma string  
  "contexto\_empresa": "farmácia"  
}

### **3\. Arquitetura de Agentes e Fluxo de Trabalho Integrado**

O sistema é orquestrado por uma cadeia de agentes inteligentes que executam um plano dinâmico.

#### **Passo 1: Enriquecimento da Descrição**

1. **Agente de Enriquecimento de Descrição (Description Enhancement Agent):** Este é o primeiro agente a atuar. Ele recebe a descricao\_produto bruta e executa as seguintes tarefas:  
   * **Correção e Normalização:** Corrige erros de digitação comuns, expande abreviações (ex: "C/" para "COM") e padroniza a capitalização.  
   * **Extração de Entidades:** Identifica e extrai atributos chave como princípio ativo, dosagem, forma farmacêutica e quantidade.  
   * **Geração de Descrição Enriquecida:** Cria uma nova descrição, mais completa e padronizada, que será usada por todos os agentes subsequentes.  
     * **Exemplo:** "DIPIRONA SODICA 500 MG C/ 10 COMP" \-\> "Medicamento Dipirona Sódica em comprimidos de 500mg, embalagem com 10 unidades."

#### **Passo 2: Análise e Planejamento Inicial**

1. O **Query Classifier Agent** recebe a entrada original e a descrição enriquecida.  
   * Se ncm estiver presente, ele classifica a tarefa como **confirmação**.  
   * Se ncm estiver nulo/ausente, ele classifica a tarefa como **determinação**.  
2. O **Planner Agent** gera um plano de ação com base na classificação.  
   * **Plano de Confirmação:** \["1. Validar NCM.", "2. Validar CEST.", "3. Finalizar."\]  
   * **Plano de Determinação:** \["1. Determinar NCM.", "2. Determinar CEST.", "3. Finalizar."\]

#### **Passo 3.A: Execução do Fluxo de Confirmação**

Este fluxo é executado quando o plano inicial é de confirmação.

1. **Validação do NCM (NCMAgent):**  
   * **Recuperação de Contexto:** O RetrievalToolbox busca informações *exclusivamente* para o NCM fornecido.  
   * **Raciocínio de Validação:** O NCMAgent usa a **descrição enriquecida** para validar o NCM.**Prompt do Agente:** "O produto 'Medicamento Dipirona Sódica em comprimidos...' é corretamente classificado pelo NCM 3004.90.69? Responda com 'Sim' ou 'Não' e justifique."  
   * **Decisão:** Se "Não", o sistema **pivota para o Fluxo de Determinação**.  
2. **Validação do CEST (CESTValidationAgent):**  
   * Ocorre se o NCM for confirmado e um cest for fornecido.  
   * Executa a dupla validação (NCM e Segmento) usando a descrição enriquecida e o contexto da empresa.  
3. **Finalização e Resposta:** O **ReconciliationAgent** compila os resultados e gera o relatório de validação.

#### **Passo 3.B: Execução do Fluxo de Determinação**

Este fluxo é executado se o plano inicial for de determinação ou se houver uma falha na confirmação.

1. **Determinação do NCM (NCMAgent):**  
   * **Recuperação de Candidatos:** O RetrievalToolbox usa a **descrição enriquecida** para realizar uma busca ampla (ex: Recuperação por Fusão) e encontrar NCMs candidatos.  
   * **Raciocínio Analítico:** O NCMAgent executa sua análise em **Cadeia de Pensamento (CoT)** para *deduzir* o NCM mais apropriado.  
2. **Determinação do CEST (CESTValidationAgent):**  
   * **Recuperação de Candidatos:** Com o NCM determinado, o sistema busca todos os CESTs aplicáveis no grafo.  
   * **Raciocínio Analítico:** O CESTValidationAgent itera sobre os candidatos, usando a descrição enriquecida e o contexto da empresa para *selecionar* o CEST correto.  
3. **Finalização e Resposta:** O **ReconciliationAgent** revisa a trilha de raciocínio, garante o grounding e monta a resposta final.

### **4\. Enriquecimento da Base de Conhecimento: Resolução de Entidades de Produto**

Para aumentar a precisão e a consistência, um processo de **Resolução de Entidades** será executado em batch para identificar e agregar produtos que são conceitualmente iguais, mas possuem descrições diferentes. Este processo não ocorre em tempo real, mas enriquece a base de conhecimento que os agentes utilizam.

Estratégia:  
A agregação será baseada na criação de uma "assinatura de produto" única, que normaliza os atributos mais importantes de um item.  
**Processo de Agregação (Batch):**

1. **Extração de Entidades com LLM:** Um processo automatizado irá iterar sobre todas as descrições de produtos na base de dados (produtos\_classificados\_formatado.json, Tabela\_ABC\_Farma...csv). Para cada descrição, um LLM será usado para extrair e normalizar entidades chave, similar ao Description Enhancement Agent.  
   * **Exemplo:**  
     * "DIPIRONA SODICA 500 MG C/ 10 COMP" \-\> {principio\_ativo: "dipirona sódica", dosagem: "500mg", forma: "comprimido", quantidade: "10"}  
     * "ANALGÉSICO DIPIRONA 500MG BL C/10" \-\> {principio\_ativo: "dipirona sódica", dosagem: "500mg", forma: "comprimido", quantidade: "10"}  
2. **Criação da Assinatura:** Para cada produto, uma assinatura única será gerada combinando seu **NCM classificado** com as **entidades normalizadas**.  
   * **Exemplo de Assinatura:** 30049069\_dipirona-sodica\_500mg\_comprimido  
3. **Agrupamento e Enriquecimento do Grafo:**  
   * O processo identificará todos os produtos (com diferentes produto\_id e descrições) que compartilham a mesma assinatura.  
   * No Neo4j, será criado um novo tipo de nó: (:ProdutoConceitual). Um nó será criado para cada assinatura única.  
   * Todos os nós :Produto originais que compartilham uma assinatura serão conectados ao seu respectivo nó :ProdutoConceitual através de uma nova relação, como \[:É\_UMA\_APRESENTACAO\_DE\].

Benefício na Prática:  
Quando o sistema precisar classificar um novo produto, o RetrievalToolbox poderá consultar o grafo e, através do nó :ProdutoConceitual, recuperar o contexto de todas as suas variações já classificadas. Isso fornece um conjunto de exemplos muito mais rico e preciso para os agentes de raciocínio, beneficiando drasticamente ambos os modos de operação.