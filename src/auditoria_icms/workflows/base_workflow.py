"""
Workflow Base para Sistema de Auditoria Fiscal v16.0
Define estrutura base para workflows LangGraph no sistema de classificação NCM/CEST
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypedDict, Literal
from dataclasses import dataclass
from datetime import datetime
import uuid
import logging

try:
    from langgraph.graph import StateGraph, END, START
    from langchain.schema import BaseMessage
    LANGGRAPH_AVAILABLE = True
except ImportError:
    # Fallback se LangGraph não estiver disponível
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = "END"
    START = "START"
    BaseMessage = object

logger = logging.getLogger(__name__)

class WorkflowState(TypedDict):
    """Estado compartilhado entre nós do workflow de classificação fiscal."""
    
    # Identificadores
    session_id: str
    job_id: str
    mercadoria_id: int
    produto_id: str
    empresa_id: int
    
    # Dados do produto
    descricao_original: str
    descricao_enriquecida: Optional[str]
    codigo_barra: Optional[str]
    codigo_produto: Optional[str]
    
    # Classificações existentes
    ncm_informado: Optional[str]
    cest_informado: Optional[str]
    
    # Atividades da empresa (contexto fiscal)
    empresa_atividades: List[str]
    
    # Resultados dos agentes
    enrichment_result: Optional[Dict[str, Any]]
    ncm_result: Optional[Dict[str, Any]]
    cest_result: Optional[Dict[str, Any]]
    reconciliation_result: Optional[Dict[str, Any]]
    aggregation_result: Optional[Dict[str, Any]]
    
    # Estado do workflow
    workflow_type: Literal["confirmation", "determination"]
    current_step: str
    completed_steps: List[str]
    next_step: Optional[str]
    
    # Controle de qualidade
    confidence_ncm: float
    confidence_cest: float
    requires_human_review: bool
    auto_approve: bool
    
    # Trilha de auditoria
    audit_trail: List[Dict[str, Any]]
    rag_contexts: List[Dict[str, Any]]
    errors: List[str]
    warnings: List[str]
    
    # Metadados de execução
    started_at: datetime
    updated_at: datetime
    processing_time_ms: int
    retry_count: int
    
    # Resultado final
    final_ncm: Optional[str]
    final_cest: Optional[str]
    final_status: str
    justificativa_ncm: Optional[str]
    justificativa_cest: Optional[str]

@dataclass
class WorkflowConfig:
    """Configuração para workflows de classificação fiscal."""
    
    # Limites de execução
    max_steps: int = 20
    timeout_minutes: int = 10
    retry_attempts: int = 3
    
    # Limiares de confiança
    confidence_threshold: float = 0.7
    auto_approve_threshold: float = 0.9
    
    # Paralelização
    enable_parallel_processing: bool = True
    max_concurrent_agents: int = 3
    
    # Agentes habilitados
    enable_enrichment: bool = True
    enable_ncm_classification: bool = True
    enable_cest_classification: bool = True
    enable_reconciliation: bool = True
    enable_aggregation: bool = True
    
    # RAG e contexto
    max_rag_contexts: int = 10
    context_window_size: int = 2000
    require_human_validation_threshold: float = 0.8


class BaseWorkflow(ABC):
    """
    Classe base para workflows de classificação fiscal.
    Implementa a estrutura comum para todos os workflows LangGraph.
    """
    
    def __init__(
        self,
        name: str,
        config: WorkflowConfig,
        agents: Dict[str, Any],
        logger=None
    ):
        self.name = name
        self.config = config
        self.agents = agents
        self.logger = logger
        self.graph = None
        
        # Construir o grafo do workflow
        self._build_graph()
        
    @abstractmethod
    def _build_graph(self):
        """Constrói o grafo LangGraph específico do workflow."""
        pass
    
    @abstractmethod
    async def _initialize_state(self, input_data: Dict[str, Any]) -> WorkflowState:
        """Inicializa o estado do workflow."""
        pass
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa o workflow completo.
        
        Args:
            input_data: Dados de entrada para o workflow
            
        Returns:
            Resultado final do workflow
        """
        if not self.graph:
            raise ValueError(f"Grafo não inicializado para workflow {self.name}")
        
        # Inicializar estado
        initial_state = await self._initialize_state(input_data)
        
        try:
            # Executar grafo
            final_state = await self.graph.ainvoke(initial_state)
            
            # Processar resultado final
            return await self._process_final_result(final_state)
            
        except Exception as e:
            self.logger.error(f"Erro na execução do workflow {self.name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "workflow": self.name
            }
    
    async def _process_final_result(self, final_state: WorkflowState) -> Dict[str, Any]:
        """Processa o resultado final do workflow."""
        
        return {
            "success": True,
            "workflow": self.name,
            "session_id": final_state["session_id"],
            "produto_id": final_state["produto_id"],
            "empresa_id": final_state["empresa_id"],
            "classification": {
                "ncm_final": final_state.get("reconciliation_result", {}).get("ncm_final"),
                "cest_final": final_state.get("reconciliation_result", {}).get("cest_final"),
                "justificativa_ncm": final_state.get("reconciliation_result", {}).get("justificativa_ncm"),
                "justificativa_cest": final_state.get("reconciliation_result", {}).get("justificativa_cest"),
                "confidence_score": final_state.get("confidence_score", 0.0)
            },
            "agent_results": {
                "enrichment": final_state.get("enrichment_result"),
                "ncm": final_state.get("ncm_result"),
                "cest": final_state.get("cest_result"),
                "reconciliation": final_state.get("reconciliation_result")
            },
            "requires_human_review": final_state.get("requires_human_review", False),
            "processing_time_ms": final_state.get("processing_time_ms", 0),
            "errors": final_state.get("errors", [])
        }
    
    # Nós comuns para workflows
    
    async def enrichment_node(self, state: WorkflowState) -> WorkflowState:
        """Nó de enriquecimento de dados."""
        try:
            enrichment_agent = self.agents.get("enrichment")
            if not enrichment_agent:
                raise ValueError("Agente de enriquecimento não encontrado")
            
            input_data = {
                "descricao_produto": state["descricao_original"],
                "gtin": state.get("gtin"),
                "ncm_atual": state.get("ncm_atual")
            }
            
            result = await enrichment_agent.process(
                input_data, 
                {"empresa_id": state["empresa_id"]}
            )
            
            state["enrichment_result"] = result
            state["descricao_enriquecida"] = result.get("enriched_description")
            state["current_step"] = "enrichment_completed"
            
        except Exception as e:
            error_msg = f"Erro no enriquecimento: {str(e)}"
            state["errors"].append(error_msg)
            self.logger.error(error_msg)
        
        return state
    
    async def ncm_classification_node(self, state: WorkflowState) -> WorkflowState:
        """Nó de classificação NCM."""
        try:
            ncm_agent = self.agents.get("ncm")
            if not ncm_agent:
                raise ValueError("Agente NCM não encontrado")
            
            input_data = {
                "descricao_produto": state["descricao_original"],
                "descricao_enriquecida": state.get("descricao_enriquecida"),
                "gtin": state.get("gtin"),
                "ncm_atual": state.get("ncm_atual")
            }
            
            result = await ncm_agent.process(
                input_data,
                {"empresa_id": state["empresa_id"]}
            )
            
            state["ncm_result"] = result
            state["current_step"] = "ncm_completed"
            
        except Exception as e:
            error_msg = f"Erro na classificação NCM: {str(e)}"
            state["errors"].append(error_msg)
            self.logger.error(error_msg)
        
        return state
    
    async def cest_classification_node(self, state: WorkflowState) -> WorkflowState:
        """Nó de classificação CEST."""
        try:
            cest_agent = self.agents.get("cest")
            if not cest_agent:
                raise ValueError("Agente CEST não encontrado")
            
            # Usar NCM classificado se disponível
            ncm_para_cest = None
            if state.get("ncm_result"):
                ncm_para_cest = state["ncm_result"].get("ncm_classificado")
            
            input_data = {
                "descricao_produto": state["descricao_original"],
                "descricao_enriquecida": state.get("descricao_enriquecida"),
                "ncm_final": ncm_para_cest,
                "ncm_classificado": ncm_para_cest,
                "cest_atual": state.get("cest_atual")
            }
            
            result = await cest_agent.process(
                input_data,
                {"empresa_id": state["empresa_id"], "estado": "RO"}
            )
            
            state["cest_result"] = result
            state["current_step"] = "cest_completed"
            
        except Exception as e:
            error_msg = f"Erro na classificação CEST: {str(e)}"
            state["errors"].append(error_msg)
            self.logger.error(error_msg)
        
        return state
    
    async def reconciliation_node(self, state: WorkflowState) -> WorkflowState:
        """Nó de reconciliação final."""
        try:
            reconciliation_agent = self.agents.get("reconciliation")
            if not reconciliation_agent:
                raise ValueError("Agente de reconciliação não encontrado")
            
            input_data = {
                "descricao_produto": state["descricao_original"],
                "descricao_enriquecida": state.get("descricao_enriquecida"),
                "ncm_result": state.get("ncm_result"),
                "cest_result": state.get("cest_result")
            }
            
            result = await reconciliation_agent.process(
                input_data,
                {"empresa_id": state["empresa_id"]}
            )
            
            state["reconciliation_result"] = result
            state["confidence_score"] = result.get("confidence_score", 0.0)
            state["requires_human_review"] = result.get("requires_human_review", False)
            state["current_step"] = "reconciliation_completed"
            
        except Exception as e:
            error_msg = f"Erro na reconciliação: {str(e)}"
            state["errors"].append(error_msg)
            self.logger.error(error_msg)
        
        return state
    
    def should_continue_to_cest(self, state: WorkflowState) -> str:
        """Decisão condicional para prosseguir para classificação CEST."""
        
        # Verificar se NCM foi classificado com sucesso
        ncm_result = state.get("ncm_result")
        if not ncm_result or not ncm_result.get("success"):
            return "error_handling"
        
        # Verificar confiança mínima
        ncm_confidence = ncm_result.get("confidence_score", 0.0)
        if ncm_confidence < 0.5:
            return "low_confidence_handling"
        
        return "cest_classification"
    
    def should_continue_to_reconciliation(self, state: WorkflowState) -> str:
        """Decisão condicional para prosseguir para reconciliação."""
        
        # Verificar se tanto NCM quanto CEST foram processados
        ncm_result = state.get("ncm_result")
        cest_result = state.get("cest_result")
        
        if not ncm_result or not cest_result:
            return "error_handling"
        
        return "reconciliation"
    
    def is_workflow_complete(self, state: WorkflowState) -> str:
        """Verifica se o workflow está completo."""
        
        if state.get("reconciliation_result"):
            return END
        
        return "error_handling"
    
    async def error_handling_node(self, state: WorkflowState) -> WorkflowState:
        """Nó de tratamento de erros."""
        
        errors = state.get("errors", [])
        
        if errors:
            self.logger.error(f"Workflow {self.name} teve erros: {errors}")
            
            # Tentar recuperação básica
            if not state.get("reconciliation_result"):
                # Criar resultado mínimo baseado no que foi processado
                state["reconciliation_result"] = {
                    "ncm_final": state.get("ncm_result", {}).get("ncm_classificado"),
                    "cest_final": state.get("cest_result", {}).get("cest_classificado"),
                    "confidence_score": 0.3,  # Baixa confiança devido a erros
                    "requires_human_review": True,
                    "errors": errors
                }
                
                state["confidence_score"] = 0.3
                state["requires_human_review"] = True
        
        state["current_step"] = "error_handled"
        return state
