"""
Agente Classificador CEST - CEST Agent
Responsável pela classificação de produtos no Código Especificador da Substituição Tributária.
"""

import time
import re
from typing import Dict, Any, List, Optional, Tuple

from .base_agent import BaseAgent


class CESTAgent(BaseAgent):
    """
    Agente especializado na classificação CEST baseada em regras NCM e padrões.
    Implementa busca por padrões e correspondência exata de códigos.
    """
    
    def __init__(self, llm, config: Dict[str, Any], logger=None):
        super().__init__("CESTAgent", llm, config, logger)
        self.pattern_matching = config.get('pattern_matching', True)
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
        Classifica um produto no CEST baseado no NCM e características do produto.
        
        Args:
            input_data: Dados do produto incluindo NCM classificado
            context: Contexto adicional (empresa, estado)
            
        Returns:
            Classificação CEST com justificativa e confiança
        """
        start_time = time.time()
        
        if not self.validate_input(input_data):
            raise ValueError("Dados de entrada inválidos para CESTAgent")
        
        descricao = input_data.get('descricao_enriquecida') or input_data['descricao_produto']
        ncm_classificado = input_data.get('ncm_final') or input_data.get('ncm_classificado')
        cest_atual = input_data.get('cest_atual')
        estado = context.get('estado', 'RO') if context else 'RO'
        
        sources_used = []
        
        # Estratégia 1: Confirmação de CEST existente
        confirmation_result = None
        if cest_atual:
            confirmation_result = await self._confirm_existing_cest(
                descricao, ncm_classificado, cest_atual, estado
            )
            if confirmation_result:
                sources_used.append("cest_confirmation")
        
        # Estratégia 2: Busca por NCM exato
        exact_match_result = await self._search_by_exact_ncm(ncm_classificado, estado)
        if exact_match_result:
            sources_used.append("exact_ncm_match")
        
        # Estratégia 3: Busca por padrões NCM (wildcards)
        pattern_result = await self._search_by_ncm_pattern(ncm_classificado, estado)
        if pattern_result:
            sources_used.append("ncm_pattern_match")
        
        # Estratégia 4: Busca semântica por descrição
        semantic_result = await self._semantic_search_cest(descricao, estado)
        if semantic_result:
            sources_used.append("semantic_search")
        
        # Estratégia 5: Análise de substituição tributária aplicável
        st_analysis = await self._analyze_substituicao_tributaria(
            descricao, ncm_classificado, estado
        )
        sources_used.append("st_analysis")
        
        # Consolidar resultados
        final_classification = await self._consolidate_cest_results(
            confirmation_result,
            exact_match_result,
            pattern_result,
            semantic_result,
            st_analysis
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        result = {
            "cest_classificado": final_classification['cest'],
            "justificativa": final_classification['justificativa'],
            "confidence_score": final_classification['confidence'],
            "segmento": final_classification.get('segmento'),
            "substituicao_tributaria": final_classification.get('st_aplicavel', False),
            "alternative_cests": final_classification.get('alternatives', []),
            "sources": list(set(sources_used)),
            "strategy_results": {
                "confirmation": confirmation_result,
                "exact_match": exact_match_result,
                "pattern_match": pattern_result,
                "semantic": semantic_result,
                "st_analysis": st_analysis
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
        """Valida se há informações suficientes para classificação CEST."""
        # Precisa de pelo menos descrição e NCM
        descricao = input_data.get('descricao_produto') or input_data.get('descricao_enriquecida')
        ncm = input_data.get('ncm_final') or input_data.get('ncm_classificado')
        
        return (
            descricao and isinstance(descricao, str) and len(descricao.strip()) >= 3 and
            ncm and isinstance(ncm, str) and len(ncm) >= 6
        )
    
    async def _confirm_existing_cest(
        self, 
        descricao: str, 
        ncm: str, 
        cest_atual: str,
        estado: str
    ) -> Optional[Dict[str, Any]]:
        """Confirma se o CEST atual é apropriado para o produto."""
        if not self.retrieval_tools:
            return None
        
        try:
            # Buscar informações sobre o CEST atual
            cest_info = await self.retrieval_tools.get_cest_info(cest_atual, estado)
            if not cest_info:
                return {"valid": False, "confidence": 0.0, "reason": "CEST não encontrado"}
            
            # Verificar se o NCM está nas regras do CEST
            ncm_matches = await self._check_ncm_in_cest_rules(ncm, cest_atual, estado)
            
            if ncm_matches['matches']:
                return {
                    "valid": True,
                    "confidence": 0.9,
                    "cest": cest_atual,
                    "reason": f"NCM {ncm} está nas regras do CEST {cest_atual}",
                    "pattern_matched": ncm_matches['pattern']
                }
            else:
                return {
                    "valid": False,
                    "confidence": 0.1,
                    "reason": f"NCM {ncm} não está nas regras do CEST {cest_atual}"
                }
                
        except Exception as e:
            self.logger.error(f"Erro na confirmação de CEST: {str(e)}")
            return {"valid": False, "confidence": 0.0, "reason": f"Erro: {str(e)}"}
    
    async def _search_by_exact_ncm(self, ncm: str, estado: str) -> Optional[Dict[str, Any]]:
        """Busca CEST por correspondência exata de NCM."""
        if not self.retrieval_tools:
            return None
        
        try:
            exact_matches = await self.retrieval_tools.search_cest_by_ncm(ncm, estado)
            
            if exact_matches:
                # Se há múltiplos CESTs para o mesmo NCM, usar o primeiro (mais específico)
                best_match = exact_matches[0]
                
                return {
                    "cest": best_match['cest'],
                    "confidence": 0.95,
                    "segmento": best_match.get('segmento'),
                    "description": best_match.get('descricao'),
                    "matches": exact_matches
                }
                
        except Exception as e:
            self.logger.error(f"Erro na busca exata por NCM: {str(e)}")
        
        return None
    
    async def _search_by_ncm_pattern(self, ncm: str, estado: str) -> Optional[Dict[str, Any]]:
        """Busca CEST usando padrões NCM (wildcards e hierarquia)."""
        if not self.retrieval_tools:
            return None
        
        try:
            # Buscar padrões de diferentes níveis de especificidade
            pattern_matches = []
            
            # Testar padrões hierárquicos: 8, 6, 4, 2 dígitos
            for length in [8, 6, 4, 2]:
                pattern = ncm[:length]
                matches = await self.retrieval_tools.search_cest_by_pattern(pattern, estado)
                
                for match in matches:
                    match['pattern_length'] = length
                    match['specificity'] = length / 8.0  # Peso por especificidade
                    pattern_matches.append(match)
            
            if not pattern_matches:
                return None
            
            # Ordenar por especificidade (padrões mais específicos primeiro)
            pattern_matches.sort(key=lambda x: x['specificity'], reverse=True)
            
            best_match = pattern_matches[0]
            confidence = best_match['specificity'] * 0.8  # Base 80% para padrões
            
            return {
                "cest": best_match['cest'],
                "confidence": confidence,
                "pattern_matched": best_match['ncm_pattern'],
                "pattern_length": best_match['pattern_length'],
                "segmento": best_match.get('segmento'),
                "all_matches": pattern_matches[:3]  # Top 3 matches
            }
            
        except Exception as e:
            self.logger.error(f"Erro na busca por padrão: {str(e)}")
        
        return None
    
    async def _semantic_search_cest(self, descricao: str, estado: str) -> Optional[Dict[str, Any]]:
        """Busca CEST por similaridade semântica da descrição."""
        if not self.retrieval_tools:
            return None
        
        try:
            similar_cests = await self.retrieval_tools.semantic_search_cest(
                descricao, estado, top_k=5
            )
            
            if not similar_cests:
                return None
            
            # Analisar distribuição de CESTs nos resultados
            cest_scores = {}
            for result in similar_cests:
                cest = result.get('cest')
                score = result.get('score', 0)
                
                if cest:
                    cest_scores[cest] = cest_scores.get(cest, 0) + score
            
            if not cest_scores:
                return None
            
            # CEST mais provável
            best_cest = max(cest_scores.items(), key=lambda x: x[1])
            max_score = max(result.get('score', 0) for result in similar_cests)
            
            return {
                "cest": best_cest[0],
                "confidence": min(max_score, 0.8),  # Máximo 80% para busca semântica
                "similar_results": similar_cests,
                "score_distribution": cest_scores
            }
            
        except Exception as e:
            self.logger.error(f"Erro na busca semântica CEST: {str(e)}")
        
        return None
    
    async def _analyze_substituicao_tributaria(
        self, 
        descricao: str, 
        ncm: str, 
        estado: str
    ) -> Dict[str, Any]:
        """Analisa se o produto está sujeito à substituição tributária."""
        
        # Categorias de produtos comumente sujeitas à ST
        st_categories = {
            "medicamentos": {
                "keywords": ["medicamento", "remédio", "farmácia", "droga", "antibiótico"],
                "ncm_patterns": ["30"],
                "likelihood": 0.9
            },
            "bebidas": {
                "keywords": ["cerveja", "refrigerante", "água", "bebida", "suco"],
                "ncm_patterns": ["22"],
                "likelihood": 0.85
            },
            "combustiveis": {
                "keywords": ["gasolina", "óleo", "combustível", "diesel"],
                "ncm_patterns": ["27"],
                "likelihood": 0.95
            },
            "cosmeticos": {
                "keywords": ["perfume", "cosmético", "shampoo", "sabonete"],
                "ncm_patterns": ["33"],
                "likelihood": 0.8
            },
            "autopeças": {
                "keywords": ["peça", "automóvel", "carro", "motor", "pneu"],
                "ncm_patterns": ["40", "87"],
                "likelihood": 0.75
            },
            "eletronicos": {
                "keywords": ["eletrônico", "telefone", "computador", "TV"],
                "ncm_patterns": ["85"],
                "likelihood": 0.7
            }
        }
        
        st_applicable = False
        category_matched = None
        likelihood = 0.0
        
        descricao_lower = descricao.lower()
        
        for category, info in st_categories.items():
            # Verificar palavras-chave
            keyword_match = any(
                keyword in descricao_lower for keyword in info["keywords"]
            )
            
            # Verificar padrões NCM
            ncm_match = any(
                ncm.startswith(pattern) for pattern in info["ncm_patterns"]
            )
            
            if keyword_match or ncm_match:
                st_applicable = True
                category_matched = category
                likelihood = info["likelihood"]
                
                # Ajustar likelihood se ambos matches
                if keyword_match and ncm_match:
                    likelihood = min(likelihood * 1.2, 0.95)
                
                break
        
        return {
            "st_aplicavel": st_applicable,
            "categoria": category_matched,
            "likelihood": likelihood,
            "reasoning": f"Categoria: {category_matched}" if category_matched else "Não identificado como sujeito à ST"
        }
    
    async def _check_ncm_in_cest_rules(
        self, 
        ncm: str, 
        cest: str, 
        estado: str
    ) -> Dict[str, Any]:
        """Verifica se um NCM está nas regras de um CEST específico."""
        if not self.retrieval_tools:
            return {"matches": False}
        
        try:
            cest_rules = await self.retrieval_tools.get_cest_ncm_rules(cest, estado)
            
            for rule in cest_rules:
                pattern = rule.get('ncm_pattern', '')
                
                # Verificar correspondência exata
                if pattern == ncm:
                    return {"matches": True, "pattern": pattern, "type": "exact"}
                
                # Verificar correspondência por padrão
                if self._ncm_matches_pattern(ncm, pattern):
                    return {"matches": True, "pattern": pattern, "type": "pattern"}
            
            return {"matches": False}
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar regras NCM-CEST: {str(e)}")
            return {"matches": False, "error": str(e)}
    
    def _ncm_matches_pattern(self, ncm: str, pattern: str) -> bool:
        """Verifica se um NCM corresponde a um padrão CEST."""
        if not pattern or not ncm:
            return False
        
        # Padrão simples: se o NCM começa com o padrão
        if ncm.startswith(pattern):
            return True
        
        # Padrões com wildcards (implementação futura)
        # Ex: "8471.*" corresponderia a qualquer NCM que comece com 8471
        
        return False
    
    async def _consolidate_cest_results(
        self,
        confirmation_result: Optional[Dict[str, Any]],
        exact_match_result: Optional[Dict[str, Any]],
        pattern_result: Optional[Dict[str, Any]],
        semantic_result: Optional[Dict[str, Any]],
        st_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Consolida todos os resultados para uma classificação CEST final."""
        
        candidates = []
        
        # Confirmação (prioridade máxima se válida)
        if confirmation_result and confirmation_result.get('valid'):
            candidates.append({
                "cest": confirmation_result['cest'],
                "confidence": confirmation_result['confidence'],
                "source": "confirmation",
                "justificativa": confirmation_result['reason']
            })
        
        # Match exato de NCM (alta prioridade)
        if exact_match_result:
            candidates.append({
                "cest": exact_match_result['cest'],
                "confidence": exact_match_result['confidence'],
                "source": "exact_ncm",
                "justificativa": f"NCM corresponde exatamente às regras do CEST {exact_match_result['cest']}",
                "segmento": exact_match_result.get('segmento')
            })
        
        # Match por padrão
        if pattern_result:
            candidates.append({
                "cest": pattern_result['cest'],
                "confidence": pattern_result['confidence'],
                "source": "pattern_match",
                "justificativa": f"NCM corresponde ao padrão {pattern_result['pattern_matched']} do CEST {pattern_result['cest']}",
                "segmento": pattern_result.get('segmento')
            })
        
        # Busca semântica
        if semantic_result:
            candidates.append({
                "cest": semantic_result['cest'],
                "confidence": semantic_result['confidence'],
                "source": "semantic",
                "justificativa": f"Baseado em similaridade semântica com produtos conhecidos",
                "segmento": None
            })
        
        # Se não há candidatos válidos
        if not candidates:
            # Verificar se produto está sujeito à ST mas não tem CEST específico
            if st_analysis.get('st_aplicavel'):
                return {
                    "cest": None,
                    "confidence": 0.0,
                    "justificativa": f"Produto pode estar sujeito à substituição tributária (categoria: {st_analysis.get('categoria')}), mas não foi encontrado CEST específico",
                    "st_aplicavel": True,
                    "categoria": st_analysis.get('categoria')
                }
            else:
                return {
                    "cest": None,
                    "confidence": 0.0,
                    "justificativa": "Produto não está sujeito à substituição tributária - CEST não aplicável",
                    "st_aplicavel": False
                }
        
        # Selecionar melhor candidato
        best_candidate = max(candidates, key=lambda x: x['confidence'])
        
        # Ajustar confiança baseada na análise de ST
        if st_analysis.get('st_aplicavel') and st_analysis.get('likelihood', 0) > 0.7:
            best_candidate['confidence'] = min(best_candidate['confidence'] * 1.1, 0.95)
        
        # Preparar alternativas
        alternatives = [
            {
                "cest": c["cest"], 
                "confidence": c["confidence"], 
                "source": c["source"]
            }
            for c in candidates if c != best_candidate
        ]
        
        return {
            "cest": best_candidate["cest"],
            "confidence": best_candidate["confidence"],
            "justificativa": best_candidate["justificativa"],
            "segmento": best_candidate.get("segmento"),
            "st_aplicavel": st_analysis.get('st_aplicavel', False),
            "alternatives": alternatives
        }
