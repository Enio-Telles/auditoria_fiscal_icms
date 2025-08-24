"""
NCM Agent - Agente Especialista em Classificação NCM
===================================================

Este agente é responsável por:
- Classificação automática de produtos NCM
- Validação de códigos NCM existentes
- Sugestão de códigos NCM alternativos
- Análise de precisão de classificação NCM
- Detecção de inconsistências NCM
"""

import asyncio
import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from difflib import SequenceMatcher

from .base_agent import BaseAgent, AgentTask, TaskPriority


class NCMAgent(BaseAgent):
    """
    Agente especializado em classificação NCM (Nomenclatura Comum do Mercosul).
    
    Capacidades:
    - Classificação automática NCM
    - Validação de códigos NCM
    - Análise de hierarquia NCM
    - Sugestão de códigos alternativos
    - Detecção de inconsistências
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o agente NCM.
        
        Args:
            config: Configurações específicas do agente
        """
        default_config = {
            "ncm_database_path": "data/ncm_database.json",
            "confidence_threshold": 0.7,
            "max_suggestions": 5,
            "enable_hierarchical_analysis": True,
            "enable_semantic_matching": True,
            "validation_strictness": "moderate"
        }
        
        # Merge configurações
        agent_config = {**default_config, **(config or {})}
        
        super().__init__(name="NCMAgent", config=agent_config)
        
        # Base de conhecimento NCM
        self.ncm_database = self._load_ncm_database()
        self.ncm_hierarchy = self._build_ncm_hierarchy()
        self.keyword_patterns = self._load_keyword_patterns()
        
        # Cache para classificações
        self.classification_cache = {}
        
        self.logger.info("NCMAgent inicializado com base de conhecimento NCM")
    
    def get_capabilities(self) -> List[str]:
        """
        Retorna capacidades do agente NCM.
        
        Returns:
            Lista de capacidades
        """
        return [
            "classify_ncm",
            "validate_ncm",
            "suggest_alternatives",
            "analyze_hierarchy",
            "detect_inconsistencies",
            "explain_classification",
            "compare_ncm_codes",
            "extract_ncm_keywords"
        ]
    
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Processa tarefa de classificação NCM.
        
        Args:
            task: Tarefa contendo dados do produto para classificação NCM
            
        Returns:
            Resultado da classificação NCM
        """
        task_type = task.type
        data = task.data
        
        self.logger.info(f"Processando tarefa NCM: {task_type}")
        
        if task_type == "classify_ncm":
            return await self._classify_ncm(data)
        elif task_type == "validate_ncm":
            return await self._validate_ncm(data)
        elif task_type == "suggest_alternatives":
            return await self._suggest_alternatives(data)
        elif task_type == "analyze_hierarchy":
            return await self._analyze_hierarchy(data)
        elif task_type == "detect_inconsistencies":
            return await self._detect_inconsistencies(data)
        elif task_type == "explain_classification":
            return await self._explain_classification(data)
        elif task_type == "compare_ncm_codes":
            return await self._compare_ncm_codes(data)
        elif task_type == "extract_ncm_keywords":
            return await self._extract_ncm_keywords(data)
        else:
            raise ValueError(f"Tipo de tarefa NCM não suportado: {task_type}")
    
    async def _classify_ncm(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifica produto com código NCM.
        
        Args:
            data: Dados do produto (descrição, características, etc.)
            
        Returns:
            Classificação NCM com confiança e justificativa
        """
        description = data.get("description", "")
        additional_info = data.get("additional_info", "")
        product_category = data.get("category", "")
        
        # Texto completo para análise
        full_text = f"{description} {additional_info}".strip()
        
        self.logger.info(f"Classificando NCM para: '{description[:50]}...'")
        
        # Verificar cache primeiro
        cache_key = self._generate_cache_key(full_text)
        if cache_key in self.classification_cache:
            cached_result = self.classification_cache[cache_key]
            cached_result["from_cache"] = True
            return cached_result
        
        # 1. Análise por palavras-chave
        keyword_matches = self._find_keyword_matches(full_text)
        
        # 2. Análise semântica
        semantic_matches = self._semantic_analysis(full_text)
        
        # 3. Análise hierárquica (se categoria fornecida)
        hierarchical_matches = []
        if product_category:
            hierarchical_matches = self._hierarchical_analysis(product_category, full_text)
        
        # 4. Combinar resultados
        all_candidates = self._combine_classification_results(
            keyword_matches, semantic_matches, hierarchical_matches
        )
        
        # 5. Selecionar melhor candidato
        best_classification = self._select_best_ncm(all_candidates, full_text)
        
        # 6. Gerar explicação
        explanation = self._generate_classification_explanation(
            best_classification, keyword_matches, semantic_matches
        )
        
        # 7. Sugerir alternativas
        alternatives = self._generate_ncm_alternatives(all_candidates, best_classification)
        
        result = {
            "ncm_code": best_classification["code"],
            "ncm_description": best_classification["description"],
            "confidence": best_classification["confidence"],
            "classification_method": best_classification["method"],
            "explanation": explanation,
            "alternatives": alternatives,
            "keyword_matches": keyword_matches,
            "processing_metadata": {
                "agent": self.name,
                "timestamp": datetime.now().isoformat(),
                "input_text_length": len(full_text),
                "candidates_analyzed": len(all_candidates)
            }
        }
        
        # Adicionar ao cache
        self.classification_cache[cache_key] = result
        
        self.logger.info(f"NCM classificado: {best_classification['code']} (confiança: {best_classification['confidence']:.2f})")
        return result
    
    async def _validate_ncm(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida código NCM existente.
        
        Args:
            data: Dados contendo código NCM e descrição do produto
            
        Returns:
            Resultado da validação
        """
        ncm_code = data.get("ncm_code", "")
        description = data.get("description", "")
        
        self.logger.info(f"Validando NCM: {ncm_code}")
        
        # 1. Verificar formato do código
        format_validation = self._validate_ncm_format(ncm_code)
        
        # 2. Verificar existência na base
        existence_validation = self._validate_ncm_existence(ncm_code)
        
        # 3. Verificar compatibilidade com descrição
        compatibility_validation = self._validate_ncm_compatibility(ncm_code, description)
        
        # 4. Calcular score geral de validação
        validation_score = self._calculate_validation_score(
            format_validation, existence_validation, compatibility_validation
        )
        
        # 5. Gerar recomendações
        recommendations = self._generate_validation_recommendations(
            ncm_code, description, validation_score
        )
        
        result = {
            "ncm_code": ncm_code,
            "is_valid": validation_score >= 0.7,
            "validation_score": validation_score,
            "format_check": format_validation,
            "existence_check": existence_validation,
            "compatibility_check": compatibility_validation,
            "recommendations": recommendations,
            "validation_details": {
                "strictness_level": self.config["validation_strictness"],
                "threshold_used": 0.7
            }
        }
        
        return result
    
    async def _suggest_alternatives(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sugere códigos NCM alternativos.
        
        Args:
            data: Dados do produto ou NCM atual
            
        Returns:
            Lista de NCMs alternativos
        """
        current_ncm = data.get("current_ncm", "")
        description = data.get("description", "")
        
        self.logger.info(f"Sugerindo alternativas para NCM: {current_ncm}")
        
        alternatives = []
        
        # 1. Alternativas baseadas na hierarquia
        if current_ncm:
            hierarchical_alternatives = self._find_hierarchical_alternatives(current_ncm)
            alternatives.extend(hierarchical_alternatives)
        
        # 2. Alternativas baseadas na descrição
        if description:
            description_alternatives = await self._classify_ncm({"description": description})
            if description_alternatives.get("alternatives"):
                alternatives.extend(description_alternatives["alternatives"])
        
        # 3. Alternativas por similaridade semântica
        semantic_alternatives = self._find_semantic_alternatives(description)
        alternatives.extend(semantic_alternatives)
        
        # 4. Remover duplicatas e ordenar
        unique_alternatives = self._deduplicate_and_rank_alternatives(alternatives)
        
        # 5. Limitar número de sugestões
        max_suggestions = self.config["max_suggestions"]
        limited_alternatives = unique_alternatives[:max_suggestions]
        
        result = {
            "current_ncm": current_ncm,
            "alternatives": limited_alternatives,
            "total_found": len(unique_alternatives),
            "search_methods": ["hierarchical", "semantic", "description_based"],
            "confidence_range": {
                "min": min(alt["confidence"] for alt in limited_alternatives) if limited_alternatives else 0,
                "max": max(alt["confidence"] for alt in limited_alternatives) if limited_alternatives else 0
            }
        }
        
        return result
    
    async def _analyze_hierarchy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa hierarquia NCM.
        
        Args:
            data: Dados contendo código NCM
            
        Returns:
            Análise hierárquica
        """
        ncm_code = data.get("ncm_code", "")
        
        if not ncm_code or len(ncm_code) < 8:
            return {"error": "Código NCM inválido para análise hierárquica"}
        
        # Extrair níveis hierárquicos
        hierarchy_levels = self._extract_hierarchy_levels(ncm_code)
        
        # Analisar cada nível
        hierarchy_analysis = {}
        for level, code in hierarchy_levels.items():
            level_info = self._get_hierarchy_level_info(level, code)
            hierarchy_analysis[level] = level_info
        
        # Encontrar códigos relacionados
        related_codes = self._find_related_ncm_codes(ncm_code)
        
        result = {
            "ncm_code": ncm_code,
            "hierarchy_levels": hierarchy_analysis,
            "related_codes": related_codes,
            "hierarchy_path": self._build_hierarchy_path(ncm_code),
            "level_descriptions": self._get_level_descriptions(ncm_code)
        }
        
        return result
    
    async def _detect_inconsistencies(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detecta inconsistências em classificações NCM.
        
        Args:
            data: Dados de produtos com NCMs para análise
            
        Returns:
            Inconsistências detectadas
        """
        products = data.get("products", [])
        
        self.logger.info(f"Detectando inconsistências em {len(products)} produtos")
        
        inconsistencies = []
        
        # 1. Inconsistências por similaridade de descrição
        description_inconsistencies = self._detect_description_inconsistencies(products)
        inconsistencies.extend(description_inconsistencies)
        
        # 2. Inconsistências hierárquicas
        hierarchical_inconsistencies = self._detect_hierarchical_inconsistencies(products)
        inconsistencies.extend(hierarchical_inconsistencies)
        
        # 3. Inconsistências de padrão
        pattern_inconsistencies = self._detect_pattern_inconsistencies(products)
        inconsistencies.extend(pattern_inconsistencies)
        
        # 4. Classificar por severidade
        classified_inconsistencies = self._classify_inconsistencies(inconsistencies)
        
        result = {
            "total_products_analyzed": len(products),
            "inconsistencies_found": len(inconsistencies),
            "inconsistencies": classified_inconsistencies,
            "summary": {
                "by_type": self._count_by_type(inconsistencies),
                "by_severity": self._count_by_severity(classified_inconsistencies)
            },
            "recommendations": self._generate_inconsistency_recommendations(classified_inconsistencies)
        }
        
        return result
    
    async def _explain_classification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Explica uma classificação NCM.
        
        Args:
            data: Dados da classificação a ser explicada
            
        Returns:
            Explicação detalhada
        """
        ncm_code = data.get("ncm_code", "")
        description = data.get("description", "")
        
        # Obter informações detalhadas do NCM
        ncm_info = self._get_detailed_ncm_info(ncm_code)
        
        # Analisar compatibilidade
        compatibility_analysis = self._analyze_classification_compatibility(ncm_code, description)
        
        # Gerar explicação estruturada
        explanation = {
            "ncm_code": ncm_code,
            "ncm_details": ncm_info,
            "classification_rationale": compatibility_analysis["rationale"],
            "key_factors": compatibility_analysis["key_factors"],
            "confidence_factors": compatibility_analysis["confidence_factors"],
            "potential_issues": compatibility_analysis["potential_issues"],
            "improvement_suggestions": compatibility_analysis["suggestions"]
        }
        
        return explanation
    
    async def _compare_ncm_codes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compara códigos NCM.
        
        Args:
            data: Dados contendo códigos NCM para comparação
            
        Returns:
            Comparação detalhada
        """
        ncm_codes = data.get("ncm_codes", [])
        
        if len(ncm_codes) < 2:
            return {"error": "Pelo menos 2 códigos NCM são necessários para comparação"}
        
        # Comparar pares de códigos
        comparisons = []
        for i, code1 in enumerate(ncm_codes):
            for code2 in ncm_codes[i+1:]:
                comparison = self._compare_ncm_pair(code1, code2)
                comparisons.append(comparison)
        
        # Análise geral
        similarity_matrix = self._build_similarity_matrix(ncm_codes)
        
        result = {
            "ncm_codes": ncm_codes,
            "pairwise_comparisons": comparisons,
            "similarity_matrix": similarity_matrix,
            "most_similar_pair": self._find_most_similar_pair(comparisons),
            "most_different_pair": self._find_most_different_pair(comparisons),
            "clustering_suggestions": self._suggest_ncm_clustering(ncm_codes, similarity_matrix)
        }
        
        return result
    
    async def _extract_ncm_keywords(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai palavras-chave relevantes para NCM.
        
        Args:
            data: Dados contendo texto para extração
            
        Returns:
            Palavras-chave extraídas
        """
        text = data.get("text", "")
        
        # Extrair diferentes tipos de keywords
        extracted_keywords = {
            "material_keywords": self._extract_material_keywords(text),
            "process_keywords": self._extract_process_keywords(text),
            "application_keywords": self._extract_application_keywords(text),
            "technical_keywords": self._extract_technical_keywords(text),
            "category_keywords": self._extract_category_keywords(text)
        }
        
        # Mapear para possíveis NCMs
        ncm_mappings = {}
        for keyword_type, keywords in extracted_keywords.items():
            mappings = self._map_keywords_to_ncm(keywords)
            if mappings:
                ncm_mappings[keyword_type] = mappings
        
        result = {
            "extracted_keywords": extracted_keywords,
            "ncm_mappings": ncm_mappings,
            "total_keywords": sum(len(kw) for kw in extracted_keywords.values()),
            "confidence_scores": self._calculate_keyword_confidence(extracted_keywords)
        }
        
        return result
    
    # Métodos auxiliares
    
    def _load_ncm_database(self) -> Dict[str, Dict[str, Any]]:
        """Carrega base de dados NCM."""
        # Base simplificada para demonstração
        return {
            "84713000": {
                "description": "Máquinas automáticas para processamento de dados, portáteis",
                "chapter": "84",
                "heading": "8471",
                "subheading": "847130",
                "keywords": ["computador", "laptop", "portátil", "processamento", "dados"]
            },
            "30049099": {
                "description": "Outros medicamentos para uso humano",
                "chapter": "30",
                "heading": "3004",
                "subheading": "300490",
                "keywords": ["medicamento", "remédio", "farmacêutico", "saúde", "tratamento"]
            },
            "22030000": {
                "description": "Cerveja de malte",
                "chapter": "22",
                "heading": "2203",
                "subheading": "220300",
                "keywords": ["cerveja", "malte", "bebida", "alcoólica", "fermentada"]
            }
        }
    
    def _build_ncm_hierarchy(self) -> Dict[str, Dict[str, Any]]:
        """Constrói hierarquia NCM."""
        hierarchy = {}
        
        for code, info in self.ncm_database.items():
            chapter = info["chapter"]
            heading = info["heading"]
            
            if chapter not in hierarchy:
                hierarchy[chapter] = {"headings": {}, "description": f"Capítulo {chapter}"}
            
            if heading not in hierarchy[chapter]["headings"]:
                hierarchy[chapter]["headings"][heading] = {"codes": [], "description": f"Posição {heading}"}
            
            hierarchy[chapter]["headings"][heading]["codes"].append(code)
        
        return hierarchy
    
    def _load_keyword_patterns(self) -> Dict[str, List[str]]:
        """Carrega padrões de palavras-chave."""
        return {
            "electronics": ["eletrônico", "digital", "computador", "processador", "chip"],
            "pharmaceuticals": ["medicamento", "remédio", "farmacêutico", "droga", "terapêutico"],
            "beverages": ["bebida", "líquido", "suco", "água", "refrigerante"],
            "machinery": ["máquina", "equipamento", "aparelho", "dispositivo", "motor"],
            "textiles": ["tecido", "têxtil", "fibra", "algodão", "poliéster"],
            "chemicals": ["químico", "substância", "composto", "reagente", "solvente"]
        }
    
    def _find_keyword_matches(self, text: str) -> List[Dict[str, Any]]:
        """Encontra matches de palavras-chave."""
        text_lower = text.lower()
        matches = []
        
        for category, keywords in self.keyword_patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Buscar NCMs relacionados a esta categoria
                    related_ncms = self._find_ncms_by_category(category)
                    for ncm_code in related_ncms:
                        matches.append({
                            "ncm_code": ncm_code,
                            "keyword": keyword,
                            "category": category,
                            "confidence": 0.8,
                            "method": "keyword_match"
                        })
        
        return matches
    
    def _semantic_analysis(self, text: str) -> List[Dict[str, Any]]:
        """Análise semântica do texto."""
        matches = []
        
        # Análise simples baseada em similaridade de strings
        for ncm_code, ncm_info in self.ncm_database.items():
            description = ncm_info["description"]
            
            # Calcular similaridade
            similarity = SequenceMatcher(None, text.lower(), description.lower()).ratio()
            
            if similarity > 0.3:  # Threshold mínimo
                matches.append({
                    "ncm_code": ncm_code,
                    "similarity": similarity,
                    "confidence": min(similarity * 1.2, 1.0),
                    "method": "semantic_analysis"
                })
        
        return sorted(matches, key=lambda x: x["confidence"], reverse=True)
    
    def _hierarchical_analysis(self, category: str, text: str) -> List[Dict[str, Any]]:
        """Análise hierárquica baseada na categoria."""
        matches = []
        
        # Mapear categoria para capítulos NCM
        category_to_chapter = {
            "eletrônicos": "84",
            "medicamentos": "30",
            "bebidas": "22",
            "alimentos": "04",
            "têxtil": "52"
        }
        
        chapter = category_to_chapter.get(category.lower())
        if chapter and chapter in self.ncm_hierarchy:
            # Buscar NCMs do capítulo
            for heading_info in self.ncm_hierarchy[chapter]["headings"].values():
                for ncm_code in heading_info["codes"]:
                    matches.append({
                        "ncm_code": ncm_code,
                        "confidence": 0.6,
                        "method": "hierarchical_analysis",
                        "chapter": chapter
                    })
        
        return matches
    
    def _combine_classification_results(self, keyword_matches: List, semantic_matches: List, hierarchical_matches: List) -> List[Dict[str, Any]]:
        """Combina resultados de diferentes métodos."""
        combined = {}
        
        # Processar matches de palavras-chave
        for match in keyword_matches:
            code = match["ncm_code"]
            if code not in combined:
                combined[code] = {
                    "code": code,
                    "confidence": 0,
                    "methods": [],
                    "details": {}
                }
            combined[code]["confidence"] = max(combined[code]["confidence"], match["confidence"])
            combined[code]["methods"].append("keyword")
            combined[code]["details"]["keyword"] = match
        
        # Processar matches semânticos
        for match in semantic_matches:
            code = match["ncm_code"]
            if code not in combined:
                combined[code] = {
                    "code": code,
                    "confidence": 0,
                    "methods": [],
                    "details": {}
                }
            combined[code]["confidence"] = max(combined[code]["confidence"], match["confidence"])
            combined[code]["methods"].append("semantic")
            combined[code]["details"]["semantic"] = match
        
        # Processar matches hierárquicos
        for match in hierarchical_matches:
            code = match["ncm_code"]
            if code not in combined:
                combined[code] = {
                    "code": code,
                    "confidence": 0,
                    "methods": [],
                    "details": {}
                }
            # Boost de confiança se múltiplos métodos concordam
            if len(combined[code]["methods"]) > 0:
                combined[code]["confidence"] = min(combined[code]["confidence"] + 0.2, 1.0)
            else:
                combined[code]["confidence"] = match["confidence"]
            combined[code]["methods"].append("hierarchical")
            combined[code]["details"]["hierarchical"] = match
        
        return list(combined.values())
    
    def _select_best_ncm(self, candidates: List[Dict[str, Any]], text: str) -> Dict[str, Any]:
        """Seleciona o melhor candidato NCM."""
        if not candidates:
            return {
                "code": "00000000",
                "description": "Não classificado",
                "confidence": 0.0,
                "method": "no_match"
            }
        
        # Ordenar por confiança
        sorted_candidates = sorted(candidates, key=lambda x: x["confidence"], reverse=True)
        best = sorted_candidates[0]
        
        # Adicionar informações do NCM
        ncm_info = self.ncm_database.get(best["code"], {})
        
        return {
            "code": best["code"],
            "description": ncm_info.get("description", "Descrição não disponível"),
            "confidence": best["confidence"],
            "method": "+".join(best["methods"]),
            "details": best["details"]
        }
    
    def _generate_classification_explanation(self, classification: Dict[str, Any], keyword_matches: List, semantic_matches: List) -> str:
        """Gera explicação da classificação."""
        explanations = []
        
        if "keyword" in classification["method"]:
            explanations.append("Baseado em palavras-chave identificadas no texto")
        
        if "semantic" in classification["method"]:
            explanations.append("Baseado em análise semântica da descrição")
        
        if "hierarchical" in classification["method"]:
            explanations.append("Baseado na categoria hierárquica do produto")
        
        confidence_text = f"Confiança: {classification['confidence']:.0%}"
        
        return f"{'; '.join(explanations)}. {confidence_text}."
    
    def _generate_ncm_alternatives(self, all_candidates: List[Dict[str, Any]], best_classification: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gera alternativas NCM."""
        alternatives = []
        
        # Excluir o melhor classificado
        best_code = best_classification["code"]
        
        for candidate in all_candidates:
            if candidate["code"] != best_code:
                ncm_info = self.ncm_database.get(candidate["code"], {})
                alternatives.append({
                    "ncm_code": candidate["code"],
                    "description": ncm_info.get("description", ""),
                    "confidence": candidate["confidence"],
                    "reason": f"Método: {'+'.join(candidate['methods'])}"
                })
        
        # Ordenar por confiança e limitar
        alternatives = sorted(alternatives, key=lambda x: x["confidence"], reverse=True)
        return alternatives[:3]  # Máximo 3 alternativas
    
    def _generate_cache_key(self, text: str) -> str:
        """Gera chave para cache."""
        return str(hash(text.lower().strip()))
    
    def _validate_ncm_format(self, ncm_code: str) -> Dict[str, Any]:
        """Valida formato do código NCM."""
        is_valid = bool(re.match(r'^\d{8}$', ncm_code))
        
        return {
            "is_valid": is_valid,
            "format_check": "8 dígitos numéricos" if is_valid else "Formato inválido",
            "code_length": len(ncm_code)
        }
    
    def _validate_ncm_existence(self, ncm_code: str) -> Dict[str, Any]:
        """Valida existência do NCM na base."""
        exists = ncm_code in self.ncm_database
        
        return {
            "exists": exists,
            "in_database": exists,
            "description": self.ncm_database.get(ncm_code, {}).get("description", "")
        }
    
    def _validate_ncm_compatibility(self, ncm_code: str, description: str) -> Dict[str, Any]:
        """Valida compatibilidade NCM-descrição."""
        if not description or ncm_code not in self.ncm_database:
            return {"compatible": False, "confidence": 0.0}
        
        ncm_info = self.ncm_database[ncm_code]
        ncm_description = ncm_info["description"]
        
        # Análise de similaridade
        similarity = SequenceMatcher(None, description.lower(), ncm_description.lower()).ratio()
        
        # Verificar palavras-chave
        keywords = ncm_info.get("keywords", [])
        keyword_matches = sum(1 for kw in keywords if kw in description.lower())
        keyword_score = keyword_matches / max(1, len(keywords))
        
        # Score combinado
        compatibility_score = (similarity * 0.7) + (keyword_score * 0.3)
        
        return {
            "compatible": compatibility_score > 0.5,
            "confidence": compatibility_score,
            "similarity": similarity,
            "keyword_matches": keyword_matches,
            "total_keywords": len(keywords)
        }
    
    def _calculate_validation_score(self, format_val: Dict, existence_val: Dict, compatibility_val: Dict) -> float:
        """Calcula score geral de validação."""
        format_score = 1.0 if format_val["is_valid"] else 0.0
        existence_score = 1.0 if existence_val["exists"] else 0.0
        compatibility_score = compatibility_val.get("confidence", 0.0)
        
        # Pesos: formato (20%), existência (30%), compatibilidade (50%)
        return (format_score * 0.2) + (existence_score * 0.3) + (compatibility_score * 0.5)
    
    def _generate_validation_recommendations(self, ncm_code: str, description: str, score: float) -> List[str]:
        """Gera recomendações de validação."""
        recommendations = []
        
        if score < 0.3:
            recommendations.append("Código NCM provavelmente incorreto - revisar classificação")
        elif score < 0.7:
            recommendations.append("Código NCM questionável - verificar compatibilidade")
        else:
            recommendations.append("Código NCM aparenta estar correto")
        
        if not self._validate_ncm_format(ncm_code)["is_valid"]:
            recommendations.append("Corrigir formato do código NCM (8 dígitos)")
        
        if ncm_code not in self.ncm_database:
            recommendations.append("Verificar se código NCM existe na nomenclatura oficial")
        
        return recommendations
    
    def _find_ncms_by_category(self, category: str) -> List[str]:
        """Encontra NCMs por categoria."""
        ncms = []
        
        for ncm_code, ncm_info in self.ncm_database.items():
            keywords = ncm_info.get("keywords", [])
            category_keywords = self.keyword_patterns.get(category, [])
            
            if any(kw in keywords for kw in category_keywords):
                ncms.append(ncm_code)
        
        return ncms
