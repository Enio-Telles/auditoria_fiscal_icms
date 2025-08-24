"""
Expansion Agent - Agente de Expansão e Enriquecimento de Dados
============================================================

Este agente é responsável por:
- Expandir descrições de produtos com informações adicionais
- Enriquecer dados com contexto de classificação
- Buscar informações complementares em bases externas
- Normalizar e padronizar descrições
"""

import asyncio
import re
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_agent import BaseAgent, AgentTask, TaskPriority


class ExpansionAgent(BaseAgent):
    """
    Agente especializado em expansão e enriquecimento de dados de produtos.
    
    Capacidades:
    - Expansão de descrições curtas
    - Normalização de textos
    - Busca de sinônimos e termos relacionados
    - Identificação de características técnicas
    - Enriquecimento com dados de contexto
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o agente de expansão.
        
        Args:
            config: Configurações específicas do agente
        """
        default_config = {
            "max_description_length": 500,
            "min_description_length": 20,
            "enable_synonym_expansion": True,
            "enable_technical_details": True,
            "expansion_sources": ["internal", "external"],
            "confidence_threshold": 0.7
        }
        
        # Merge configurações
        agent_config = {**default_config, **(config or {})}
        
        super().__init__(name="ExpansionAgent", config=agent_config)
        
        # Base de sinônimos e termos técnicos
        self.synonyms_db = self._load_synonyms_database()
        self.technical_patterns = self._load_technical_patterns()
        
        self.logger.info("ExpansionAgent inicializado com capacidades de enriquecimento")
    
    def get_capabilities(self) -> List[str]:
        """
        Retorna capacidades do agente de expansão.
        
        Returns:
            Lista de capacidades
        """
        return [
            "expand_description",
            "normalize_text", 
            "extract_features",
            "enrich_product_data",
            "identify_technical_specs",
            "suggest_synonyms"
        ]
    
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Processa tarefa de expansão/enriquecimento.
        
        Args:
            task: Tarefa contendo dados do produto a ser expandido
            
        Returns:
            Dados expandidos e enriquecidos
        """
        task_type = task.type
        data = task.data
        
        self.logger.info(f"Processando tarefa de {task_type}")
        
        if task_type == "expand_description":
            return await self._expand_description(data)
        elif task_type == "normalize_text":
            return await self._normalize_text(data)
        elif task_type == "extract_features":
            return await self._extract_features(data)
        elif task_type == "enrich_product_data":
            return await self._enrich_product_data(data)
        elif task_type == "identify_technical_specs":
            return await self._identify_technical_specs(data)
        elif task_type == "suggest_synonyms":
            return await self._suggest_synonyms(data)
        else:
            raise ValueError(f"Tipo de tarefa não suportado: {task_type}")
    
    async def _expand_description(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expande descrição de produto com informações adicionais.
        
        Args:
            data: Dados contendo descrição original
            
        Returns:
            Descrição expandida e metadados
        """
        original_description = data.get("description", "")
        product_code = data.get("code", "")
        category = data.get("category", "")
        
        self.logger.info(f"Expandindo descrição: '{original_description[:50]}...'")
        
        # 1. Normalizar texto original
        normalized = self._clean_and_normalize(original_description)
        
        # 2. Identificar características técnicas
        technical_features = self._extract_technical_features(normalized)
        
        # 3. Buscar sinônimos e termos relacionados
        synonyms = self._find_relevant_synonyms(normalized)
        
        # 4. Construir descrição expandida
        expanded_parts = [normalized]
        
        # Adicionar características técnicas se encontradas
        if technical_features:
            tech_text = " - " + ", ".join(technical_features)
            expanded_parts.append(tech_text)
        
        # Adicionar contexto baseado na categoria
        if category:
            category_context = self._get_category_context(category)
            if category_context:
                expanded_parts.append(f" ({category_context})")
        
        # Montar descrição final
        expanded_description = "".join(expanded_parts)
        
        # Verificar limites de tamanho
        max_length = self.config["max_description_length"]
        if len(expanded_description) > max_length:
            expanded_description = expanded_description[:max_length-3] + "..."
        
        # Calcular confiança da expansão
        confidence = self._calculate_expansion_confidence(
            original_description, expanded_description, technical_features
        )
        
        result = {
            "original_description": original_description,
            "expanded_description": expanded_description,
            "technical_features": technical_features,
            "synonyms_found": synonyms,
            "expansion_confidence": confidence,
            "character_count": len(expanded_description),
            "expansion_ratio": len(expanded_description) / max(1, len(original_description)),
            "processing_metadata": {
                "agent": self.name,
                "timestamp": datetime.now().isoformat(),
                "method": "rule_based_expansion"
            }
        }
        
        self.logger.info(f"Descrição expandida com confiança {confidence:.2f}")
        return result
    
    async def _normalize_text(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza texto removendo inconsistências.
        
        Args:
            data: Dados contendo texto a ser normalizado
            
        Returns:
            Texto normalizado
        """
        text = data.get("text", "")
        
        normalized = self._clean_and_normalize(text)
        
        return {
            "original_text": text,
            "normalized_text": normalized,
            "changes_made": self._get_normalization_changes(text, normalized)
        }
    
    async def _extract_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai características específicas do produto.
        
        Args:
            data: Dados do produto
            
        Returns:
            Características extraídas
        """
        description = data.get("description", "")
        
        features = {
            "dimensions": self._extract_dimensions(description),
            "materials": self._extract_materials(description),
            "colors": self._extract_colors(description),
            "specifications": self._extract_specifications(description),
            "brand_indicators": self._extract_brand_indicators(description)
        }
        
        # Filtrar features vazias
        features = {k: v for k, v in features.items() if v}
        
        return {
            "extracted_features": features,
            "feature_count": len(features),
            "confidence_scores": self._calculate_feature_confidence(features)
        }
    
    async def _enrich_product_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquece dados completos do produto.
        
        Args:
            data: Dados completos do produto
            
        Returns:
            Dados enriquecidos com informações adicionais
        """
        # Combinar todas as funcionalidades
        expanded_desc = await self._expand_description(data)
        features = await self._extract_features(data)
        
        # Adicionar contexto de classificação
        classification_hints = self._generate_classification_hints(data)
        
        # Sugerir melhorias
        improvement_suggestions = self._suggest_data_improvements(data)
        
        return {
            "enriched_data": {
                **data,
                "expanded_description": expanded_desc["expanded_description"],
                "extracted_features": features["extracted_features"],
                "classification_hints": classification_hints,
                "data_quality_score": self._calculate_data_quality_score(data)
            },
            "improvements_suggested": improvement_suggestions,
            "enrichment_metadata": {
                "expansion_confidence": expanded_desc["expansion_confidence"],
                "features_extracted": len(features["extracted_features"]),
                "processing_time": datetime.now().isoformat()
            }
        }
    
    async def _identify_technical_specs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identifica especificações técnicas no texto.
        
        Args:
            data: Dados contendo texto para análise
            
        Returns:
            Especificações técnicas identificadas
        """
        text = data.get("description", "") + " " + data.get("additional_info", "")
        
        specs = {}
        
        # Padrões para diferentes tipos de especificações
        for pattern_name, pattern_config in self.technical_patterns.items():
            matches = self._find_pattern_matches(text, pattern_config)
            if matches:
                specs[pattern_name] = matches
        
        return {
            "technical_specifications": specs,
            "specification_count": len(specs),
            "confidence_by_spec": {
                spec: self._calculate_spec_confidence(matches)
                for spec, matches in specs.items()
            }
        }
    
    async def _suggest_synonyms(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sugere sinônimos para melhorar descrição.
        
        Args:
            data: Dados contendo texto para análise
            
        Returns:
            Sinônimos sugeridos
        """
        text = data.get("text", "")
        context = data.get("context", "")
        
        # Extrair palavras-chave
        keywords = self._extract_keywords(text)
        
        # Buscar sinônimos para cada palavra-chave
        synonym_suggestions = {}
        for keyword in keywords:
            synonyms = self._find_synonyms(keyword, context)
            if synonyms:
                synonym_suggestions[keyword] = synonyms
        
        return {
            "original_keywords": keywords,
            "synonym_suggestions": synonym_suggestions,
            "suggestion_count": sum(len(syns) for syns in synonym_suggestions.values())
        }
    
    # Métodos auxiliares
    
    def _load_synonyms_database(self) -> Dict[str, List[str]]:
        """Carrega base de sinônimos."""
        return {
            "plástico": ["polímero", "sintético", "PVC", "polietileno"],
            "metal": ["metálico", "aço", "ferro", "alumínio", "liga"],
            "vidro": ["cristal", "transparente", "vítreo"],
            "madeira": ["madeireira", "florestal", "tábua", "compensado"],
            "tecido": ["têxtil", "fibra", "algodão", "poliéster"],
            "eletrônico": ["digital", "tecnológico", "computacional"],
            "medicamento": ["farmacêutico", "medicinal", "terapêutico"],
            "alimento": ["alimentício", "comestível", "nutritivo"]
        }
    
    def _load_technical_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Carrega padrões para identificação de especificações técnicas."""
        return {
            "dimensions": {
                "patterns": [
                    r"(\d+(?:,\d+)?)\s*x\s*(\d+(?:,\d+)?)\s*x\s*(\d+(?:,\d+)?)\s*(cm|mm|m)",
                    r"(\d+(?:,\d+)?)\s*(cm|mm|m)\s*x\s*(\d+(?:,\d+)?)\s*(cm|mm|m)",
                    r"diâmetro\s*(\d+(?:,\d+)?)\s*(cm|mm|m)",
                    r"largura\s*(\d+(?:,\d+)?)\s*(cm|mm|m)"
                ],
                "confidence": 0.9
            },
            "weight": {
                "patterns": [
                    r"(\d+(?:,\d+)?)\s*(kg|g|ton|t)",
                    r"peso\s*(\d+(?:,\d+)?)\s*(kg|g|ton|t)"
                ],
                "confidence": 0.85
            },
            "voltage": {
                "patterns": [
                    r"(\d+)\s*v(?:olts?)?",
                    r"tensão\s*(\d+)\s*v",
                    r"(\d+)\s*volts?"
                ],
                "confidence": 0.8
            },
            "power": {
                "patterns": [
                    r"(\d+(?:,\d+)?)\s*w(?:atts?)?",
                    r"potência\s*(\d+(?:,\d+)?)\s*w",
                    r"(\d+(?:,\d+)?)\s*kw"
                ],
                "confidence": 0.8
            }
        }
    
    def _clean_and_normalize(self, text: str) -> str:
        """Limpa e normaliza texto."""
        if not text:
            return ""
        
        # Converter para minúsculas
        text = text.lower()
        
        # Remover caracteres especiais desnecessários
        text = re.sub(r'[^\w\s\-\(\)\.,]', '', text)
        
        # Normalizar espaços
        text = re.sub(r'\s+', ' ', text)
        
        # Remover espaços no início e fim
        text = text.strip()
        
        return text
    
    def _extract_technical_features(self, text: str) -> List[str]:
        """Extrai características técnicas do texto."""
        features = []
        
        for pattern_name, pattern_config in self.technical_patterns.items():
            matches = self._find_pattern_matches(text, pattern_config)
            if matches:
                features.extend([f"{pattern_name}: {match}" for match in matches[:2]])  # Limite 2 por tipo
        
        return features
    
    def _find_relevant_synonyms(self, text: str) -> List[str]:
        """Encontra sinônimos relevantes no texto."""
        synonyms = []
        words = text.split()
        
        for word in words:
            if word in self.synonyms_db:
                synonyms.extend(self.synonyms_db[word][:2])  # Máximo 2 sinônimos por palavra
        
        return list(set(synonyms))  # Remove duplicatas
    
    def _get_category_context(self, category: str) -> str:
        """Retorna contexto baseado na categoria."""
        category_contexts = {
            "eletrônicos": "dispositivo eletrônico",
            "medicamentos": "produto farmacêutico",
            "alimentos": "produto alimentício",
            "vestuário": "artigo de vestuário",
            "automóveis": "componente automotivo"
        }
        return category_contexts.get(category.lower(), "")
    
    def _calculate_expansion_confidence(self, original: str, expanded: str, features: List[str]) -> float:
        """Calcula confiança da expansão."""
        base_confidence = 0.6
        
        # Bonus por características técnicas encontradas
        if features:
            base_confidence += 0.2
        
        # Bonus por expansão significativa
        if len(expanded) > len(original) * 1.3:
            base_confidence += 0.1
        
        # Penalty por expansão excessiva
        if len(expanded) > len(original) * 3:
            base_confidence -= 0.1
        
        return min(1.0, max(0.0, base_confidence))
    
    def _find_pattern_matches(self, text: str, pattern_config: Dict[str, Any]) -> List[str]:
        """Encontra correspondências de padrão no texto."""
        matches = []
        for pattern in pattern_config["patterns"]:
            found = re.findall(pattern, text, re.IGNORECASE)
            if found:
                matches.extend([str(match) for match in found])
        return matches
    
    def _extract_dimensions(self, text: str) -> List[str]:
        """Extrai dimensões do texto."""
        patterns = self.technical_patterns["dimensions"]["patterns"]
        dimensions = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dimensions.extend([str(match) for match in matches])
        return dimensions
    
    def _extract_materials(self, text: str) -> List[str]:
        """Extrai materiais mencionados."""
        materials = []
        for material, synonyms in self.synonyms_db.items():
            if material in text or any(syn in text for syn in synonyms):
                materials.append(material)
        return materials
    
    def _extract_colors(self, text: str) -> List[str]:
        """Extrai cores mencionadas."""
        colors = ["azul", "vermelho", "verde", "amarelo", "preto", "branco", "cinza", "rosa"]
        found_colors = [color for color in colors if color in text]
        return found_colors
    
    def _extract_specifications(self, text: str) -> Dict[str, str]:
        """Extrai especificações diversas."""
        specs = {}
        
        # Buscar padrões de especificação
        for spec_type, pattern_config in self.technical_patterns.items():
            matches = self._find_pattern_matches(text, pattern_config)
            if matches:
                specs[spec_type] = matches[0]  # Primeira ocorrência
        
        return specs
    
    def _extract_brand_indicators(self, text: str) -> List[str]:
        """Extrai indicadores de marca."""
        # Padrões simples para marcas
        brand_patterns = [
            r"marca\s+(\w+)",
            r"fabricante\s+(\w+)",
            r"®",
            r"™"
        ]
        
        indicators = []
        for pattern in brand_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            indicators.extend(matches)
        
        return indicators
    
    def _calculate_feature_confidence(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Calcula confiança das características extraídas."""
        confidence_scores = {}
        
        for feature_type, feature_data in features.items():
            if isinstance(feature_data, list) and feature_data:
                confidence_scores[feature_type] = 0.8  # Base confidence
            elif isinstance(feature_data, dict) and feature_data:
                confidence_scores[feature_type] = 0.7
            else:
                confidence_scores[feature_type] = 0.5
        
        return confidence_scores
    
    def _generate_classification_hints(self, data: Dict[str, Any]) -> List[str]:
        """Gera dicas para classificação."""
        hints = []
        
        description = data.get("description", "").lower()
        
        # Dicas baseadas em palavras-chave
        if any(word in description for word in ["eletrônico", "digital", "computador"]):
            hints.append("Provável categoria: Eletrônicos")
        
        if any(word in description for word in ["medicamento", "remédio", "farmacêutico"]):
            hints.append("Provável categoria: Medicamentos")
        
        if any(word in description for word in ["alimento", "comida", "bebida"]):
            hints.append("Provável categoria: Alimentos")
        
        return hints
    
    def _suggest_data_improvements(self, data: Dict[str, Any]) -> List[str]:
        """Sugere melhorias nos dados."""
        suggestions = []
        
        description = data.get("description", "")
        
        if len(description) < self.config["min_description_length"]:
            suggestions.append("Descrição muito curta - considere adicionar mais detalhes")
        
        if not any(char.isdigit() for char in description):
            suggestions.append("Considere adicionar especificações numéricas (dimensões, peso, etc.)")
        
        if not data.get("category"):
            suggestions.append("Categoria não informada - importante para classificação precisa")
        
        return suggestions
    
    def _calculate_data_quality_score(self, data: Dict[str, Any]) -> float:
        """Calcula score de qualidade dos dados."""
        score = 0.0
        
        # Descrição presente e adequada
        description = data.get("description", "")
        if description:
            score += 0.3
            if len(description) >= self.config["min_description_length"]:
                score += 0.2
        
        # Categoria presente
        if data.get("category"):
            score += 0.2
        
        # Código/ID presente
        if data.get("code") or data.get("id"):
            score += 0.1
        
        # Especificações técnicas presentes
        if any(char.isdigit() for char in description):
            score += 0.2
        
        return min(1.0, score)
    
    def _get_normalization_changes(self, original: str, normalized: str) -> List[str]:
        """Identifica mudanças feitas na normalização."""
        changes = []
        
        if original != normalized:
            if original.upper() != normalized.upper():
                changes.append("Convertido para minúsculas")
            
            if len(original.split()) != len(normalized.split()):
                changes.append("Espaços normalizados")
            
            if re.search(r'[^\w\s\-\(\)\.,]', original):
                changes.append("Caracteres especiais removidos")
        
        return changes
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrai palavras-chave do texto."""
        words = text.lower().split()
        
        # Filtrar stopwords simples
        stopwords = ["de", "da", "do", "para", "com", "em", "por", "a", "o", "e", "que"]
        keywords = [word for word in words if word not in stopwords and len(word) > 2]
        
        return list(set(keywords))[:10]  # Máximo 10 keywords
    
    def _find_synonyms(self, keyword: str, context: str = "") -> List[str]:
        """Encontra sinônimos para uma palavra-chave."""
        synonyms = []
        
        # Buscar na base de sinônimos
        for base_word, synonym_list in self.synonyms_db.items():
            if keyword == base_word or keyword in synonym_list:
                synonyms.extend(synonym_list)
                break
        
        return list(set(synonyms))[:3]  # Máximo 3 sinônimos
    
    def _calculate_spec_confidence(self, matches: List[str]) -> float:
        """Calcula confiança de especificações extraídas."""
        if not matches:
            return 0.0
        
        # Mais matches = maior confiança
        base_confidence = 0.6
        if len(matches) > 1:
            base_confidence += 0.2
        
        return min(1.0, base_confidence)
