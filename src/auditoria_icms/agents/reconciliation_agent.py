"""
Agente de Reconciliação - Reconciliation Agent
Responsável pela análise final, validação cruzada e resolução de conflitos
entre as classificações NCM e CEST dos agentes especializados.
"""

import time
from typing import Dict, Any, Optional

from .base_agent import BaseAgent


class ReconciliationAgent(BaseAgent):
    """
    Agente de reconciliação que realiza validação cruzada entre NCM e CEST,
    resolve conflitos e produz a classificação final consolidada.
    """

    def __init__(self, llm, config: Dict[str, Any], logger=None):
        super().__init__("ReconciliationAgent", llm, config, logger)
        self.cross_validation = config.get("cross_validation", True)
        self.audit_trail = config.get("audit_trail", True)
        self.retrieval_tools = None

    def set_retrieval_tools(self, retrieval_tools):
        """Injeta as ferramentas de busca na base de conhecimento."""
        self.retrieval_tools = retrieval_tools

    async def process(
        self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Reconcilia e valida as classificações NCM e CEST dos agentes especializados.

        Args:
            input_data: Dados com resultados dos outros agentes
            context: Contexto adicional

        Returns:
            Classificação final reconciliada com análise de consistência
        """
        start_time = time.time()

        if not self.validate_input(input_data):
            raise ValueError("Dados de entrada inválidos para ReconciliationAgent")

        # Extrair classificações dos agentes anteriores
        ncm_result = input_data.get("ncm_result", {})
        cest_result = input_data.get("cest_result", {})
        descricao = (
            input_data.get("descricao_enriquecida") or input_data["descricao_produto"]
        )

        sources_used = ["reconciliation_analysis"]

        # 1. Validação cruzada NCM-CEST
        cross_validation_result = await self._cross_validate_ncm_cest(
            ncm_result, cest_result
        )

        # 2. Análise de consistência
        consistency_analysis = await self._analyze_consistency(
            ncm_result, cest_result, descricao
        )

        # 3. Resolução de conflitos
        conflict_resolution = await self._resolve_conflicts(
            ncm_result, cest_result, cross_validation_result, consistency_analysis
        )

        # 4. Validação com Golden Set
        golden_set_validation = await self._validate_against_golden_set(
            descricao,
            conflict_resolution["ncm_final"],
            conflict_resolution["cest_final"],
        )

        # 5. Análise de confiança final
        final_confidence = await self._calculate_final_confidence(
            ncm_result,
            cest_result,
            cross_validation_result,
            consistency_analysis,
            golden_set_validation,
        )

        # 6. Gerar justificativas detalhadas
        detailed_justification = await self._generate_detailed_justification(
            ncm_result,
            cest_result,
            cross_validation_result,
            consistency_analysis,
            conflict_resolution,
            golden_set_validation,
        )

        processing_time = int((time.time() - start_time) * 1000)

        result = {
            "ncm_final": conflict_resolution["ncm_final"],
            "cest_final": conflict_resolution["cest_final"],
            "justificativa_ncm": conflict_resolution["justificativa_ncm"],
            "justificativa_cest": conflict_resolution["justificativa_cest"],
            "confidence_score": final_confidence,
            "cross_validation": cross_validation_result,
            "consistency_analysis": consistency_analysis,
            "conflict_resolution": conflict_resolution,
            "golden_set_match": golden_set_validation,
            "detailed_justification": detailed_justification,
            "requires_human_review": final_confidence < self.get_confidence_threshold(),
            "sources": sources_used,
            "success": True,
        }

        # Criar registro de decisão
        self.create_decision_record(
            input_data=input_data,
            output_data=result,
            reasoning=detailed_justification,
            confidence_score=final_confidence,
            sources_used=sources_used,
            processing_time_ms=processing_time,
        )

        return result

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Valida se há resultados dos agentes NCM e CEST para reconciliar."""
        return (
            "ncm_result" in input_data
            and "cest_result" in input_data
            and (
                "descricao_produto" in input_data
                or "descricao_enriquecida" in input_data
            )
        )

    async def _cross_validate_ncm_cest(
        self, ncm_result: Dict[str, Any], cest_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Valida se NCM e CEST são compatíveis entre si."""

        ncm_classificado = ncm_result.get("ncm_classificado")
        cest_classificado = cest_result.get("cest_classificado")

        if not ncm_classificado or not cest_classificado:
            return {
                "compatible": False,
                "reason": "NCM ou CEST não classificado",
                "confidence": 0.0,
            }

        try:
            # Buscar regras do CEST para verificar se incluem o NCM
            if self.retrieval_tools:
                cest_rules = await self.retrieval_tools.get_cest_ncm_rules(
                    cest_classificado
                )

                ncm_compatible = False
                matching_pattern = None

                for rule in cest_rules:
                    pattern = rule.get("ncm_pattern", "")
                    if self._ncm_matches_cest_pattern(ncm_classificado, pattern):
                        ncm_compatible = True
                        matching_pattern = pattern
                        break

                if ncm_compatible:
                    return {
                        "compatible": True,
                        "reason": f"NCM {ncm_classificado} está nas regras do CEST {cest_classificado}",
                        "matching_pattern": matching_pattern,
                        "confidence": 0.9,
                    }
                else:
                    return {
                        "compatible": False,
                        "reason": f"NCM {ncm_classificado} NÃO está nas regras do CEST {cest_classificado}",
                        "confidence": 0.1,
                    }

        except Exception as e:
            self.logger.error(f"Erro na validação cruzada: {str(e)}")

        return {
            "compatible": None,
            "reason": "Não foi possível validar compatibilidade",
            "confidence": 0.5,
        }

    async def _analyze_consistency(
        self, ncm_result: Dict[str, Any], cest_result: Dict[str, Any], descricao: str
    ) -> Dict[str, Any]:
        """Analisa a consistência interna das classificações."""

        analysis = {
            "ncm_consistency": {},
            "cest_consistency": {},
            "overall_consistency": 0.0,
        }

        # Análise de consistência do NCM
        ncm_confidence = ncm_result.get("confidence_score", 0.0)
        ncm_alternatives = ncm_result.get("alternative_ncms", [])

        # Se há muitas alternativas com confiança similar, há inconsistência
        if len(ncm_alternatives) > 2:
            high_conf_alternatives = [
                alt
                for alt in ncm_alternatives
                if alt.get("confidence", 0) > ncm_confidence * 0.8
            ]

            if len(high_conf_alternatives) > 1:
                analysis["ncm_consistency"]["multiple_high_confidence"] = True
                analysis["ncm_consistency"]["consistency_score"] = 0.6
            else:
                analysis["ncm_consistency"]["consistency_score"] = 0.8
        else:
            analysis["ncm_consistency"]["consistency_score"] = min(ncm_confidence, 0.9)

        # Análise de consistência do CEST
        cest_confidence = cest_result.get("confidence_score", 0.0)
        cest_alternatives = cest_result.get("alternative_cests", [])

        if len(cest_alternatives) > 2:
            high_conf_cest_alternatives = [
                alt
                for alt in cest_alternatives
                if alt.get("confidence", 0) > cest_confidence * 0.8
            ]

            if len(high_conf_cest_alternatives) > 1:
                analysis["cest_consistency"]["multiple_high_confidence"] = True
                analysis["cest_consistency"]["consistency_score"] = 0.6
            else:
                analysis["cest_consistency"]["consistency_score"] = 0.8
        else:
            analysis["cest_consistency"]["consistency_score"] = min(
                cest_confidence, 0.9
            )

        # Consistência geral
        analysis["overall_consistency"] = (
            analysis["ncm_consistency"]["consistency_score"]
            + analysis["cest_consistency"]["consistency_score"]
        ) / 2

        return analysis

    async def _resolve_conflicts(
        self,
        ncm_result: Dict[str, Any],
        cest_result: Dict[str, Any],
        cross_validation: Dict[str, Any],
        consistency_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Resolve conflitos entre classificações e determina valores finais."""

        ncm_classificado = ncm_result.get("ncm_classificado")
        cest_classificado = cest_result.get("cest_classificado")

        resolution = {
            "conflicts_detected": [],
            "resolution_strategy": "standard",
            "ncm_final": ncm_classificado,
            "cest_final": cest_classificado,
            "justificativa_ncm": ncm_result.get("justificativa", ""),
            "justificativa_cest": cest_result.get("justificativa", ""),
        }

        # Detectar conflitos
        conflicts = []

        # Conflito 1: NCM e CEST incompatíveis
        if cross_validation.get("compatible") is False:
            conflicts.append(
                {
                    "type": "ncm_cest_incompatible",
                    "description": cross_validation.get("reason", ""),
                    "severity": "high",
                }
            )

        # Conflito 2: Baixa consistência interna
        if consistency_analysis["overall_consistency"] < 0.6:
            conflicts.append(
                {
                    "type": "low_internal_consistency",
                    "description": "Múltiplas alternativas com confiança similar",
                    "severity": "medium",
                }
            )

        # Conflito 3: Baixa confiança geral
        ncm_conf = ncm_result.get("confidence_score", 0.0)
        cest_conf = cest_result.get("confidence_score", 0.0)

        if ncm_conf < 0.7 or cest_conf < 0.7:
            conflicts.append(
                {
                    "type": "low_confidence",
                    "description": f"Confiança NCM: {ncm_conf:.2%}, CEST: {cest_conf:.2%}",
                    "severity": "medium",
                }
            )

        resolution["conflicts_detected"] = conflicts

        # Aplicar estratégias de resolução
        if conflicts:
            if any(c["type"] == "ncm_cest_incompatible" for c in conflicts):
                # Estratégia: Priorizar NCM e revalidar CEST
                resolution = await self._resolve_incompatibility_conflict(
                    ncm_result, cest_result, resolution
                )

            elif any(c["severity"] == "high" for c in conflicts):
                # Estratégia: Usar alternativas mais confiáveis
                resolution = await self._resolve_high_severity_conflicts(
                    ncm_result, cest_result, resolution
                )

        return resolution

    async def _resolve_incompatibility_conflict(
        self,
        ncm_result: Dict[str, Any],
        cest_result: Dict[str, Any],
        resolution: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Resolve conflito de incompatibilidade entre NCM e CEST."""

        ncm_conf = ncm_result.get("confidence_score", 0.0)
        cest_conf = cest_result.get("confidence_score", 0.0)

        # Priorizar o resultado com maior confiança
        if ncm_conf > cest_conf:
            # Manter NCM, tentar encontrar CEST compatível
            ncm_final = ncm_result.get("ncm_classificado")

            if self.retrieval_tools:
                try:
                    compatible_cests = await self.retrieval_tools.search_cest_by_ncm(
                        ncm_final
                    )
                    if compatible_cests:
                        cest_final = compatible_cests[0]["cest"]
                        resolution.update(
                            {
                                "resolution_strategy": "ncm_priority_cest_revalidation",
                                "cest_final": cest_final,
                                "justificativa_cest": f"CEST revalidado para compatibilidade com NCM {ncm_final}",
                            }
                        )
                except Exception:
                    pass
        else:
            # Manter CEST, verificar se NCM pode ser ajustado
            resolution["resolution_strategy"] = "cest_priority_ncm_check"

        return resolution

    async def _resolve_high_severity_conflicts(
        self,
        ncm_result: Dict[str, Any],
        cest_result: Dict[str, Any],
        resolution: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Resolve conflitos de alta severidade usando alternativas."""

        # Tentar usar alternativas com maior confiança
        ncm_alternatives = ncm_result.get("alternative_ncms", [])
        cest_alternatives = cest_result.get("alternative_cests", [])

        if ncm_alternatives:
            best_ncm_alt = max(ncm_alternatives, key=lambda x: x.get("confidence", 0))
            if best_ncm_alt.get("confidence", 0) > ncm_result.get(
                "confidence_score", 0
            ):
                resolution.update(
                    {
                        "ncm_final": best_ncm_alt["ncm"],
                        "justificativa_ncm": f"Alternativa selecionada: {best_ncm_alt.get('source', '')}",
                    }
                )

        if cest_alternatives:
            best_cest_alt = max(cest_alternatives, key=lambda x: x.get("confidence", 0))
            if best_cest_alt.get("confidence", 0) > cest_result.get(
                "confidence_score", 0
            ):
                resolution.update(
                    {
                        "cest_final": best_cest_alt["cest"],
                        "justificativa_cest": f"Alternativa selecionada: {best_cest_alt.get('source', '')}",
                    }
                )

        resolution["resolution_strategy"] = "alternative_selection"
        return resolution

    async def _validate_against_golden_set(
        self, descricao: str, ncm_final: str, cest_final: str
    ) -> Dict[str, Any]:
        """Valida a classificação final contra o Golden Set."""

        if not self.retrieval_tools:
            return {"match_found": False, "confidence": 0.0}

        try:
            # Buscar correspondências no Golden Set
            golden_matches = await self.retrieval_tools.search_golden_set(
                descricao, top_k=3
            )

            if not golden_matches:
                return {"match_found": False, "confidence": 0.0}

            # Verificar se há match exato de classificação
            for match in golden_matches:
                if match.get("ncm") == ncm_final and match.get("cest") == cest_final:
                    return {
                        "match_found": True,
                        "match_type": "exact_classification",
                        "confidence": 0.95,
                        "golden_entry": match,
                        "similarity_score": match.get("score", 0),
                    }

            # Verificar match parcial (só NCM ou só CEST)
            ncm_matches = [m for m in golden_matches if m.get("ncm") == ncm_final]
            cest_matches = [m for m in golden_matches if m.get("cest") == cest_final]

            if ncm_matches:
                return {
                    "match_found": True,
                    "match_type": "ncm_only",
                    "confidence": 0.8,
                    "golden_entry": ncm_matches[0],
                }

            if cest_matches:
                return {
                    "match_found": True,
                    "match_type": "cest_only",
                    "confidence": 0.7,
                    "golden_entry": cest_matches[0],
                }

            return {"match_found": False, "confidence": 0.0}

        except Exception as e:
            self.logger.error(f"Erro na validação com Golden Set: {str(e)}")
            return {"match_found": False, "confidence": 0.0, "error": str(e)}

    async def _calculate_final_confidence(
        self,
        ncm_result: Dict[str, Any],
        cest_result: Dict[str, Any],
        cross_validation: Dict[str, Any],
        consistency_analysis: Dict[str, Any],
        golden_set_validation: Dict[str, Any],
    ) -> float:
        """Calcula a confiança final da classificação reconciliada."""

        # Confiança base dos agentes
        ncm_conf = ncm_result.get("confidence_score", 0.0)
        cest_conf = cest_result.get("confidence_score", 0.0)
        base_confidence = (ncm_conf + cest_conf) / 2

        # Fator de validação cruzada
        cross_validation_factor = 1.0
        if cross_validation.get("compatible") is True:
            cross_validation_factor = 1.2
        elif cross_validation.get("compatible") is False:
            cross_validation_factor = 0.7

        # Fator de consistência
        consistency_factor = consistency_analysis.get("overall_consistency", 0.5)

        # Fator Golden Set
        golden_set_factor = 1.0
        if golden_set_validation.get("match_found"):
            match_type = golden_set_validation.get("match_type", "")
            if match_type == "exact_classification":
                golden_set_factor = 1.3
            elif match_type in ["ncm_only", "cest_only"]:
                golden_set_factor = 1.1

        # Calcular confiança final
        final_confidence = (
            base_confidence
            * cross_validation_factor
            * consistency_factor
            * golden_set_factor
        )

        # Normalizar para [0, 1]
        return min(final_confidence, 1.0)

    async def _generate_detailed_justification(
        self,
        ncm_result: Dict[str, Any],
        cest_result: Dict[str, Any],
        cross_validation: Dict[str, Any],
        consistency_analysis: Dict[str, Any],
        conflict_resolution: Dict[str, Any],
        golden_set_validation: Dict[str, Any],
    ) -> str:
        """Gera justificativa detalhada para a classificação final."""

        justification_parts = [
            "=== ANÁLISE DE RECONCILIAÇÃO ===",
            "",
            f"NCM Final: {conflict_resolution.get('ncm_final', 'N/A')}",
            f"CEST Final: {conflict_resolution.get('cest_final', 'N/A')}",
            "",
            "1. VALIDAÇÃO CRUZADA NCM-CEST:",
            f"   Compatibilidade: {cross_validation.get('compatible', 'N/A')}",
            f"   Razão: {cross_validation.get('reason', 'N/A')}",
            "",
            "2. ANÁLISE DE CONSISTÊNCIA:",
            f"   Consistência NCM: {consistency_analysis['ncm_consistency'].get('consistency_score', 0):.2%}",
            f"   Consistência CEST: {consistency_analysis['cest_consistency'].get('consistency_score', 0):.2%}",
            f"   Consistência Geral: {consistency_analysis.get('overall_consistency', 0):.2%}",
        ]

        # Adicionar informações sobre conflitos
        conflicts = conflict_resolution.get("conflicts_detected", [])
        if conflicts:
            justification_parts.extend(
                [
                    "",
                    "3. CONFLITOS DETECTADOS:",
                ]
            )
            for i, conflict in enumerate(conflicts, 1):
                justification_parts.append(
                    f"   {i}. {conflict['type']}: {conflict['description']} (Severidade: {conflict['severity']})"
                )

            justification_parts.extend(
                [
                    "",
                    f"4. ESTRATÉGIA DE RESOLUÇÃO: {conflict_resolution.get('resolution_strategy', 'N/A')}",
                ]
            )

        # Adicionar validação Golden Set
        if golden_set_validation.get("match_found"):
            justification_parts.extend(
                [
                    "",
                    "5. VALIDAÇÃO GOLDEN SET:",
                    f"   Match encontrado: {golden_set_validation['match_type']}",
                    f"   Confiança do match: {golden_set_validation.get('confidence', 0):.2%}",
                ]
            )

        return "\n".join(justification_parts)

    def _ncm_matches_cest_pattern(self, ncm: str, pattern: str) -> bool:
        """Verifica se um NCM corresponde ao padrão de um CEST."""
        if not pattern or not ncm:
            return False

        # Correspondência exata
        if pattern == ncm:
            return True

        # Correspondência por prefixo (padrão hierárquico)
        if ncm.startswith(pattern):
            return True

        return False
