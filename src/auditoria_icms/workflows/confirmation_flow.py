"""
Workflow de Confirmação - LangGraph
Fluxo para confirmar classificações NCM/CEST já existentes
"""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from datetime import datetime

from .base_workflow import BaseWorkflow, WorkflowConfig


class ConfirmationFlow(BaseWorkflow):
    """
    Workflow para confirmação de classificações NCM/CEST existentes

    Fluxo:
    1. Enriquecimento de dados
    2. Validação NCM
    3. Determinação/Validação CEST
    4. Reconciliação final
    """

    def __init__(self, config: WorkflowConfig):
        # Chamar o constructor da classe base
        super().__init__(
            name="ConfirmationFlow",
            config=config,
            agents={},  # Simplificado por enquanto
            logger=None,
        )

    def _build_graph(self):
        """Constrói o grafo de confirmação - implementação do método abstrato"""
        self.graph = self.build_graph()

    async def _initialize_state(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Inicializa o estado do workflow - implementação do método abstrato"""
        return {
            "produto_dados": input_data,
            "status": "INICIADO",
            "audit_trail": [],
            "error": None,
            "final_result": {},
            **input_data,
        }

    def build_graph(self):
        """Constrói o grafo de confirmação"""

        # Criação do StateGraph
        graph = StateGraph(dict)

        # Adição dos nós
        graph.add_node("enrichment", self._enrichment_node)
        graph.add_node("ncm_validation", self._ncm_validation_node)
        graph.add_node("cest_validation", self._cest_validation_node)
        graph.add_node("reconciliation", self._reconciliation_node)
        graph.add_node("completion", self._completion_node)

        # Fluxo linear simplificado para primeiro teste
        graph.set_entry_point("enrichment")
        graph.add_edge("enrichment", "ncm_validation")
        graph.add_edge("ncm_validation", "cest_validation")
        graph.add_edge("cest_validation", "reconciliation")
        graph.add_edge("reconciliation", "completion")
        graph.add_edge("completion", END)

        return graph.compile()

    def _enrichment_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Nó de enriquecimento de dados"""
        try:
            self._log_step(state, "enrichment", "Iniciando enriquecimento de dados")

            # Mock do enriquecimento por enquanto
            enriched_data = {
                "confidence": 0.8,
                "additional_info": "Mock enrichment data",
            }

            # Atualizar estado
            state["produto_dados"].update(enriched_data)
            state["enrichment_confidence"] = enriched_data.get("confidence", 0.0)

            self._log_step(
                state,
                "enrichment",
                f"Enriquecimento concluído. Confiança: {state['enrichment_confidence']}",
            )

            return state

        except Exception as e:
            return self._handle_error(state, "enrichment", str(e))

    def _ncm_validation_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Nó de validação NCM"""
        try:
            self._log_step(state, "ncm_validation", "Iniciando validação NCM")

            ncm_informado = state["produto_dados"].get("ncm_informado")

            if not ncm_informado:
                self._log_step(state, "ncm_validation", "NCM não informado")
                state["ncm_validation_result"] = {
                    "valid": False,
                    "confidence": 0.0,
                    "reason": "NCM não informado",
                }
                return state

            # Mock da validação NCM
            validation_result = {
                "valid": True,
                "confidence": 0.85,
                "ncm_validado": ncm_informado,
                "justificativa": "NCM validado com sucesso (mock)",
            }

            state["ncm_validation_result"] = validation_result

            self._log_step(
                state,
                "ncm_validation",
                f"Validação NCM concluída. Válido: {validation_result['valid']}, "
                f"Confiança: {validation_result['confidence']}",
            )

            return state

        except Exception as e:
            return self._handle_error(state, "ncm_validation", str(e))

    def _cest_validation_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Nó de validação/determinação CEST"""
        try:
            self._log_step(state, "cest_validation", "Iniciando validação CEST")

            cest_informado = state["produto_dados"].get("cest_informado")
            ncm_validado = state["ncm_validation_result"]["valid"]

            if not ncm_validado:
                self._log_step(state, "cest_validation", "NCM inválido, pulando CEST")
                state["cest_validation_result"] = {
                    "valid": False,
                    "confidence": 0.0,
                    "reason": "NCM inválido",
                }
                return state

            # Mock da validação/determinação CEST
            if cest_informado:
                validation_result = {
                    "valid": True,
                    "confidence": 0.8,
                    "cest_validado": cest_informado,
                    "justificativa": "CEST validado (mock)",
                }
            else:
                validation_result = {
                    "valid": True,
                    "confidence": 0.75,
                    "cest_determinado": "28.123.45",
                    "justificativa": "CEST determinado (mock)",
                    "action": "determined",
                }

            state["cest_validation_result"] = validation_result

            self._log_step(
                state,
                "cest_validation",
                f"Validação CEST concluída. Válido: {validation_result.get('valid', False)}, "
                f"Confiança: {validation_result['confidence']}",
            )

            return state

        except Exception as e:
            return self._handle_error(state, "cest_validation", str(e))

    def _reconciliation_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Nó de reconciliação final"""
        try:
            self._log_step(state, "reconciliation", "Iniciando reconciliação")

            # Coletar todos os resultados
            _reconciliation_data = {
                "produto_dados": state["produto_dados"],
                "enrichment_confidence": state.get("enrichment_confidence", 0.0),
                "ncm_validation": state.get("ncm_validation_result", {}),
                "cest_validation": state.get("cest_validation_result", {}),
                "audit_trail": state.get("audit_trail", []),
            }

            # Mock da reconciliação
            final_result = {
                "ncm_final": state.get("ncm_validation_result", {}).get(
                    "ncm_validado", ""
                ),
                "cest_final": state.get("cest_validation_result", {}).get(
                    "cest_validado", ""
                ),
                "justificativa_ncm": "NCM confirmado via workflow de confirmação",
                "justificativa_cest": "CEST confirmado via workflow de confirmação",
                "confidence": 0.8,
                "status": "CONFIRMADO",
            }

            state["final_result"] = final_result
            state["final_confidence"] = final_result.get("confidence", 0.0)

            self._log_step(
                state,
                "reconciliation",
                f"Reconciliação concluída. Confiança final: {state['final_confidence']}",
            )

            return state

        except Exception as e:
            return self._handle_error(state, "reconciliation", str(e))

    def _manual_review_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Nó para marcar necessidade de revisão manual"""
        self._log_step(state, "manual_review", "Produto marcado para revisão manual")

        state["status"] = "REVISAO_MANUAL"
        state["requires_human_review"] = True

        # Preparar contexto para revisão humana
        state["review_context"] = {
            "reason": self._get_review_reason(state),
            "low_confidence_areas": self._identify_low_confidence_areas(state),
            "suggested_actions": self._suggest_review_actions(state),
        }

        return state

    def _completion_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Nó de finalização do workflow"""
        self._log_step(state, "completion", "Workflow de confirmação concluído")

        state["status"] = "CONFIRMADO"
        state["workflow_completed"] = True
        state["completion_timestamp"] = self._get_timestamp()

        return state

    def _after_ncm_validation(self, state: Dict[str, Any]) -> str:
        """Decide próximo passo após validação NCM"""

        if state.get("error"):
            return "error"

        ncm_result = state.get("ncm_validation_result", {})
        confidence = ncm_result.get("confidence", 0.0)

        if confidence < self.config.confidence_threshold:
            return "manual_review"

        return "continue"

    def _after_cest_validation(self, state: Dict[str, Any]) -> str:
        """Decide próximo passo após validação CEST"""

        if state.get("error"):
            return "error"

        cest_result = state.get("cest_validation_result", {})
        confidence = cest_result.get("confidence", 0.0)

        if confidence < self.config.confidence_threshold:
            return "manual_review"

        return "reconciliation"

    def _after_reconciliation(self, state: Dict[str, Any]) -> str:
        """Decide próximo passo após reconciliação"""

        final_confidence = state.get("final_confidence", 0.0)

        if final_confidence < self.config.confidence_threshold:
            return "manual_review"

        return "completion"

    def _get_review_reason(self, state: Dict[str, Any]) -> str:
        """Identifica razão para revisão manual"""
        reasons = []

        ncm_result = state.get("ncm_validation_result", {})
        if ncm_result.get("confidence", 0.0) < self.config.confidence_threshold:
            reasons.append(
                f"Baixa confiança na validação NCM ({ncm_result.get('confidence', 0.0):.2f})"
            )

        cest_result = state.get("cest_validation_result", {})
        if cest_result.get("confidence", 0.0) < self.config.confidence_threshold:
            reasons.append(
                f"Baixa confiança na validação CEST ({cest_result.get('confidence', 0.0):.2f})"
            )

        if state.get("final_confidence", 0.0) < self.config.confidence_threshold:
            reasons.append(
                f"Baixa confiança final ({state.get('final_confidence', 0.0):.2f})"
            )

        return "; ".join(reasons) if reasons else "Revisão necessária"

    def _identify_low_confidence_areas(self, state: Dict[str, Any]) -> List[str]:
        """Identifica áreas com baixa confiança"""
        areas = []

        if state.get("enrichment_confidence", 0.0) < self.config.confidence_threshold:
            areas.append("enriquecimento_dados")

        ncm_result = state.get("ncm_validation_result", {})
        if ncm_result.get("confidence", 0.0) < self.config.confidence_threshold:
            areas.append("validacao_ncm")

        cest_result = state.get("cest_validation_result", {})
        if cest_result.get("confidence", 0.0) < self.config.confidence_threshold:
            areas.append("validacao_cest")

        return areas

    def _suggest_review_actions(self, state: Dict[str, Any]) -> List[str]:
        """Sugere ações para revisão manual"""
        actions = []

        ncm_result = state.get("ncm_validation_result", {})
        if not ncm_result.get("valid", False):
            actions.append("Verificar adequação do NCM informado")

        cest_result = state.get("cest_validation_result", {})
        if not cest_result.get("valid", False):
            actions.append("Verificar necessidade e adequação do CEST")

        if state.get("enrichment_confidence", 0.0) < 0.5:
            actions.append("Revisar e complementar dados do produto")

        return actions

    def _log_step(self, state: Dict[str, Any], step: str, message: str):
        """Log de etapa do workflow"""
        if "audit_trail" not in state:
            state["audit_trail"] = []

        state["audit_trail"].append(
            {"step": step, "message": message, "timestamp": datetime.now().isoformat()}
        )

    def _handle_error(
        self, state: Dict[str, Any], step: str, error_message: str
    ) -> Dict[str, Any]:
        """Trata erros no workflow"""
        state["error"] = error_message
        state["status"] = "ERROR"
        self._log_step(state, step, f"Erro: {error_message}")
        return state

    def _get_timestamp(self) -> str:
        """Retorna timestamp atual"""
        return datetime.now().isoformat()
