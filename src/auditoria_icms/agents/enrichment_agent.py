"""
Agente de Enriquecimento - Enrichment Agent
Responsável por enriquecer a descrição original do produto com informações técnicas,
contextuais e regulamentares para melhorar a classificação fiscal.
"""

import time
import re
from typing import Dict, Any, Optional

from .base_agent import BaseAgent


class EnrichmentAgent(BaseAgent):
    """
    Agente especializado em enriquecimento de descrições de produtos.
    Adiciona contexto técnico, regulamentar e semântico às descrições originais.
    """

    def __init__(self, llm, config: Dict[str, Any], logger=None):
        super().__init__("EnrichmentAgent", llm, config, logger)
        self.enhancement_strategies = config.get(
            "enhancement_strategies", ["semantic", "regulatory", "contextual"]
        )

    async def process(
        self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Enriquece a descrição do produto com informações relevantes para classificação fiscal.

        Args:
            input_data: Dados do produto incluindo descrição original
            context: Contexto adicional (empresa, setor, etc.)

        Returns:
            Descrição enriquecida e informações adicionais extraídas
        """
        start_time = time.time()

        if not self.validate_input(input_data):
            raise ValueError("Dados de entrada inválidos para EnrichmentAgent")

        descricao_original = input_data["descricao_produto"]
        gtin = input_data.get("gtin")
        ncm_sugerido = input_data.get("ncm_atual")

        # Análise inicial da descrição
        analysis = await self._analyze_description(descricao_original)

        # Aplicar estratégias de enriquecimento
        enrichments = {}
        sources_used = []

        for strategy in self.enhancement_strategies:
            try:
                if strategy == "semantic":
                    result = await self._semantic_enhancement(
                        descricao_original, analysis
                    )
                elif strategy == "regulatory":
                    result = await self._regulatory_enhancement(
                        descricao_original, ncm_sugerido
                    )
                elif strategy == "contextual":
                    result = await self._contextual_enhancement(
                        descricao_original, gtin, context
                    )
                else:
                    continue

                enrichments[strategy] = result
                sources_used.extend(result.get("sources", []))

            except Exception as e:
                self.logger.warning(f"Erro na estratégia {strategy}: {str(e)}")
                enrichments[strategy] = {"error": str(e)}

        # Consolidar enriquecimentos
        enriched_description = await self._consolidate_enrichments(
            descricao_original, enrichments, analysis
        )

        # Extrair características técnicas
        technical_features = await self._extract_technical_features(
            enriched_description
        )

        processing_time = int((time.time() - start_time) * 1000)

        result = {
            "enriched_description": enriched_description,
            "original_description": descricao_original,
            "technical_features": technical_features,
            "analysis": analysis,
            "enrichment_strategies": enrichments,
            "confidence_score": self._calculate_enrichment_confidence(enrichments),
            "sources": list(set(sources_used)),
            "success": True,
        }

        # Criar registro de decisão
        self.create_decision_record(
            input_data=input_data,
            output_data=result,
            reasoning=f"Enriquecimento aplicado usando estratégias: {', '.join(self.enhancement_strategies)}",
            confidence_score=result["confidence_score"],
            sources_used=result["sources"],
            processing_time_ms=processing_time,
        )

        return result

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Valida se os dados contêm uma descrição válida do produto."""
        if "descricao_produto" not in input_data:
            return False

        descricao = input_data["descricao_produto"]
        if not isinstance(descricao, str) or len(descricao.strip()) < 3:
            return False

        return True

    async def _analyze_description(self, description: str) -> Dict[str, Any]:
        """Analisa a descrição original para identificar características principais."""

        analysis = {
            "length": len(description),
            "word_count": len(description.split()),
            "has_technical_terms": False,
            "has_brand": False,
            "has_model": False,
            "has_materials": False,
            "has_dimensions": False,
            "language": "portuguese",
            "structure_quality": "basic",
        }

        # Padrões para identificação de características
        patterns = {
            "technical_terms": [
                r"\b(tensão|voltagem|potência|frequência|capacidade|resistência)\b",
                r"\b(diâmetro|comprimento|largura|altura|peso|volume)\b",
                r"\b(aço|plástico|alumínio|ferro|cobre|madeira|tecido)\b",
            ],
            "brand_indicators": [
                r"\b[A-Z][a-z]+\s*(®|™|\(R\))\b",
                r"\bmarca\s+[A-Z][a-z]+\b",
            ],
            "model_indicators": [
                r"\bmodelo\s+[A-Z0-9]+\b",
                r"\bref\.?\s*[A-Z0-9]+\b",
                r"\bcód\.?\s*[A-Z0-9]+\b",
            ],
            "dimension_patterns": [
                r"\d+\s*(mm|cm|m|pol|polegadas)\b",
                r"\d+\s*x\s*\d+",
                r"\d+,?\d*\s*(kg|g|ton|litros?|ml)\b",
            ],
        }

        description_lower = description.lower()

        # Verificar padrões
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, description, re.IGNORECASE):
                    if category == "technical_terms":
                        analysis["has_technical_terms"] = True
                    elif category == "brand_indicators":
                        analysis["has_brand"] = True
                    elif category == "model_indicators":
                        analysis["has_model"] = True
                    elif category == "dimension_patterns":
                        analysis["has_dimensions"] = True

        # Verificar materiais
        materials = [
            "aço",
            "plástico",
            "alumínio",
            "ferro",
            "cobre",
            "madeira",
            "tecido",
            "vidro",
            "cerâmica",
            "borracha",
            "silicone",
        ]
        analysis["has_materials"] = any(
            material in description_lower for material in materials
        )

        # Avaliar qualidade da estrutura
        if analysis["word_count"] > 10 and (
            analysis["has_technical_terms"] or analysis["has_materials"]
        ):
            analysis["structure_quality"] = "good"
        elif analysis["word_count"] > 20:
            analysis["structure_quality"] = "detailed"

        return analysis

    async def _semantic_enhancement(
        self, description: str, analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enriquecimento semântico usando conhecimento de domínio."""

        # Mapeamento de termos comuns para termos técnicos
        semantic_mappings = {
            "remédio": "medicamento",
            "celular": "aparelho telefônico móvel",
            "carro": "veículo automotor",
            "computador": "equipamento de processamento de dados",
            "TV": "aparelho receptor de televisão",
            "geladeira": "refrigerador doméstico",
            "fogão": "aparelho para cocção",
            "máquina": "equipamento mecânico",
        }

        enhanced_description = description
        applied_mappings = []

        for common_term, technical_term in semantic_mappings.items():
            if common_term.lower() in description.lower():
                enhanced_description = re.sub(
                    rf"\b{re.escape(common_term)}\b",
                    f"{common_term} ({technical_term})",
                    enhanced_description,
                    flags=re.IGNORECASE,
                )
                applied_mappings.append(f"{common_term} -> {technical_term}")

        # Adicionar contexto de uso quando apropriado
        uso_contexts = {
            "medicamento": "para uso humano",
            "brinquedo": "para entretenimento infantil",
            "ferramenta": "para uso profissional/doméstico",
            "equipamento": "para aplicação industrial/comercial",
        }

        for context_key, context_desc in uso_contexts.items():
            if context_key in enhanced_description.lower():
                if context_desc not in enhanced_description:
                    enhanced_description += f" ({context_desc})"

        return {
            "enhanced_text": enhanced_description,
            "applied_mappings": applied_mappings,
            "sources": ["semantic_knowledge_base"],
            "confidence": 0.8 if applied_mappings else 0.5,
        }

    async def _regulatory_enhancement(
        self, description: str, ncm_sugerido: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enriquecimento com informações regulamentares e normativas."""

        regulatory_keywords = {
            "medicamento": {
                "regulamento": "Anvisa",
                "categoria": "produto farmacêutico",
                "observacoes": "sujeito a registro sanitário",
            },
            "alimento": {
                "regulamento": "Anvisa/MAPA",
                "categoria": "produto alimentício",
                "observacoes": "sujeito a vigilância sanitária",
            },
            "eletrônico": {
                "regulamento": "Anatel",
                "categoria": "equipamento eletrônico",
                "observacoes": "sujeito a homologação",
            },
            "automóvel": {
                "regulamento": "Inmetro/Contran",
                "categoria": "veículo automotor",
                "observacoes": "sujeito a normas de segurança",
            },
        }

        enhanced_info = []
        sources = []

        description_lower = description.lower()

        for keyword, info in regulatory_keywords.items():
            if keyword in description_lower:
                enhanced_info.append(
                    f"Produto classificado como {info['categoria']}, "
                    f"regulamentado por {info['regulamento']}. "
                    f"{info['observacoes']}."
                )
                sources.append(f"regulatory_base_{info['regulamento']}")

        # Adicionar informações específicas do NCM se disponível
        if ncm_sugerido:
            enhanced_info.append(f"NCM sugerido: {ncm_sugerido}")
            sources.append("ncm_database")

        return {
            "regulatory_info": enhanced_info,
            "sources": sources,
            "confidence": 0.9 if enhanced_info else 0.3,
        }

    async def _contextual_enhancement(
        self,
        description: str,
        gtin: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Enriquecimento contextual baseado em GTIN e contexto empresarial."""

        contextual_info = []
        sources = []

        # Informações do GTIN
        if gtin:
            gtin_info = self._analyze_gtin(gtin)
            if gtin_info:
                contextual_info.append(f"GTIN: {gtin} - {gtin_info}")
                sources.append("gtin_database")

        # Contexto empresarial
        if context:
            empresa_setor = context.get("empresa_setor")
            if empresa_setor:
                contextual_info.append(f"Setor empresarial: {empresa_setor}")
                sources.append("empresa_context")

        return {
            "contextual_info": contextual_info,
            "sources": sources,
            "confidence": 0.7 if contextual_info else 0.4,
        }

    def _analyze_gtin(self, gtin: str) -> Optional[str]:
        """Analisa o GTIN para extrair informações básicas."""
        if not gtin or len(gtin) not in [8, 12, 13, 14]:
            return None

        # Prefixos de países conhecidos
        country_prefixes = {"789": "Brasil", "790": "Brasil", "780": "Brasil"}

        if len(gtin) >= 3:
            prefix = gtin[:3]
            country = country_prefixes.get(prefix)
            if country:
                return f"Produto nacional (país: {country})"

        return "Produto com código de barras válido"

    async def _consolidate_enrichments(
        self, original: str, enrichments: Dict[str, Any], analysis: Dict[str, Any]
    ) -> str:
        """Consolida todos os enriquecimentos em uma descrição final."""

        consolidated = original

        # Aplicar enriquecimento semântico
        semantic = enrichments.get("semantic", {})
        if semantic.get("enhanced_text"):
            consolidated = semantic["enhanced_text"]

        # Adicionar informações regulamentares
        regulatory = enrichments.get("regulatory", {})
        if regulatory.get("regulatory_info"):
            regulatory_text = " ".join(regulatory["regulatory_info"])
            consolidated += f" [Regulamentação: {regulatory_text}]"

        # Adicionar contexto
        contextual = enrichments.get("contextual", {})
        if contextual.get("contextual_info"):
            contextual_text = " ".join(contextual["contextual_info"])
            consolidated += f" [Contexto: {contextual_text}]"

        return consolidated

    async def _extract_technical_features(self, description: str) -> Dict[str, Any]:
        """Extrai características técnicas da descrição enriquecida."""

        features = {
            "materials": [],
            "dimensions": [],
            "technical_specs": [],
            "usage": [],
            "regulatory": [],
        }

        # Extrair materiais
        material_patterns = [
            r"\b(aço|plástico|alumínio|ferro|cobre|madeira|tecido|vidro|cerâmica)\b"
        ]

        for pattern in material_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            features["materials"].extend(matches)

        # Extrair dimensões
        dimension_patterns = [
            r"\d+\s*(mm|cm|m|pol|polegadas)",
            r"\d+\s*x\s*\d+",
            r"\d+,?\d*\s*(kg|g|ton|litros?|ml)",
        ]

        for pattern in dimension_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            features["dimensions"].extend(matches)

        # Extrair especificações técnicas
        tech_patterns = [
            r"\d+\s*(V|volts?|watts?|Hz|hertz)",
            r"\d+\s*(Ah|mAh|amperes?)",
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            features["technical_specs"].extend(matches)

        return features

    def _calculate_enrichment_confidence(self, enrichments: Dict[str, Any]) -> float:
        """Calcula a confiança geral do enriquecimento."""

        confidences = []

        for strategy, result in enrichments.items():
            if isinstance(result, dict) and "confidence" in result:
                confidences.append(result["confidence"])

        if not confidences:
            return 0.5

        # Média ponderada das confianças
        return sum(confidences) / len(confidences)
