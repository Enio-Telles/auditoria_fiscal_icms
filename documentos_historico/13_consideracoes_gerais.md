O sistema multi-agentes rag de auditoria de icms de empresas deve dar a possibilidade, inclusive, na interface web frontend, de:
0) a classificação das mercadorias em termos de ncm e cest será feita com base na descrição da mercadoria, os ncm e cest serão analisados para confirmação: primeiro os agentes irão verificar se a classificação inicial está correta, caso não se confirme essa classificação, os agentes irão fazer nova classificação e determinar o ncm e o cest
0.1) um agente irá identificar e agregar produtos que são iguais, mas possuem descrições diferentes; por exemplo, produtos que tem descrições iguais já são agregados na consulta inicial (id_agregados), pois são iguais, mesmo que com ncm, cest, codigo_produto, codigo_barra e produto_id diferentes (nesse caso, a confirmação dos códigos ncm e cest será feita em relação à todas as classificações dos produtos agregados – que são iguais, com mesmo id_agregados); caso do codigo_produto seja igual, mas a descrição seja similar, é provável que sejam produtos iguais; caso tenham codigo_produto diferentes, e descrição similar, é possível que sejam produtos iguais
1) Na interface web frontend, ter uma página para cada opção de classificação: classificar apenas um produto, classificar um determinado número de produtos, ou classificar todos os produtos da base de dados da empresa;
2) a base de dados da empresa será importada de outros bancos de dados (como postgres e SQL), a exemplo da consulta do banco de dados referenciado à empresa do banco de dados db_04565289005297
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
# PostgreSQL Configuration
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=db_04565289005297
DB_USER=postgres
DB_PASSWORD=sefin
DB_SCHEMA=dbo
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
20) as atividades da empresa devem fazer parte do contexto da classificação do produto: por exemplo, vendedores de autopeças provavelmente vendem produtos do segmento CEST autopeças; farmácias vendem medicamentos; empresas que fazem venda porta a porta se enquadram nesse segmento do CEST 28
21) ao confirmar ou determinar o ncm, considerar:
	-> a atividade da empresa auxilia na identificação das mercadorias
	-> a estrutura hierárquica de abrangência do código NCM (capítulo → posição → subposição → item → subitem).
-> que código NCM  tem essa forma AABB.CC.DD - 8 dígitos (exemplo: 3004.90.69)
AA - Capítulo - 30 = -30 Produtos Farmacêuticos – abrange as demais posições, subposições e subitens
BB - Posição (tipo geral/função e aplicação) - 04 = Medicamentos
CC - Subposição (tipo específico/variação técnica ou industrial) - 90 = -90 outros
DD - Subitem (maior especificidade) – 9
-> o código ncm é estruturado com 8 dígitos em uma hierarquia de especificidade: os primeiros dígitos representam categorias mais abrangentes, enquanto os últimos produtos mais específicos: por exemplo, o capítulo 84 abrange o código 8407, que agrange o 8407.3 abrange os códigos 8407.31, 8407.31.1, que abrange 8407.31.10, que abrange 8407.31.90
	-> Usar Regras Gerais de Interpretação (RGI) do Sistema Harmonizado
o processo de identificação do NCM de uma mercadoria começa pela análise dos textos das posições e das Notas de Seção e de Capítulo. Se a mercadoria não puder ser classificada diretamente, as Regras Gerais 2 a 5 são aplicadas sequencialmente. Finalmente, a Regra 6 e as RGCs fornecem orientações para a classificação nos níveis de subposição, item e subitem, e para casos específicos como embalagens reutilizáveis e exceções ("Ex").
As Regras Gerais Complementares fornecem diretrizes adicionais para a interpretação e aplicação das Regras Gerais, especialmente em níveis mais detalhados da Nomenclatura.
	• RGC 1: Aplicação das Regras Gerais a Níveis Detalhados As Regras Gerais para Interpretação do Sistema Harmonizado aplicar-se-ão, mutatis mutandis, para determinar, dentro de cada posição ou subposição, o item aplicável e, dentro deste último, o subitem correspondente. Entende-se que apenas são comparáveis desdobramentos regionais (itens e subitens) do mesmo nível.
	• RGC 2: Regime de Classificação de Embalagens Reutilizáveis As embalagens que contêm mercadorias e que são claramente suscetíveis de utilização repetida (mencionadas na Regra 5 b)), seguirão seu próprio regime de classificação sempre que estejam submetidas aos regimes aduaneiros especiais de admissão temporária ou de exportação temporária. Caso contrário, seguirão o regime de classificação das mercadorias contidas.
Regra Geral Complementar da TIPI (RGC/TIPI)
RGC/TIPI 1: Determinação do "Ex" Aplicável As Regras Gerais para Interpretação do Sistema Harmonizado aplicar-se-ão, mutatis mutandis, para determinar, no âmbito de cada código, quando for o caso, o "Ex" aplicável, entendendo-se que apenas são comparáveis "Ex" de um mesmo código.
22) ao confirmar ou determinar o CEST, considerar:
	-> cada CEST tem um segmento e uma descrição específicos
	-> verificar se a descrição do produto se enquadra em alguma das descrições do produto
	-> verificar se o NCM tem um CEST correspondente
	-> o CEST tem uma descrição que deve corresponder à descrição do produto, que deve estar contido no segmento CEST
	-> todo CEST se relaciona a um NCM ou grupo de NCMs
  	-> Nem todo NCM tem CEST
    ->  Um CEST pode abranger vários NCMs
	->Um CEST pode abranger vários NCMs ou grupos de NCM
        nas tabelas que relacionam CEST NCM podem constar, por exemplo CEST relacionado a mais de um ncm, como no caso do CEST 01.001.00, que engloba os NCMs 3815.12.10 e 3815.12.90. Nesse a mercadoria deve se enquadrar nesse NCM e com base na descrição contida na tabela.
        Em outros casos, a o CEST pode se referir a uma categoria de NCMs, como no CEST 01.002.00, que se refere ao NCM 3917. Nesse caso, o NCM deve se enquadrar nessa categoria e estar conforme a descrição.
        Pode ocorrer também de, como ocorre no CEST 01.006.00, de a categoria de NCM estar mais detalhada, como a relação com o NCM 4010.3
    -> o produto pode ter ncm que se enquadra no cest mas não fazer parte do segmento, então essa descrição fica sem cest (exemplo, produtos não vendidos porta a porta não se enquadram no segmento 28 do CEST)
    -> No caso do segmento Venda Porta a Porta (Segmento 28, Anexo XXIX), depende da descrição da atividade da empresa (se faz venda porta a porta). Se não faz, não se enquadra. – considerar item 20)
        Operações que envolvem contribuintes que atuam na modalidade porta a porta devem observar o CEST previsto no Anexo XXIX, mesmo que as mercadorias estejam listadas em outros anexos.
    ->  seguir a estrutura do código CEST SS.III.DD (7 dígitos): identificar o segmento econômico e se o ncm se enquadra no CEST correspondente
            SS - Segmento Econômico
            III - item dentro do segmento
            DD - diferenciação ou agrupamento
23) as consultas RAG devem ser referenciadas com metadados dos arquivos de origem (arquivo, capítulo, campo se tabela)
24) base de dados
    Da data\raw\Tabela_NCM.xlsx, serão importados os campos Código (que representa o código ncm) e Descrição;
    O arquivo descricoes_ncm.json é uma reprodução da Tabela_NCM.xlsx, porém com a diferença que as descrições dos códigos são agrupadas com base na estrutura do código NCM
    Do arquivo conv_142_formatado.json, serão importadas todos os campos (Anexo se refere ao Anexo do Convênio 142, Segmento representa o número do segmento descrito pelo nome do Anexo; cest representa o código cest; ncm representa o grupo de ncms associados ao cest; descricao_oficial_cest representa a descrição do cest - um produto, para se enquadrar em um código cest, deve se enquadrar no segmento e na descrição);
    no arquivo produtos_selecionados (serão importados todos os campos), o campo gtin contém o número que descreve um produto único (como em codigo_barra); o campo descrição contém a descrição desse produto; o campo ncm contém o ncm desse produto; e o campo cest, se nulo, indica que não há código cest para esse produto e, se há código cest, representa o código cest do produto descrito);
    O arquivo CEST_RO representa as classificações de cest para o Estado de Rondônia, com lógica semelhante à do arquivo conv_142_formatado.json, porém com mais informações – cada CEST relaciona-se a um grupo de ncm (campo NCM/SH), e a uma descrição, com os MVAs, o campo situação refere-se à situação atual do Item da Tabela (que se referem ao CEST), se está vigente ou se foi alterado pela legislação. Os campos Início vig. e Fim vig. informam o período de início e fim da vigência (quando o segundo campo está vazio, ainda não ocorreu o fim da vigência)
    O arquivo nesh-2022_REGRAS_GERAIS.docx contém as regras gerais.
    O arquivo nesh-2022.pdf é um compêndio estruturado das notas explicativas sobre o código ncm (compreende o  conteúdo do arquivo nesh-2022_REGRAS_GERAIS.docx, porém é mais abrangente)
    A data\raw\Tabela_ABC_Farma_V2.xlsx contém a descrição completa dos produtos associada ao codigo_barras: são todos Medicamentos que se enquadram no capítulo 30 do NCM (3003 ou 3004) e no segmento 13 do CEST. Usar para identificar as mercadorias analisadas ncm e cest.
