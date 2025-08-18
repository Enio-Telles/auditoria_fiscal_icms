# **Plano de Implementação Detalhado – Fase 1: Construção da Base de Conhecimento Fiscal**

Versão: 1.0  
Data: 18 de Agosto de 2025  
Objetivo: Construir uma Base de Conhecimento Tri-Híbrida (Relacional, Vetorial e Grafo), processando todas as fontes de dados e modelando com precisão as complexas regras hierárquicas fiscais, para servir de alicerce ao sistema de agentes de IA.

### **1\. Análise dos Arquivos Fonte e Relações de Dados**

A primeira etapa é compreender profundamente cada fonte de dados e como elas se interconectam. Esta análise dita a estratégia de modelagem e processamento.

#### **1.1. Fontes de Dados Estruturados (O Alicerce)**

* **Tabela\_NCM.xlsx / descricoes\_ncm.json:**  
  * **Propósito:** Define a espinha dorsal da classificação fiscal: a Nomenclatura Comum do Mercosul. Contém todos os códigos NCM e suas descrições oficiais.  
  * **Análise Estrutural:** O NCM possui uma hierarquia de 8 dígitos (formato AABB.CC.DD) onde cada par representa um nível de especificidade:  
    * **AA (Capítulo):** Categoria mais ampla (ex: 30 \- Produtos Farmacêuticos).  
    * **BB (Posição):** Subdivisão do capítulo (ex: 3004 \- Medicamentos).  
    * **CC (Subposição):** Detalhamento da posição (ex: 3004.90 \- Outros).  
    * **DD (Subitem):** Nível mais específico.  
  * **Estratégia:** decompor cada NCM de 8 dígitos em suas partes hierárquicas (2,4,5,6,7 e 8 dígitos). Isso permitirá que os agentes realizem buscas em qualquer nível de granularidade, conforme exigido pelas regras do CEST.  
* **conv\_142\_formatado.json e CEST\_RO.xlsx:**  
  * **Propósito:** Definem as regras do Código Especificador da Substituição Tributária (CEST), que ligam um produto (via NCM) a um regime de tributação específico.  
  * **Análise da Relação NCM-CEST:** Esta é a relação mais complexa. Uma única regra de CEST pode se aplicar a:  
    1. **Um NCM específico:** Ex: CEST 01.001.00 aplica-se a 3815.12.10.  
    2. **Múltiplos NCMs específicos:** Ex: CEST 01.001.00 aplica-se a 3815.12.10 E 3815.12.90.  
    3. **Um padrão de NCM (abrangência):** Ex: CEST 01.002.00 aplica-se a 3917, o que significa que se aplica a **todos** os NCMs que começam com 3917 (ex: 3917.10.00, 3917.21.00, etc.). Isso pode ocorrer em qualquer nível (Capítulo, Posição, etc.).  
  * **Estratégia:** A melhor forma de modelar isso é criar uma tabela de associação que armazene o código CEST e o "padrão NCM" da regra. O sistema poderá então usar consultas LIKE 'padrão%' para encontrar todos os NCMs completos que se encaixam na regra. Os dados de Rondônia (CEST\_RO.xlsx), por serem mais ricos (com vigência e situação), terão prioridade.  
* **produtos\_selecionados.json**   
  * **Propósito:** Fornecem exemplos do mundo real de produtos já classificados. São a matéria-prima para o nosso "Golden Set" e para treinar a busca semântica.  
  * **Estratégia:** Serão carregados em uma tabela de exemplos, servindo como base para validação e para o enriquecimento da busca vetorial.  
* **Tabela\_ABC\_Farma...:** contém o gtin e a descrição de medicamentos (que se enquadram, necessariamente, no NCM 30 e no CEST 13

#### **1.2. Fontes de Dados Não-Estruturados (O Contexto)**

* **nesh-2022.pdf e nesh-2022\_REGRAS\_GERAIS.docx:**  
  * **Propósito:** Contêm o "espírito da lei" – as Notas Explicativas do Sistema Harmonizado (NESH) e as Regras Gerais de Interpretação. São textos descritivos que explicam o que está incluído ou excluído de cada categoria NCM.  
  * **Estratégia:** O desafio é a **extração e o chunking lógicos**. O texto deve ser segmentado de forma inteligente, associando cada parágrafo ou seção ao seu respectivo código NCM (ex: "Capítulo 30", "Posição 30.04") ou a uma regra geral. Isso é fundamental para que o RAG possa recuperar o contexto textual correto para uma dada classificação.

### **2\. Estrutura da Base de Dados Relacional (SQLite)**

O banco de dados SQLite será o repositório central para os dados limpos e estruturados.

* **Arquivo:** data/processed/knowledge\_base.sqlite  
* **Schema das Tabelas:**  
  * **ncm**:  
    * codigo (TEXT, PK): O código NCM de 8 dígitos, sem pontuação.  
    * descricao (TEXT): A descrição oficial do NCM de 8 dígitos.  
    * capitulo (TEXT): Os 2 primeiros dígitos.  
    * posicao (TEXT): Os 4 primeiros dígitos.  
    * subposicao (TEXT): Os 6 primeiros dígitos.  
  * **cest\_regras**:  
    * cest (TEXT, PK): O código CEST.  
    * descricao (TEXT): A descrição oficial do CEST.  
    * segmento\_id (INTEGER, FK): Chave estrangeira para a tabela segmentos.  
    * situacao (TEXT): Vigente, alterado, etc.  
    * vigencia\_inicio (TEXT), vigencia\_fim (TEXT).  
  * **segmentos**:  
    * id (INTEGER, PK): ID único do segmento.  
    * descricao (TEXT): Nome do segmento (ex: "AUTOPEÇAS").  
  * **ncm\_cest\_associacao**:  
    * cest\_codigo (TEXT, FK): Chave estrangeira para cest\_regras.  
    * ncm\_pattern (TEXT): O padrão NCM da regra (pode ter 2, 4, 6, 8 dígitos).  
  * **produtos\_exemplos**:  
    * gtin (TEXT, PK): Código de barras do produto.  
    * descricao (TEXT): Descrição do produto.  
    * ncm (TEXT), cest (TEXT).  
  * **nesh\_notes**:  
    * id (INTEGER, PK): ID único.  
    * codigo\_referencia (TEXT): O NCM ou a Regra a que o texto se refere.  
    * texto (TEXT): O conteúdo da nota explicativa.

### **3\. Plano de Implementação da Fase 1 (Etapas e Tarefas)**

#### **Etapa 1 (Semana 1): Estruturação dos Dados Fundamentais**

* **Tarefa 1.1: Configuração do Ambiente e Criação do Banco de Dados**  
  * **Ação:** Configurar o ambiente Python, Git, Docker. Definir o schema acima em um script Python que cria o arquivo knowledge\_base.sqlite vazio.  
* **Tarefa 1.2: Processamento e Carga dos Dados Estruturados**  
  * **Ação:** Desenvolver o script src/data\_processing/structured\_loader.py. Este script é o coração da Etapa 1 e executará a ingestão, limpeza, normalização e carga de todas as fontes de dados tabulares.  
  * **Código:**

import pandas as pd  
import json  
import sqlite3  
import re  
from sqlalchemy import create\_engine, text

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

def create\_knowledge\_base(db\_path='data/processed/knowledge\_base.sqlite'):  
    """  
    Função principal para ler todos os arquivos fonte, processá-los e  
    criar a base de conhecimento relacional em SQLite.  
    """  
    print("Iniciando a criação da base de conhecimento em SQLite...")  
    engine \= create\_engine(f'sqlite:///{db\_path}')

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
        ncm\_final\_df.to\_sql('ncm', engine, if\_exists='replace', index=False)  
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
        segmentos\_df\['id'\] \= segmentos\_df.index \+ 1  
        segmentos\_df.to\_sql('segmentos', engine, if\_exists='replace', index=False)  
          
        all\_cest\_df \= all\_cest\_df.merge(segmentos\_df, on='segmento\_descricao', how='left')  
        cest\_regras\_df \= all\_cest\_df\[\['cest', 'descricao', 'id', 'situacao', 'vigencia\_inicio', 'vigencia\_fim'\]\].drop\_duplicates(subset=\['cest'\])  
        cest\_regras\_df.rename(columns={'id': 'segmento\_id'}, inplace=True)  
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
    import os  
    os.makedirs('data/processed', exist\_ok=True)  
    create\_knowledge\_base()

    engine \= create\_engine('sqlite:///data/processed/knowledge\_base.sqlite')  
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
