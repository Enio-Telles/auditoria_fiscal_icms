O sistema multi-agentes rag de auditoria de icms de empresas deve dar a possibilidade, inclusive, na interface web frontend, de: 
0) a classificação das mercadorias em termos de ncm e cest será feita com base na descrição da mercadoria; primeiro os agentes irão verificar se a classificação inicial está correta, caso não se confirme essa classificação, os agentes irão fazer nova classificação
0.1) um agente irá identificar e agregar produtos que são iguais, mas possuem descrições diferentes; por exemplo, produtos que tem descrições iguais já são agregados na consulta inicial (id_agregados), pois são iguais, mesmo que com ncm, cest, codigo_produto, codigo_barra e produto_id diferentes (nesse caso, a confirmação dos códigos ncm e cest será feita em relação à todas as classificações dos produtos agregados – que são iguais, com mesmo id_agregados); caso do codigo_produto seja igual, mas a descrição seja similar, é provável que sejam produtos iguais; caso tenham codigo_produto diferentes, e descrição similar, é possível que sejam produtos iguais
1) Na interface web frontend, ter uma página para cada opção de classificação: classificar apenas um produto, classificar um determinado número de produtos, ou classificar todos os produtos da base de dados da empresa;
2) a base de dados da empresa será importada de outros bancos de dados (como postgres e SQL), a exemplo da consulta
“””
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
            WHERE descricao_produto IS NOT NULL
”””
'''
# exemplo PostgreSQL externo a ser importado pelo sistema
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=db_04565289005297
DB_USER=postgres
DB_PASSWORD=sefin
DB_SCHEMA=dbo
'''
3) ter uma página de login usuário;
4) faça e armazene cadastro de usuários e de empresas a serem analisadas em banco de dados do sistema;
a) criar bando de dados usuários – nome – email – cargo - identificação - primeiro: Enio Telles – eniotelles@gmail.com
b) criar banco de dados empresas – dados gerais (como no sintegra, sócios, contador, endereço) –> obrigatórios: nome e atividades
-> identificar empresa cujos produtos estão sendo classificados e agrupados (futuramente, serão implementadas outras funções relacionadas à análise das atividades da empresa) e possibilitar selecionar, ou cadastrar nova empresa)
->dentro do banco de dados da empresa existirão várias tabelas 
- (modularidade que comporte verificação de estoques posterior) – 
pretendo que, futuramente, importe dados da efd (diveras tabelas inter-relacionadas) 
- no sistema atual, é para ter banco de dados de produtos, importado de outro banco de dados (Postgres), em que o nome do banco de dados identifica a empresa (é um outro banco de dados sobre a empresa, cujo nome é, por exemplo, DB_NAME=db_04565289005297)
	->possibilidade de importar dados de bancos de dados oracle sql e postgres
5) após login do usuário, apresentar página com todas as possibilidades do sistema em botões, ícones ou links
6) possibilitar opções de reimportar dados dos produtos e reinicar a classificação (por exemplo, reimportar dados das mercadorias e reiniciar classificações)
7) ao importar dados identificar de onde vai extrair os dados (PostGres, SQL, nome do banco de dados) - Incialmente vai importar dados do postgres de mercadorias (por exemplo: vai importar as colunas produto_id, descricao_produto, codigo_barra, código_produto, ncm e cest da tabela dbo.produto do banco de dados DB_NAME=db_04565289005297 – são as mercadorias a serem classificadas) -> criar tabela mercadorias a classificar
8) ao fazer a consulta no banco de dados relativo à empresa para importar para os bancos de dados do sistema (também um por empresa):
->  como comentado em 0.1) , é feita uma agregação inicial mediante a consulta sql (descrições iguais)
-_ Criar tabelas dentro do banco do sistema por empresa, com tabelas sobre os dados cadastrais da empresa e tabelas sobre os produtos (acessíveis por meio da interface web)
9) possibilitar executar as funçõesoes de apenas um agente (acessível pelo ambiente web): enriquecer descrições, classificação ncm, classificação cest, agregação de produtos iguais com descrições diferentes – 
10) no contexto das classificações e agregações pelo sistema, armazenar nos bancos de dados as justificativas e os contextos RAG que fundamentaram as decisões 
11) dar a possibilidade (inclusive na interface web) de escolher quantas mercadorias classificar ou todas
- possibilitar retomar a classificação ou classificar as mercadorias restantes ou quantas mais classificar - identificar quais dados devem constar
12) dar a possibilidade de visualizar classificações realizadas
13) dar a possibilidade de reclassificar - classificar novamente
14) dar a possibilidade de somente agregar mercadorias
15) em relação às mercadorias agregadas pelo sistema, identificar quantas mercadorias foram unidas em uma só e fazer um relatório completo sobre a agregação (informar em uma página no formato web – o sistema é local)
16) dar a possibilidade de revisar a classificação, com visualização de todas as informações sobre a classificação, inclusive justificativas e consultas RAG que fundamentaram a classificação (todos os campos, inclusive produto_id, descricao_produto, codigo_barra, código_produto, ncm e cest), com identificação do usuário que fez a correção: confirmar, corrigir e incluir a classificação no golden set (tornar possível incluir as classificações corrigidas no golden set)
17) criação de golden set para futuramente realimentar o sistema – criar um banco próprio a ser usado por todas as empresas - índice próprio- referência a fonte: usuário e empresa -
18) Possibilidade de revisar e alterar golden set por dados e por mercadorias (inclusive na inteface web)
19) cada decisão dos agentes deve ser documentada: acessos a bancos de dados RAG, contexto, justificativas para decisões 
20)  dar a possibilidade de usar outros llm locais além do llama3, como o gemma3, gemma3n, gpt-oss:20– 




 
