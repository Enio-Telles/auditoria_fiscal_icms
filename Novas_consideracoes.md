# Plano do Sistema Multiagentes RAG Local de Auditoria de ICMS
- usar ambiente python do tipo conda
## Estrutura de Documentação
- O arquivo **README.md** deve ser atualizado sempre que houver mudanças no código, com resumo dos demais arquivos `.md`(exceto Novas_consideracoes.md).
- Criar a pasta **documentos** e mover os demais arquivos `.md` para dentro dela (exceto Novas_consideracoes.md e , MANUAL_USUARIO_FINAL.MD).
- Padronizar nomes no formato `01_nome_antigo.md`, seguindo a ordem de criação e alteração.
- Excluir códigos antigos não utilizados, mantendo apenas os ativos na arquitetura.
- reorganizar estrutura de códigos, mantendo a estrututura do projeto conforme o diagrama de arquitetura.

## Funcionalidades do Sistema

### Classificação de Mercadorias
- A classificação será feita com base na **descrição da mercadoria**.
- as atividades da empresa devem fazer parte do contexto da classificação do produto, pois a atividade da empresa auxilia na identificação das mercadorias. Por exemplo, vendedores de autopeças provavelmente vendem produtos do segmento CEST autopeças; farmácias vendem medicamentos; empresas que fazem venda porta a porta se enquadram nesse segmento do CEST 28
- a entrada das informações das mercadorias da empresa a serem verificadas e classificadas em termos de ncm e cest será com os seguintes campos, no mínimo: produto_id, descricao_produto, codigo_produto, codigo_barra, ncm, cest 
- Os agentes verificarão se a classificação inicial em termos de **NCM** e **CEST** está correta. Caso contrário, gerarão nova classificação de **NCM** e **CEST**.
- ao importar os dados de outro banco de dados, ou após essas informações serem integradas ao banco de dados da empresa (que contém as informações das mercadorias da empresa), será feita consulta inicial para agregar produtos com descrição igual (já na importação, ou após a importação dos dados para o banco de dados da empresa): Produtos com mesma descrição já são agregados na consulta inicial (`id_agregados`).
- produtos iguais com descrições diferentes serão identificados e agregados por agente.
- Se códigos forem diferentes, mas a descrição similar, é possível que sejam o mesmo produto.

### Interface Web
A interface deve ser intuitiva, com explicações claras e fluxos guiados para usuários menos experientes.
Incluir logs de auditoria visíveis para cada decisão, com possibilidade de comentários e justificativas.
1. Página para classificar:
   - Apenas um produto
   - Um lote de produtos
   - Todos os produtos da base da empresa
2. Login de usuários.
3. Cadastro de usuários (nome, e-mail, cargo, identificação).
4. Cadastro de empresas (dados gerais, sócios, contador, endereço, atividades).
5. Página inicial com todas as funcionalidades em botões/ícones/links. Incluir explicações detalhadas sobre cada funcionalidade para facilitar o uso (como usar, o que está sendo acessado, etc)
6. Opção de reimportar dados e reiniciar classificações.
7. Visualização e relatório completo de classificações realizadas por produto e por lote.
8. Função de reclassificação e agregação de mercadorias.
8.1. Função para retomar a classificação (por exemplo, classificou 10 mercadorias do banco de dados da empresa no sistema multiagentes, classificar mais 10 ou todo o restante)
9. Revisão de classificações, com justificativas e contexto RAG.
10. Inclusão de classificações corrigidas em um **golden set** deve conter no mínimo (id_golden, descricao_produto, descricao_expandida, codigo_produto, codigo_barra, ncm, cest ). Implementar controle de versões para o golden set, com histórico de alterações e responsáveis.
11. Página inicial com resumo das características do sistema e acesso facilitado às funcionalidades disponíveis.
11.1. incluir possibilidade de edição manual das classificações realizadas.
11.2. Possibilidade de revisar e alterar golden set por dados e por mercadorias (inclusive na inteface web)
12. Página em que seja possível executar as funções de apenas um agente para um produto específico, visualizando detalhamentamente cada atividade desempenhada pelo agente, bem como a justificativa de cada uma das decisões tomadas.
13. Relatório completo da agregação de mercadorias (por exemplo -> Resumo Executivo com quantidade total de mercadorias originais analisadas, número de agrupamentos gerados (categorias finais), percentual de redução de duplicidades (ex.: de 10.000 itens para 7.200 categorias, redução de 28%), e destaques de inconsistências encontradas (ex.: NCM divergentes para mesma descrição, descrições ambíguas); Metodologia de Agregação: regras aplicadas para considerar mercadorias como iguais (ex.: comparação exata de descrição, normalização de texto, similaridade por embeddings, equivalência de NCM/CEST),Campos utilizados como chaves de comparação (ex.: código de barras, código interno, NCM, CEST, descrição).Critérios de desempate (ex.: manter o NCM mais específico, priorizar CEST válido, escolher descrição mais completa).Inconsistências e Alertas:Mercadorias iguais com NCM diferentes.Itens sem CEST ou NCM informado.Descrições genéricas que podem gerar erro na classificação.Possíveis duplicidades não resolvidas.

### Banco de Dados
- Cada empresa terá um banco específico no sistema.
- incluir tabelas para armazenar logs detalhados de auditoria e evidências RAG.
- Garantir que os dados importados mantenham metadados de origem para rastreabilidade.
- Estrutura modular para cadastro de empresa, produtos e futuras integrações (ex: EFD).
- Integração inicial com PostgreSQL local (não o do próprio sistema multiagentes), com possibilidade de Oracle SQL.
- possibilidade de extração de dados de Excel e csv
- identificar origem dos dados (tipo de banco de dados, por exemplo: PostGres ou SQL, nome do banco de dados de origem, nome da tabela de origem, campos importados // exemplo para o caso da importação de tabela com informações das mercadorias: PostGres, DB_NAME=db_04565289005297,tabela dbo.produto ,colunas produto_id, descricao_produto, codigo_barra, código_produto, ncm e cest )
- Exemplo de consulta inicial:
# Configuração do PostgreSQL local
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=db_04565289005297 #identificação do banco de dados com informações da empresa que serão importadas para o banco de dados do sistema multiagentes relativo à empresa
DB_USER=postgres
DB_PASSWORD=sefin
DB_SCHEMA=dbo

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
Incluir validação automática para detectar inconsistências (ex: NCM sem CEST, descrições genéricas)
#### NCM
- As regras gerais de interpretação (RGI) e complementares (RGC) devem ser formalizadas em um módulo de regras reutilizável. Usar arquivos '01_nesh-2022.pdf' e '01_nesh-2022_REGRAS_GERAIS.docx' como referências para essas regras.
- Estrutura: `AABB.CC.DD` (8 dígitos).
- Hierarquia: capítulo → posição → subposição → item → subitem. Por exemplo, o capítulo 84 abrange o código 8407, que agrange o 8407.3 abrange os códigos 8407.31, 8407.31.1, que abrange 8407.31.10, que abrange 8407.31.90
- Aplicar Regras Gerais de Interpretação (RGI) e Regras Gerais Complementares (RGC/TIPI).
- Considerar as atividades da empresa como contexto.
- Usar Regras Gerais de Interpretação (RGI) e Regras Gerais Complementares (RGC) do Sistema Harmonizado
o processo de identificação do NCM de uma mercadoria começa pela análise dos textos das posições e das Notas de Seção e de Capítulo. Se a mercadoria não puder ser classificada diretamente, as Regras Gerais 2 a 5 são aplicadas sequencialmente. Finalmente, a Regra 6 e as RGCs fornecem orientações para a classificação nos níveis de subposição, item e subitem, e para casos específicos como embalagens reutilizáveis e exceções ("Ex").
As Regras Gerais Complementares fornecem diretrizes adicionais para a interpretação e aplicação das Regras Gerais, especialmente em níveis mais detalhados da Nomenclatura.
	• RGC 1: Aplicação das Regras Gerais a Níveis Detalhados As Regras Gerais para Interpretação do Sistema Harmonizado aplicar-se-ão, mutatis mutandis, para determinar, dentro de cada posição ou subposição, o item aplicável e, dentro deste último, o subitem correspondente. Entende-se que apenas são comparáveis desdobramentos regionais (itens e subitens) do mesmo nível.
	• RGC 2: Regime de Classificação de Embalagens Reutilizáveis As embalagens que contêm mercadorias e que são claramente suscetíveis de utilização repetida (mencionadas na Regra 5 b)), seguirão seu próprio regime de classificação sempre que estejam submetidas aos regimes aduaneiros especiais de admissão temporária ou de exportação temporária. Caso contrário, seguirão o regime de classificação das mercadorias contidas.
Regra Geral Complementar da TIPI (RGC/TIPI)
RGC/TIPI 1: Determinação do "Ex" Aplicável As Regras Gerais para Interpretação do Sistema Harmonizado aplicar-se-ão, mutatis mutandis, para determinar, no âmbito de cada código, quando for o caso, o "Ex" aplicável, entendendo-se que apenas são comparáveis "Ex" de um mesmo código.

#### CEST
- Estrutura: `SS.III.DD` (7 dígitos).
- Cada CEST relaciona-se a um segmento e um NCM ou grupo de NCMs e tem uma descrição específica.Por exemplo, um produto pode ter ncm que se enquadra no cest mas não fazer parte do segmento, então essa descrição fica sem cest (exemplo, produtos não vendidos porta a porta não se enquadram no segmento 28 do CEST)
- Nem todo NCM tem CEST; um CEST pode abranger vários NCMs. Por exemplo CEST relacionado a mais de um ncm, como no caso do CEST 01.001.00, que engloba os NCMs 3815.12.10 e 3815.12.90
- Considerar as atividades da empresa como contexto. Em outros casos, a o CEST pode se referir a um grupo, como no CEST 01.002.00, que se refere ao NCM 3917. Nesse caso, o NCM deve se enquadrar nessa categoria e estar conforme a descrição. Pode ocorrer também de, como ocorre no CEST 01.006.00, de a categoria de NCM estar mais detalhada, como a relação com o NCM 4010.3
- Segmentos podem depender da atividade da empresa (ex: venda porta a porta → segmento 28).

### Justificativas e Rastreabilidade
- Armazenar em banco de dados as justificativas e consultas RAG que fundamentaram as decisões.
- registrar todas as decisões com evidências e metadados.
- Permitir revisão de classificações com registro do usuário responsável.
- as consultas RAG devem ser referenciadas com metadados dos arquivos de origem (arquivo, capítulo, campo se tabela)
- as consultas RAG devem ser referenciadas com metadados dos arquivos de origem (arquivo, capítulo, campo se tabela)
- Implementar um sistema de versionamento para as justificativas, permitindo auditoria histórica.
- Garantir que as consultas RAG estejam sempre associadas a metadados completos (arquivo, capítulo, trecho).

### Golden Set
- Criar base consolidada de classificações corretas para realimentação do sistema.
- Revisão e alteração possível via interface web.
- Deve ser tratado como fonte de verdade para treinamento e validação.
- Incluir processos automáticos para atualização e validação contínua.
- Permitir exportação/importação para integração com outros sistemas.

### Fluxo de Trabalho (Agentes)
-cada decisão dos agentes deve ser documentada: acessos a bancos de dados RAG, contexto, justificativas para decisões 
- Definir contratos claros (JSON schemas) para inputs e outputs, garantindo interoperabilidade.
- Implementar logs detalhados para cada agente, incluindo versões de modelos e prompts usados.
- Prever fallback para revisão humana em casos de baixa confiança.
- Para o agente de agregação, combinar técnicas de similaridade textual (fuzzy matching) com embeddings semânticos para maior robustez.
1. **ExpansionAgent** – Enriquece descrições brutas usando LLM.
2. **AggregationAgent** – Agrupa produtos semelhantes e define representantes.
3. **NCMAgent** – Confirma ou determina o NCM via RAG e base estruturada.
4. **CESTAgent** – Confirma ou determina o CEST com base no NCM atribuído.
5. **ReconcilerAgent** – Audita o par NCM/CEST, resolve conflitos e valida a classificação final.
6. **Propagação** – Aplica a classificação final a todos os produtos do grupo agregado.
 implementar IA Real com LLM com integração Ollama/OpenAI (prever possibilidade de mudar facilmente LLM usado na interface web frontend: usar ou llama3, ou gemma3n, ou gpt-oss:20b)
### Base de Dados de Apoio para RAG
*Metadados RAG padronizados e rastreáveis
- `01_nesh-2022_REGRAS_GERAIS.docx` e `01_nesh-2022.pdf`: 6 regras gerais e notas explicativas sobre NCM contidas em seções que detalham características de grupos de produtos. Estrutura delineada no SUMÁRIO.
- `01_Tabela_NCM.xlsx`: códigos e descrições do NCM. Campos [Código,Descrição, Data Início, Data Fim, Ato Legal Início, Número, Ano]
- `01-1_descricoes_ncm.json`: descrições dos códigos agrupadas com base na estrutura do código NCM . Campos [Código, Descrição_Completa]
- `02_conv_142_formatado.json`: mapeamento CEST x NCM. Segmento representa o número do segmento descrito pelo nome do Anexo; cest representa o código cest; ncm representa o grupo de ncms associados ao cest; descricao_oficial_cest representa a descrição do cest - um produto, para se enquadrar em um código cest, deve se enquadrar no segmento e na descrição); Campos [Anexo, segmento, cest, ncm, descricao_oficial_cest]
- `02-2_CEST_RO`: classificações CEST de Rondônia. Campos [ITEM,	CEST,	NCM/SH,	DESCRIÇÃO,	MVA ORIGINAL,	MVA AJUSTADA 4%,	MVA AJUSTADA 7%,	MVA AJUSTADA 12%,	MVA CORRIGIDA ALCGM,	MVA ORIGINAL - Atacado,	MVA ORIGINAL - Indústria,	Situação,	Início vig.,	Fim vig.,	TABELA	ANEXO
]
- `03_produtos_selecionados`: dados de produtos (GTIN, descrição, NCM, CEST). Campos [gtin, descricao, ncm, cest]
- `04_Tabela_ABC_Farma_V2.xlsx`: medicamentos (capítulo 30 NCM, segmento 13 CEST). Referência para identificação de medicamentos. campos [codigo_barras, DESCRICAO_BRUTA]

### Arquitetura Técnica
- Uso de banco relacional para dados estruturados e indexação vetorial para RAG é adequado.
- Orquestração via Celery/Redis ou similar garante escalabilidade.
- Prever monitoramento e alertas para falhas e desempenho.
- Documentar APIs e contratos para facilitar manutenção e evolução.


## 2 — Melhores práticas e prioridades

1. **Contratos (schemas) claros entre agentes**

2. **Metadados RAG padronizados e rastreáveis**

3. **Tabela/coleção de evidências (audit_log)**

4. **Abordagem híbrida: regras + RAG** — aplicar regras determinísticas antes ou como filtro ao RAG (ex.: filtro por capítulo NCM, mapas CEST→NCM, vigências legais).

5. **Fluxo human-in-the-loop** — definir limiares: auto-aplicar (alto score + compatibilidade com regras), revisão (médio), bloqueio/revisão manual (baixo).





