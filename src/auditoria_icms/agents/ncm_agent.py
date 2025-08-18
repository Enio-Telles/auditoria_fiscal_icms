"""
Agente Classificador NCM - NCM Agent
Responsável pela classificação de produtos na Nomenclatura Comum do Mercosul (NCM).
"""

import time
import re
from typing import Dict, Any, List, Optional, Tuple

from .base_agent import BaseAgent


class NCMAgent(BaseAgent):
    """
    Agente especializado na classificação de produtos conforme a tabela NCM.
    Utiliza busca hierárquica e análise semântica para determinar o código correto.
    """
    
    def __init__(self, llm, config: Dict[str, Any], logger=None):
        super().__init__("NCMAgent", llm, config, logger)
        self.hierarchy_levels = config.get('hierarchy_levels', [
            'capitulo', 'posicao', 'subposicao', 'item'
        ])
        self.retrieval_tools = None  # Será injetado pelo sistema
        
    def set_retrieval_tools(self, retrieval_tools):
        """Injeta as ferramentas de busca na base de conhecimento."""
        self.retrieval_tools = retrieval_tools
        
    async def process(
        self, 
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classifica um produto na tabela NCM usando estratégias hierárquicas.
        
        Args:
            input_data: Dados do produto (descrição, GTIN, NCM atual se disponível)
            context: Contexto adicional
            
        Returns:
            Classificação NCM com justificativa e confiança
        """
        start_time = time.time()
        
        if not self.validate_input(input_data):
            raise ValueError("Dados de entrada inválidos para NCMAgent")
        
        descricao = input_data.get('descricao_enriquecida') or input_data['descricao_produto']
        ncm_atual = input_data.get('ncm_atual')
        gtin = input_data.get('gtin')
        
        sources_used = []
        
        # Estratégia 1: Busca por GTIN em exemplos conhecidos
        gtin_result = None
        if gtin:
            gtin_result = await self._search_by_gtin(gtin)
            if gtin_result and gtin_result.get('ncm'):
                sources_used.append("gtin_examples")
        
        # Estratégia 2: Confirmação de NCM existente
        confirmation_result = None
        if ncm_atual:
            confirmation_result = await self._confirm_existing_ncm(descricao, ncm_atual)
            sources_used.append("ncm_confirmation")
        
        # Estratégia 3: Classificação hierárquica completa
        hierarchical_result = await self._hierarchical_classification(descricao)
        sources_used.extend(hierarchical_result.get('sources', []))
        
        # Estratégia 4: Busca semântica em descrições similares
        semantic_result = await self._semantic_search(descricao)
        sources_used.extend(semantic_result.get('sources', []))
        
        # Consolidar resultados
        final_classification = await self._consolidate_ncm_results(
            gtin_result, confirmation_result, hierarchical_result, semantic_result
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        result = {
            "ncm_classificado": final_classification['ncm'],
            "justificativa": final_classification['justificativa'],
            "confidence_score": final_classification['confidence'],
            "hierarchy_level": final_classification['level'],
            "alternative_ncms": final_classification.get('alternatives', []),
            "sources": list(set(sources_used)),
            "strategy_results": {
                "gtin": gtin_result,
                "confirmation": confirmation_result,
                "hierarchical": hierarchical_result,
                "semantic": semantic_result
            },
            "success": True
        }
        
        # Criar registro de decisão
        self.create_decision_record(
            input_data=input_data,
            output_data=result,
            reasoning=final_classification['justificativa'],
            confidence_score=final_classification['confidence'],
            sources_used=result['sources'],
            processing_time_ms=processing_time
        )
        
        return result
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Valida se há descrição suficiente para classificação."""
        descricao = input_data.get('descricao_produto') or input_data.get('descricao_enriquecida')
        return descricao and isinstance(descricao, str) and len(descricao.strip()) >= 3
    
    async def _search_by_gtin(self, gtin: str) -> Optional[Dict[str, Any]]:
        """Busca NCM por GTIN em exemplos conhecidos."""
        if not self.retrieval_tools:
            return None
        
        try:
            result = await self.retrieval_tools.search_by_gtin(gtin)
            if result:
                return {
                    "ncm": result.get('ncm'),
                    "confidence": 0.95,  # Alta confiança para match exato de GTIN
                    "source": "gtin_database",
                    "description_match": result.get('descricao')
                }
        except Exception as e:
            self.logger.error(f"Erro na busca por GTIN: {str(e)}")
        
        return None
    
    async def _confirm_existing_ncm(self, descricao: str, ncm_atual: str) -> Dict[str, Any]:
        """Confirma se o NCM atual é apropriado para a descrição."""
        if not self.retrieval_tools:
            return {"valid": False, "confidence": 0.0}
        
        try:
            # Buscar informações sobre o NCM atual
            ncm_info = await self.retrieval_tools.get_ncm_info(ncm_atual)
            if not ncm_info:
                return {"valid": False, "confidence": 0.0, "reason": "NCM não encontrado"}
            
            # Analisar compatibilidade entre descrição e NCM
            compatibility = await self._analyze_description_ncm_compatibility(
                descricao, ncm_atual, ncm_info
            )
            
            return {
                "valid": compatibility['compatible'],
                "confidence": compatibility['confidence'],
                "ncm_description": ncm_info.get('descricao'),
                "analysis": compatibility['analysis'],
                "reason": compatibility.get('reason', '')
            }
            
        except Exception as e:
            self.logger.error(f"Erro na confirmação de NCM: {str(e)}")
            return {"valid": False, "confidence": 0.0, "reason": f"Erro: {str(e)}"}
    
    async def _hierarchical_classification(self, descricao: str) -> Dict[str, Any]:
        """Realiza classificação hierárquica do capítulo ao item."""
        if not self.retrieval_tools:
            return {"ncm": None, "confidence": 0.0}
        
        try:
            # Etapa 1: Identificar capítulo (2 dígitos)
            capitulo_result = await self._classify_chapter(descricao)
            if not capitulo_result or capitulo_result['confidence'] < 0.6:
                return {"ncm": None, "confidence": 0.0, "step": "capitulo_failed"}
            
            # Etapa 2: Identificar posição (4 dígitos)
            posicao_result = await self._classify_position(
                descricao, capitulo_result['capitulo']
            )
            if not posicao_result or posicao_result['confidence'] < 0.6:
                return {
                    "ncm": capitulo_result['capitulo'] + "0000",
                    "confidence": capitulo_result['confidence'] * 0.7,
                    "level": "capitulo"
                }
            
            # Etapa 3: Identificar subposição (6 dígitos)
            subposicao_result = await self._classify_subposition(
                descricao, posicao_result['posicao']
            )
            if not subposicao_result or subposicao_result['confidence'] < 0.6:
                return {
                    "ncm": posicao_result['posicao'] + "00",
                    "confidence": posicao_result['confidence'] * 0.8,
                    "level": "posicao"
                }
            
            # Etapa 4: Identificar item específico (8 dígitos)
            item_result = await self._classify_item(
                descricao, subposicao_result['subposicao']
            )
            if item_result and item_result['confidence'] >= 0.6:
                return {
                    "ncm": item_result['ncm'],
                    "confidence": item_result['confidence'],
                    "level": "item",
                    "sources": ["hierarchical_classification"]
                }
            
            # Fallback para subposição
            return {
                "ncm": subposicao_result['subposicao'] + "00",
                "confidence": subposicao_result['confidence'] * 0.9,
                "level": "subposicao",
                "sources": ["hierarchical_classification"]
            }
            
        except Exception as e:
            self.logger.error(f"Erro na classificação hierárquica: {str(e)}")
            return {"ncm": None, "confidence": 0.0, "error": str(e)}
    
    async def _classify_chapter(self, descricao: str) -> Optional[Dict[str, Any]]:
        """Classifica o produto em um capítulo NCM (2 dígitos)."""
        if not self.retrieval_tools:
            return None
        
        # Buscar capítulos compatíveis usando busca semântica
        chapters = await self.retrieval_tools.search_chapters(descricao)
        
        if not chapters:
            return None
        
        # Usar o capítulo com maior score semântico
        best_chapter = max(chapters, key=lambda x: x.get('score', 0))
        
        return {
            "capitulo": best_chapter['codigo'][:2],
            "confidence": best_chapter.get('score', 0.5),
            "description": best_chapter.get('descricao')
        }
    
    async def _classify_position(self, descricao: str, capitulo: str) -> Optional[Dict[str, Any]]:
        """Classifica em uma posição específica dentro do capítulo."""
        if not self.retrieval_tools:
            return None
        
        positions = await self.retrieval_tools.search_positions(descricao, capitulo)
        
        if not positions:
            return None
        
        best_position = max(positions, key=lambda x: x.get('score', 0))
        
        return {
            "posicao": best_position['codigo'][:4],
            "confidence": best_position.get('score', 0.5),
            "description": best_position.get('descricao')
        }
    
    async def _classify_subposition(self, descricao: str, posicao: str) -> Optional[Dict[str, Any]]:
        """Classifica em uma subposição específica."""
        if not self.retrieval_tools:
            return None
        
        subpositions = await self.retrieval_tools.search_subpositions(descricao, posicao)
        
        if not subpositions:
            return None
        
        best_subposition = max(subpositions, key=lambda x: x.get('score', 0))
        
        return {
            "subposicao": best_subposition['codigo'][:6],
            "confidence": best_subposition.get('score', 0.5),
            "description": best_subposition.get('descricao')
        }
    
    async def _classify_item(self, descricao: str, subposicao: str) -> Optional[Dict[str, Any]]:
        """Classifica no item específico final (8 dígitos)."""
        if not self.retrieval_tools:
            return None
        
        items = await self.retrieval_tools.search_items(descricao, subposicao)
        
        if not items:
            return None
        
        best_item = max(items, key=lambda x: x.get('score', 0))
        
        return {
            "ncm": best_item['codigo'],
            "confidence": best_item.get('score', 0.5),
            "description": best_item.get('descricao')
        }
    
    async def _semantic_search(self, descricao: str) -> Dict[str, Any]:
        """Busca semântica por produtos similares já classificados."""
        if not self.retrieval_tools:
            return {"results": [], "confidence": 0.0}
        
        try:
            similar_products = await self.retrieval_tools.semantic_search_products(
                descricao, top_k=5
            )
            
            if not similar_products:
                return {"results": [], "confidence": 0.0}
            
            # Analisar distribuição de NCMs nos resultados similares
            ncm_counts = {}
            total_score = 0
            
            for product in similar_products:
                ncm = product.get('ncm')
                score = product.get('score', 0)
                
                if ncm:
                    ncm_counts[ncm] = ncm_counts.get(ncm, 0) + score
                    total_score += score
            
            if not ncm_counts:
                return {"results": [], "confidence": 0.0}
            
            # NCM mais provável
            most_likely_ncm = max(ncm_counts.items(), key=lambda x: x[1])
            confidence = most_likely_ncm[1] / total_score if total_score > 0 else 0
            
            return {
                "results": similar_products,
                "suggested_ncm": most_likely_ncm[0],
                "confidence": confidence,
                "sources": ["semantic_search"]
            }
            
        except Exception as e:
            self.logger.error(f"Erro na busca semântica: {str(e)}")
            return {"results": [], "confidence": 0.0, "error": str(e)}
    
    async def _analyze_description_ncm_compatibility(
        self, 
        descricao: str, 
        ncm: str, 
        ncm_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analisa a compatibilidade entre descrição do produto e NCM."""
        
        # Extrair palavras-chave da descrição
        descricao_keywords = self._extract_keywords(descricao.lower())
        ncm_desc_keywords = self._extract_keywords(ncm_info.get('descricao', '').lower())
        
        # Calcular sobreposição de palavras-chave
        common_keywords = set(descricao_keywords) & set(ncm_desc_keywords)
        keyword_overlap = len(common_keywords) / max(len(descricao_keywords), 1)
        
        # Verificar exclusões explícitas nas notas do NCM
        exclusions = ncm_info.get('exclusions', [])
        has_exclusions = any(
            exclusion.lower() in descricao.lower() 
            for exclusion in exclusions
        )
        
        # Calcular compatibilidade
        compatibility_score = keyword_overlap
        
        if has_exclusions:
            compatibility_score *= 0.3  # Penalizar fortemente se há exclusões
        
        compatible = compatibility_score >= 0.5 and not has_exclusions
        
        return {
            "compatible": compatible,
            "confidence": compatibility_score,
            "keyword_overlap": keyword_overlap,
            "common_keywords": list(common_keywords),
            "has_exclusions": has_exclusions,
            "analysis": f"Sobreposição de keywords: {keyword_overlap:.2%}, Exclusões: {has_exclusions}"
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrai palavras-chave relevantes de um texto."""
        # Remover palavras comuns (stopwords)
        stopwords = {
            'de', 'da', 'do', 'das', 'dos', 'em', 'na', 'no', 'nas', 'nos',
            'para', 'por', 'com', 'sem', 'sob', 'sobre', 'entre', 'contra',
            'e', 'ou', 'mas', 'que', 'se', 'o', 'a', 'os', 'as', 'um', 'uma',
            'uns', 'umas', 'este', 'esta', 'estes', 'estas', 'esse', 'essa',
            'esses', 'essas', 'aquele', 'aquela', 'aqueles', 'aquelas'
        }
        
        # Extrair palavras alfabéticas com mais de 2 caracteres
        words = re.findall(r'\b[a-záàâãéèêíìîóòôõúùûç]{3,}\b', text.lower())
        
        # Filtrar stopwords
        keywords = [word for word in words if word not in stopwords]
        
        return keywords
    
    async def _consolidate_ncm_results(
        self, 
        gtin_result: Optional[Dict[str, Any]],
        confirmation_result: Optional[Dict[str, Any]],
        hierarchical_result: Dict[str, Any],
        semantic_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Consolida todos os resultados para uma classificação final."""
        
        candidates = []
        
        # Resultado por GTIN (prioridade máxima)
        if gtin_result and gtin_result.get('ncm'):
            candidates.append({
                "ncm": gtin_result['ncm'],
                "confidence": gtin_result['confidence'],
                "source": "gtin_match",
                "justificativa": f"NCM encontrado via GTIN {gtin_result.get('source', '')}"
            })
        
        # Confirmação de NCM existente
        if confirmation_result and confirmation_result.get('valid'):
            candidates.append({
                "ncm": confirmation_result.get('ncm'),
                "confidence": confirmation_result['confidence'],
                "source": "confirmation",
                "justificativa": f"NCM atual confirmado: {confirmation_result.get('reason', '')}"
            })
        
        # Resultado hierárquico
        if hierarchical_result.get('ncm'):
            candidates.append({
                "ncm": hierarchical_result['ncm'],
                "confidence": hierarchical_result['confidence'],
                "source": "hierarchical",
                "justificativa": f"Classificação hierárquica - nível: {hierarchical_result.get('level', 'completo')}"
            })
        
        # Resultado semântico
        if semantic_result.get('suggested_ncm'):
            candidates.append({
                "ncm": semantic_result['suggested_ncm'],
                "confidence": semantic_result['confidence'],
                "source": "semantic",
                "justificativa": f"Baseado em similaridade semântica com produtos conhecidos"
            })
        
        if not candidates:
            return {
                "ncm": None,
                "confidence": 0.0,
                "level": "none",
                "justificativa": "Nenhuma classificação NCM pôde ser determinada"
            }
        
        # Selecionar melhor candidato por confiança
        best_candidate = max(candidates, key=lambda x: x['confidence'])
        
        # Listar alternativas
        alternatives = [
            {"ncm": c["ncm"], "confidence": c["confidence"], "source": c["source"]}
            for c in candidates if c != best_candidate
        ]
        
        return {
            "ncm": best_candidate["ncm"],
            "confidence": best_candidate["confidence"],
            "level": hierarchical_result.get('level', 'determined'),
            "justificativa": best_candidate["justificativa"],
            "alternatives": alternatives
        }
