"""
CEST Agent - Agente Especialista em Classificação CEST
=====================================================

Este agente é responsável por:
- Classificação automática de produtos CEST
- Validação de códigos CEST existentes
- Análise de substituição tributária
- Sugestão de códigos CEST alternativos
- Detecção de inconsistências CEST
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from difflib import SequenceMatcher

from .base_agent import BaseAgent, AgentTask


class CESTAgent(BaseAgent):
    """
    Agente especializado em classificação CEST (Código Especificador da Substituição Tributária).

    Capacidades:
    - Classificação automática CEST
    - Validação de códigos CEST
    - Análise de substituição tributária
    - Mapeamento NCM-CEST
    - Detecção de inconsistências
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o agente CEST.

        Args:
            config: Configurações específicas do agente
        """
        default_config = {
            "cest_database_path": "data/cest_database.json",
            "confidence_threshold": 0.7,
            "max_suggestions": 5,
            "enable_ncm_mapping": True,
            "enable_st_analysis": True,
            "validation_strictness": "moderate",
        }

        # Merge configurações
        agent_config = {**default_config, **(config or {})}

        super().__init__(name="CESTAgent", config=agent_config)

        # Base de conhecimento CEST
        self.cest_database = self._load_cest_database()
        self.ncm_cest_mapping = self._build_ncm_cest_mapping()
        self.st_segments = self._load_st_segments()

        # Cache para classificações
        self.classification_cache = {}

        self.logger.info("CESTAgent inicializado com base de conhecimento CEST")

    def get_capabilities(self) -> List[str]:
        """
        Retorna capacidades do agente CEST.

        Returns:
            Lista de capacidades
        """
        return [
            "classify_cest",
            "validate_cest",
            "map_ncm_to_cest",
            "analyze_st_requirement",
            "suggest_alternatives",
            "detect_inconsistencies",
            "explain_classification",
            "compare_cest_codes",
            "extract_cest_keywords",
        ]

    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Processa tarefa de classificação CEST.

        Args:
            task: Tarefa contendo dados do produto para classificação CEST

        Returns:
            Resultado da classificação CEST
        """
        task_type = task.type
        data = task.data

        self.logger.info(f"Processando tarefa CEST: {task_type}")

        if task_type == "classify_cest":
            return await self._classify_cest(data)
        elif task_type == "validate_cest":
            return await self._validate_cest(data)
        elif task_type == "map_ncm_to_cest":
            return await self._map_ncm_to_cest(data)
        elif task_type == "analyze_st_requirement":
            return await self._analyze_st_requirement(data)
        elif task_type == "suggest_alternatives":
            return await self._suggest_alternatives(data)
        elif task_type == "detect_inconsistencies":
            return await self._detect_inconsistencies(data)
        elif task_type == "explain_classification":
            return await self._explain_classification(data)
        elif task_type == "compare_cest_codes":
            return await self._compare_cest_codes(data)
        elif task_type == "extract_cest_keywords":
            return await self._extract_cest_keywords(data)
        else:
            raise ValueError(f"Tipo de tarefa CEST não suportado: {task_type}")

    async def _classify_cest(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifica produto com código CEST.

        Args:
            data: Dados do produto (descrição, NCM, estado, etc.)

        Returns:
            Classificação CEST com confiança e justificativa
        """
        description = data.get("description", "")
        ncm_code = data.get("ncm_code", "")  # usado em cache e análise
        state = data.get("state", "")
        additional_info = data.get("additional_info", "")

        full_text = f"{description} {additional_info}".strip()
        self.logger.info(f"Classificando CEST para: '{description[:50]}...'")

        cache_key = self._generate_cache_key(f"{full_text}_{ncm_code}_{state}")
        if cache_key in self.classification_cache:
            cached = self.classification_cache[cache_key]
            cached["from_cache"] = True
            return cached

        ncm_based_matches: List[Dict[str, Any]] = []
        if ncm_code:
            ncm_based_matches = self._classify_by_ncm(ncm_code)

        keyword_matches = self._find_cest_keyword_matches(full_text)
        semantic_matches = self._cest_semantic_analysis(full_text)
        state_specific_matches: List[Dict[str, Any]] = []
        if state:
            state_specific_matches = self._find_state_specific_cest(state, full_text)

        all_candidates = self._combine_cest_results(
            ncm_based_matches, keyword_matches, semantic_matches, state_specific_matches
        )
        best = self._select_best_cest(all_candidates, full_text, ncm_code)
        st_analysis = self._analyze_st_requirement_for_cest(best["code"], state)
        explanation = self._generate_cest_explanation(best, ncm_code, st_analysis)
        alternatives = self._generate_cest_alternatives(all_candidates, best)

        result = {
            "cest_code": best["code"],
            "cest_description": best["description"],
            "confidence": best["confidence"],
            "classification_method": best["method"],
            "st_analysis": st_analysis,
            "explanation": explanation,
            "alternatives": alternatives,
            "ncm_cest_compatibility": self._check_ncm_cest_compatibility(
                ncm_code, best["code"]
            ),
            "processing_metadata": {
                "agent": self.name,
                "timestamp": datetime.now().isoformat(),
                "input_ncm": ncm_code,
                "state": state,
                "candidates_analyzed": len(all_candidates),
            },
        }

        self.classification_cache[cache_key] = result
        self.logger.info(
            f"CEST classificado: {best['code']} (confiança: {best['confidence']:.2f})"
        )
        return result

    async def _validate_cest(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida código CEST existente.

        Args:
            data: Dados contendo código CEST e informações do produto

        Returns:
            Resultado da validação
        """
        cest_code = data.get("cest_code", "")
        description = data.get("description", "")
        ncm_code = data.get("ncm_code", "")
        state = data.get("state", "")

        self.logger.info(f"Validando CEST: {cest_code}")

        # 1. Verificar formato do código
        format_validation = self._validate_cest_format(cest_code)

        # 2. Verificar existência na base
        existence_validation = self._validate_cest_existence(cest_code)

        # 3. Verificar compatibilidade com NCM
        ncm_compatibility = self._validate_cest_ncm_compatibility(cest_code, ncm_code)

        # 4. Verificar compatibilidade com descrição
        description_compatibility = self._validate_cest_description_compatibility(
            cest_code, description
        )

        # 5. Verificar aplicabilidade no estado
        state_applicability = self._validate_cest_state_applicability(cest_code, state)

        # 6. Calcular score geral de validação
        validation_score = self._calculate_cest_validation_score(
            format_validation,
            existence_validation,
            ncm_compatibility,
            description_compatibility,
            state_applicability,
        )

        # 7. Gerar recomendações
        recommendations = self._generate_cest_validation_recommendations(
            cest_code, validation_score, format_validation, existence_validation
        )

        result = {
            "cest_code": cest_code,
            "is_valid": validation_score >= 0.7,
            "validation_score": validation_score,
            "format_check": format_validation,
            "existence_check": existence_validation,
            "ncm_compatibility": ncm_compatibility,
            "description_compatibility": description_compatibility,
            "state_applicability": state_applicability,
            "recommendations": recommendations,
            "validation_details": {
                "strictness_level": self.config["validation_strictness"],
                "threshold_used": 0.7,
            },
        }

        return result

    async def _map_ncm_to_cest(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mapeia código NCM para possíveis códigos CEST.

        Args:
            data: Dados contendo código NCM

        Returns:
            Mapeamento NCM-CEST
        """
        ncm_code = data.get("ncm_code", "")
        state = data.get("state", "")

        self.logger.info(f"Mapeando NCM {ncm_code} para CEST")

        if not ncm_code:
            return {"error": "Código NCM é obrigatório para mapeamento"}

        # Buscar CESTs relacionados ao NCM
        related_cests = self._find_cests_for_ncm(ncm_code)

        # Filtrar por estado se especificado
        if state and related_cests:
            state_filtered = self._filter_cests_by_state(related_cests, state)
            if state_filtered:
                related_cests = state_filtered

        # Enriquecer com informações detalhadas
        enriched_cests = []
        for cest_code in related_cests:
            cest_info = self.cest_database.get(cest_code, {})
            enriched_cests.append(
                {
                    "cest_code": cest_code,
                    "description": cest_info.get("description", ""),
                    "st_required": cest_info.get("st_required", False),
                    "applicable_states": cest_info.get("applicable_states", []),
                    "confidence": self._calculate_ncm_cest_confidence(
                        ncm_code, cest_code
                    ),
                }
            )

        # Ordenar por confiança
        enriched_cests = sorted(
            enriched_cests, key=lambda x: x["confidence"], reverse=True
        )

        result = {
            "ncm_code": ncm_code,
            "state": state,
            "related_cests": enriched_cests,
            "total_found": len(enriched_cests),
            "mapping_confidence": self._calculate_mapping_confidence(
                ncm_code, enriched_cests
            ),
            "st_implications": self._analyze_st_implications(enriched_cests, state),
        }

        return result

    async def _analyze_st_requirement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa exigência de substituição tributária (ST)."""
        cest_code = data.get("cest_code", "")
        state = data.get("state", "")
        operation_type = data.get("operation_type", "sale")

        self.logger.info(f"Analisando ST para CEST {cest_code} no estado {state}")
        cest_info = self.cest_database.get(cest_code, {})

        st_analysis: Dict[str, Any] = {
            "cest_code": cest_code,
            "state": state,
            "operation_type": operation_type,
            "st_required": False,
            "analysis_details": {},
        }

        if cest_info:
            st_analysis["st_required"] = cest_info.get("st_required", False)
            applicable_states = cest_info.get("applicable_states", [])
            if state and applicable_states:
                st_analysis["applicable_in_state"] = state in applicable_states
            else:
                st_analysis["applicable_in_state"] = True

            st_analysis["analysis_details"] = {
                "cest_description": cest_info.get("description", ""),
                "st_segment": cest_info.get("st_segment", ""),
                "mva": cest_info.get("mva", 0),
                "base_calculation": cest_info.get("base_calculation", ""),
                "exemptions": cest_info.get("exemptions", []),
            }
            st_analysis["is_exempt"] = self._check_st_exemption(
                operation_type, cest_info.get("exemptions", [])
            )
            st_analysis["tax_impact"] = self._calculate_st_tax_impact(
                cest_info, operation_type
            )
        else:
            st_analysis["error"] = "CEST não encontrado na base de dados"

        st_analysis["recommendations"] = self._generate_st_recommendations(st_analysis)
        return st_analysis

    async def _suggest_alternatives(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sugere códigos CEST alternativos."""
        current_cest = data.get("current_cest", "")
        description = data.get("description", "")
        ncm_code = data.get("ncm_code", "")

        self.logger.info(f"Sugerindo alternativas para CEST: {current_cest}")

        alternatives: List[Dict[str, Any]] = []

        if ncm_code:
            ncm_alternatives = await self._map_ncm_to_cest({"ncm_code": ncm_code})
            related = ncm_alternatives.get("related_cests") or []
            alternatives.extend(related)

        if description:
            description_alternatives = await self._classify_cest(
                {"description": description}
            )
            alt_list = description_alternatives.get("alternatives") or []
            alternatives.extend(alt_list)

        if current_cest:
            semantic_alternatives = self._find_similar_cests(current_cest)
            alternatives.extend(semantic_alternatives)

        unique_alternatives = self._deduplicate_and_rank_cest_alternatives(alternatives)
        max_suggestions = self.config.get("max_suggestions", 5)
        limited_alternatives = unique_alternatives[:max_suggestions]

        if limited_alternatives:
            conf_min = min(a["confidence"] for a in limited_alternatives)
            conf_max = max(a["confidence"] for a in limited_alternatives)
        else:
            conf_min = conf_max = 0.0

        return {
            "current_cest": current_cest,
            "alternatives": limited_alternatives,
            "total_found": len(unique_alternatives),
            "search_methods": ["ncm_based", "semantic", "description_based"],
            "confidence_range": {"min": conf_min, "max": conf_max},
        }

    def _load_cest_database(self) -> Dict[str, Dict[str, Any]]:
        """Carrega (ou define) base simplificada de códigos CEST."""
        return {
            "0100100": {
                "description": "Autopeças - Pneus novos",
                "st_required": True,
                "st_segment": "autopecas",
                "applicable_states": ["SP", "RJ", "MG", "RS"],
                "related_ncms": ["40111000", "40112000"],
                "mva": 41.53,
                "keywords": ["pneu", "autopeca", "automóvel", "veículo"],
            },
            "0100200": {
                "description": "Autopeças - Câmaras de ar",
                "st_required": True,
                "st_segment": "autopecas",
                "applicable_states": ["SP", "RJ", "MG", "RS"],
                "related_ncms": ["40131000"],
                "mva": 41.53,
                "keywords": ["câmara", "ar", "pneu", "autopeca"],
            },
            "1700100": {
                "description": "Medicamentos para uso humano",
                "st_required": True,
                "st_segment": "medicamentos",
                "applicable_states": ["SP", "RJ", "MG", "RS", "PR", "SC"],
                "related_ncms": ["30049099", "30041000"],
                "mva": 31.06,
                "keywords": ["medicamento", "remédio", "farmácia", "saúde"],
            },
        }

    def _build_ncm_cest_mapping(self) -> Dict[str, List[str]]:
        """Constrói mapeamento NCM-CEST."""
        mapping = {}

        for cest_code, cest_info in self.cest_database.items():
            related_ncms = cest_info.get("related_ncms", [])

            for ncm in related_ncms:
                if ncm not in mapping:
                    mapping[ncm] = []
                mapping[ncm].append(cest_code)

        return mapping

    def _load_st_segments(self) -> Dict[str, Dict[str, Any]]:
        """Carrega segmentos de substituição tributária."""
        return {
            "autopecas": {
                "description": "Autopeças",
                "typical_mva": 41.53,
                "main_operations": ["venda", "importação"],
                "common_ncms": ["40111000", "40112000", "40131000"],
            },
            "medicamentos": {
                "description": "Medicamentos",
                "typical_mva": 31.06,
                "main_operations": ["venda", "distribuição"],
                "common_ncms": ["30049099", "30041000", "30042000"],
            },
            "combustiveis": {
                "description": "Combustíveis",
                "typical_mva": 0,  # Regime especial
                "main_operations": ["distribuição", "revenda"],
                "common_ncms": ["27101990", "27111900"],
            },
        }

    def _classify_by_ncm(self, ncm_code: str) -> List[Dict[str, Any]]:
        """Classifica CEST baseado no NCM."""
        matches = []

        if ncm_code in self.ncm_cest_mapping:
            cest_codes = self.ncm_cest_mapping[ncm_code]

            for cest_code in cest_codes:
                matches.append(
                    {
                        "code": cest_code,
                        "confidence": 0.9,  # Alta confiança para mapeamento direto NCM-CEST
                        "method": "ncm_mapping",
                    }
                )

        return matches

    def _find_cest_keyword_matches(self, text: str) -> List[Dict[str, Any]]:
        """Encontra matches de palavras-chave CEST."""
        text_lower = text.lower()
        matches = []

        for cest_code, cest_info in self.cest_database.items():
            keywords = cest_info.get("keywords", [])

            keyword_matches = sum(1 for keyword in keywords if keyword in text_lower)

            if keyword_matches > 0:
                confidence = min(keyword_matches / len(keywords), 1.0) * 0.8
                matches.append(
                    {
                        "code": cest_code,
                        "confidence": confidence,
                        "method": "keyword_match",
                        "matched_keywords": [kw for kw in keywords if kw in text_lower],
                    }
                )

        return matches

    def _cest_semantic_analysis(self, text: str) -> List[Dict[str, Any]]:
        """Análise semântica para CEST."""
        matches = []

        for cest_code, cest_info in self.cest_database.items():
            description = cest_info.get("description", "")

            # Calcular similaridade
            similarity = SequenceMatcher(
                None, text.lower(), description.lower()
            ).ratio()

            if similarity > 0.3:  # Threshold mínimo
                matches.append(
                    {
                        "code": cest_code,
                        "confidence": min(similarity * 1.1, 1.0),
                        "method": "semantic_analysis",
                        "similarity_score": similarity,
                    }
                )

        return sorted(matches, key=lambda x: x["confidence"], reverse=True)

    def _find_state_specific_cest(self, state: str, text: str) -> List[Dict[str, Any]]:
        """Encontra CESTs específicos do estado."""
        matches = []

        for cest_code, cest_info in self.cest_database.items():
            applicable_states = cest_info.get("applicable_states", [])

            if state in applicable_states:
                # Bonus por ser aplicável no estado
                matches.append(
                    {"code": cest_code, "confidence": 0.6, "method": "state_specific"}
                )

        return matches

    def _combine_cest_results(
        self,
        ncm_matches: List,
        keyword_matches: List,
        semantic_matches: List,
        state_matches: List,
    ) -> List[Dict[str, Any]]:
        """Combina resultados de diferentes métodos CEST."""
        combined = {}

        all_matches = ncm_matches + keyword_matches + semantic_matches + state_matches

        for match in all_matches:
            code = match["code"]

            if code not in combined:
                combined[code] = {
                    "code": code,
                    "confidence": 0,
                    "methods": [],
                    "details": {},
                }

            # Atualizar confiança (usar máximo ou combinar)
            if match["method"] == "ncm_mapping":
                # NCM mapping tem alta prioridade
                combined[code]["confidence"] = max(
                    combined[code]["confidence"], match["confidence"]
                )
            else:
                # Combinar outras confianças
                combined[code]["confidence"] = min(
                    combined[code]["confidence"] + match["confidence"] * 0.3, 1.0
                )

            combined[code]["methods"].append(match["method"])
            combined[code]["details"][match["method"]] = match

        return list(combined.values())

    def _select_best_cest(
        self, candidates: List[Dict[str, Any]], text: str, ncm_code: str
    ) -> Dict[str, Any]:
        """Seleciona o melhor candidato CEST."""
        if not candidates:
            return {
                "code": "0000000",
                "description": "Não sujeito à ST",
                "confidence": 0.0,
                "method": "no_match",
            }

        # Ordenar por confiança, priorizando NCM mapping
        sorted_candidates = sorted(
            candidates,
            key=lambda x: (1 if "ncm_mapping" in x["methods"] else 0, x["confidence"]),
            reverse=True,
        )

        best = sorted_candidates[0]

        # Adicionar informações do CEST
        cest_info = self.cest_database.get(best["code"], {})

        return {
            "code": best["code"],
            "description": cest_info.get("description", "Descrição não disponível"),
            "confidence": best["confidence"],
            "method": "+".join(best["methods"]),
            "details": best["details"],
        }

    def _analyze_st_requirement_for_cest(
        self, cest_code: str, state: str
    ) -> Dict[str, Any]:
        """Analisa exigência de ST para um CEST específico."""
        cest_info = self.cest_database.get(cest_code, {})

        if not cest_info:
            return {"st_required": False, "reason": "CEST não encontrado"}

        st_required = cest_info.get("st_required", False)
        applicable_states = cest_info.get("applicable_states", [])

        analysis = {
            "st_required": st_required,
            "applicable_in_state": not state
            or state in applicable_states
            or not applicable_states,
            "mva": cest_info.get("mva", 0),
            "st_segment": cest_info.get("st_segment", ""),
            "reason": "",
        }

        if not st_required:
            analysis["reason"] = "CEST não sujeito à substituição tributária"
        elif state and applicable_states and state not in applicable_states:
            analysis["reason"] = f"ST não aplicável no estado {state}"
        else:
            analysis["reason"] = "Sujeito à substituição tributária"

        return analysis

    def _generate_cest_explanation(
        self, classification: Dict[str, Any], ncm_code: str, st_analysis: Dict[str, Any]
    ) -> str:
        """Gera explicação da classificação CEST."""
        explanations = []

        if "ncm_mapping" in classification["method"]:
            explanations.append(f"Baseado no mapeamento direto do NCM {ncm_code}")

        if "keyword_match" in classification["method"]:
            explanations.append("Baseado em palavras-chave específicas do produto")

        if "semantic_analysis" in classification["method"]:
            explanations.append("Baseado em análise semântica da descrição")

        # Adicionar informação sobre ST
        if st_analysis.get("st_required"):
            explanations.append("Produto sujeito à substituição tributária")

        confidence_text = f"Confiança: {classification['confidence']:.0%}"

        return f"{'; '.join(explanations)}. {confidence_text}."

    def _generate_cest_alternatives(
        self, all_candidates: List[Dict[str, Any]], best_classification: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Gera alternativas CEST."""
        alternatives = []

        # Excluir o melhor classificado
        best_code = best_classification["code"]

        for candidate in all_candidates:
            if candidate["code"] != best_code:
                cest_info = self.cest_database.get(candidate["code"], {})
                alternatives.append(
                    {
                        "cest_code": candidate["code"],
                        "description": cest_info.get("description", ""),
                        "confidence": candidate["confidence"],
                        "st_required": cest_info.get("st_required", False),
                        "reason": f"Método: {'+'.join(candidate['methods'])}",
                    }
                )

        # Ordenar por confiança e limitar
        alternatives = sorted(alternatives, key=lambda x: x["confidence"], reverse=True)
        return alternatives[:3]  # Máximo 3 alternativas

    def _check_ncm_cest_compatibility(
        self, ncm_code: str, cest_code: str
    ) -> Dict[str, Any]:
        """Verifica compatibilidade NCM-CEST."""
        if not ncm_code or not cest_code:
            return {"compatible": False, "reason": "NCM ou CEST não fornecido"}

        cest_info = self.cest_database.get(cest_code, {})
        related_ncms = cest_info.get("related_ncms", [])

        is_compatible = ncm_code in related_ncms

        return {
            "compatible": is_compatible,
            "reason": (
                "NCM compatível com CEST"
                if is_compatible
                else "NCM não relacionado ao CEST"
            ),
            "related_ncms": related_ncms,
        }

    def _generate_cache_key(self, text: str) -> str:
        """Gera chave para cache."""
        return str(hash(text.lower().strip()))

    def _validate_cest_format(self, cest_code: str) -> Dict[str, Any]:
        """Valida formato do código CEST."""
        is_valid = bool(re.match(r"^\d{7}$", cest_code))

        return {
            "is_valid": is_valid,
            "format_check": "7 dígitos numéricos" if is_valid else "Formato inválido",
            "code_length": len(cest_code),
        }

    def _validate_cest_existence(self, cest_code: str) -> Dict[str, Any]:
        """Valida existência do CEST na base."""
        exists = cest_code in self.cest_database

        return {
            "exists": exists,
            "in_database": exists,
            "description": self.cest_database.get(cest_code, {}).get("description", ""),
        }

    def _validate_cest_ncm_compatibility(
        self, cest_code: str, ncm_code: str
    ) -> Dict[str, Any]:
        """Valida compatibilidade CEST-NCM."""
        if not ncm_code:
            return {"compatible": True, "reason": "NCM não fornecido para validação"}

        compatibility = self._check_ncm_cest_compatibility(ncm_code, cest_code)
        return compatibility

    def _validate_cest_description_compatibility(
        self, cest_code: str, description: str
    ) -> Dict[str, Any]:
        """Valida compatibilidade CEST com descrição do produto."""
        if not description:
            return {
                "compatible": True,
                "score": 0.5,
                "reason": "Descrição não fornecida",
            }

        cest_info = self.cest_database.get(cest_code, {})
        cest_description = cest_info.get("description", "")
        keywords = cest_info.get("keywords", [])

        # Calcular similaridade
        description_similarity = SequenceMatcher(
            None, description.lower(), cest_description.lower()
        ).ratio()

        # Verificar palavras-chave
        description_lower = description.lower()
        keyword_matches = sum(1 for keyword in keywords if keyword in description_lower)
        keyword_score = keyword_matches / len(keywords) if keywords else 0

        # Score combinado
        combined_score = (description_similarity * 0.4) + (keyword_score * 0.6)

        return {
            "compatible": combined_score > 0.3,
            "score": combined_score,
            "description_similarity": description_similarity,
            "keyword_score": keyword_score,
            "matched_keywords": [kw for kw in keywords if kw in description_lower],
        }

    def _validate_cest_state_applicability(
        self, cest_code: str, state: str
    ) -> Dict[str, Any]:
        """Valida aplicabilidade do CEST no estado."""
        if not state:
            return {"applicable": True, "reason": "Estado não especificado"}

        cest_info = self.cest_database.get(cest_code, {})
        applicable_states = cest_info.get("applicable_states", [])

        if not applicable_states:
            # Se não especificado, assume aplicável
            return {"applicable": True, "reason": "Aplicável em todos os estados"}

        is_applicable = state in applicable_states

        return {
            "applicable": is_applicable,
            "reason": (
                f"Aplicável no estado {state}"
                if is_applicable
                else f"Não aplicável no estado {state}"
            ),
            "applicable_states": applicable_states,
        }

    def _calculate_cest_validation_score(
        self,
        format_val: Dict,
        existence_val: Dict,
        ncm_comp: Dict,
        desc_comp: Dict,
        state_app: Dict,
    ) -> float:
        """Calcula score geral de validação CEST."""
        weights = {
            "format": 0.2,
            "existence": 0.3,
            "ncm_compatibility": 0.2,
            "description_compatibility": 0.2,
            "state_applicability": 0.1,
        }

        scores = {
            "format": 1.0 if format_val["is_valid"] else 0.0,
            "existence": 1.0 if existence_val["exists"] else 0.0,
            "ncm_compatibility": 1.0 if ncm_comp["compatible"] else 0.0,
            "description_compatibility": desc_comp.get("score", 0.0),
            "state_applicability": 1.0 if state_app["applicable"] else 0.0,
        }

        weighted_score = sum(scores[key] * weights[key] for key in scores)
        return round(weighted_score, 3)

    def _generate_cest_validation_recommendations(
        self,
        cest_code: str,
        validation_score: float,
        format_val: Dict,
        existence_val: Dict,
    ) -> List[str]:
        """Gera recomendações de validação CEST."""
        recommendations = []

        if validation_score < 0.7:
            if not format_val["is_valid"]:
                recommendations.append(
                    "Corrigir formato do código CEST (deve ter 7 dígitos)"
                )

            if not existence_val["exists"]:
                recommendations.append(
                    "Verificar se o código CEST está correto - não encontrado na base"
                )

            if validation_score < 0.5:
                recommendations.append("Revisar completamente a classificação CEST")
            elif validation_score < 0.7:
                recommendations.append(
                    "Validar novamente alguns aspectos da classificação"
                )
        else:
            recommendations.append("Classificação CEST aprovada")

        return recommendations

    def _find_cests_for_ncm(self, ncm_code: str) -> List[str]:
        """Encontra CESTs relacionados a um NCM."""
        return self.ncm_cest_mapping.get(ncm_code, [])

    def _filter_cests_by_state(self, cest_codes: List[str], state: str) -> List[str]:
        """Filtra CESTs por estado."""
        filtered = []

        for cest_code in cest_codes:
            cest_info = self.cest_database.get(cest_code, {})
            applicable_states = cest_info.get("applicable_states", [])

            if not applicable_states or state in applicable_states:
                filtered.append(cest_code)

        return filtered

    def _calculate_ncm_cest_confidence(self, ncm_code: str, cest_code: str) -> float:
        """Calcula confiança do mapeamento NCM-CEST."""
        cest_info = self.cest_database.get(cest_code, {})
        related_ncms = cest_info.get("related_ncms", [])

        if ncm_code in related_ncms:
            # Confiança baseada no número de NCMs relacionados
            base_confidence = 0.9
            ncm_specificity = 1.0 / len(related_ncms) if related_ncms else 0
            return min(base_confidence + (ncm_specificity * 0.1), 1.0)

        return 0.0

    def _calculate_mapping_confidence(self, ncm_code: str, cests: List[Dict]) -> float:
        """Calcula confiança geral do mapeamento."""
        if not cests:
            return 0.0

        total_confidence = sum(cest["confidence"] for cest in cests)
        return min(total_confidence / len(cests), 1.0)

    def _analyze_st_implications(self, cests: List[Dict], state: str) -> Dict[str, Any]:
        """Analisa implicações de ST."""
        st_required_count = sum(1 for cest in cests if cest.get("st_required", False))

        implications = {
            "total_cests": len(cests),
            "st_required_count": st_required_count,
            "st_percentage": (st_required_count / len(cests)) * 100 if cests else 0,
            "likely_st_required": st_required_count > len(cests) / 2,
            "state": state,
        }

        if state:
            state_applicable = sum(
                1
                for cest in cests
                if not cest.get("applicable_states")
                or state in cest.get("applicable_states", [])
            )
            implications["state_applicable_count"] = state_applicable
            implications["state_applicability_percentage"] = (
                (state_applicable / len(cests)) * 100 if cests else 0
            )

        return implications

    def _check_st_exemption(self, operation_type: str, exemptions: List[str]) -> bool:
        """Verifica se operação está isenta de ST."""
        return operation_type in exemptions

    def _calculate_st_tax_impact(
        self, cest_info: Dict, operation_type: str
    ) -> Dict[str, Any]:
        """Calcula impacto tributário da ST."""
        mva = cest_info.get("mva", 0)

        impact = {
            "mva_percentage": mva,
            "operation_type": operation_type,
            "impact_level": "low" if mva < 20 else "medium" if mva < 50 else "high",
        }

        if mva > 0:
            impact["estimated_tax_increase"] = f"{mva}% sobre o valor da operação"
        else:
            impact["estimated_tax_increase"] = "Sem impacto adicional"

        return impact

    def _generate_st_recommendations(self, st_analysis: Dict) -> List[str]:
        """Gera recomendações de ST."""
        recommendations = []

        if st_analysis.get("st_required"):
            if st_analysis.get("applicable_in_state"):
                recommendations.append("Calcular ST conforme legislação estadual")
                recommendations.append("Verificar MVA aplicável")

                if st_analysis.get("is_exempt"):
                    recommendations.append(
                        "Operação pode estar isenta - verificar condições"
                    )
            else:
                recommendations.append("ST não aplicável neste estado")
        else:
            recommendations.append("Produto não sujeito à substituição tributária")

        return recommendations

    def _find_similar_cests(self, cest_code: str) -> List[Dict[str, Any]]:
        """Encontra CESTs similares."""
        similar = []

        if cest_code not in self.cest_database:
            return similar

        base_cest = self.cest_database[cest_code]
        base_segment = base_cest.get("st_segment", "")
        base_keywords = set(base_cest.get("keywords", []))

        for code, info in self.cest_database.items():
            if code == cest_code:
                continue

            similarity_score = 0.0

            # Mesmo segmento ST
            if info.get("st_segment") == base_segment and base_segment:
                similarity_score += 0.4

            # Palavras-chave em comum
            common_keywords = base_keywords.intersection(set(info.get("keywords", [])))
            if base_keywords:
                keyword_similarity = len(common_keywords) / len(base_keywords)
                similarity_score += keyword_similarity * 0.6

            if similarity_score > 0.3:
                similar.append(
                    {
                        "cest_code": code,
                        "description": info.get("description", ""),
                        "confidence": similarity_score,
                        "st_required": info.get("st_required", False),
                        "similarity_factors": {
                            "same_segment": info.get("st_segment") == base_segment,
                            "common_keywords": list(common_keywords),
                            "keyword_similarity": (
                                keyword_similarity if base_keywords else 0
                            ),
                        },
                    }
                )

        return sorted(similar, key=lambda x: x["confidence"], reverse=True)

    def _deduplicate_and_rank_cest_alternatives(
        self, alternatives: List[Dict]
    ) -> List[Dict]:
        """Remove duplicatas e ordena alternativas CEST."""
        unique_alternatives = {}

        for alt in alternatives:
            code = alt.get("cest_code") or alt.get("code")

            if code not in unique_alternatives:
                unique_alternatives[code] = alt
            else:
                # Manter o com maior confiança
                if alt.get("confidence", 0) > unique_alternatives[code].get(
                    "confidence", 0
                ):
                    unique_alternatives[code] = alt

        # Ordenar por confiança
        sorted_alternatives = sorted(
            unique_alternatives.values(),
            key=lambda x: x.get("confidence", 0),
            reverse=True,
        )

        return sorted_alternatives

    def _detect_ncm_cest_inconsistencies(self, products: List[Dict]) -> List[Dict]:
        """Detecta inconsistências NCM-CEST."""
        inconsistencies = []

        for product in products:
            ncm_code = product.get("ncm_code", "")
            cest_code = product.get("cest_code", "")

            if ncm_code and cest_code:
                compatibility = self._check_ncm_cest_compatibility(ncm_code, cest_code)

                if not compatibility["compatible"]:
                    inconsistencies.append(
                        {
                            "type": "ncm_cest_incompatibility",
                            "product_id": product.get("id"),
                            "ncm_code": ncm_code,
                            "cest_code": cest_code,
                            "description": compatibility["reason"],
                            "severity": "high",
                        }
                    )

        return inconsistencies

    def _detect_st_inconsistencies(self, products: List[Dict]) -> List[Dict]:
        """Detecta inconsistências de ST."""
        inconsistencies = []

        for product in products:
            cest_code = product.get("cest_code", "")
            state = product.get("state", "")
            st_applied = product.get("st_applied", False)

            if cest_code:
                st_analysis = self._analyze_st_requirement_for_cest(cest_code, state)
                should_have_st = st_analysis.get(
                    "st_required", False
                ) and st_analysis.get("applicable_in_state", True)

                if should_have_st != st_applied:
                    inconsistencies.append(
                        {
                            "type": "st_application_inconsistency",
                            "product_id": product.get("id"),
                            "cest_code": cest_code,
                            "expected_st": should_have_st,
                            "applied_st": st_applied,
                            "description": f"ST {'deveria estar' if should_have_st else 'não deveria estar'} aplicada",
                            "severity": "medium",
                        }
                    )

        return inconsistencies

    def _detect_cest_description_inconsistencies(
        self, products: List[Dict]
    ) -> List[Dict]:
        """Detecta inconsistências de descrição CEST."""
        inconsistencies = []

        # Agrupar produtos por CEST
        cest_groups = {}
        for product in products:
            cest_code = product.get("cest_code", "")
            if cest_code:
                if cest_code not in cest_groups:
                    cest_groups[cest_code] = []
                cest_groups[cest_code].append(product)

        # Verificar consistência dentro de cada grupo
        for cest_code, group_products in cest_groups.items():
            if len(group_products) > 1:
                descriptions = [p.get("description", "") for p in group_products]

                # Calcular similaridade entre descrições
                for i, desc1 in enumerate(descriptions):
                    for j, desc2 in enumerate(descriptions[i + 1 :], i + 1):
                        similarity = SequenceMatcher(
                            None, desc1.lower(), desc2.lower()
                        ).ratio()

                        if similarity < 0.3:  # Baixa similaridade
                            inconsistencies.append(
                                {
                                    "type": "cest_description_inconsistency",
                                    "cest_code": cest_code,
                                    "product_ids": [
                                        group_products[i].get("id"),
                                        group_products[j].get("id"),
                                    ],
                                    "descriptions": [desc1, desc2],
                                    "similarity": similarity,
                                    "description": "Produtos com mesmo CEST têm descrições muito diferentes",
                                    "severity": "low",
                                }
                            )

        return inconsistencies

    def _classify_cest_inconsistencies(self, inconsistencies: List[Dict]) -> List[Dict]:
        """Classifica inconsistências por severidade."""
        severity_order = {"high": 3, "medium": 2, "low": 1}

        return sorted(
            inconsistencies,
            key=lambda x: severity_order.get(x.get("severity", "low"), 1),
            reverse=True,
        )

    def _count_inconsistencies_by_type(
        self, inconsistencies: List[Dict]
    ) -> Dict[str, int]:
        """Conta inconsistências por tipo."""
        counts = {}

        for inconsistency in inconsistencies:
            inc_type = inconsistency.get("type", "unknown")
            counts[inc_type] = counts.get(inc_type, 0) + 1

        return counts

    def _count_inconsistencies_by_severity(
        self, inconsistencies: List[Dict]
    ) -> Dict[str, int]:
        """Conta inconsistências por severidade."""
        counts = {"high": 0, "medium": 0, "low": 0}

        for inconsistency in inconsistencies:
            severity = inconsistency.get("severity", "low")
            counts[severity] = counts.get(severity, 0) + 1

        return counts

    def _generate_cest_inconsistency_recommendations(
        self, inconsistencies: List[Dict]
    ) -> List[str]:
        """Gera recomendações para inconsistências CEST."""
        recommendations = []

        high_severity = [
            inc for inc in inconsistencies if inc.get("severity") == "high"
        ]
        medium_severity = [
            inc for inc in inconsistencies if inc.get("severity") == "medium"
        ]

        if high_severity:
            recommendations.append(
                f"Corrigir urgentemente {len(high_severity)} inconsistências de alta severidade"
            )

        if medium_severity:
            recommendations.append(
                f"Revisar {len(medium_severity)} inconsistências de média severidade"
            )

        # Recomendações específicas por tipo
        type_counts = self._count_inconsistencies_by_type(inconsistencies)

        if type_counts.get("ncm_cest_incompatibility", 0) > 0:
            recommendations.append(
                "Verificar compatibilidade NCM-CEST nos produtos identificados"
            )

        if type_counts.get("st_application_inconsistency", 0) > 0:
            recommendations.append("Revisar aplicação de substituição tributária")

        if type_counts.get("cest_description_inconsistency", 0) > 0:
            recommendations.append("Padronizar descrições de produtos com mesmo CEST")

        if not inconsistencies:
            recommendations.append("Todas as classificações CEST estão consistentes")

        return recommendations

    async def _explain_classification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Explica uma classificação CEST específica."""
        cest_code = data.get("cest_code", "")

        if not cest_code:
            return {"error": "Código CEST é obrigatório"}

        cest_info = self.cest_database.get(cest_code, {})

        if not cest_info:
            return {"error": "CEST não encontrado na base de dados"}

        explanation = {
            "cest_code": cest_code,
            "description": cest_info.get("description", ""),
            "characteristics": {
                "st_required": cest_info.get("st_required", False),
                "st_segment": cest_info.get("st_segment", ""),
                "mva": cest_info.get("mva", 0),
                "applicable_states": cest_info.get("applicable_states", []),
                "related_ncms": cest_info.get("related_ncms", []),
                "keywords": cest_info.get("keywords", []),
            },
            "usage_guidelines": self._generate_cest_usage_guidelines(cest_info),
            "common_applications": self._get_cest_common_applications(cest_code),
            "regulatory_notes": self._get_cest_regulatory_notes(cest_info),
        }

        return explanation

    async def _compare_cest_codes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Compara dois ou mais códigos CEST."""
        cest_codes = data.get("cest_codes", [])

        if len(cest_codes) < 2:
            return {
                "error": "Pelo menos dois códigos CEST são necessários para comparação"
            }

        comparison = {
            "codes_compared": cest_codes,
            "detailed_comparison": [],
            "similarities": [],
            "differences": [],
            "recommendations": [],
        }

        # Comparação detalhada
        for code in cest_codes:
            cest_info = self.cest_database.get(code, {})
            comparison["detailed_comparison"].append(
                {
                    "cest_code": code,
                    "description": cest_info.get("description", "Não encontrado"),
                    "st_required": cest_info.get("st_required", False),
                    "st_segment": cest_info.get("st_segment", ""),
                    "mva": cest_info.get("mva", 0),
                    "applicable_states": cest_info.get("applicable_states", []),
                    "related_ncms": cest_info.get("related_ncms", []),
                }
            )

        # Identificar semelhanças e diferenças
        comparison["similarities"], comparison["differences"] = (
            self._analyze_cest_similarities_differences(
                comparison["detailed_comparison"]
            )
        )

        # Recomendações
        comparison["recommendations"] = self._generate_cest_comparison_recommendations(
            comparison["similarities"], comparison["differences"]
        )

        return comparison

    async def _extract_cest_keywords(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai palavras-chave relevantes para classificação CEST."""
        text = data.get("text", "")

        if not text:
            return {"error": "Texto é obrigatório"}

        # Extrair palavras-chave específicas do domínio CEST
        cest_keywords = {
            "product_indicators": [],
            "st_indicators": [],
            "technical_terms": [],
            "commercial_terms": [],
        }

        text_lower = text.lower()

        # Indicadores de produto
        product_patterns = {
            "autopeças": ["pneu", "câmara", "filtro", "vela", "bateria", "óleo"],
            "medicamentos": [
                "medicamento",
                "remédio",
                "comprimido",
                "cápsula",
                "xarope",
            ],
            "combustível": ["gasolina", "diesel", "álcool", "combustível"],
            "bebidas": ["cerveja", "refrigerante", "água", "suco", "bebida"],
        }

        for category, keywords in product_patterns.items():
            found_keywords = [kw for kw in keywords if kw in text_lower]
            if found_keywords:
                cest_keywords["product_indicators"].extend(
                    [{"keyword": kw, "category": category} for kw in found_keywords]
                )

        # Indicadores de ST
        st_indicators = [
            "substituição",
            "tributária",
            "st",
            "margem",
            "valor",
            "agregado",
            "mva",
        ]
        cest_keywords["st_indicators"] = [
            kw for kw in st_indicators if kw in text_lower
        ]

        # Termos técnicos
        technical_patterns = re.findall(r"\b\d+[a-z]*\b|\b[A-Z]{2,}\b", text)
        cest_keywords["technical_terms"] = list(set(technical_patterns))

        # Sugerir CESTs baseados nas palavras-chave
        suggested_cests = self._suggest_cests_from_keywords(cest_keywords)

        return {
            "extracted_keywords": cest_keywords,
            "suggested_cests": suggested_cests,
            "extraction_confidence": self._calculate_keyword_extraction_confidence(
                cest_keywords
            ),
            "analysis_summary": self._summarize_keyword_analysis(cest_keywords),
        }

    # Métodos auxiliares para as novas funcionalidades

    def _generate_cest_usage_guidelines(self, cest_info: Dict) -> List[str]:
        """Gera diretrizes de uso do CEST."""
        guidelines = []

        if cest_info.get("st_required"):
            guidelines.append("Produto sujeito à substituição tributária")
            guidelines.append("Verificar legislação estadual específica")

            mva = cest_info.get("mva", 0)
            if mva > 0:
                guidelines.append(f"MVA típica: {mva}%")

        applicable_states = cest_info.get("applicable_states", [])
        if applicable_states:
            guidelines.append(f"Aplicável nos estados: {', '.join(applicable_states)}")

        guidelines.append("Verificar compatibilidade com NCM do produto")

        return guidelines

    def _get_cest_common_applications(self, cest_code: str) -> List[str]:
        """Obtém aplicações comuns do CEST."""
        # Base simplificada - em produção seria mais elaborada
        common_apps = {
            "0100100": [
                "Pneus para veículos",
                "Pneus para motocicletas",
                "Pneus para bicicletas",
            ],
            "1700100": [
                "Medicamentos genéricos",
                "Medicamentos de marca",
                "Antibióticos",
            ],
        }

        return common_apps.get(cest_code, ["Consultar legislação específica"])

    def _get_cest_regulatory_notes(self, cest_info: Dict) -> List[str]:
        """Obtém notas regulamentares do CEST."""
        notes = []

        if cest_info.get("st_required"):
            notes.append("Convênio ICMS 142/2018 - Lista de produtos sujeitos à ST")

        st_segment = cest_info.get("st_segment", "")
        if st_segment:
            notes.append(f"Segmento: {st_segment}")

        notes.append("Verificar atualizações na legislação estadual")

        return notes

    def _analyze_cest_similarities_differences(
        self, detailed_comparison: List[Dict]
    ) -> Tuple[List[str], List[str]]:
        """Analisa semelhanças e diferenças entre CESTs."""
        similarities = []
        differences = []

        if len(detailed_comparison) < 2:
            return similarities, differences

        # Verificar semelhanças
        # first_cest removido (não utilizado)

        # ST requirement
        st_requirements = [
            cest.get("st_required", False) for cest in detailed_comparison
        ]
        if all(st_requirements) or not any(st_requirements):
            similarities.append(
                f"Todos {'requerem' if st_requirements[0] else 'não requerem'} substituição tributária"
            )
        else:
            differences.append("Diferem na exigência de substituição tributária")

        # ST segment
        segments = [cest.get("st_segment", "") for cest in detailed_comparison]
        unique_segments = set(segments)
        if len(unique_segments) == 1 and segments[0]:
            similarities.append(f"Mesmo segmento ST: {segments[0]}")
        elif len(unique_segments) > 1:
            differences.append(f"Segmentos diferentes: {', '.join(unique_segments)}")

        return similarities, differences

    def _generate_cest_comparison_recommendations(
        self, similarities: List[str], differences: List[str]
    ) -> List[str]:
        """Gera recomendações baseadas na comparação."""
        recommendations = []

        if similarities:
            recommendations.append(
                "CESTs têm características similares - verificar se produtos são realmente diferentes"
            )

        if differences:
            recommendations.append(
                "CESTs têm diferenças significativas - confirmar classificação adequada"
            )

        recommendations.append("Verificar documentação específica de cada CEST")
        recommendations.append(
            "Consultar legislação estadual para confirmar aplicabilidade"
        )

        return recommendations

    def _suggest_cests_from_keywords(self, keywords: Dict) -> List[Dict]:
        """Sugere CESTs baseado em palavras-chave extraídas."""
        suggestions = []

        # Analisar indicadores de produto
        for indicator in keywords.get("product_indicators", []):
            category = indicator.get("category", "")

            # Mapear categorias para segmentos CEST
            category_mapping = {
                "autopeças": "autopecas",
                "medicamentos": "medicamentos",
                "combustível": "combustiveis",
                "bebidas": "bebidas",
            }

            target_segment = category_mapping.get(category)

            if target_segment:
                # Encontrar CESTs do segmento
                for cest_code, cest_info in self.cest_database.items():
                    if cest_info.get("st_segment") == target_segment:
                        suggestions.append(
                            {
                                "cest_code": cest_code,
                                "description": cest_info.get("description", ""),
                                "confidence": 0.7,
                                "reason": f"Baseado na categoria: {category}",
                            }
                        )

        # Remover duplicatas e ordenar
        unique_suggestions = {}
        for suggestion in suggestions:
            code = suggestion["cest_code"]
            if (
                code not in unique_suggestions
                or suggestion["confidence"] > unique_suggestions[code]["confidence"]
            ):
                unique_suggestions[code] = suggestion

        return sorted(
            unique_suggestions.values(), key=lambda x: x["confidence"], reverse=True
        )[:5]

    def _calculate_keyword_extraction_confidence(self, keywords: Dict) -> float:
        """Calcula confiança da extração de palavras-chave."""
        total_keywords = sum(
            len(keywords[key]) for key in keywords if isinstance(keywords[key], list)
        )

        if total_keywords == 0:
            return 0.0

        # Peso por tipo de palavra-chave
        weights = {
            "product_indicators": 0.4,
            "st_indicators": 0.3,
            "technical_terms": 0.2,
            "commercial_terms": 0.1,
        }

        weighted_score = 0.0
        for key, weight in weights.items():
            if key in keywords and isinstance(keywords[key], list):
                keyword_count = len(keywords[key])
                weighted_score += (
                    min(keyword_count / 5, 1.0) * weight
                )  # Máximo 5 keywords por categoria

        return min(weighted_score, 1.0)

    def _summarize_keyword_analysis(self, keywords: Dict) -> str:
        """Resumo da análise de palavras-chave."""
        summaries = []

        product_indicators = keywords.get("product_indicators", [])
        if product_indicators:
            categories = set(ind.get("category") for ind in product_indicators)
            summaries.append(f"Identificadas {len(categories)} categorias de produto")

        st_indicators = keywords.get("st_indicators", [])
        if st_indicators:
            summaries.append(
                f"Encontrados {len(st_indicators)} termos relacionados à ST"
            )

        technical_terms = keywords.get("technical_terms", [])
        if technical_terms:
            summaries.append(f"Identificados {len(technical_terms)} termos técnicos")

        if not summaries:
            return "Poucas palavras-chave específicas identificadas"

        return "; ".join(summaries)
