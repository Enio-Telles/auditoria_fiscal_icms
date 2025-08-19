"""
Processador de documentos NCM - NESH 2022
Processa arquivo nesh-2022.pdf com regras gerais e notas explicativas NCM
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import re

# Tentar importar PyPDF2 para processamento de PDF
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("PyPDF2 não disponível. Usando dados simulados para NESH.")

logger = logging.getLogger(__name__)

class NESHProcessor:
    """
    Processador para documentos NESH (Notas Explicativas do Sistema Harmonizado)
    Processa nesh-2022.pdf com regras gerais de interpretação NCM
    """
    
    def __init__(self, data_path: str = "data/raw"):
        se    print(f"Orientação para '{test_desc}':")

    def aplicar_regras_sequenciais(self, produto_info: Dict) -> Dict:
        """
        Aplica regras gerais de interpretação sequencialmente conforme ponto 21 do plano
        
        Args:
            produto_info: Informações do produto (descricao, ncm_atual, etc.)
            
        Returns:
            Dict: Resultado da aplicação das regras
        """
        descricao = produto_info.get('descricao', '')
        ncm_atual = produto_info.get('ncm', '')
        atividade_empresa = produto_info.get('atividade_empresa', '')
        
        resultado = {
            'regras_aplicadas': [],
            'ncm_sugerido': '',
            'cest_sugerido': '',
            'confianca': 0.0,
            'justificativas': [],
            'estrutura_hierarquica': {}
        }
        
        # Regra 1: Verificar textos das posições
        regra1_resultado = self._aplicar_regra_1(descricao, atividade_empresa)
        resultado['regras_aplicadas'].append(regra1_resultado)
        
        # Se Regra 1 não resolve, aplicar Regra 2
        if not regra1_resultado.get('classificacao_definida', False):
            regra2_resultado = self._aplicar_regra_2(descricao, ncm_atual)
            resultado['regras_aplicadas'].append(regra2_resultado)
            
            # Se ainda não resolve, aplicar Regra 3
            if not regra2_resultado.get('classificacao_definida', False):
                regra3_resultado = self._aplicar_regra_3(descricao, produto_info)
                resultado['regras_aplicadas'].append(regra3_resultado)
                
                # Se ainda não resolve, aplicar Regra 4 (analogia)
                if not regra3_resultado.get('classificacao_definida', False):
                    regra4_resultado = self._aplicar_regra_4(descricao)
                    resultado['regras_aplicadas'].append(regra4_resultado)
        
        # Compilar resultado final
        self._compilar_resultado_final(resultado)
        
        return resultado
    
    def _aplicar_regra_1(self, descricao: str, atividade_empresa: str) -> Dict:
        """
        Aplica Regra 1: Valor Indicativo dos Títulos
        Considera atividade da empresa conforme ponto 20 do plano
        """
        resultado = {
            'regra': '1',
            'titulo': 'Valor Indicativo dos Títulos',
            'classificacao_definida': False,
            'observacoes': []
        }
        
        descricao_lower = descricao.lower()
        atividade_lower = atividade_empresa.lower()
        
        # Identificar capítulo baseado na descrição e atividade
        capitulo_identificado = None
        posicao_sugerida = None
        
        # Medicamentos (Capítulo 30)
        if any(termo in descricao_lower for termo in ['medicamento', 'remedio', 'farmaco', 'comprimido', 'capsula', 'xarope']):
            capitulo_identificado = '30'
            if any(termo in atividade_lower for termo in ['farmacia', 'drogaria', 'medicamentos']):
                resultado['confianca'] = 0.9
                resultado['observacoes'].append('Descrição indica medicamento e empresa do ramo farmacêutico')
            else:
                resultado['confianca'] = 0.7
                resultado['observacoes'].append('Descrição indica medicamento')
            
            # Determinar posição específica
            if any(termo in descricao_lower for termo in ['comprimido', 'capsula', 'drágea']):
                posicao_sugerida = '3004'  # Medicamentos acondicionados
            else:
                posicao_sugerida = '3003'  # Medicamentos não acondicionados
        
        # Autopeças (Capítulo 87)
        elif any(termo in descricao_lower for termo in ['autopeca', 'motor', 'peca', 'veiculo']):
            capitulo_identificado = '87'
            if any(termo in atividade_lower for termo in ['autopeca', 'veiculo', 'mecanica']):
                resultado['confianca'] = 0.8
                resultado['observacoes'].append('Descrição indica autopeças e empresa do ramo automotivo')
            
        if capitulo_identificado:
            resultado['classificacao_definida'] = True
            resultado['capitulo_sugerido'] = capitulo_identificado
            resultado['posicao_sugerida'] = posicao_sugerida
            resultado['observacoes'].append(f'Capítulo {capitulo_identificado} identificado pela descrição')
        
        return resultado
    
    def _aplicar_regra_2(self, descricao: str, ncm_atual: str) -> Dict:
        """
        Aplica Regra 2: Artigos Incompletos, Desmontados, Misturas e Compostos
        """
        resultado = {
            'regra': '2',
            'titulo': 'Artigos Incompletos, Desmontados, Misturas',
            'classificacao_definida': False,
            'observacoes': []
        }
        
        descricao_lower = descricao.lower()
        
        # Verificar se é artigo incompleto/desmontado (Regra 2A)
        if any(termo in descricao_lower for termo in ['incompleto', 'desmontado', 'kit', 'conjunto']):
            resultado['sub_regra'] = '2A'
            resultado['observacoes'].append('Produto pode ser incompleto ou desmontado')
            
            # Verificar características essenciais
            if 'medicamento' in descricao_lower:
                resultado['classificacao_definida'] = True
                resultado['ncm_sugerido'] = '3004'  # Manter capítulo medicamentos
                resultado['confianca'] = 0.8
        
        # Verificar se é mistura/composto (Regra 2B)
        elif any(termo in descricao_lower for termo in ['mistura', 'composto', 'associado', 'combinado']):
            resultado['sub_regra'] = '2B'
            resultado['observacoes'].append('Produto pode ser mistura ou composto')
            resultado['observacoes'].append('Aplicar Regra 3 para determinar característica essencial')
        
        return resultado
    
    def _aplicar_regra_3(self, descricao: str, produto_info: Dict) -> Dict:
        """
        Aplica Regra 3: Classificação em Duas ou Mais Posições
        """
        resultado = {
            'regra': '3',
            'titulo': 'Classificação em Múltiplas Posições',
            'classificacao_definida': False,
            'observacoes': []
        }
        
        # Simular análise de posições possíveis
        posicoes_possiveis = []
        
        # Para medicamentos, verificar subposições
        if 'medicamento' in descricao.lower():
            posicoes_possiveis = ['3003', '3004']
            
            # Regra 3A: Posição mais específica
            if any(termo in descricao.lower() for termo in ['comprimido', 'capsula']):
                resultado['posicao_especifica'] = '3004'
                resultado['sub_regra'] = '3A'
                resultado['observacoes'].append('Posição 3004 mais específica para medicamentos acondicionados')
                resultado['classificacao_definida'] = True
                resultado['confianca'] = 0.85
        
        return resultado
    
    def _aplicar_regra_4(self, descricao: str) -> Dict:
        """
        Aplica Regra 4: Artigos Mais Semelhantes (Analogia)
        """
        resultado = {
            'regra': '4',
            'titulo': 'Artigos Mais Semelhantes (Analogia)',
            'classificacao_definida': False,
            'observacoes': []
        }
        
        # Buscar produtos similares para analogia
        # Esta seria integrada com o processador ABC Farma V2
        resultado['observacoes'].append('Classificação por analogia baseada em produtos similares')
        resultado['metodo_analogia'] = 'denominacao_caracteristicas'
        
        return resultado
    
    def _compilar_resultado_final(self, resultado: Dict):
        """
        Compila resultado final da aplicação sequencial das regras
        """
        regras_com_classificacao = [
            regra for regra in resultado['regras_aplicadas'] 
            if regra.get('classificacao_definida', False)
        ]
        
        if regras_com_classificacao:
            # Usar primeira regra que definiu classificação
            regra_definitiva = regras_com_classificacao[0]
            resultado['ncm_sugerido'] = regra_definitiva.get('ncm_sugerido', '')
            resultado['confianca'] = regra_definitiva.get('confianca', 0.5)
            
            # Compilar justificativas
            for regra in resultado['regras_aplicadas']:
                resultado['justificativas'].extend(regra.get('observacoes', []))
    
    def validar_estrutura_hierarquica_ncm(self, ncm: str) -> Dict:
        """
        Valida estrutura hierárquica do NCM conforme ponto 21 do plano
        Formato: AABB.CC.DD (exemplo: 3004.90.69)
        """
        resultado = {
            'ncm': ncm,
            'valido': False,
            'estrutura': {},
            'observacoes': []
        }
        
        # Limpar NCM
        ncm_limpo = ncm.replace('.', '').replace('-', '').strip()
        
        if len(ncm_limpo) != 8 or not ncm_limpo.isdigit():
            resultado['observacoes'].append('NCM deve ter 8 dígitos numéricos')
            return resultado
        
        # Extrair estrutura hierárquica
        estrutura = {
            'capitulo': ncm_limpo[:2],        # AA - Capítulo
            'posicao': ncm_limpo[2:4],        # BB - Posição  
            'subposicao': ncm_limpo[4:6],     # CC - Subposição
            'item': ncm_limpo[6:7],           # D - Item
            'subitem': ncm_limpo[7:8]         # D - Subitem
        }
        
        resultado['estrutura'] = estrutura
        
        # Validações específicas
        capitulo = estrutura['capitulo']
        posicao = estrutura['posicao']
        
        # Validar capítulo de medicamentos
        if capitulo == '30':
            resultado['observacoes'].append('Capítulo 30 - Produtos Farmacêuticos')
            
            if posicao == '03':
                resultado['observacoes'].append('Posição 3003 - Medicamentos não acondicionados para venda a retalho')
            elif posicao == '04':
                resultado['observacoes'].append('Posição 3004 - Medicamentos acondicionados para venda a retalho')
            else:
                resultado['observacoes'].append(f'Posição {posicao} não é típica para medicamentos')
        
        # Validar hierarquia crescente de especificidade
        resultado['hierarquia_valida'] = True
        resultado['especificidade'] = f"Capítulo {capitulo} → Posição {posicao} → Subposição {estrutura['subposicao']}"
        
        resultado['valido'] = True
        return resultado
    
    def aplicar_regras_cest(self, produto_info: Dict) -> Dict:
        """
        Aplica regras para determinação de CEST conforme ponto 22 do plano
        
        Args:
            produto_info: Informações do produto incluindo NCM e atividade da empresa
            
        Returns:
            Dict: Resultado da aplicação das regras CEST
        """
        resultado = {
            'cest_sugerido': '',
            'segmento': '',
            'aplicavel': False,
            'observacoes': [],
            'confianca': 0.0
        }
        
        ncm = produto_info.get('ncm', '')
        descricao = produto_info.get('descricao', '')
        atividade_empresa = produto_info.get('atividade_empresa', '')
        
        # Medicamentos - Segmento 13
        if ncm.startswith('30') and any(termo in descricao.lower() for termo in ['medicamento', 'farmaco']):
            resultado['segmento'] = '13'
            resultado['segmento_nome'] = 'Medicamentos'
            resultado['aplicavel'] = True
            
            # CEST 13.001.00 - Medicamentos em geral
            if any(termo in descricao.lower() for termo in ['comprimido', 'capsula', 'drágea']):
                resultado['cest_sugerido'] = '13.001.00'
                resultado['confianca'] = 0.9
                resultado['observacoes'].append('CEST 13.001.00 - Medicamentos para uso humano em formas sólidas')
            
            # CEST 13.002.00 - Medicamentos líquidos
            elif any(termo in descricao.lower() for termo in ['xarope', 'solução', 'suspensão']):
                resultado['cest_sugerido'] = '13.002.00'
                resultado['confianca'] = 0.9
                resultado['observacoes'].append('CEST 13.002.00 - Medicamentos líquidos')
        
        # Venda Porta a Porta - Segmento 28 (conforme ponto 22 do plano)
        if 'porta a porta' in atividade_empresa.lower() or 'vendas diretas' in atividade_empresa.lower():
            resultado['segmento_adicional'] = '28'
            resultado['observacoes'].append('Empresa atua na modalidade porta a porta - aplicar Segmento 28')
            resultado['observacoes'].append('CEST do Anexo XXIX prevalece sobre outros anexos')
        
        # Autopeças - Segmento 01
        elif ncm.startswith('87') or 'autopeca' in atividade_empresa.lower():
            resultado['segmento'] = '01'
            resultado['segmento_nome'] = 'Autopeças'
            resultado['aplicavel'] = True
            resultado['observacoes'].append('Segmento 01 - Autopeças')
        
        # Verificar se produto tem NCM mas não se enquadra em nenhum CEST
        if not resultado['aplicavel'] and ncm:
            resultado['observacoes'].append('Produto possui NCM mas não se enquadra em nenhum segmento CEST')
        
        return resultado
f.data_path = Path(data_path)
        self.nesh_content = None
        self.processed_rules = {}
        self.ncm_explanations = {}
        
    def load_nesh_pdf(self) -> Dict:
        """
        Carrega e processa o arquivo nesh-2022.pdf
        """
        try:
            nesh_file = self.data_path / "nesh-2022.pdf"
            
            if not nesh_file.exists():
                logger.warning(f"Arquivo {nesh_file} não encontrado. Criando estrutura de exemplo...")
                return self._create_sample_nesh_data()
            
            # Tentar processar PDF real se PyPDF2 estiver disponível
            if PDF_AVAILABLE:
                logger.info(f"Processando PDF real: {nesh_file}")
                pdf_data = self._extract_from_pdf(nesh_file)
                if pdf_data:
                    self.nesh_content = pdf_data
                    return pdf_data
            
            # Fallback para dados simulados
            logger.info(f"Usando dados simulados do NESH")
            nesh_data = self._create_comprehensive_nesh_data()
            self.nesh_content = nesh_data
            
            logger.info(f"NESH processado com {len(nesh_data.get('regras_gerais', {}))} regras gerais")
            return nesh_data
            
        except Exception as e:
            logger.error(f"Erro ao processar NESH: {str(e)}")
            return {}
    
    def _extract_from_pdf(self, pdf_path: Path) -> Optional[Dict]:
        """
        Extrai dados do PDF NESH real
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                texto_completo = ""
                
                logger.info(f"Extraindo texto de {len(pdf_reader.pages)} páginas...")
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        texto_pagina = page.extract_text()
                        if texto_pagina.strip():
                            texto_completo += f"\n[PÁGINA {page_num + 1}]\n{texto_pagina}"
                    except Exception as e:
                        logger.warning(f"Erro ao extrair página {page_num + 1}: {e}")
                        continue
                
                if not texto_completo.strip():
                    logger.warning("Nenhum texto extraído do PDF")
                    return None
                
                # Processar texto extraído
                return self._process_extracted_text(texto_completo)
                
        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF: {e}")
            return None
    
    def _process_extracted_text(self, texto: str) -> Dict:
        """
        Processa texto extraído do PDF
        """
        resultado = {
            'metadados': {
                'fonte': 'nesh-2022.pdf',
                'tipo': 'NESH - Notas Explicativas do Sistema Harmonizado',
                'caracteres_extraidos': len(texto)
            },
            'regras_gerais': {},
            'capitulos': {},
            'posicoes': {},
            'notas_explicativas': {}
        }
        
        # Extrair Regras Gerais de Interpretação
        resultado['regras_gerais'] = self._extract_regras_gerais(texto)
        
        # Extrair estrutura de capítulos
        resultado['capitulos'] = self._extract_capitulos(texto)
        
        # Extrair posições NCM
        resultado['posicoes'] = self._extract_posicoes(texto)
        
        # Extrair notas explicativas
        resultado['notas_explicativas'] = self._extract_notas_explicativas(texto)
        
        logger.info(f"Processamento concluído: {len(resultado['regras_gerais'])} regras, "
                   f"{len(resultado['capitulos'])} capítulos, {len(resultado['posicoes'])} posições")
        
        return resultado
    
    def _extract_regras_gerais(self, texto: str) -> Dict:
        """Extrai as Regras Gerais de Interpretação do texto"""
        regras = {}
        
        # Padrões para identificar regras gerais
        padrao_rgi = re.compile(r'REGRA\s+GERAL\s+(\d+[A-Za-z]?)\s*[-–]?\s*(.+?)(?=REGRA\s+GERAL|\n\n|\Z)', 
                               re.IGNORECASE | re.DOTALL)
        
        regras_encontradas = padrao_rgi.findall(texto)
        
        for numero, texto_regra in regras_encontradas:
            regras[numero] = {
                'numero': numero,
                'texto': texto_regra.strip()[:1000],  # Limitar tamanho
                'tipo': 'Regra Geral de Interpretação'
            }
        
        # Extrair RGCs (Regras Gerais Complementares)
        padrao_rgc = re.compile(r'RGC\s+(\d+)\s*[-–]?\s*(.+?)(?=RGC|\n\n|\Z)', 
                               re.IGNORECASE | re.DOTALL)
        
        rgcs_encontradas = padrao_rgc.findall(texto)
        
        for numero, texto_rgc in rgcs_encontradas:
            regras[f"RGC{numero}"] = {
                'numero': f"RGC{numero}",
                'texto': texto_rgc.strip()[:1000],
                'tipo': 'Regra Geral Complementar'
            }
        
        # Se não encontrar regras no PDF, usar as regras conhecidas
        if not regras:
            regras = self._get_known_regras_gerais()
        
        return regras
    
    def _extract_capitulos(self, texto: str) -> Dict:
        """Extrai informações dos capítulos NCM"""
        capitulos = {}
        
        padrao_capitulo = re.compile(r'CAPÍTULO\s+(\d+)\s*[-–]\s*(.+?)(?=\n|\r)', re.IGNORECASE)
        capitulos_encontrados = padrao_capitulo.findall(texto)
        
        for numero, titulo in capitulos_encontrados:
            capitulos[numero] = {
                'numero': numero,
                'titulo': titulo.strip(),
                'descricao': f"Capítulo {numero} - {titulo.strip()}"
            }
        
        return capitulos
    
    def _extract_posicoes(self, texto: str) -> Dict:
        """Extrai posições NCM do texto"""
        posicoes = {}
        
        padrao_posicao = re.compile(r'(\d{2})\.(\d{2})\s*[-–]\s*(.+?)(?=\n|\r)', re.IGNORECASE)
        posicoes_encontradas = padrao_posicao.findall(texto)
        
        for capitulo, posicao, descricao in posicoes_encontradas:
            codigo_posicao = f"{capitulo}.{posicao}"
            posicoes[codigo_posicao] = {
                'capitulo': capitulo,
                'posicao': posicao,
                'codigo': codigo_posicao,
                'descricao': descricao.strip()
            }
        
        return posicoes
    
    def _extract_notas_explicativas(self, texto: str) -> Dict:
        """Extrai notas explicativas específicas"""
        notas = {}
        
        # Dividir texto em seções por posições
        secoes = re.split(r'\n(?=\d{2}\.\d{2})', texto)
        
        for secao in secoes:
            # Identificar código da posição
            match_posicao = re.match(r'(\d{2})\.(\d{2})', secao)
            if match_posicao:
                codigo = f"{match_posicao.group(1)}.{match_posicao.group(2)}"
                
                # Extrair informações relevantes da seção
                notas[codigo] = {
                    'texto_completo': secao[:2000],  # Limitar tamanho
                    'exclusoes': self._extract_exclusoes(secao),
                    'inclusoes': self._extract_inclusoes(secao),
                    'exemplos': self._extract_exemplos(secao)
                }
        
        return notas
    
    def _extract_exclusoes(self, texto: str) -> List[str]:
        """Extrai exclusões do texto"""
        padrao = re.compile(r'Excluem?-se.+?(?=\n\n|\d+\)|$)', re.IGNORECASE | re.DOTALL)
        return [exc.strip() for exc in padrao.findall(texto)]
    
    def _extract_inclusoes(self, texto: str) -> List[str]:
        """Extrai inclusões do texto"""
        padrao = re.compile(r'Incluem?-se.+?(?=\n\n|\d+\)|$)', re.IGNORECASE | re.DOTALL)
        return [inc.strip() for inc in padrao.findall(texto)]
    
    def _extract_exemplos(self, texto: str) -> List[str]:
        """Extrai exemplos do texto"""
        padrao = re.compile(r'(?:Por exemplo|Exemplo).+?(?=\n\n|\d+\)|$)', re.IGNORECASE | re.DOTALL)
        return [ex.strip() for ex in padrao.findall(texto)]
    
    def _get_known_regras_gerais(self) -> Dict:
        """
        Retorna regras gerais conhecidas como fallback
        Baseadas no arquivo Regras_gerais_complementares.md
        """
        return {
            "1": {
                "numero": "1",
                "titulo": "Valor Indicativo dos Títulos",
                "texto": "Os títulos de Seções, Capítulos e Subcapítulos têm apenas valor indicativo. Para efeitos legais, a classificação é determinada pelos textos das posições e pelas Notas de Seção e de Capítulo. As regras seguintes são aplicadas apenas se não forem contrárias a esses textos e notas. Isso significa que o texto das posições e as notas prevalecem sobre qualquer outra consideração para a classificação.",
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Base fundamental - textos das posições são determinantes"
            },
            "2A": {
                "numero": "2A",
                "titulo": "Artigos Incompletos ou Desmontados",
                "texto": "Qualquer referência a um artigo em uma posição abrange esse artigo mesmo que incompleto ou inacabado, desde que apresente as características essenciais do artigo completo. Abrange também o artigo completo, mesmo que se apresente desmontado ou por montar. Operações de montagem simples são consideradas, mas os elementos não podem exigir trabalho adicional para complementar sua condição de produto acabado.",
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Produtos incompletos com características essenciais"
            },
            "2B": {
                "numero": "2B",
                "titulo": "Matérias Misturadas e Artigos Compostos",
                "texto": "Qualquer referência a uma matéria em uma posição abrange essa matéria em estado puro, misturada ou associada a outras matérias. Da mesma forma, refere-se a obras feitas inteira ou parcialmente por essa matéria. A classificação desses produtos misturados ou artigos compostos é feita conforme os princípios da Regra 3.",
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Matérias puras, misturas e compostos"
            },
            "3A": {
                "numero": "3A",
                "titulo": "Posição Mais Específica",
                "texto": "A posição mais específica prevalece sobre as mais genéricas. Contudo, se duas ou mais posições se referirem a apenas uma parte dos componentes de um produto misturado/composto ou a um dos componentes de sortidos para venda a retalho, elas são consideradas igualmente específicas, mesmo que uma descrição seja mais precisa.",
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Especificidade prevalece sobre generalidade"
            },
            "3B": {
                "numero": "3B",
                "titulo": "Característica Essencial",
                "texto": "Se a Regra 3 a) não resolver a classificação, os produtos misturados, as obras compostas de matérias/artigos diferentes e os sortidos para venda a retalho são classificados pela matéria ou artigo que lhes confira a característica essencial, se for possível determinar. O fator que determina a característica essencial pode variar (natureza, volume, quantidade, peso, valor, importância para a utilização).",
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Característica essencial determina classificação"
            },
            "3C": {
                "numero": "3C",
                "titulo": "Última Posição em Ordem Numérica",
                "texto": "Nos casos em que as Regras 3 a) e 3 b) não permitem a classificação, a mercadoria é classificada na posição situada em último lugar na ordem numérica entre as suscetíveis de serem consideradas.",
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Critério de desempate por ordem numérica"
            },
            "4": {
                "numero": "4",
                "titulo": "Artigos Mais Semelhantes (Analogia)",
                "texto": "Mercadorias que não podem ser classificadas pelas Regras 1 a 3 são classificadas na posição correspondente aos artigos mais semelhantes. A analogia pode basear-se na denominação, nas características ou na utilização.",
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Classificação por analogia quando outras regras falham"
            },
            "5A": {
                "numero": "5A",
                "titulo": "Estojos e Artigos Semelhantes",
                "texto": "Estojos para câmeras fotográficas, instrumentos musicais, armas, instrumentos de desenho, joias e artigos semelhantes, especialmente fabricados para conter um artigo ou sortido determinado e suscetíveis de uso prolongado, quando apresentados com os artigos a que se destinam, classificam-se com estes últimos, desde que sejam do tipo normalmente vendido com tais artigos e não confiram ao conjunto a sua característica essencial.",
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Estojos seguem classificação do conteúdo principal"
            },
            "5B": {
                "numero": "5B",
                "titulo": "Embalagens",
                "texto": "Sem prejuízo da Regra 5 a), as embalagens que contêm mercadorias são classificadas com estas últimas quando são do tipo normalmente utilizado para seu acondicionamento. Contudo, esta disposição não é obrigatória quando as embalagens são claramente suscetíveis de utilização repetida.",
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Embalagens seguem mercadoria, exceto se reutilizáveis"
            },
            "6": {
                "numero": "6",
                "titulo": "Classificação em Subposições",
                "texto": "A classificação de mercadorias nas subposições de uma mesma posição é determinada, para efeitos legais, pelos textos dessas subposições e das Notas de subposição respectivas, bem como, mutatis mutandis (com as devidas modificações), pelas Regras precedentes. Apenas são comparáveis subposições do mesmo nível (ex: um travessão com um travessão, dois travessões com dois travessões). As Notas de Seção e de Capítulo também são aplicáveis, salvo disposições em contrário.",
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Regras aplicáveis a níveis detalhados (subposições)"
            },
            "RGC1": {
                "numero": "RGC1",
                "titulo": "Aplicação das Regras Gerais a Níveis Detalhados",
                "texto": "As Regras Gerais para Interpretação do Sistema Harmonizado aplicar-se-ão, mutatis mutandis, para determinar, dentro de cada posição ou subposição, o item aplicável e, dentro deste último, o subitem correspondente. Entende-se que apenas são comparáveis desdobramentos regionais (itens e subitens) do mesmo nível.",
                "tipo": "Regra Geral Complementar",
                "aplicacao": "Extensão das regras para itens e subitens regionais"
            },
            "RGC2": {
                "numero": "RGC2",
                "titulo": "Regime de Classificação de Embalagens Reutilizáveis",
                "texto": "As embalagens que contêm mercadorias e que são claramente suscetíveis de utilização repetida (mencionadas na Regra 5 b)), seguirão seu próprio regime de classificação sempre que estejam submetidas aos regimes aduaneiros especiais de admissão temporária ou de exportação temporária. Caso contrário, seguirão o regime de classificação das mercadorias contidas.",
                "tipo": "Regra Geral Complementar",
                "aplicacao": "Regimes especiais para embalagens reutilizáveis"
            },
            "RGC_TIPI1": {
                "numero": "RGC_TIPI1",
                "titulo": "Determinação do 'Ex' Aplicável",
                "texto": "As Regras Gerais para Interpretação do Sistema Harmonizado aplicar-se-ão, mutatis mutandis, para determinar, no âmbito de cada código, quando for o caso, o 'Ex' aplicável, entendendo-se que apenas são comparáveis 'Ex' de um mesmo código.",
                "tipo": "Regra Geral Complementar da TIPI",
                "aplicacao": "Classificação de exceções (Ex) na TIPI brasileira"
            }
        }
    
    def _create_comprehensive_nesh_data(self) -> Dict:
        """
        Cria estrutura completa das regras NESH baseada no sistema real
        """
        return {
            "regras_gerais": {
                "rg1": {
                    "titulo": "Regra Geral 1 - Textos das posições e notas",
                    "descricao": "Os títulos das Seções, Capítulos e Subcapítulos têm apenas valor indicativo. Para os efeitos legais, a classificação é determinada pelos textos das posições e das Notas de Seção e de Capítulo e, desde que não sejam contrárias aos textos das referidas posições e Notas, pelas Regras seguintes.",
                    "aplicacao": "Primeira regra a ser aplicada. Verificar se o produto se enquadra diretamente em alguma posição específica.",
                    "exemplos": [
                        "Produto claramente descrito em uma posição específica",
                        "Verificação de notas de seção e capítulo antes de aplicar outras regras"
                    ]
                },
                "rg2a": {
                    "titulo": "Regra Geral 2(a) - Artigos incompletos ou não acabados",
                    "descricao": "Qualquer referência a um artigo em determinada posição abrange esse artigo mesmo incompleto ou não acabado, desde que apresente, no estado em que se encontra, as características essenciais do artigo completo ou acabado.",
                    "aplicacao": "Para produtos não acabados que mantêm características essenciais",
                    "exemplos": [
                        "Motores sem algumas peças mas reconhecíveis como motores",
                        "Móveis desmontados para transporte"
                    ]
                },
                "rg2b": {
                    "titulo": "Regra Geral 2(b) - Misturas e artigos compostos",
                    "descricao": "Qualquer referência a uma matéria em determinada posição abrange essa matéria mesmo misturada ou associada a outras matérias. Da mesma forma, qualquer referência a obras de uma matéria determinada abrange as obras constituídas inteira ou parcialmente por essa matéria.",
                    "aplicacao": "Para misturas e produtos compostos de várias matérias",
                    "exemplos": [
                        "Ligas metálicas",
                        "Produtos químicos misturados"
                    ]
                },
                "rg3a": {
                    "titulo": "Regra Geral 3(a) - Posição mais específica",
                    "descricao": "A posição mais específica prevalece sobre as mais gerais.",
                    "aplicacao": "Quando múltiplas posições podem ser aplicáveis",
                    "exemplos": [
                        "Produto pode ser classificado como 'máquina' (geral) ou 'máquina de costura' (específica) - prevalece a específica"
                    ]
                },
                "rg3b": {
                    "titulo": "Regra Geral 3(b) - Matéria ou parte que confere caráter essencial",
                    "descricao": "Os produtos compostos, as obras constituídas por matérias diferentes ou constituídas pela reunião de artigos diferentes e as mercadorias apresentadas em sortidos classificam-se pela matéria ou artigo que lhes confira o caráter essencial.",
                    "aplicacao": "Para produtos compostos quando não há posição específica",
                    "exemplos": [
                        "Estojo com instrumentos - classificado pelo instrumento principal",
                        "Produto com embalagem especial - classificado pelo produto, não pela embalagem"
                    ]
                },
                "rg3c": {
                    "titulo": "Regra Geral 3(c) - Última posição na ordem numérica",
                    "descricao": "Nos casos em que as Regras 3(a) e 3(b) não permitam efetuar a classificação, os produtos classificam-se na posição situada em último lugar na ordem numérica, dentre as suscetíveis de validamente se tomarem em consideração.",
                    "aplicacao": "Último recurso quando outras regras não se aplicam",
                    "exemplos": [
                        "Produto pode ser classificado em múltiplas posições equivalentes - escolher a de maior número"
                    ]
                },
                "rg4": {
                    "titulo": "Regra Geral 4 - Produtos não classificáveis pelas regras anteriores",
                    "descricao": "Os produtos que não possam ser classificados por aplicação das regras acima enunciadas classificam-se na posição correspondente aos artigos mais análogos.",
                    "aplicacao": "Para produtos verdadeiramente novos ou únicos",
                    "exemplos": [
                        "Tecnologias novas não previstas na nomenclatura",
                        "Produtos híbridos sem classificação específica"
                    ]
                },
                "rg5a": {
                    "titulo": "Regra Geral 5(a) - Estojos e embalagens para venda a retalho",
                    "descricao": "Os estojos para aparelhos fotográficos, para instrumentos de música, para armas, para instrumentos de desenho, os colares e os artigos semelhantes, especialmente concebidos para conterem um artigo determinado ou um sortido, e suscetíveis de uso prolongado, classificam-se com os respectivos artigos quando destes tipos normalmente vendidos.",
                    "aplicacao": "Para embalagens reutilizáveis e estojos especiais",
                    "exemplos": [
                        "Estojo de violino - classificado com o violino",
                        "Caixa de ferramentas especial - classificada com as ferramentas"
                    ]
                },
                "rg5b": {
                    "titulo": "Regra Geral 5(b) - Matérias de acondicionamento e recipientes",
                    "descricao": "Ressalvadas as disposições da Regra 5(a) acima, as matérias de acondicionamento e os recipientes apresentados com as mercadorias que acondicionam classificam-se com essas mercadorias quando sejam dos tipos normalmente utilizados para o acondicionamento das mesmas.",
                    "aplicacao": "Para embalagens normais apresentadas com produtos",
                    "exemplos": [
                        "Garrafa com vinho - classificada com o vinho",
                        "Lata com conserva - classificada com a conserva"
                    ]
                },
                "rg6": {
                    "titulo": "Regra Geral 6 - Classificação de subposições",
                    "descricao": "A classificação de mercadorias nas subposições de uma mesma posição é determinada, para efeitos legais, pelos textos dessas subposições e das Notas de subposições respectivas, assim como, mutatis mutandis, pelas Regras precedentes.",
                    "aplicacao": "Para classificação em níveis mais específicos (subposições)",
                    "exemplos": [
                        "Após determinar a posição (4 dígitos), aplicar as mesmas regras para subposições (6 dígitos)"
                    ]
                }
            },
            "regras_complementares": {
                "rgc1": {
                    "titulo": "RGC 1 - Aplicação a níveis detalhados",
                    "descricao": "As Regras Gerais para Interpretação do Sistema Harmonizado aplicar-se-ão, mutatis mutandis, para determinar, dentro de cada posição ou subposição, o item aplicável e, dentro deste último, o subitem correspondente.",
                    "aplicacao": "Para classificação em 8 dígitos (itens e subitens)",
                    "observacao": "Apenas são comparáveis desdobramentos regionais do mesmo nível"
                },
                "rgc2": {
                    "titulo": "RGC 2 - Embalagens reutilizáveis",
                    "descricao": "As embalagens que contêm mercadorias e que são claramente suscetíveis de utilização repetida seguirão seu próprio regime de classificação sempre que estejam submetidas aos regimes aduaneiros especiais.",
                    "aplicacao": "Para embalagens reutilizáveis em regimes especiais",
                    "condicoes": "Admissão temporária ou exportação temporária"
                },
                "rgc_tipi": {
                    "titulo": "RGC/TIPI 1 - Determinação do Ex aplicável",
                    "descricao": "As Regras Gerais aplicar-se-ão para determinar, no âmbito de cada código, o Ex aplicável.",
                    "aplicacao": "Para códigos com exceções (Ex)",
                    "observacao": "Apenas são comparáveis Ex de um mesmo código"
                }
            },
            "estrutura_ncm": {
                "formato": "AABB.CC.DD (8 dígitos)",
                "componentes": {
                    "AA": "Capítulo - categoria mais abrangente",
                    "BB": "Posição - tipo geral/função e aplicação",
                    "CC": "Subposição - tipo específico/variação técnica",
                    "DD": "Subitem - maior especificidade"
                },
                "hierarquia": "Cada nível representa maior especificidade",
                "exemplo": {
                    "codigo": "3004.90.69",
                    "significado": {
                        "30": "Capítulo 30 - Produtos Farmacêuticos",
                        "04": "Posição 3004 - Medicamentos",
                        "90": "Subposição 3004.90 - Outros",
                        "69": "Subitem - Especificação detalhada"
                    }
                }
            },
            "notas_importantes": {
                "ordem_aplicacao": [
                    "1. Verificar textos das posições e notas (RG1)",
                    "2. Considerar produtos incompletos/não acabados (RG2a)",
                    "3. Considerar misturas e compostos (RG2b)", 
                    "4. Aplicar hierarquia de especificidade (RG3a-c)",
                    "5. Buscar produtos análogos se necessário (RG4)",
                    "6. Considerar embalagens e estojos (RG5a-b)",
                    "7. Aplicar mesmas regras para subposições (RG6)"
                ],
                "principios_fundamentais": [
                    "Especificidade prevalece sobre generalidade",
                    "Textos das posições são determinantes",
                    "Notas de seção e capítulo são vinculantes",
                    "Classificação deve ser inequívoca",
                    "Aplicação sequencial das regras"
                ]
            },
            "capitulos_farmaceuticos": {
                "capitulo_30": {
                    "titulo": "Produtos Farmacêuticos",
                    "abrangencia": "Medicamentos de uso humano e veterinário",
                    "posicoes_principais": {
                        "3003": "Medicamentos não acondicionados para venda a retalho",
                        "3004": "Medicamentos acondicionados para venda a retalho",
                        "3005": "Pastas, gazes, ataduras medicamentosas",
                        "3006": "Preparações e artigos farmacêuticos"
                    },
                    "notas_especificas": [
                        "Produtos devem ter propriedades terapêuticas ou profiláticas",
                        "Destinação para diagnóstico, tratamento ou prevenção de doenças",
                        "Concentração de princípios ativos relevante para classificação"
                    ]
                }
            }
        }
    
    def _create_sample_nesh_data(self) -> Dict:
        """
        Cria dados simplificados de exemplo quando arquivo não está disponível
        """
        return {
            "regras_gerais": {
                "rg1": {
                    "titulo": "Regra Geral 1",
                    "descricao": "Classificação pelos textos das posições e notas",
                    "aplicacao": "Primeira verificação"
                }
            },
            "exemplo": True,
            "fonte": "Dados de exemplo - arquivo PDF não encontrado"
        }
    
    def get_classification_rules(self, ncm_code: str = None) -> Dict:
        """
        Retorna regras de classificação aplicáveis
        """
        if self.nesh_content is None:
            self.load_nesh_pdf()
        
        rules = self.nesh_content.get('regras_gerais', {})
        
        if ncm_code:
            # Filtra regras específicas para o NCM
            capitulo = ncm_code[:2] if len(ncm_code) >= 2 else None
            if capitulo == "30":
                # Regras específicas para produtos farmacêuticos
                farm_rules = self.nesh_content.get('capitulos_farmaceuticos', {}).get('capitulo_30', {})
                return {
                    'regras_gerais': rules,
                    'regras_especificas': farm_rules,
                    'aplicavel_para': f"NCM {ncm_code} - Capítulo {capitulo}"
                }
        
        return {
            'regras_gerais': rules,
            'estrutura_ncm': self.nesh_content.get('estrutura_ncm', {}),
            'ordem_aplicacao': self.nesh_content.get('notas_importantes', {}).get('ordem_aplicacao', [])
        }
    
    def validate_ncm_structure(self, ncm_code: str) -> Dict:
        """
        Valida estrutura do código NCM conforme regras NESH
        """
        validation = {
            'valido': False,
            'formato_correto': False,
            'observacoes': [],
            'estrutura_detectada': {}
        }
        
        # Remove pontos e espaços
        clean_ncm = re.sub(r'[.\s]', '', str(ncm_code))
        
        # Verifica formato (8 dígitos)
        if re.match(r'^\d{8}$', clean_ncm):
            validation['formato_correto'] = True
            
            # Decompõe estrutura
            validation['estrutura_detectada'] = {
                'capitulo': clean_ncm[:2],
                'posicao': clean_ncm[:4],
                'subposicao': clean_ncm[:6],
                'subitem': clean_ncm,
                'formato_usual': f"{clean_ncm[:4]}.{clean_ncm[4:6]}.{clean_ncm[6:]}"
            }
            
            # Verifica capítulo
            capitulo = int(clean_ncm[:2])
            if 1 <= capitulo <= 99:
                validation['valido'] = True
                validation['observacoes'].append(f"Capítulo {capitulo:02d} válido")
                
                # Verifica se é farmacêutico
                if capitulo == 30:
                    validation['observacoes'].append("Produto farmacêutico - Capítulo 30")
                    validation['regras_especiais'] = self.nesh_content.get('capitulos_farmaceuticos', {}).get('capitulo_30', {})
            else:
                validation['observacoes'].append(f"Capítulo {capitulo} inválido (deve ser 01-99)")
        else:
            validation['observacoes'].append("Formato inválido - deve ter 8 dígitos")
        
        return validation
    
    def get_classification_guidance(self, product_description: str, current_ncm: str = None) -> Dict:
        """
        Fornece orientação para classificação baseada nas regras NESH
        """
        if self.nesh_content is None:
            self.load_nesh_pdf()
        
        guidance = {
            'regras_aplicaveis': [],
            'recomendacoes': [],
            'verificacoes_necessarias': [],
            'ncm_sugerido': current_ncm
        }
        
        # Analisa descrição do produto
        desc_upper = product_description.upper()
        
        # Identifica se é produto farmacêutico
        termos_farmaceuticos = ['MEDICAMENTO', 'COMPRIMIDO', 'CÁPSULA', 'XAROPE', 'POMADA', 'DIPIRONA', 'PARACETAMOL', 'IBUPROFENO']
        is_farmaceutico = any(termo in desc_upper for termo in termos_farmaceuticos)
        
        if is_farmaceutico:
            guidance['regras_aplicaveis'].append('RG1 - Verificar posições do Capítulo 30')
            guidance['recomendacoes'].append('Produto aparenta ser farmacêutico - verificar NCM 3003.xx.xx ou 3004.xx.xx')
            guidance['verificacoes_necessarias'].extend([
                'Verificar se é medicamento para venda a retalho (3004) ou não (3003)',
                'Confirmar princípio ativo e concentração',
                'Verificar forma farmacêutica (comprimido, cápsula, etc.)'
            ])
            
            if not current_ncm or not current_ncm.startswith('30'):
                guidance['ncm_sugerido'] = '3004.90.69'  # Posição genérica para outros medicamentos
        
        # Verifica NCM atual se fornecido
        if current_ncm:
            validation = self.validate_ncm_structure(current_ncm)
            if validation['valido']:
                guidance['ncm_atual_valido'] = True
                guidance['observacoes_ncm_atual'] = validation['observacoes']
            else:
                guidance['ncm_atual_valido'] = False
                guidance['problemas_ncm_atual'] = validation['observacoes']
        
        # Adiciona regras gerais sempre aplicáveis
        guidance['regras_sempre_aplicaveis'] = [
            'RG1 - Verificar textos das posições e notas de seção/capítulo',
            'RG3(a) - Posição mais específica prevalece sobre a mais geral',
            'RG6 - Aplicar mesmas regras para subposições e subitens'
        ]
        
        return guidance
    
    def export_nesh_rules(self, output_path: str = "data/processed") -> str:
        """
        Exporta regras NESH processadas para arquivo JSON
        """
        if self.nesh_content is None:
            self.load_nesh_pdf()
        
        output_file = Path(output_path) / "nesh_2022_rules.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        export_data = {
            'metadata': {
                'fonte': 'nesh-2022.pdf',
                'processado_em': str(Path(__file__).name),
                'versao': '2022'
            },
            'conteudo': self.nesh_content
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Regras NESH exportadas para: {output_file}")
        return str(output_file)
    
    def validate_ncm(self, ncm: str, descricao: str = "") -> Dict:
        """
        Valida código NCM usando regras NESH
        
        Args:
            ncm: Código NCM para validar
            descricao: Descrição do produto (opcional)
            
        Returns:
            Dict: Resultado da validação
        """
        return self.validate_ncm_structure(ncm)
    
    def get_classification_guidance(self, descricao: str, ncm: str = "") -> Dict:
        """
        Fornece orientação para classificação baseada nas regras NESH
        
        Args:
            descricao: Descrição do produto
            ncm: Código NCM (opcional)
            
        Returns:
            Dict: Orientação de classificação
        """
        guidance = {
            'regras_aplicaveis': [],
            'recomendacoes': []
        }
        
        descricao_lower = descricao.lower()
        
        # Identificar tipo de produto e aplicar regras relevantes
        if any(termo in descricao_lower for termo in ['medicamento', 'farmacêutico', 'comprimido', 'cápsula', 'xarope']):
            guidance['regras_aplicaveis'].append('RG1 - Verificar posições do Capítulo 30')
            guidance['recomendacoes'].append('Produto aparenta ser farmacêutico - verificar NCM 3003.xx.xx ou 3004.xx.xx')
            
            if 'comprimido' in descricao_lower or 'cápsula' in descricao_lower:
                guidance['recomendacoes'].append('Forma sólida - provável posição 3004.xx.xx')
        
        if ncm and ncm.startswith('30'):
            guidance['regras_aplicaveis'].append('RG2A - Produto farmacêutico completo')
            guidance['recomendacoes'].append('NCM capítulo 30 apropriado para produtos farmacêuticos')
        
        return guidance

def main():
    """Função principal para teste do processador NESH"""
    processor = NESHProcessor()
    
    # Carrega NESH
    nesh_data = processor.load_nesh_pdf()
    print(f"NESH carregado com {len(nesh_data.get('regras_gerais', {}))} regras gerais")
    
    # Testa validação de NCM
    def validate_ncm(self, ncm: str, descricao: str = "") -> Dict:
        """
        Valida código NCM usando regras NESH
        
        Args:
            ncm: Código NCM para validar
            descricao: Descrição do produto (opcional)
            
        Returns:
            Dict: Resultado da validação
        """
        return self.validate_ncm_structure(ncm, descricao)
    
    def get_classification_guidance(self, descricao: str, ncm: str = "") -> Dict:
        """
        Fornece orientação para classificação baseada nas regras NESH
        
        Args:
            descricao: Descrição do produto
            ncm: Código NCM (opcional)
            
        Returns:
            Dict: Orientação de classificação
        """
        guidance = {
            'regras_aplicaveis': [],
            'recomendacoes': []
        }
        
        descricao_lower = descricao.lower()
        
        # Identificar tipo de produto e aplicar regras relevantes
        if any(termo in descricao_lower for termo in ['medicamento', 'farmacêutico', 'comprimido', 'cápsula', 'xarope']):
            guidance['regras_aplicaveis'].append('RG1 - Verificar posições do Capítulo 30')
            guidance['recomendacoes'].append('Produto aparenta ser farmacêutico - verificar NCM 3003.xx.xx ou 3004.xx.xx')
            
            if 'comprimido' in descricao_lower or 'cápsula' in descricao_lower:
                guidance['recomendacoes'].append('Forma sólida - provável posição 3004.xx.xx')
        
        if ncm and ncm.startswith('30'):
            guidance['regras_aplicaveis'].append('RG2A - Produto farmacêutico completo')
            guidance['recomendacoes'].append('NCM capítulo 30 apropriado para produtos farmacêuticos')
        
        return guidance
    
    test_ncm = "3004.90.69"
    validation = processor.validate_ncm_structure(test_ncm)
    print(f"\nValidação NCM {test_ncm}:")
    print(f"Válido: {validation['valido']}")
    print(f"Observações: {validation['observacoes']}")
    
    # Testa orientação de classificação
    test_desc = "DIPIRONA SÓDICA 500MG COMPRIMIDO"
    guidance = processor.get_classification_guidance(test_desc, test_ncm)
    print(f"\nOrientação para '{test_desc}':")
    print(f"Regras aplicáveis: {guidance['regras_aplicaveis']}")
    print(f"Recomendações: {guidance['recomendacoes']}")
    
    # Exporta regras
    output_file = processor.export_nesh_rules()
    print(f"\nRegras exportadas para: {output_file}")

if __name__ == "__main__":
    main()
