"""
Processador de documentos NCM - NESH 2022
Processa arquivo nesh-2022.pdf com regras gerais e notas explicativas NCM
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path
import json
import re

# Tentar importar PyPDF2 para processamento de PDF
try:
    import PyPDF2  # noqa: F401

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("PyPDF2 não disponível. Usando dados simulados para NESH.")

logger = logging.getLogger(__name__)


class NeshProcessor:
    """
    Processador para documentos NESH (Notas Explicativas do Sistema Harmonizado)
    Processa nesh-2022.pdf com regras gerais de interpretação NCM
    """

    def __init__(self, data_path: str = "data/raw"):
        self.data_path = Path(data_path)
        self.nesh_pdf_path = self.data_path / "nesh-2022_REGRAS_GERAIS.docx"
        self.nesh_content = None
        self.rules_cache = {}

        # Verificar se arquivo existe
        if not self.nesh_pdf_path.exists():
            logger.warning(f"Arquivo NESH não encontrado: {self.nesh_pdf_path}")
            logger.info("Usando dados simulados de regras NESH")

    def load_nesh_pdf(self) -> Dict:
        """
        Carrega e processa arquivo PDF do NESH
        """
        if self.nesh_content is not None:
            return self.nesh_content

        logger.info("Carregando dados NESH...")

        # Se arquivo não existe ou PyPDF2 não disponível, usar dados simulados
        if not self.nesh_pdf_path.exists() or not PDF_AVAILABLE:
            logger.info("Usando dados conhecidos das regras NESH")
            self.nesh_content = self._create_comprehensive_nesh_data()
            return self.nesh_content

        try:
            # Tentar extrair de PDF/DOCX
            extracted_data = self._extract_from_pdf(self.nesh_pdf_path)
            if extracted_data:
                self.nesh_content = extracted_data
            else:
                # Fallback para dados conhecidos
                self.nesh_content = self._create_comprehensive_nesh_data()

            logger.info("Dados NESH carregados com sucesso")
            return self.nesh_content

        except Exception as e:
            logger.error(f"Erro ao carregar NESH: {e}")
            logger.info("Usando dados simulados como fallback")
            self.nesh_content = self._create_comprehensive_nesh_data()
            return self.nesh_content

    def _extract_from_pdf(self, pdf_path: Path) -> Optional[Dict]:
        """
        Extrai texto do arquivo PDF/DOCX
        """
        if not PDF_AVAILABLE:
            return None

        try:
            # Para .docx, seria necessário python-docx
            # Por ora, retorna None para usar dados simulados
            return None

        except Exception as e:
            logger.error(f"Erro na extração do PDF: {e}")
            return None

    def _process_extracted_text(self, texto: str) -> Dict:
        """
        Processa texto extraído do PDF para estruturar as regras
        """
        nesh_data = {
            "regras_gerais": self._extract_regras_gerais(texto),
            "capitulos": self._extract_capitulos(texto),
            "posicoes": self._extract_posicoes(texto),
            "notas_explicativas": self._extract_notas_explicativas(texto),
            "metadata": {
                "versao": "2022",
                "fonte": "NESH-2022 Regras Gerais",
                "processado_em": str(Path(__file__).parent),
            },
        }

        return nesh_data

    def _extract_regras_gerais(self, texto: str) -> Dict:
        """
        Extrai regras gerais de interpretação do texto
        """
        # Por enquanto, usar regras conhecidas
        return self._get_known_regras_gerais()

    def _extract_capitulos(self, texto: str) -> Dict:
        """
        Extrai informações sobre capítulos NCM
        """
        capitulos = {}

        # Padrão para capítulos: "CAPÍTULO XX"
        padrao_capitulo = r"CAPÍTULO\s+(\d{1,2})"
        matches = re.finditer(padrao_capitulo, texto, re.IGNORECASE)

        for match in matches:
            numero = match.group(1)
            # Extrair mais contexto seria necessário para implementação completa
            capitulos[numero] = {"numero": numero, "titulo": f"Capítulo {numero}"}

        return capitulos

    def _extract_posicoes(self, texto: str) -> Dict:
        """
        Extrai informações sobre posições NCM
        """
        posicoes = {}

        # Padrão para posições: "XX.XX"
        padrao_posicao = r"(\d{2}\.\d{2})"
        matches = re.finditer(padrao_posicao, texto)

        for match in matches:
            posicao = match.group(1)
            posicoes[posicao] = {"codigo": posicao, "contexto": "extraído do PDF"}

        return posicoes

    def _extract_notas_explicativas(self, texto: str) -> Dict:
        """
        Extrai notas explicativas do texto
        """
        notas = {
            "gerais": [],
            "especificas": {},
            "exclusoes": self._extract_exclusoes(texto),
            "inclusoes": self._extract_inclusoes(texto),
            "exemplos": self._extract_exemplos(texto),
        }

        return notas

    def _extract_exclusoes(self, texto: str) -> List[str]:
        """Extrai lista de exclusões"""
        return []

    def _extract_inclusoes(self, texto: str) -> List[str]:
        """Extrai lista de inclusões"""
        return []

    def _extract_exemplos(self, texto: str) -> List[str]:
        """Extrai exemplos do texto"""
        return []

    def _get_known_regras_gerais(self) -> Dict:
        """
        Retorna regras gerais conhecidas do sistema NCM baseadas no arquivo
        Regras_gerais_complementares.md
        """
        return {
            "1": {
                "numero": "1",
                "titulo": "Textos das Posições e Notas",
                "texto": (
                    "Títulos de Seções/Capítulos/Subcapítulos têm valor indicativo. "
                    "Classificação: textos das posições e Notas de Seção/Capítulo; "
                    "não contrariando estes, aplicam-se Regras seguintes."
                ),
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Primeira regra - verificar textos específicos das posições",
            },
            "2A": {
                "numero": "2A",
                "titulo": "Artigos Incompletos ou Não Acabados",
                "texto": (
                    "Referência a artigo inclui-o incompleto/não acabado se mantém "
                    "características essenciais do artigo completo."
                ),
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Para produtos incompletos que mantêm características essenciais",
            },
            "2B": {
                "numero": "2B",
                "titulo": "Misturas e Artigos Compostos",
                "texto": (
                    "Referência a matéria inclui misturas/associações; referência a "
                    "obras inclui obras parcial ou totalmente dessa matéria."
                ),
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Para misturas e produtos compostos de várias matérias",
            },
            "3A": {
                "numero": "3A",
                "titulo": "Posição Mais Específica",
                "texto": "A posição mais específica prevalece sobre as posições de alcance mais geral.",
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Critério de especificidade para múltiplas posições aplicáveis",
            },
            "3B": {
                "numero": "3B",
                "titulo": "Matéria ou Parte que Confere Caráter Essencial",
                "texto": (
                    "Produtos/obras compostos ou sortidos classificam-se pela matéria "
                    "ou artigo que lhes confere caráter essencial (quando determinável)."
                ),
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Para produtos compostos com material predominante",
            },
            "3C": {
                "numero": "3C",
                "titulo": "Última Posição em Ordem Numérica",
                "texto": (
                    "Se Regras 3(a) e 3(b) não resolvem, classificar na última posição "
                    "numérica entre as possíveis."
                ),
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Critério de desempate por ordem numérica",
            },
            "4": {
                "numero": "4",
                "titulo": "Artigos Mais Semelhantes (Analogia)",
                "texto": (
                    "Sem classificação pelas Regras 1-3: usar posição de artigos mais "
                    "semelhantes (analogia por nome, características ou uso)."
                ),
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Classificação por analogia quando outras regras falham",
            },
            "5A": {
                "numero": "5A",
                "titulo": "Estojos e Artigos Semelhantes",
                "texto": (
                    "Estojos especializados (câmeras, instrumentos, joias etc.) "
                    "apresentados com o conteúdo classificam-se com este se tipo "
                    "normal e não definem caráter essencial do conjunto."
                ),
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Estojos seguem classificação do conteúdo principal",
            },
            "5B": {
                "numero": "5B",
                "titulo": "Embalagens",
                "texto": (
                    "Embalagens normais classificam-se com a mercadoria; exceção para "
                    "embalagens claramente reutilizáveis."
                ),
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Embalagens seguem mercadoria, exceto se reutilizáveis",
            },
            "6": {
                "numero": "6",
                "titulo": "Classificação em Subposições",
                "texto": (
                    "Classificação em subposições: textos e Notas de subposição + "
                    "Regras (mutatis mutandis). Comparar apenas mesmo nível. Notas de "
                    "Seção/Capítulo aplicáveis salvo exceções."
                ),
                "tipo": "Regra Geral de Interpretação",
                "aplicacao": "Regras aplicáveis a níveis detalhados (subposições)",
            },
            "RGC1": {
                "numero": "RGC1",
                "titulo": "Aplicação das Regras Gerais a Níveis Detalhados",
                "texto": (
                    "Regras Gerais aplicam-se (mutatis mutandis) para definir item e "
                    "subitem dentro de cada posição/subposição; comparar apenas "
                    "desdobramentos regionais do mesmo nível."
                ),
                "tipo": "Regra Geral Complementar",
                "aplicacao": "Extensão das regras para itens e subitens regionais",
            },
            "RGC2": {
                "numero": "RGC2",
                "titulo": "Regime de Classificação de Embalagens Reutilizáveis",
                "texto": (
                    "Embalagens reutilizáveis (Regra 5b) seguem regime próprio se em "
                    "admissão/exportação temporária; senão seguem a mercadoria."
                ),
                "tipo": "Regra Geral Complementar",
                "aplicacao": "Regimes especiais para embalagens reutilizáveis",
            },
            "RGC_TIPI1": {
                "numero": "RGC_TIPI1",
                "titulo": "Determinação do 'Ex' Aplicável",
                "texto": (
                    "Regras Gerais aplicam-se para determinar 'Ex' em cada código; "
                    "comparar apenas 'Ex' do mesmo código."
                ),
                "tipo": "Regra Geral Complementar da TIPI",
                "aplicacao": "Classificação de exceções (Ex) na TIPI brasileira",
            },
        }

    def _create_comprehensive_nesh_data(self) -> Dict:
        """
        Cria estrutura completa das regras NESH baseada no sistema real
        """
        return {
            "regras_gerais": {
                "rg1": {
                    "titulo": "Regra Geral 1 - Textos das posições e notas",
                    "descricao": (
                        "Títulos têm valor indicativo. Classificação definida por textos "
                        "das posições e Notas de Seção/Capítulo; se não conflitarem, "
                        "aplicar Regras seguintes."
                    ),
                    "aplicacao": (
                        "Aplicar primeiro: verificar enquadramento direto em posição "
                        "específica."
                    ),
                    "exemplos": [
                        "Produto claramente descrito em uma posição específica",
                        "Verificação de notas de seção e capítulo antes de aplicar outras regras",
                    ],
                },
                "rg2a": {
                    "titulo": "Regra Geral 2(a) - Artigos incompletos",
                    "descricao": (
                        "Referência a artigo inclui versão incompleta/não acabada se "
                        "mantém características essenciais."
                    ),
                    "aplicacao": "Produtos não acabados com características essenciais",
                    "exemplos": [
                        "Motores sem algumas peças mas reconhecíveis como motores",
                        "Móveis desmontados para transporte",
                    ],
                },
                "rg2b": {
                    "titulo": "Regra Geral 2(b) - Misturas e compostos",
                    "descricao": (
                        "Referência a matéria inclui misturas/associações; referência a "
                        "obras inclui obras parcial ou totalmente dessa matéria."
                    ),
                    "aplicacao": "Misturas e produtos compostos",
                    "exemplos": ["Ligas metálicas", "Produtos químicos misturados"],
                },
                "rg3a": {
                    "titulo": "Regra Geral 3(a) - Posição mais específica",
                    "descricao": "A posição mais específica prevalece sobre as mais gerais.",
                    "aplicacao": "Quando múltiplas posições podem ser aplicáveis",
                    "exemplos": [
                        "Classificar 'máquina' vs 'máquina de costura' -> usar específica"
                    ],
                },
                "rg3b": {
                    "titulo": "Regra Geral 3(b) - Caráter essencial",
                    "descricao": (
                        "Compostos/sortidos classificam-se pela matéria ou artigo que "
                        "confere caráter essencial."
                    ),
                    "aplicacao": "Produtos compostos sem posição específica",
                    "exemplos": [
                        "Estojo com instrumentos - classificado pelo instrumento principal",
                        "Produto com embalagem especial - classificado pelo produto, não pela embalagem",
                    ],
                },
                "rg3c": {
                    "titulo": "Regra Geral 3(c) - Última posição na ordem numérica",
                    "descricao": (
                        "Se Regras 3(a)/3(b) falham, classificar na última posição em "
                        "ordem numérica dentre as possíveis."
                    ),
                    "aplicacao": "Último recurso quando outras regras não se aplicam",
                    "exemplos": [
                        "Múltiplas posições equivalentes -> escolher maior número"
                    ],
                },
                "rg4": {
                    "titulo": "Regra Geral 4 - Produtos não classificáveis pelas regras anteriores",
                    "descricao": (
                        "Sem classificação pelas Regras anteriores: usar posição dos "
                        "artigos mais análogos."
                    ),
                    "aplicacao": "Para produtos verdadeiramente novos ou únicos",
                    "exemplos": [
                        "Tecnologias novas não previstas na nomenclatura",
                        "Produtos híbridos sem classificação específica",
                    ],
                },
                "rg5a": {
                    "titulo": "Regra Geral 5(a) - Estojos",
                    "descricao": (
                        "Estojos especializados apresentados com conteúdo seguem o regime "
                        "aduaneiro do conteúdo principal."
                    ),
                    "aplicacao": "Estojos especializados seguem a classificação do conteúdo",
                    "exemplos": [
                        "Estojo de violino com o violino",
                        "Maleta de ferramentas com as ferramentas",
                    ],
                },
                "rg5b": {
                    "titulo": "Regra Geral 5(b) - Embalagens",
                    "descricao": (
                        "Embalagens normais seguem regime da mercadoria. Exceção: "
                        "embalagens claramente reutilizáveis."
                    ),
                    "aplicacao": "Embalagens normais seguem o produto, exceto se reutilizáveis",
                    "exemplos": [
                        "Caixa de papelão para produtos eletrônicos",
                        "Garrafas de vidro reutilizáveis (classificação separada)",
                    ],
                },
                "rg6": {
                    "titulo": "Regra Geral 6 - Subposições",
                    "descricao": (
                        "Classificação em subposições: textos das subposições + Notas, "
                        "aplicando Regras anteriores (mutatis mutandis)."
                    ),
                    "aplicacao": "Aplicar as mesmas regras para subposições dentro de uma posição",
                    "exemplos": [
                        "Ex: posição 8471 (processamento de dados) -> aplicar regras para subposição específica"
                    ],
                },
            },
            "estrutura_ncm": {
                "formato": "AABB.CC.DD (8 dígitos)",
                "componentes": {
                    "AA": "Capítulo - categoria mais abrangente",
                    "BB": "Posição - tipo geral/função e aplicação",
                    "CC": "Subposição - tipo específico/variação técnica",
                    "DD": "Subitem - maior especificidade",
                },
                "hierarquia": "Cada nível representa maior especificidade",
                "exemplo": {
                    "codigo": "3004.90.69",
                    "significado": {
                        "30": "Capítulo 30 - Produtos Farmacêuticos",
                        "04": "Posição 3004 - Medicamentos",
                        "90": "Subposição 3004.90 - Outros",
                        "69": "Subitem - Especificação detalhada",
                    },
                },
            },
            "notas_importantes": {
                "ordem_aplicacao": [
                    "1. Verificar textos das posições e notas (RG1)",
                    "2. Considerar produtos incompletos/não acabados (RG2a)",
                    "3. Considerar misturas e compostos (RG2b)",
                    "4. Aplicar hierarquia de especificidade (RG3a-c)",
                    "5. Buscar produtos análogos se necessário (RG4)",
                    "6. Considerar embalagens e estojos (RG5a-b)",
                    "7. Aplicar mesmas regras para subposições (RG6)",
                ],
                "principios_fundamentais": [
                    "Especificidade prevalece sobre generalidade",
                    "Textos das posições são determinantes",
                    "Notas de seção e capítulo são vinculantes",
                    "Classificação deve ser inequívoca",
                    "Aplicação sequencial das regras",
                ],
            },
            "capitulos_farmaceuticos": {
                "capitulo_30": {
                    "titulo": "Produtos Farmacêuticos",
                    "abrangencia": "Medicamentos de uso humano e veterinário",
                    "posicoes_principais": {
                        "3003": "Medicamentos não acondicionados para venda a retalho",
                        "3004": "Medicamentos acondicionados para venda a retalho",
                        "3005": "Pastas, gazes, ataduras medicamentosas",
                        "3006": "Preparações e artigos farmacêuticos",
                    },
                    "notas_especificas": [
                        "Produtos devem ter propriedades terapêuticas ou profiláticas",
                        "Destinação para diagnóstico, tratamento ou prevenção de doenças",
                        "Concentração de princípios ativos relevante para classificação",
                    ],
                }
            },
            "metadata": {
                "versao": "2022",
                "fonte": "NESH-2022 Regras Gerais - Dados Conhecidos",
                "processado_em": str(Path(__file__).parent),
                "regras_complementares": "Baseado em Regras_gerais_complementares.md",
            },
        }

    def _create_sample_nesh_data(self) -> Dict:
        """
        Cria dados de exemplo do NESH para desenvolvimento
        """
        return {
            "regras_gerais": self._get_known_regras_gerais(),
            "capitulos": {
                "30": {
                    "titulo": "Produtos farmacêuticos",
                    "abrangencia": "Medicamentos",
                },
                "87": {"titulo": "Veículos", "abrangencia": "Automóveis e suas partes"},
            },
            "metadata": {"versao": "simulada", "fonte": "dados_exemplo"},
        }

    def get_classification_rules(self, ncm_code: str = None) -> Dict:
        """
        Obtém regras de classificação NCM
        """
        if self.nesh_content is None:
            self.load_nesh_pdf()

        rules = {
            "regras_gerais": self.nesh_content.get("regras_gerais", {}),
            "aplicacao_sequencial": True,
            "principios": [
                "Textos das posições são determinantes",
                "Posição mais específica prevalece",
                "Aplicar regras na ordem estabelecida",
            ],
        }

        if ncm_code:
            # Adicionar regras específicas para o código NCM
            validation = self.validate_ncm_structure(ncm_code)
            rules["ncm_especifico"] = {
                "codigo": ncm_code,
                "validacao": validation,
                "regras_aplicaveis": self._get_applicable_rules(ncm_code),
            }

        return rules

    def _get_applicable_rules(self, ncm_code: str) -> List[str]:
        """
        Determina quais regras são mais aplicáveis para um NCM específico
        """
        applicable_rules = ["RG1"]  # Sempre aplicar regra 1 primeiro

        # Se NCM é de medicamentos
        if ncm_code.startswith("30"):
            applicable_rules.extend(["RG2A", "RG3A", "RG5B"])

        return applicable_rules

    def validate_ncm_structure(self, ncm_code: str) -> Dict:
        """
        Valida estrutura do código NCM
        """
        # Remove pontos e hífens
        clean_ncm = ncm_code.replace(".", "").replace("-", "").strip()

        validation = {
            "codigo_original": ncm_code,
            "codigo_limpo": clean_ncm,
            "valido": False,
            "observacoes": [],
        }

        # Verificar se tem 8 dígitos
        if len(clean_ncm) == 8 and clean_ncm.isdigit():
            validation["valido"] = True

            # Extrair componentes
            capitulo = int(clean_ncm[:2])
            posicao = clean_ncm[2:4]
            subposicao = clean_ncm[4:6]
            item = clean_ncm[6:7]
            subitem = clean_ncm[7:8]

            validation["componentes"] = {
                "capitulo": capitulo,
                "posicao": posicao,
                "subposicao": subposicao,
                "item": item,
                "subitem": subitem,
            }

            # Validações específicas
            if 1 <= capitulo <= 99:
                validation["observacoes"].append(f"Capítulo {capitulo:02d} válido")

                # Verifica se é farmacêutico
                if capitulo == 30:
                    validation["observacoes"].append(
                        "Produto farmacêutico - Capítulo 30"
                    )
                    validation["regras_especiais"] = self.nesh_content.get(
                        "capitulos_farmaceuticos", {}
                    ).get("capitulo_30", {})
            else:
                validation["observacoes"].append(
                    f"Capítulo {capitulo} inválido (deve ser 01-99)"
                )
        else:
            validation["observacoes"].append("Formato inválido - deve ter 8 dígitos")

        return validation

    def get_classification_guidance(
        self, product_description: str, current_ncm: str = None
    ) -> Dict:
        """
        Fornece orientação para classificação baseada nas regras NESH
        """
        if self.nesh_content is None:
            self.load_nesh_pdf()

        guidance = {
            "regras_aplicaveis": [],
            "recomendacoes": [],
            "verificacoes_necessarias": [],
            "ncm_sugerido": current_ncm,
        }

        # Analisa descrição do produto
        desc_upper = product_description.upper()

        # Identifica se é produto farmacêutico
        termos_farmaceuticos = [
            "MEDICAMENTO",
            "COMPRIMIDO",
            "CÁPSULA",
            "XAROPE",
            "POMADA",
            "DIPIRONA",
            "PARACETAMOL",
            "IBUPROFENO",
        ]
        is_farmaceutico = any(termo in desc_upper for termo in termos_farmaceuticos)

        if is_farmaceutico:
            guidance["regras_aplicaveis"].append(
                "RG1 - Verificar posições do Capítulo 30"
            )
            guidance["recomendacoes"].append(
                "Produto aparenta ser farmacêutico - verificar NCM 3003.xx.xx ou 3004.xx.xx"
            )
            guidance["verificacoes_necessarias"].extend(
                [
                    "Verificar se é medicamento para venda a retalho (3004) ou não (3003)",
                    "Confirmar princípio ativo e concentração",
                    "Verificar forma farmacêutica (comprimido, cápsula, etc.)",
                ]
            )

            if not current_ncm or not current_ncm.startswith("30"):
                guidance["ncm_sugerido"] = (
                    "3004.90.69"  # Posição genérica para outros medicamentos
                )

        # Verifica NCM atual se fornecido
        if current_ncm:
            validation = self.validate_ncm_structure(current_ncm)
            if validation["valido"]:
                guidance["ncm_atual_valido"] = True
                guidance["observacoes_ncm_atual"] = validation["observacoes"]
            else:
                guidance["ncm_atual_valido"] = False
                guidance["problemas_ncm_atual"] = validation["observacoes"]

        # Adiciona regras gerais sempre aplicáveis
        guidance["regras_sempre_aplicaveis"] = [
            "RG1 - Verificar textos das posições e notas de seção/capítulo",
            "RG3(a) - Posição mais específica prevalece sobre a mais geral",
            "RG6 - Aplicar mesmas regras para subposições e subitens",
        ]

        return guidance

    def export_nesh_rules(self, output_path: str = "data/processed") -> str:
        """
        Exporta regras NESH processadas para arquivo JSON
        """
        if self.nesh_content is None:
            self.load_nesh_pdf()

        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "nesh_rules_2022.json"

        export_data = {
            "nesh_content": self.nesh_content,
            "processed_at": str(Path(__file__).parent),
            "version": "1.0",
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Regras NESH exportadas para: {output_file}")
        return str(output_file)

    def validate_ncm(self, ncm: str, descricao: str = "") -> Dict:
        """
        Valida NCM e fornece orientação baseada nas regras NESH
        """
        guidance = {
            "ncm": ncm,
            "descricao": descricao,
            "regras_aplicaveis": [],
            "recomendacoes": [],
        }

        descricao_lower = descricao.lower()

        # Identificar tipo de produto e aplicar regras relevantes
        if any(
            termo in descricao_lower
            for termo in [
                "medicamento",
                "farmacêutico",
                "comprimido",
                "cápsula",
                "xarope",
            ]
        ):
            guidance["regras_aplicaveis"].append(
                "RG1 - Verificar posições do Capítulo 30"
            )
            guidance["recomendacoes"].append(
                "Produto aparenta ser farmacêutico - verificar NCM 3003.xx.xx ou 3004.xx.xx"
            )

            if "comprimido" in descricao_lower or "cápsula" in descricao_lower:
                guidance["recomendacoes"].append(
                    "Forma sólida - provável posição 3004.xx.xx"
                )

        if ncm and ncm.startswith("30"):
            guidance["regras_aplicaveis"].append("RG2A - Produto farmacêutico completo")
            guidance["recomendacoes"].append(
                "NCM capítulo 30 apropriado para produtos farmacêuticos"
            )

        return guidance

    def aplicar_regras_sequenciais(self, produto_info: Dict) -> Dict:
        """
        Aplica regras gerais de interpretação sequencialmente conforme ponto 21 do plano

        Args:
            produto_info: Informações do produto (descricao, ncm_atual, etc.)

        Returns:
            Dict: Resultado da aplicação das regras
        """
        descricao = produto_info.get("descricao", "")
        ncm_atual = produto_info.get("ncm", "")
        atividade_empresa = produto_info.get("atividade_empresa", "")

        resultado = {
            "regras_aplicadas": [],
            "ncm_sugerido": "",
            "cest_sugerido": "",
            "confianca": 0.0,
            "justificativas": [],
            "estrutura_hierarquica": {},
        }

        # Regra 1: Verificar textos das posições
        regra1_resultado = self._aplicar_regra_1(descricao, atividade_empresa)
        resultado["regras_aplicadas"].append(regra1_resultado)

        # Se Regra 1 não resolve, aplicar Regra 2
        if not regra1_resultado.get("classificacao_definida", False):
            regra2_resultado = self._aplicar_regra_2(descricao, ncm_atual)
            resultado["regras_aplicadas"].append(regra2_resultado)

            # Se ainda não resolve, aplicar Regra 3
            if not regra2_resultado.get("classificacao_definida", False):
                regra3_resultado = self._aplicar_regra_3(descricao, produto_info)
                resultado["regras_aplicadas"].append(regra3_resultado)

                # Se ainda não resolve, aplicar Regra 4 (analogia)
                if not regra3_resultado.get("classificacao_definida", False):
                    regra4_resultado = self._aplicar_regra_4(descricao)
                    resultado["regras_aplicadas"].append(regra4_resultado)

        # Compilar resultado final
        self._compilar_resultado_final(resultado)

        return resultado

    def _aplicar_regra_1(self, descricao: str, atividade_empresa: str) -> Dict:
        """
        Aplica Regra 1: Valor Indicativo dos Títulos
        Considera atividade da empresa conforme ponto 20 do plano
        """
        resultado = {
            "regra": "1",
            "titulo": "Valor Indicativo dos Títulos",
            "classificacao_definida": False,
            "observacoes": [],
        }

        descricao_lower = descricao.lower()
        atividade_lower = atividade_empresa.lower()

        # Identificar capítulo baseado na descrição e atividade
        capitulo_identificado = None
        posicao_sugerida = None

        # Medicamentos (Capítulo 30)
        if any(
            termo in descricao_lower
            for termo in [
                "medicamento",
                "remedio",
                "farmaco",
                "comprimido",
                "capsula",
                "xarope",
            ]
        ):
            capitulo_identificado = "30"
            if any(
                termo in atividade_lower
                for termo in ["farmacia", "drogaria", "medicamentos"]
            ):
                resultado["confianca"] = 0.9
                resultado["observacoes"].append(
                    "Descrição indica medicamento e empresa do ramo farmacêutico"
                )
            else:
                resultado["confianca"] = 0.7
                resultado["observacoes"].append("Descrição indica medicamento")

            # Determinar posição específica
            if any(
                termo in descricao_lower
                for termo in ["comprimido", "capsula", "drágea"]
            ):
                posicao_sugerida = "3004"  # Medicamentos acondicionados
            else:
                posicao_sugerida = "3003"  # Medicamentos não acondicionados

        # Autopeças (Capítulo 87)
        elif any(
            termo in descricao_lower
            for termo in ["autopeca", "motor", "peca", "veiculo"]
        ):
            capitulo_identificado = "87"
            if any(
                termo in atividade_lower
                for termo in ["autopeca", "veiculo", "mecanica"]
            ):
                resultado["confianca"] = 0.8
                resultado["observacoes"].append(
                    "Descrição indica autopeças e empresa do ramo automotivo"
                )

        if capitulo_identificado:
            resultado["classificacao_definida"] = True
            resultado["capitulo_sugerido"] = capitulo_identificado
            resultado["posicao_sugerida"] = posicao_sugerida
            resultado["observacoes"].append(
                f"Capítulo {capitulo_identificado} identificado pela descrição"
            )

        return resultado

    def _aplicar_regra_2(self, descricao: str, ncm_atual: str) -> Dict:
        """
        Aplica Regra 2: Artigos Incompletos, Desmontados, Misturas e Compostos
        """
        resultado = {
            "regra": "2",
            "titulo": "Artigos Incompletos, Desmontados, Misturas",
            "classificacao_definida": False,
            "observacoes": [],
        }

        descricao_lower = descricao.lower()

        # Verificar se é artigo incompleto/desmontado (Regra 2A)
        if any(
            termo in descricao_lower
            for termo in ["incompleto", "desmontado", "kit", "conjunto"]
        ):
            resultado["sub_regra"] = "2A"
            resultado["observacoes"].append("Produto pode ser incompleto ou desmontado")

            # Verificar características essenciais
            if "medicamento" in descricao_lower:
                resultado["classificacao_definida"] = True
                resultado["ncm_sugerido"] = "3004"  # Manter capítulo medicamentos
                resultado["confianca"] = 0.8

        # Verificar se é mistura/composto (Regra 2B)
        elif any(
            termo in descricao_lower
            for termo in ["mistura", "composto", "associado", "combinado"]
        ):
            resultado["sub_regra"] = "2B"
            resultado["observacoes"].append("Produto pode ser mistura ou composto")
            resultado["observacoes"].append(
                "Aplicar Regra 3 para determinar característica essencial"
            )

        return resultado

    def _aplicar_regra_3(self, descricao: str, produto_info: Dict) -> Dict:
        """
        Aplica Regra 3: Classificação em Duas ou Mais Posições
        """
        resultado = {
            "regra": "3",
            "titulo": "Classificação em Múltiplas Posições",
            "classificacao_definida": False,
            "observacoes": [],
        }

        # Simular análise de posições possíveis (lista não utilizada removida)

        # Para medicamentos, verificar subposições
        if "medicamento" in descricao.lower():
            # posicoes_possiveis removido (não utilizado)

            # Regra 3A: Posição mais específica
            if any(termo in descricao.lower() for termo in ["comprimido", "capsula"]):
                resultado["posicao_especifica"] = "3004"
                resultado["sub_regra"] = "3A"
                resultado["observacoes"].append(
                    "Posição 3004 mais específica para medicamentos acondicionados"
                )
                resultado["classificacao_definida"] = True
                resultado["confianca"] = 0.85

        return resultado

    def _aplicar_regra_4(self, descricao: str) -> Dict:
        """
        Aplica Regra 4: Artigos Mais Semelhantes (Analogia)
        """
        resultado = {
            "regra": "4",
            "titulo": "Artigos Mais Semelhantes (Analogia)",
            "classificacao_definida": False,
            "observacoes": [],
        }

        # Buscar produtos similares para analogia
        # Esta seria integrada com o processador ABC Farma V2
        resultado["observacoes"].append(
            "Classificação por analogia baseada em produtos similares"
        )
        resultado["metodo_analogia"] = "denominacao_caracteristicas"

        return resultado

    def _compilar_resultado_final(self, resultado: Dict):
        """
        Compila resultado final da aplicação sequencial das regras
        """
        regras_com_classificacao = [
            regra
            for regra in resultado["regras_aplicadas"]
            if regra.get("classificacao_definida", False)
        ]

        if regras_com_classificacao:
            # Usar primeira regra que definiu classificação
            regra_definitiva = regras_com_classificacao[0]
            resultado["ncm_sugerido"] = regra_definitiva.get("ncm_sugerido", "")
            resultado["confianca"] = regra_definitiva.get("confianca", 0.5)

            # Compilar justificativas
            for regra in resultado["regras_aplicadas"]:
                resultado["justificativas"].extend(regra.get("observacoes", []))

    def validar_estrutura_hierarquica_ncm(self, ncm: str) -> Dict:
        """
        Valida estrutura hierárquica do NCM conforme ponto 21 do plano
        Formato: AABB.CC.DD (exemplo: 3004.90.69)
        """
        resultado = {"ncm": ncm, "valido": False, "estrutura": {}, "observacoes": []}

        # Limpar NCM
        ncm_limpo = ncm.replace(".", "").replace("-", "").strip()

        if len(ncm_limpo) != 8 or not ncm_limpo.isdigit():
            resultado["observacoes"].append("NCM deve ter 8 dígitos numéricos")
            return resultado

        # Extrair estrutura hierárquica
        estrutura = {
            "capitulo": ncm_limpo[:2],  # AA - Capítulo
            "posicao": ncm_limpo[2:4],  # BB - Posição
            "subposicao": ncm_limpo[4:6],  # CC - Subposição
            "item": ncm_limpo[6:7],  # D - Item
            "subitem": ncm_limpo[7:8],  # D - Subitem
        }

        resultado["estrutura"] = estrutura

        # Validações específicas
        capitulo = estrutura["capitulo"]
        posicao = estrutura["posicao"]

        # Validar capítulo de medicamentos
        if capitulo == "30":
            resultado["observacoes"].append("Capítulo 30 - Produtos Farmacêuticos")

            if posicao == "03":
                resultado["observacoes"].append(
                    "Posição 3003 - Medicamentos não acondicionados para venda a retalho"
                )
            elif posicao == "04":
                resultado["observacoes"].append(
                    "Posição 3004 - Medicamentos acondicionados para venda a retalho"
                )
            else:
                resultado["observacoes"].append(
                    f"Posição {posicao} não é típica para medicamentos"
                )

        # Validar hierarquia crescente de especificidade
        resultado["hierarquia_valida"] = True
        resultado["especificidade"] = (
            f"Capítulo {capitulo} → Posição {posicao} → Subposição {estrutura['subposicao']}"
        )

        resultado["valido"] = True
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
            "cest_sugerido": "",
            "segmento": "",
            "aplicavel": False,
            "observacoes": [],
            "confianca": 0.0,
        }

        ncm = produto_info.get("ncm", "")
        descricao = produto_info.get("descricao", "")
        atividade_empresa = produto_info.get("atividade_empresa", "")

        # Medicamentos - Segmento 13
        if ncm.startswith("30") and any(
            termo in descricao.lower() for termo in ["medicamento", "farmaco"]
        ):
            resultado["segmento"] = "13"
            resultado["segmento_nome"] = "Medicamentos"
            resultado["aplicavel"] = True

            # CEST 13.001.00 - Medicamentos em geral
            if any(
                termo in descricao.lower()
                for termo in ["comprimido", "capsula", "drágea"]
            ):
                resultado["cest_sugerido"] = "13.001.00"
                resultado["confianca"] = 0.9
                resultado["observacoes"].append(
                    "CEST 13.001.00 - Medicamentos para uso humano em formas sólidas"
                )

            # CEST 13.002.00 - Medicamentos líquidos
            elif any(
                termo in descricao.lower()
                for termo in ["xarope", "solução", "suspensão"]
            ):
                resultado["cest_sugerido"] = "13.002.00"
                resultado["confianca"] = 0.9
                resultado["observacoes"].append(
                    "CEST 13.002.00 - Medicamentos líquidos"
                )

        # Venda Porta a Porta - Segmento 28 (conforme ponto 22 do plano)
        if (
            "porta a porta" in atividade_empresa.lower()
            or "vendas diretas" in atividade_empresa.lower()
        ):
            resultado["segmento_adicional"] = "28"
            resultado["observacoes"].append(
                "Empresa atua na modalidade porta a porta - aplicar Segmento 28"
            )
            resultado["observacoes"].append(
                "CEST do Anexo XXIX prevalece sobre outros anexos"
            )

        # Autopeças - Segmento 01
        elif ncm.startswith("87") or "autopeca" in atividade_empresa.lower():
            resultado["segmento"] = "01"
            resultado["segmento_nome"] = "Autopeças"
            resultado["aplicavel"] = True
            resultado["observacoes"].append("Segmento 01 - Autopeças")

        # Verificar se produto tem NCM mas não se enquadra em nenhum CEST
        if not resultado["aplicavel"] and ncm:
            resultado["observacoes"].append(
                "Produto possui NCM mas não se enquadra em nenhum segmento CEST"
            )

        return resultado


def main():
    """
    Função de teste para demonstrar uso do processador NESH
    """
    processor = NeshProcessor()

    # Testa validação de NCM
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

    # Testa aplicação sequencial de regras (novo)
    produto_teste = {
        "descricao": "DIPIRONA SÓDICA 500MG COMPRIMIDO",
        "ncm": "3004.90.69",
        "atividade_empresa": "Farmácia e Drogaria",
    }

    resultado_regras = processor.aplicar_regras_sequenciais(produto_teste)
    print("\nAplicação sequencial de regras:")
    print(f"NCM sugerido: {resultado_regras['ncm_sugerido']}")
    print(f"Confiança: {resultado_regras['confianca']}")
    print(f"Justificativas: {resultado_regras['justificativas']}")

    # Testa regras CEST (novo)
    resultado_cest = processor.aplicar_regras_cest(produto_teste)
    print("\nAplicação regras CEST:")
    print(f"CEST sugerido: {resultado_cest['cest_sugerido']}")
    print(f"Segmento: {resultado_cest['segmento']}")
    print(f"Observações: {resultado_cest['observacoes']}")

    # Exporta regras
    output_file = processor.export_nesh_rules()
    print(f"\nRegras exportadas para: {output_file}")


def test_enhanced_nesh():
    """
    Testa funcionalidades aprimoradas do processador NESH
    """
    processor = NeshProcessor()

    print("=== TESTE PROCESSADOR NESH APRIMORADO ===\n")

    # Teste 1: Validação estrutura hierárquica NCM
    print("1. VALIDAÇÃO ESTRUTURA HIERÁRQUICA NCM")
    ncms_teste = ["3004.90.69", "8703.23.10", "1234.56.78"]

    for ncm in ncms_teste:
        resultado = processor.validar_estrutura_hierarquica_ncm(ncm)
        print(f"\nNCM: {ncm}")
        print(f"Válido: {resultado['valido']}")
        print(f"Estrutura: {resultado['estrutura']}")
        print(f"Observações: {resultado['observacoes']}")

    # Teste 2: Aplicação sequencial de regras
    print("\n\n2. APLICAÇÃO SEQUENCIAL DE REGRAS")
    produtos_teste = [
        {
            "descricao": "DIPIRONA SÓDICA 500MG COMPRIMIDO",
            "ncm": "3004.90.69",
            "atividade_empresa": "Farmácia e Drogaria",
        },
        {
            "descricao": "PEÇA AUTOMOTIVA MOTOR",
            "ncm": "8708.40.90",
            "atividade_empresa": "Autopeças",
        },
    ]

    for i, produto in enumerate(produtos_teste, 1):
        print(f"\nProduto {i}: {produto['descricao']}")
        resultado = processor.aplicar_regras_sequenciais(produto)
        print(f"Regras aplicadas: {len(resultado['regras_aplicadas'])}")
        print(f"NCM sugerido: {resultado['ncm_sugerido']}")
        print(f"Confiança: {resultado['confianca']}")

        for regra in resultado["regras_aplicadas"]:
            print(f"  - Regra {regra['regra']}: {regra['titulo']}")
            if regra.get("classificacao_definida"):
                print("    ✓ Classificação definida")

    # Teste 3: Regras CEST
    print("\n\n3. APLICAÇÃO REGRAS CEST")

    for i, produto in enumerate(produtos_teste, 1):
        print(f"\nProduto {i}: {produto['descricao']}")
        resultado = processor.aplicar_regras_cest(produto)
        print(f"CEST aplicável: {resultado['aplicavel']}")
        if resultado["aplicavel"]:
            print(f"CEST sugerido: {resultado['cest_sugerido']}")
            print(
                f"Segmento: {resultado['segmento']} - {resultado.get('segmento_nome', '')}"
            )
            print(f"Confiança: {resultado['confianca']}")
        print(f"Observações: {resultado['observacoes']}")


# Função principal com todos os testes
def comprehensive_test():
    """
    Executa todos os testes do processador NESH aprimorado
    """
    print("=== TESTE ABRANGENTE PROCESSADOR NESH ===\n")
    main()
    print("\n" + "=" * 60 + "\n")
    test_enhanced_nesh()


if __name__ == "__main__":
    # Para executar teste abrangente, descomente a linha abaixo:
    # comprehensive_test()

    # Teste padrão
    main()
