# Plano do Sistema Multiagentes RAG de Auditoria de ICMS

## Estrutura de Documentação
- O arquivo **README.md** deve ser atualizado sempre que houver mudanças no código, com resumo dos demais arquivos `.md`.
- Criar a pasta **documentos** e mover os demais arquivos `.md` para dentro dela.
- Padronizar nomes no formato `01_nome_antigo.md`, seguindo a ordem de criação e alteração.
- Excluir códigos antigos não utilizados, mantendo apenas os ativos na arquitetura.

## Funcionalidades do Sistema

### Classificação de Mercadorias
- A classificação será feita com base na **descrição da mercadoria**.
- Os agentes verificarão se a classificação inicial está correta. Caso contrário, gerarão nova classificação de **NCM** e **CEST**.
- Produtos iguais com descrições diferentes serão identificados e agregados.
- Produtos com mesma descrição já são agregados na consulta inicial (`id_agregados`).
- Se códigos forem diferentes, mas a descrição similar, é possível que sejam o mesmo produto.

### Interface Web
1. Página para classificar:
   - Apenas um produto
   - Um lote de produtos
   - Todos os produtos da base da empresa
2. Login de usuários.
3. Cadastro de usuários (nome, e-mail, cargo, identificação).
4. Cadastro de empresas (dados gerais, sócios, contador, endereço, atividades obrigatórias).
5. Página inicial com todas as funcionalidades em botões/ícones/links.
6. Opção de reimportar dados e reiniciar classificações.
7. Visualização e relatório de classificações realizadas.
8. Função de reclassificação e agregação de mercadorias.
9. Revisão de classificações, com justificativas e contexto RAG.
10. Inclusão de classificações corrigidas em um **golden set**.

### Banco de Dados
- Cada empresa terá um banco específico no sistema.
- Estrutura modular para cadastro de empresa, produtos e futuras integrações (ex: EFD).
- Integração inicial com PostgreSQL, com possibilidade futura de Oracle SQL.
- Exemplo de consulta inicial:

```sql
SELECT
    produto_id,
    descricao_produto,
    codigo_produto,
    codigo_barra,
    ncm,
    cest,
    DENSE_RANK() OVER (ORDER BY descricao_produto) AS id_agregados,
    COUNT(*) OVER (PARTITION BY descricao_produto) AS qtd_mesma_desc
FROM dbo.produto
WHERE descricao_produto IS NOT NULL;
```

### Regras de Classificação
#### NCM
- Estrutura: `AABB.CC.DD` (8 dígitos).
- Hierarquia: capítulo → posição → subposição → item → subitem.
- Aplicar Regras Gerais de Interpretação (RGI) e Regras Gerais Complementares (RGC/TIPI).
- Considerar as atividades da empresa como contexto.

#### CEST
- Estrutura: `SS.III.DD` (7 dígitos).
- Cada CEST relaciona-se a um segmento e um NCM ou grupo de NCMs.
- Nem todo NCM tem CEST; um CEST pode abranger vários NCMs.
- Segmentos dependem da atividade da empresa (ex: venda porta a porta → segmento 28).

### Justificativas e Rastreabilidade
- Armazenar em banco de dados as justificativas e consultas RAG que fundamentaram as decisões.
- Permitir revisão de classificações com registro do usuário responsável.

### Golden Set
- Criar base consolidada de classificações corretas para realimentação do sistema.
- Revisão e alteração possível via interface web.

### Fluxo de Trabalho (Agentes)
1. **ExpansionAgent** – Enriquece descrições brutas usando LLM.
2. **AggregationAgent** – Agrupa produtos semelhantes e define representantes.
3. **NCMAgent** – Confirma ou determina o NCM via RAG e base estruturada.
4. **CESTAgent** – Confirma ou determina o CEST com base no NCM atribuído.
5. **ReconcilerAgent** – Audita o par NCM/CEST, resolve conflitos e valida a classificação final.
6. **Propagação** – Aplica a classificação final a todos os produtos do grupo agregado.

### Base de Dados de Apoio
- `Tabela_NCM.xlsx`: códigos e descrições do NCM.
- `descricoes_ncm.json`: estrutura hierárquica do NCM.
- `conv_142_formatado.json`: mapeamento CEST x NCM.
- `produtos_selecionados`: dados de produtos (GTIN, descrição, NCM, CEST).
- `CEST_RO`: classificações CEST de Rondônia.
- `nesh-2022_REGRAS_GERAIS.docx` e `nesh-2022.pdf`: regras gerais e notas explicativas.
- `Tabela_ABC_Farma_V2.xlsx`: medicamentos (capítulo 30 NCM, segmento 13 CEST).

 Plano: Sistema de Classificação Fiscal (formato Markdown)

**Data:** 18 de Agosto de 2025

---

## 1 — Resumo rápido / objetivo

O pipeline está organizado em módulos/"agentes": Expansão → Agregação → NCM → CEST → Reconciliação → Propagação. Este documento descreve melhorias, contratos, integração dos agentes com arquivos e RAG, arquitetura recomendada, esquema de dados e exemplos completos de prompts RAG (System + User + Formato esperado) para o **Agente NCM** e o **Agente CEST**.

---

## 2 — Melhores práticas e prioridades (alto impacto)

1. **Contratos (schemas) claros entre agentes** — defina JSON schema para o que cada agente recebe e produz (campos obrigatórios: `product_id`, `company_id`, `id_agregados`, `descricao_original`, `descricao_enriquecida`, `ncm_sugerido`/`score`, `cest_sugerido`/`score`, `rag_context_ids`, `timestamp`, `model_version`).

2. **Metadados RAG padronizados e rastreáveis** — cada consulta RAG grava: `chunk_id`, `arquivo`, `file_path`, `posicao`, `similarity_score`, trecho_texto, `timestamp`.

3. **Tabela/coleção de evidências (audit_log)** — registre `input_snapshot`, `agente`, `decisao`, `confidence`, `rag_context_pointers`, `user_override`.

4. **Abordagem híbrida: regras + RAG** — aplicar regras determinísticas antes ou como filtro ao RAG (ex.: filtro por capítulo NCM, mapas CEST→NCM, vigências legais).

5. **Fluxo human-in-the-loop** — definir limiares: auto-aplicar (alto score + compatibilidade com regras), revisão (médio), bloqueio/revisão manual (baixo).

---

## 3 — Integração técnica por agente (contratos, acesso a arquivos, RAG)

> Observação: todos os nomes e tabelas abaixo estão em português.

### Agente de Expansão
**Objetivo:** transformar `descricao_original` em `descricao_enriquecida` e extrair campos estruturados (marca, modelo, unidade, concentração, apresentação).

**Input:** registro `produto` com (`product_id`, `company_id`, `descricao_original`, `codigo_barra`, `codigo_produto`, `ncm`, `cest`, `id_agregados`).

**Output:** `descricao_enriquecida`, `campos_estruturados`, `embedding` (opcional), `confidence`, `rag_context_ids` (se RAG usado).

**Integração com arquivos & RAG:** ler CSV/JSON/XLSX com `pandas`; para documentos (PDF/DOCX) usar PyPDF2 / python-docx. Usar RAG apenas para disambiguar termos técnicos ou consultar notas explicativas; sempre registrar `rag_context_ids`.

**Técnicas:** LLM local + regex + heurísticas. Salvar versão do prompt e `model_version`.

---

### Agente de Agregação
**Objetivo:** agrupar produtos semelhantes em `grupo_produto` (representante por grupo).

**Input:** produtos com `descricao_enriquecida` e possivelmente `embeddings`.

**Output:** `clusters`, `representante_id`, mapeamento `product_id → group_id`, `merge_report`.

**Como integrar:** usar `id_agregados` inicial (query SQL) como primeiro corte; combinar fuzzy token matching (ex.: token_set_ratio), embeddings + clustering (HDBSCAN/DBSCAN) e regras (mesmo GTIN -> forçar merge). Opcional: anotar evidências com snippets do golden_set via RAG.

---

### Agente NCM
**Objetivo:** sugerir e validar códigos NCM para o representante do grupo usando RAG + regras.

**Input:** representante com `descricao_enriquecida`, `company_activity`, `group_id`, `embeddings`.

**Output:** `ncm_candidates` (lista com `codigo`, `razao_curta`, `score`, `rag_context_ids`), `decisao_final_ncm`, `confidence`, `regra_flags`.

**Integração com arquivos & RAG:** indexar fontes de conhecimento (planilhas NCM, descrições oficiais, notas explicativas em PDF) no vector store; chunking de 200–600 tokens com overlap; metadata por chunk: `arquivo`, `capitulo`, `chunk_id`, `start`, `end`.

**Processo:** combinar busca semântica (top-K) com filtros por capítulo e regras. Na ambiguidade, executar prompt RAG com os snippets. Salvar `rag_context_ids` e `prompt_template` usado.

---

### Agente CEST
**Objetivo:** atribuir/confirmar CEST com base no NCM e na descrição; usar tabelas de convênios e RAG.

**Input:** `decisao_ncm` (ou `ncm_candidates`), `descricao_enriquecida`, `company_activity`.

**Output:** `cest_candidates`, `decisao_final_cest`, `rag_context_ids`, `confidence`, `vigencia_legal`.

**Integração:** usar tabela `convênio` (formato indexado) e `CEST_RO`; busca fast-path por NCM→CEST exato antes de abrir RAG. Quando necessário, usar RAG com snippets que contenham notas e descrições do convênio.

---

### Agente de Reconciliação
**Objetivo:** auditar par NCM/CEST, aplicar políticas (thresholds) e decidir propagação.

**Input:** outputs dos agentes anteriores (`ncm`, `cest`, `scores`, `rag_context_ids`).

**Output:** `classificacao_final` (`ncm`, `cest`), `reason_codes`, `acao` (`auto_aplicar`, `revisar`, `bloquear`), `audit_log_id`.

**Processo:** calcular `score_final` como combinação ponderada de `semantic_similarity_score`, `rule_match_score` e `consistencia_com_golden_set`. Se abaixo do limiar, enviar para revisão humana com evidências (snippets + justificativa).

---

### Propagação
**Objetivo:** aplicar classificação final a todos os produtos do grupo e gerar relatórios.

**Processo:** atualizar linhas `produto` com `ncm_final`, `cest_final`, `propagation_timestamp`, `propagated_by` e anexar `evidence_id`. Gerar relatório com métricas (itens propagados, % concordância, itens para revisão).

---

## 4 — Arquitetura recomendada

- **Ingestão:** ETL em Python → tabela `staging` (por `company_id`).
- **Armazenamento Relacional:** Postgres para `produto`, `grupo_produto`, `classificacao`, `conjunto_dourado`, `audit_log`.
- **Indexação Vetorial:** FAISS/Milvus local para embeddings e `rag_fragmentos`.
- **Object Store:** sistema de arquivos ou S3 local para `Tabela_NCM.xlsx`, `convênio.json`, PDFs.
- **Orquestração:** Celery + Redis ou orquestrador simples baseado em fila/REST.
- **LLM:** modelo local (ex.: Gemma via LM Studio / Ollama) e embeddings locais (sentence-transformers ou embedding do modelo).
- **UI:** painel web para revisão humana, inclusão no conjunto dourado, controlar reprocessamento e visualizar evidências RAG.

---

## 5 — Esquema de dados mínimo sugerido (nomes em português)

- `produto` (`product_id`, `company_id`, `descricao_original`, `descricao_enriquecida`, `codigo_barra`, `codigo_produto`, `ncm_original`, `cest_original`, `group_id`, `created_at`)
- `grupo_produto` (`group_id`, `representante_product_id`, `metodo_agregacao`, `created_at`)
- `classificacao` (`id`, `product_id`/`group_id`, `agente`, `ncm`, `cest`, `confidence`, `status`, `rag_evidence_ids`, `model_version`, `created_at`)
- `rag_fragmentos` (`chunk_id`, `arquivo`, `caminho_arquivo`, `start`, `end`, `texto`, `metadata_json`)
- `evidencia_rag` (`id`, `classificacao_id`, `chunk_id`, `similarity_score`)
- `conjunto_dourado` (`id`, `assinatura_produto`, `ncm`, `cest`, `usuario_origem`, `company_id`, `created_at`)
- `log_auditoria` (`id`, `agente`, `input_snapshot_json`, `output_snapshot_json`, `rag_evidence_ids`, `user_override_id`, `timestamp`)

---

## 6 — Prompting / RAG: boas práticas e exemplos completos

**Boas práticas:** sempre envie ao LLM: (1) instrução curta com regras aplicáveis (RGI/TIPI), (2) top-K snippets com metadados (`arquivo`, `capitulo`, `chunk_id`), (3) `descricao_enriquecida`, (4) pergunta específica e formato de saída esperado (JSON). Salve `prompt`, `response`, `chunk_ids` e `model_version` no `log_auditoria`.

### Exemplo de prompt RAG para o **Agente NCM**

**System (instrução do sistema):**
```
Você é um classificador fiscal especializado em NCM (Nomenclatura Comum do Mercosul). Aplique as regras do RGI/TIPI quando apropriado. Não invente códigos. Se houver incerteza, retorne candidatos ordenados com justificativa e os IDs dos fragmentos (chunk_id) usados como evidência. Produza a saída no formato JSON exato solicitado.
```

**User (contexto + evidências):**
```
Descrição do produto (descricao_enriquecida):
<<DESCRICAO_ENRIQUECIDA_AQUI>>

Atividade da empresa: <<ATIVIDADE_EMPRESA_AQUI>>

Trechos recuperados (top-5):
1) arquivo: <<NOME_ARQUIVO_1>>, capitulo: <<CAPITULO_1>>, chunk_id: <<CHUNK_1>>
   texto: "<<TEXTO_CHUNK_1>>"
2) arquivo: <<NOME_ARQUIVO_2>>, capitulo: <<CAPITULO_2>>, chunk_id: <<CHUNK_2>>
   texto: "<<TEXTO_CHUNK_2>>"
... (até top-5)

Pergunta: Com base na descrição e nos trechos, indique os **3 melhores códigos NCM** ordenados por relevância. Para cada candidato, forneça:
- codigo (formato NN.NN.NN.NN ou sem pontos)
- justificativa_curta (2–3 frases)
- score (valor numérico entre 0 e 1 representando confiança)
- regras_aplicadas (lista de regras/detecção aplicadas, ex.: 'capítulo 30 compatível', 'nota explicativa X')
- chunk_ids usados (lista)

Retorne apenas JSON no formato exato abaixo.
```

**Formato de saída esperado (JSON):**
```json
{
  "ncm_candidates": [
    {
      "codigo": "3004.90.69",
      "justificativa_curta": "Descrição menciona fórmulas X e apresentação Y; corresponde à posição 3004 e notas explicativas.",
      "score": 0.87,
      "regras_aplicadas": ["capitulo_30", "nota_explica_3"],
      "chunk_ids": ["chunk_123", "chunk_456"]
    },
    {
      "codigo": "3004.90.10",
      "justificativa_curta": "Produto similar, porém concentração diferente; menos compatível.",
      "score": 0.64,
      "regras_aplicadas": ["capitulo_30"],
      "chunk_ids": ["chunk_789"]
    }
  ],
  "decisao_final_ncm": "3004.90.69",
  "confidence": 0.82,
  "applied_rules": ["capitulo_30", "match_descricao_keywords"]
}
```

> **Observação:** adapte `score` e `confidence` de acordo com sua função de combinação (similaridade semântica + regra_match).

---

### Exemplo de prompt RAG para o **Agente CEST**

**System (instrução do sistema):**
```
Você é um classificador especializado em CEST (Código Especificador da Substituição Tributária). Use os trechos do convênio e tabelas oficiais fornecidos. Verifique vigência legal das entradas e informe se há custo/observação de vigência. Produza somente JSON no formato solicitado.
```

**User (contexto + evidências):**
```
NCM sugerido: <<NCM_SUGERIDO_AQUI>>
Descricao_enriquecida: <<DESCRICAO_ENRIQUECIDA>>
Atividade da empresa: <<ATIVIDADE_EMPRESA>>
Trechos recuperados (top-5):
1) arquivo: convênio_142_formatado.json, chunk_id: <<CHUNK_A>>
   texto: "<<TEXTO_CHUNK_A>>"
2) arquivo: CEST_RO.csv, chunk_id: <<CHUNK_B>>
   texto: "<<TEXTO_CHUNK_B>>"
...

Pergunta: Com base nos trechos e no NCM, indique até 3 códigos CEST possíveis, para cada um forneça:
- codigo_cest (7 dígitos no formato SS.III.DD ou sem pontos)
- justificativa_curta
- score (0–1)
- vigencia (se aplicável, formato YYYY-MM-DD a YYYY-MM-DD, ou null)
- chunk_ids (lista)

Retorne apenas JSON no formato exato abaixo.
```

**Formato de saída esperado (JSON):**
```json
{
  "cest_candidates": [
    {
      "codigo_cest": "28.001.00",
      "justificativa_curta": "Convênio indica esse CEST para NCM 3004.90; descrição do produto igual à descrição do convênio.",
      "score": 0.9,
      "vigencia": "2018-01-01 a 2025-12-31",
      "chunk_ids": ["chunk_conv_12", "chunk_cest_34"]
    }
  ],
  "decisao_final_cest": "28.001.00",
  "confidence": 0.88,
  "applied_rules": ["mapeamento_NCM_to_CEST", "vigencia_check"]
}
```

---

## 7 — Conjunto dourado (golden set) e aprendizagem contínua

- O **conjunto dourado** é uma tabela de referência com decisões humanas validadas. Decisões confirmadas por revisores devem alimentar esse conjunto.
- Use o conjunto dourado para calibrar prompts, ajustar pesos de scoring e treinar um classificador leve para pre-rankeamento.
- Implementar rotina de *backfill* para reprocessar lotes quando o conjunto dourado sofrer mudanças relevantes.

---

## 8 — Logs, compliance e rastreabilidade

Cada decisão precisa ser reconstruível: salve `input_snapshot`, `agentes_envolvidos`, `topK_rag_chunks` (com `arquivo` e `posicao`), `model_version`, `user_override`.

---

## 9 — Checklist técnico de implementação (curto prazo)

1. Definir JSON schemas para inputs/outputs de cada agente.
2. Criar tabela `rag_fragmentos` e indexar arquivos de referência (Tabela_NCM.xlsx, descricoes_ncm.json, convênio formatado, PDFs).
3. Implementar Agente de Expansão e gravação de `descricao_enriquecida`.
4. Implementar Agente de Agregação (usar `id_agregados` inicial + fuzzy/embeddings).
5. Implementar Agente NCM com fluxo híbrido (regras rápidas -> RAG+LLM para ambiguidade).
6. Criar `log_auditoria` e UI básica para revisão e inclusão no `conjunto_dourado`.

---



---

