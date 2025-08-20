"""
Workflow de Determinação - LangGraph
Fluxo para determinar classificações NCM/CEST quando não existem ou são inadequadas
"""

from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from datetime import datetime

from .base_workflow import BaseWorkflow, WorkflowState, WorkflowConfig


class DeterminationFlow(BaseWorkflow):
    """
    Workflow para determinação de novas classificações NCM/CEST
    
    Fluxo:
    1. Enriquecimento de dados
    2. Determinação NCM
    3. Determinação CEST  
    4. Reconciliação final
    """
    
    def __init__(self, config: WorkflowConfig):
        # Chamar o constructor da classe base
        super().__init__(
            name="DeterminationFlow",
            config=config,
            agents={},  # Simplificado por enquanto
            logger=None
        )
        
    def _build_graph(self):
        """Constrói o grafo de determinação - implementação do método abstrato"""
        self.graph = self.build_graph()
    
    async def _initialize_state(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Inicializa o estado do workflow - implementação do método abstrato"""
        return {
            "produto_dados": input_data,
            "status": "INICIADO",
            "audit_trail": [],
            "error": None,
            "final_result": {},
            **input_data
        }
    
    def build_graph(self):
        """Constrói o grafo de determinação"""
        
        # Criação do StateGraph
        graph = StateGraph(dict)
        
        # Adição dos nós
        graph.add_node("enrichment", self._enrichment_node)
        graph.add_node("ncm_determination", self._ncm_determination_node)
        graph.add_node("ncm_refinement", self._ncm_refinement_node)
        graph.add_node("cest_determination", self._cest_determination_node)
        graph.add_node("reconciliation", self._reconciliation_node)
        graph.add_node("manual_review", self._manual_review_node)
        graph.add_node("completion", self._completion_node)
        
        # Definição das arestas - fluxo linear simplificado
        graph.set_entry_point("enrichment")
        
        graph.add_edge("enrichment", "ncm_determination")
        graph.add_edge("ncm_determination", "ncm_refinement")
        graph.add_edge("ncm_refinement", "cest_determination")
        graph.add_edge("cest_determination", "reconciliation")
        graph.add_edge("reconciliation", "completion")
        graph.add_edge("completion", END)
        
        graph.add_edge("manual_review", END)
        graph.add_edge("completion", END)
        
        return graph.compile()
    
    def _enrichment_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Nó de enriquecimento de dados"""
        try:
            self._log_step(state, "enrichment", "Iniciando enriquecimento profundo de dados")
            
            # Mock do enriquecimento mais robusto para determinação
            enriched_data = {
                "confidence": 0.85,
                "additional_info": "Mock deep enrichment data",
                "similar_products": [
                    {"produto_id": "123", "similarity": 0.9},
                    {"produto_id": "456", "similarity": 0.8}
                ],
                "regulatory_hints": [
                    {"tipo": "ncm", "hint": "Produto farmacêutico - NCM 30.xx"},
                    {"tipo": "cest", "hint": "Medicamento - CEST 28.xxx"}
                ]
            }
            
            # Atualizar estado
            state["produto_dados"].update(enriched_data)
            state["enrichment_confidence"] = enriched_data.get("confidence", 0.0)
            state["similar_products"] = enriched_data.get("similar_products", [])
            state["regulatory_hints"] = enriched_data.get("regulatory_hints", [])
            
            self._log_step(
                state, 
                "enrichment", 
                f"Enriquecimento concluído. Confiança: {state['enrichment_confidence']}, "
                f"Produtos similares: {len(state['similar_products'])}"
            )
            
            return state
            
        except Exception as e:
            return self._handle_error(state, "enrichment", str(e))
    
    def _ncm_determination_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Nó de determinação inicial do NCM"""
        try:
            self._log_step(state, "ncm_determination", "Iniciando determinação NCM")
            
            # Mock da determinação NCM com múltiplas estratégias
            determination_result = {
                "ncm_sugerido": "30049099",
                "confidence": 0.82,
                "justificativa": "NCM determinado baseado em análise de produto farmacêutico (mock)",
                "candidates": [
                    {"ncm": "30049099", "confidence": 0.82, "justificativa": "Outros medicamentos"},
                    {"ncm": "30049019", "confidence": 0.75, "justificativa": "Outros medicamentos em formas farmacêuticas"},
                    {"ncm": "30049090", "confidence": 0.70, "justificativa": "Medicamentos diversos"}
                ]
            }
            
            state["ncm_determination_result"] = determination_result
            state["ncm_candidates"] = determination_result.get("candidates", [])
            
            self._log_step(
                state, 
                "ncm_determination", 
                f"NCM determinado: {determination_result.get('ncm_sugerido')}, "
                f"Confiança: {determination_result.get('confidence', 0.0)}, "
                f"Candidatos: {len(state['ncm_candidates'])}"
            )
            
            return state
            
        except Exception as e:
            return self._handle_error(state, "ncm_determination", str(e))
    
    def _ncm_refinement_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Nó de refinamento da determinação NCM"""
        try:
            self._log_step(state, "ncm_refinement", "Refinando determinação NCM")
            
            # Refinamento com análise adicional
            refinement_result = self.ncm_agent.refine_ncm_determination(
                state["produto_dados"],
                state["ncm_determination_result"],
                state["ncm_candidates"],
                state.get("empresa_id")
            )
            
            # Atualizar com resultado refinado
            state["ncm_determination_result"].update(refinement_result)
            state["ncm_refinement_applied"] = True
            
            self._log_step(
                state, 
                "ncm_refinement", 
                f"Refinamento concluído. Nova confiança: {refinement_result.get('confidence', 0.0)}"
            )
            
            return state
            
        except Exception as e:
            return self._handle_error(state, "ncm_refinement", str(e))
    
    def _cest_determination_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Nó de determinação CEST"""
        try:
            self._log_step(state, "cest_determination", "Iniciando determinação CEST")
            
            ncm_result = state.get("ncm_determination_result", {})
            ncm_determinado = ncm_result.get("ncm_sugerido")
            
            if not ncm_determinado or ncm_result.get("confidence", 0.0) < 0.3:
                self._log_step(state, "cest_determination", "NCM insuficiente para determinação CEST")
                state["cest_determination_result"] = {
                    "cest_sugerido": None,
                    "confidence": 0.0,
                    "reason": "NCM insuficiente"
                }
                return state
            
            # Atualizar dados do produto com NCM determinado
            updated_product_data = state["produto_dados"].copy()
            updated_product_data["ncm_determinado"] = ncm_determinado
            
            # Determinar CEST baseado no NCM
            determination_result = self.cest_agent.determine_cest(
                updated_product_data,
                state.get("empresa_id"),
                ncm_context=ncm_result
            )
            
            state["cest_determination_result"] = determination_result
            
            self._log_step(
                state, 
                "cest_determination", 
                f"CEST determinado: {determination_result.get('cest_sugerido')}, "
                f"Confiança: {determination_result.get('confidence', 0.0)}"
            )
            
            return state
            
        except Exception as e:
            return self._handle_error(state, "cest_determination", str(e))
    
    def _reconciliation_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Nó de reconciliação final"""
        try:
            self._log_step(state, "reconciliation", "Iniciando reconciliação de determinações")
            
            # Coletar todos os resultados
            reconciliation_data = {
                "produto_dados": state["produto_dados"],
                "enrichment_confidence": state.get("enrichment_confidence", 0.0),
                "ncm_determination": state.get("ncm_determination_result", {}),
                "cest_determination": state.get("cest_determination_result", {}),
                "similar_products": state.get("similar_products", []),
                "regulatory_hints": state.get("regulatory_hints", []),
                "audit_trail": state.get("audit_trail", [])
            }
            
            # Executar reconciliação
            final_result = self.reconciliation_agent.reconcile_determination(
                reconciliation_data,
                state.get("empresa_id")
            )
            
            state["final_result"] = final_result
            state["final_confidence"] = final_result.get("confidence", 0.0)
            
            # Calcular score de qualidade da determinação
            quality_score = self._calculate_determination_quality(state)
            state["determination_quality"] = quality_score
            
            self._log_step(
                state, 
                "reconciliation", 
                f"Reconciliação concluída. Confiança final: {state['final_confidence']}, "
                f"Qualidade: {quality_score}"
            )
            
            return state
            
        except Exception as e:
            return self._handle_error(state, "reconciliation", str(e))
    
    def _manual_review_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Nó para marcar necessidade de revisão manual"""
        self._log_step(state, "manual_review", "Determinação marcada para revisão manual")
        
        state["status"] = "REVISAO_MANUAL"
        state["requires_human_review"] = True
        
        # Preparar contexto detalhado para revisão humana
        state["review_context"] = {
            "reason": self._get_review_reason(state),
            "determination_challenges": self._identify_determination_challenges(state),
            "suggested_research": self._suggest_research_areas(state),
            "alternative_classifications": self._get_alternative_classifications(state)
        }
        
        return state
    
    def _completion_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Nó de finalização do workflow"""
        self._log_step(state, "completion", "Workflow de determinação concluído")
        
        state["status"] = "DETERMINADO"
        state["workflow_completed"] = True
        state["completion_timestamp"] = self._get_timestamp()
        
        # Preparar dados para possível adição ao Golden Set
        if state.get("determination_quality", 0.0) > 0.8:
            state["golden_set_candidate"] = True
            state["golden_set_data"] = self._prepare_golden_set_data(state)
        
        return state
    
    def _after_ncm_determination(self, state: Dict[str, Any]) -> str:
        """Decide próximo passo após determinação NCM"""
        
        if state.get("error"):
            return "error"
        
        ncm_result = state.get("ncm_determination_result", {})
        confidence = ncm_result.get("confidence", 0.0)
        
        # Se confiança muito baixa, revisão manual
        if confidence < 0.3:
            return "manual_review"
        
        # Se confiança intermediária, tentar refinamento
        if confidence < self.config.confidence_threshold:
            return "refinement"
        
        return "continue"
    
    def _after_ncm_refinement(self, state: Dict[str, Any]) -> str:
        """Decide próximo passo após refinamento NCM"""
        
        if state.get("error"):
            return "error"
        
        ncm_result = state.get("ncm_determination_result", {})
        confidence = ncm_result.get("confidence", 0.0)
        
        if confidence < self.config.confidence_threshold:
            return "manual_review"
        
        return "continue"
    
    def _after_cest_determination(self, state: Dict[str, Any]) -> str:
        """Decide próximo passo após determinação CEST"""
        
        if state.get("error"):
            return "error"
        
        cest_result = state.get("cest_determination_result", {})
        confidence = cest_result.get("confidence", 0.0)
        
        # CEST é opcional em muitos casos, então limiar mais baixo
        if confidence < (self.config.confidence_threshold * 0.7):
            return "manual_review"
        
        return "reconciliation"
    
    def _after_reconciliation(self, state: Dict[str, Any]) -> str:
        """Decide próximo passo após reconciliação"""
        
        final_confidence = state.get("final_confidence", 0.0)
        determination_quality = state.get("determination_quality", 0.0)
        
        # Considera tanto confiança quanto qualidade
        if final_confidence < self.config.confidence_threshold or determination_quality < 0.6:
            return "manual_review"
        
        return "completion"
    
    def _calculate_determination_quality(self, state: Dict[str, Any]) -> float:
        """Calcula score de qualidade da determinação"""
        factors = []
        
        # Qualidade do enriquecimento
        enrichment_conf = state.get("enrichment_confidence", 0.0)
        factors.append(enrichment_conf * 0.2)
        
        # Qualidade da determinação NCM
        ncm_result = state.get("ncm_determination_result", {})
        ncm_conf = ncm_result.get("confidence", 0.0)
        factors.append(ncm_conf * 0.4)
        
        # Qualidade da determinação CEST
        cest_result = state.get("cest_determination_result", {})
        cest_conf = cest_result.get("confidence", 0.0)
        factors.append(cest_conf * 0.3)
        
        # Consistência dos resultados
        final_conf = state.get("final_confidence", 0.0)
        factors.append(final_conf * 0.1)
        
        return sum(factors)
    
    def _get_review_reason(self, state: Dict[str, Any]) -> str:
        """Identifica razão específica para revisão manual"""
        reasons = []
        
        enrichment_conf = state.get("enrichment_confidence", 0.0)
        if enrichment_conf < 0.5:
            reasons.append("Dados insuficientes para análise")
        
        ncm_result = state.get("ncm_determination_result", {})
        if ncm_result.get("confidence", 0.0) < self.config.confidence_threshold:
            reasons.append(f"Determinação NCM incerta ({ncm_result.get('confidence', 0.0):.2f})")
        
        cest_result = state.get("cest_determination_result", {})
        if cest_result.get("confidence", 0.0) < (self.config.confidence_threshold * 0.7):
            reasons.append(f"Determinação CEST incerta ({cest_result.get('confidence', 0.0):.2f})")
        
        quality = state.get("determination_quality", 0.0)
        if quality < 0.6:
            reasons.append(f"Qualidade geral baixa ({quality:.2f})")
        
        return "; ".join(reasons) if reasons else "Determinação requer validação"
    
    def _identify_determination_challenges(self, state: Dict[str, Any]) -> List[str]:
        """Identifica desafios específicos na determinação"""
        challenges = []
        
        if len(state.get("similar_products", [])) == 0:
            challenges.append("Ausência de produtos similares para comparação")
        
        if len(state.get("regulatory_hints", [])) == 0:
            challenges.append("Falta de contexto regulatório específico")
        
        ncm_candidates = state.get("ncm_candidates", [])
        if len(ncm_candidates) > 5:
            challenges.append("Múltiplas opções de NCM viáveis")
        elif len(ncm_candidates) == 0:
            challenges.append("Nenhuma opção de NCM identificada")
        
        product_data = state.get("produto_dados", {})
        if not product_data.get("descricao_detalhada"):
            challenges.append("Descrição do produto insuficiente")
        
        return challenges
    
    def _suggest_research_areas(self, state: Dict[str, Any]) -> List[str]:
        """Sugere áreas para pesquisa adicional"""
        suggestions = []
        
        ncm_result = state.get("ncm_determination_result", {})
        if ncm_result.get("confidence", 0.0) < 0.7:
            suggestions.append("Pesquisar especificações técnicas detalhadas do produto")
            suggestions.append("Consultar nomenclatura oficial NCM atualizada")
        
        cest_result = state.get("cest_determination_result", {})
        if cest_result.get("confidence", 0.0) < 0.5:
            suggestions.append("Verificar enquadramento no regime de substituição tributária")
            suggestions.append("Consultar convênios CEST específicos do estado")
        
        if state.get("enrichment_confidence", 0.0) < 0.5:
            suggestions.append("Buscar informações adicionais sobre fabricante/fornecedor")
            suggestions.append("Verificar classificações em bases de dados oficiais")
        
        return suggestions
    
    def _get_alternative_classifications(self, state: Dict[str, Any]) -> Dict[str, List]:
        """Obtém classificações alternativas para consideração"""
        alternatives = {
            "ncm_candidates": [],
            "cest_options": []
        }
        
        # Candidatos NCM
        ncm_candidates = state.get("ncm_candidates", [])
        alternatives["ncm_candidates"] = [
            {
                "ncm": candidate.get("ncm"),
                "confidence": candidate.get("confidence", 0.0),
                "justificativa": candidate.get("justificativa", "")
            }
            for candidate in ncm_candidates[:5]  # Top 5
        ]
        
        # Opções CEST (se disponíveis)
        cest_result = state.get("cest_determination_result", {})
        cest_options = cest_result.get("alternatives", [])
        alternatives["cest_options"] = [
            {
                "cest": option.get("cest"),
                "confidence": option.get("confidence", 0.0),
                "aplicabilidade": option.get("aplicabilidade", "")
            }
            for option in cest_options[:3]  # Top 3
        ]
        
        return alternatives
    
    def _prepare_golden_set_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara dados para possível adição ao Golden Set"""
        ncm_result = state.get("ncm_determination_result", {})
        cest_result = state.get("cest_determination_result", {})
        
        return {
            "produto_descricao": state["produto_dados"].get("descricao_original", ""),
            "ncm_correto": ncm_result.get("ncm_sugerido"),
            "cest_correto": cest_result.get("cest_sugerido"),
            "justificativa_ncm": ncm_result.get("justificativa", ""),
            "justificativa_cest": cest_result.get("justificativa", ""),
            "fonte_determinacao": "workflow_automatico",
            "confianca_geral": state.get("final_confidence", 0.0),
            "qualidade_determinacao": state.get("determination_quality", 0.0)
        }
    
    def _log_step(self, state: Dict[str, Any], step: str, message: str):
        """Log de etapa do workflow"""
        if "audit_trail" not in state:
            state["audit_trail"] = []
        
        state["audit_trail"].append({
            "step": step,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def _handle_error(self, state: Dict[str, Any], step: str, error_message: str) -> Dict[str, Any]:
        """Trata erros no workflow"""
        state["error"] = error_message
        state["status"] = "ERROR"
        self._log_step(state, step, f"Erro: {error_message}")
        return state
    
    def _get_timestamp(self) -> str:
        """Retorna timestamp atual"""
        return datetime.now().isoformat()
