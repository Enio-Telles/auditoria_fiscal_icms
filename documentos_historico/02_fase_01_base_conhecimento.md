# **Plano de Implementação Detalhado – Fase 1: Construção da Base de Conhecimento Fiscal**

Versão: 2.0 (PostgreSQL e Estrutura de Grafo Detalhada)  
Data: 18 de Agosto de 2025  
Objetivo: Construir uma Base de Conhecimento Tri-Híbrida (Relacional, Vetorial e Grafo), utilizando PostgreSQL como base relacional, e modelando com precisão as complexas regras hierárquicas fiscais para servir de alicerce ao sistema de agentes de IA.

### **1\. Análise dos Arquivos Fonte e Relações de Dados**

A análise das fontes de dados permanece a mesma, com a estratégia de modelagem agora direcionada para um ambiente PostgreSQL, que oferece maior escalabilidade e robustez para uma aplicação de produção.

* **Fontes Estruturadas:** Tabela\_NCM.xlsx, conv\_142\_formatado.json, CEST\_RO.xlsx, produtos\_selecionados.json, descricoes\_ncm.json.  
* **Fontes Não-Estruturadas:** nesh-2022.pdf, nesh-2022\_REGRAS\_GERAIS.docx.

A estratégia de decomposição da hierarquia NCM e a modelagem da relação NCM-CEST através de uma tabela de associação continuam sendo os pilares da nossa abordagem.

### **2\. Estrutura da Base de Dados Relacional (PostgreSQL)**

O banco de dados PostgreSQL será o repositório central para os dados limpos e estruturados, oferecendo performance e confiabilidade.

* **Banco de Dados:** knowledge\_base (em uma instância PostgreSQL)  
* **Schema das Tabelas:** O schema permanece conceitualmente o mesmo, mas otimizado para PostgreSQL com tipos de dados apropriados e índices para performance.  
  * **ncm**: codigo (VARCHAR(8), PK), descricao (TEXT), capitulo (VARCHAR(2)), posicao (VARCHAR(4)), subposicao (VARCHAR(6)).  
  * **cest\_regras**: cest (VARCHAR(9), PK), descricao (TEXT), segmento\_id (INTEGER, FK), situacao (VARCHAR(50)), vigencia\_inicio (DATE), vigencia\_fim (DATE).  
  * **segmentos**: id (SERIAL, PK), descricao (TEXT, UNIQUE).  
  * **ncm\_cest\_associacao**: cest\_codigo (VARCHAR(9), FK), ncm\_pattern (VARCHAR(8)).  
  * **produtos\_exemplos**: gtin (VARCHAR(14), PK), descricao (TEXT), ncm (VARCHAR(8)), cest (VARCHAR(9)).  
  * **nesh\_notes**: id (SERIAL, PK), codigo\_referencia (TEXT), texto (TEXT).

### **3\. Estrutura do Grafo de Conhecimento (Neo4j) e Estratégia de Graph RAG**

A base de dados de grafo é o que permite aos agentes "raciocinar" sobre as conexões entre as entidades fiscais.

#### **3.1. Modelo de Dados do Grafo**

* **Nós (Entidades):**  
  * (:Capitulo {id: '30'})  
  * (:Posicao {id: '3004'})  
  * (:Subposicao {id: '300490'})  
  * (:Subitem {id: '30049069', descricao: '...'})  
  * (:CEST {id: '28.064.00', descricao: 'Artigos infantis'})  
  * (:Segmento {id: '28', descricao: 'VENDA DE MERCADORIAS...'})  
  * (:Produto {descricao: 'Dipirona 500mg'})  
* **Relações (Conexões):**  
  * \[:PERTENCE\_A\]: Modela a hierarquia NCM. Ex: (:Subitem)-\[:PERTENCE\_A\]-\>(:Subposicao).  
  * \[:TEM\_REGRA\_CEST\]: Conecta um nó da hierarquia NCM a um nó CEST. **Esta é a relação chave**, pois pode partir de qualquer nível (ex: (:Capitulo)-\[:TEM\_REGRA\_CEST\]-\>(:CEST)).  
  * \[:CONTIDO\_EM\]: Conecta um (:CEST) ao seu (:Segmento).  
  * \[:EXEMPLO\_DE\]: Conecta um (:Produto) ao seu (:Subitem) NCM.

#### **3.2. Estratégia de Consulta (Como os Agentes usarão o Grafo)**

O Graph RAG permite que os agentes executem consultas complexas que seriam difíceis em um banco relacional. O fluxo de raciocínio de um agente para validar um CEST será:

1. **Ponto de Partida:** Dado um produto com NCM 49019900\. O agente localiza o nó :Subitem {id: '49019900'} no grafo.  
2. **Travessia Hierárquica:** O agente percorre a hierarquia para trás usando a relação \[:PERTENCE\_A\] para identificar todos os seus ancestrais: :Subposicao {id: '490199'}, :Posicao {id: '4901'}, :Capitulo {id: '49'}.  
3. **Busca de Regras em Múltiplos Níveis:** Para cada nó na hierarquia (do mais específico ao mais geral), o agente busca por relações \[:TEM\_REGRA\_CEST\] de saída. Isso permite encontrar todas as regras de CEST que se aplicam, seja ao subitem exato, à posição, ou ao capítulo inteiro.  
4. **Validação de Segmento:** Para cada regra de CEST candidata encontrada, o agente segue a relação \[:CONTIDO\_EM\] até o nó :Segmento.  
5. **Decisão Final:** O agente então compara a descrição do :Segmento (ex: "Venda de mercadorias pelo sistema porta a porta") com o contexto\_empresa fornecido na consulta. Somente se houver compatibilidade, a regra de CEST é considerada válida.

### **4\. Plano de Implementação da Fase 1 (Etapas e Tarefas)**

#### **Etapa 1 (Semana 1): Estruturação dos Dados Fundamentais**

* **Tarefa 1.1: Configuração do Ambiente e Criação do Banco de Dados**  
  * **Ação:** Configurar o ambiente Python, Git, Docker. Instalar as dependências necessárias, incluindo psycopg2-binary para a conexão com PostgreSQL. Definir o schema em um script Python que cria as tabelas no PostgreSQL.  
* **Tarefa 1.2: Processamento e Carga dos Dados Estruturados**  
  * **Ação:** Desenvolver o script src/data\_processing/structured\_loader.py para conectar ao PostgreSQL, realizar a ingestão, limpeza, normalização e carga de todas as fontes de dados tabulares.  
  * **Código:**

import pandas as pd  
import json  
import re  
from sqlalchemy import create\_engine, text  
import os

\# \--- Funções de Limpeza e Normalização \---

def clean\_ncm\_code(code):  
    """Remove a pontuação de um código NCM e garante a consistência."""  
    if not isinstance(code, str):  
        code \= str(code)  
    cleaned\_code \= re.sub(r'\[^0-9\]', '', code)  
    return cleaned\_code

def get\_ncm\_hierarchy(code):  
    """Extrai a hierarquia de um código NCM de 8 dígitos."""  
    code \= clean\_ncm\_code(code).ljust(8, '0')  
    return {  
        'capitulo': code\[:2\],  
        'posicao': code\[:4\],  
        'subposicao': code\[:6\]  
    }

def normalize\_cest\_ncm\_column(ncm\_string):  
    """Normaliza a coluna NCM dos arquivos CEST, que pode conter múltiplos valores."""  
    if not isinstance(ncm\_string, str):  
        return \[\]  
    items \= re.sub(r'\[\\s.\]', '', ncm\_string).split(',')  
    return \[item for item in items if item\]

\# \--- Função Principal de Processamento \---

def create\_knowledge\_base(db\_uri):  
    """  
    Função principal para ler todos os arquivos fonte, processá-los e  
    criar a base de conhecimento relacional em PostgreSQL.  
    """  
    print("Iniciando a criação da base de conhecimento em PostgreSQL...")  
    engine \= create\_engine(db\_uri)

    \# \--- 1\. Processamento da Tabela NCM \---  
    print("Processando Tabela NCM...")  
    try:  
        ncm\_df \= pd.read\_csv('Tabela\_NCM.xlsx \- Tabela NCM.csv', dtype={'Código': str})  
        ncm\_df.rename(columns={'Código': 'ncm\_codigo', 'Descrição': 'descricao'}, inplace=True)  
          
        ncm\_full\_df \= ncm\_df\[ncm\_df\['ncm\_codigo'\].str.match(r'^\\d{4}\\.\\d{2}\\.\\d{2}$')\].copy()  
        ncm\_full\_df\['codigo'\] \= ncm\_full\_df\['ncm\_codigo'\].apply(clean\_ncm\_code)  
          
        hierarchy\_df \= pd.DataFrame(ncm\_full\_df\['codigo'\].apply(get\_ncm\_hierarchy).tolist())  
        ncm\_final\_df \= pd.concat(\[ncm\_full\_df.reset\_index(drop=True), hierarchy\_df\], axis=1)  
          
        ncm\_final\_df \= ncm\_final\_df\[\['codigo', 'descricao', 'capitulo', 'posicao', 'subposicao'\]\]  
        ncm\_final\_df.to\_sql('ncm', engine, if\_exists='replace', index=True, index\_label='id')  
        print(f"Tabela 'ncm' criada com {len(ncm\_final\_df)} registros.")

    except Exception as e:  
        print(f"Erro ao processar Tabela\_NCM: {e}")

    \# \--- 2\. Processamento das Regras CEST \---  
    print("Processando regras CEST...")  
    try:  
        with open('conv\_142\_formatado.json', 'r', encoding='utf-8') as f:  
            conv142\_data \= json.load(f)  
        cest\_conv\_df \= pd.DataFrame(conv142\_data)  
        cest\_conv\_df.rename(columns={'Anexo': 'segmento\_descricao', 'descricao\_oficial\_cest': 'descricao'}, inplace=True)  
        cest\_conv\_df\['fonte'\] \= 'Convenio\_142'

        cest\_ro\_df \= pd.read\_csv('CEST\_RO.xlsx \- Planilha1.csv', dtype=str)  
        cest\_ro\_df.rename(columns={'CEST': 'cest', 'NCM/SH': 'ncm', 'DESCRIÇÃO': 'descricao', 'Situação': 'situacao', 'Início vig.': 'vigencia\_inicio', 'Fim vig.': 'vigencia\_fim', 'TABELA': 'segmento\_descricao'}, inplace=True)  
        cest\_ro\_df\['fonte'\] \= 'CEST\_RO'  
          
        cest\_ro\_df\_vigente \= cest\_ro\_df\[cest\_ro\_df\['situacao'\].str.lower() \== 'vigente'\].copy()  
        all\_cest\_df \= pd.concat(\[cest\_ro\_df\_vigente, cest\_conv\_df\]).drop\_duplicates(subset=\['cest', 'ncm'\], keep='first')

        segmentos\_df \= all\_cest\_df\[\['segmento\_descricao'\]\].drop\_duplicates().reset\_index(drop=True)  
        segmentos\_df.index.name \= 'id'  
        segmentos\_df.to\_sql('segmentos', engine, if\_exists='replace')  
          
        \# Reload segmentos to get the generated IDs  
        segmentos\_df \= pd.read\_sql('segmentos', engine, index\_col='id')  
        segmentos\_map \= {desc: idx for idx, desc in segmentos\_df\['segmento\_descricao'\].to\_dict().items()}

        all\_cest\_df\['segmento\_id'\] \= all\_cest\_df\['segmento\_descricao'\].map(segmentos\_map)  
        cest\_regras\_df \= all\_cest\_df\[\['cest', 'descricao', 'segmento\_id', 'situacao', 'vigencia\_inicio', 'vigencia\_fim'\]\].drop\_duplicates(subset=\['cest'\])  
        cest\_regras\_df.to\_sql('cest\_regras', engine, if\_exists='replace', index=False)  
          
        ncm\_cest\_list \= \[\]  
        for \_, row in all\_cest\_df.iterrows():  
            ncms \= normalize\_cest\_ncm\_column(row\['ncm'\])  
            for ncm\_pattern in ncms:  
                ncm\_cest\_list.append({'cest\_codigo': row\['cest'\], 'ncm\_pattern': ncm\_pattern})  
          
        ncm\_cest\_assoc\_df \= pd.DataFrame(ncm\_cest\_list).drop\_duplicates()  
        ncm\_cest\_assoc\_df.to\_sql('ncm\_cest\_associacao', engine, if\_exists='replace', index=False)  
        print(f"Tabelas 'segmentos', 'cest\_regras' e 'ncm\_cest\_associacao' criadas.")

    except Exception as e:  
        print(f"Erro ao processar arquivos CEST: {e}")

    \# \--- 3\. Processamento dos Produtos de Exemplo \---  
    print("Processando produtos de exemplo...")  
    try:  
        with open('produtos\_selecionados.json', 'r', encoding='utf-8') as f:  
            produtos\_data \= json.load(f)  
        produtos\_df \= pd.DataFrame(produtos\_data)  
        produtos\_df\['ncm'\] \= produtos\_df\['ncm'\].apply(clean\_ncm\_code)  
        produtos\_df\['cest'\] \= produtos\_df\['cest'\].apply(clean\_ncm\_code)  
        produtos\_df.to\_sql('produtos\_exemplos', engine, if\_exists='replace', index=False)  
        print(f"Tabela 'produtos\_exemplos' criada com {len(produtos\_df)} registros.")

    except Exception as e:  
        print(f"Erro ao processar produtos\_selecionados: {e}")

    print("\\nCriação da base de conhecimento concluída.")

\# \--- Execução e Verificação \---  
if \_\_name\_\_ \== '\_\_main\_\_':  
    \# Use variáveis de ambiente para as credenciais do banco de dados  
    \# Exemplo: postgresql://user:password@host:port/database  
    DB\_USER \= os.getenv("DB\_USER", "user")  
    DB\_PASSWORD \= os.getenv("DB\_PASSWORD", "password")  
    DB\_HOST \= os.getenv("DB\_HOST", "localhost")  
    DB\_PORT \= os.getenv("DB\_PORT", "5432")  
    DB\_NAME \= os.getenv("DB\_NAME", "knowledge\_base")  
      
    DATABASE\_URI \= f"postgresql://{DB\_USER}:{DB\_PASSWORD}@{DB\_HOST}:{DB\_PORT}/{DB\_NAME}"

    create\_knowledge\_base(DATABASE\_URI)

    engine \= create\_engine(DATABASE\_URI)  
    with engine.connect() as connection:  
        print("\\n--- VERIFICAÇÃO DAS REGRAS DE NEGÓCIO \---")  
        \# Cenário: NCM (4901.99.00) que corresponde a um Capítulo (49)  
        print("\\n\[Cenário\] Teste de correspondência por Capítulo (Porta a Porta):")  
        query \= text("""  
            SELECT n.codigo as ncm\_produto, nca.ncm\_pattern, cr.cest, s.descricao as segmento  
            FROM ncm n  
            JOIN ncm\_cest\_associacao nca ON n.capitulo \= nca.ncm\_pattern  
            JOIN cest\_regras cr ON nca.cest\_codigo \= cr.cest  
            JOIN segmentos s ON cr.segmento\_id \= s.id  
            WHERE n.codigo \= '49019900' AND s.descricao LIKE '%PORTA A PORTA%'  
        """)  
        result \= connection.execute(query).fetchall()  
        if result:  
            print("Regra encontrada para NCM 49019900 no segmento 'Porta a Porta':")  
            for row in result:  
                print(f"  \- NCM: {row\[0\]}, Padrão da Regra: {row\[1\]}, CEST: {row\[2\]}, Segmento: {row\[3\]}")  
        else:  
            print("Nenhuma regra de correspondência por Capítulo encontrada.")  
