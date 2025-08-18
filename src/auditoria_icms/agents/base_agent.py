"""
Agente Base para Sistema de Auditoria Fiscal ICMS
Classe abstrata que define a interface comum para todos os agentes especializados.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
import uuid
import logging

from langchain.schema import BaseMessage
from langchain.llms.base import BaseLLM


@dataclass
class AgentDecision:
    """Estrutura para armazenar decisões dos agentes com auditabilidade completa."""
    agent_name: str
    decision_id: str
    timestamp: datetime
    input_data: Dict[str, Any]
    reasoning: str
    confidence_score: float
    output_data: Dict[str, Any]
    sources_used: List[str]
    processing_time_ms: int


@dataclass
class AuditTrail:
    """Trilha de auditoria para rastreamento completo de decisões."""
    session_id: str
    product_id: str
    empresa_id: int
    agent_decisions: List[AgentDecision]
    final_classification: Dict[str, Any]
    human_review_required: bool
    created_at: datetime


class BaseAgent(ABC):
    """
    Classe base abstrata para todos os agentes do sistema.
    Define a interface comum e funcionalidades de auditoria.
    """
    
    def __init__(
        self,
        name: str,
        llm: BaseLLM,
        config: Dict[str, Any],
        logger: Optional[logging.Logger] = None
    ):
        self.name = name
        self.llm = llm
        self.config = config
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.decisions_history: List[AgentDecision] = []
        
    @abstractmethod
    async def process(
        self, 
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Método principal de processamento do agente.
        
        Args:
            input_data: Dados de entrada para processamento
            context: Contexto adicional (empresa, usuário, etc.)
            
        Returns:
            Dict contendo o resultado do processamento
        """
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Valida se os dados de entrada são adequados para o agente."""
        pass
    
    def create_decision_record(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        reasoning: str,
        confidence_score: float,
        sources_used: List[str],
        processing_time_ms: int
    ) -> AgentDecision:
        """Cria um registro de decisão para auditoria."""
        decision = AgentDecision(
            agent_name=self.name,
            decision_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            input_data=input_data,
            reasoning=reasoning,
            confidence_score=confidence_score,
            output_data=output_data,
            sources_used=sources_used,
            processing_time_ms=processing_time_ms
        )
        
        self.decisions_history.append(decision)
        return decision
    
    def get_confidence_threshold(self) -> float:
        """Retorna o limiar de confiança configurado para este agente."""
        return self.config.get('confidence_threshold', 0.8)
    
    def requires_human_review(self, confidence_score: float) -> bool:
        """Determina se a decisão requer revisão humana baseada na confiança."""
        return confidence_score < self.get_confidence_threshold()
    
    async def explain_decision(self, decision_id: str) -> str:
        """
        Gera uma explicação detalhada de uma decisão específica.
        Usado para transparência e auditoria.
        """
        decision = next(
            (d for d in self.decisions_history if d.decision_id == decision_id),
            None
        )
        
        if not decision:
            return f"Decisão {decision_id} não encontrada."
        
        explanation = f"""
        Agente: {decision.agent_name}
        Timestamp: {decision.timestamp}
        Confiança: {decision.confidence_score:.2%}
        
        Dados de Entrada:
        {decision.input_data}
        
        Raciocínio:
        {decision.reasoning}
        
        Fontes Consultadas:
        {', '.join(decision.sources_used)}
        
        Resultado:
        {decision.output_data}
        """
        
        return explanation
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de performance do agente."""
        if not self.decisions_history:
            return {"total_decisions": 0}
        
        total_decisions = len(self.decisions_history)
        avg_confidence = sum(d.confidence_score for d in self.decisions_history) / total_decisions
        avg_processing_time = sum(d.processing_time_ms for d in self.decisions_history) / total_decisions
        
        high_confidence_decisions = sum(
            1 for d in self.decisions_history 
            if d.confidence_score >= self.get_confidence_threshold()
        )
        
        return {
            "total_decisions": total_decisions,
            "average_confidence": avg_confidence,
            "average_processing_time_ms": avg_processing_time,
            "high_confidence_ratio": high_confidence_decisions / total_decisions,
            "decisions_requiring_review": total_decisions - high_confidence_decisions
        }
    
    def clear_history(self):
        """Limpa o histórico de decisões (usado entre sessões)."""
        self.decisions_history = []
        
    def __str__(self) -> str:
        return f"Agent({self.name})"
    
    def __repr__(self) -> str:
        return f"Agent(name='{self.name}', decisions={len(self.decisions_history)})"
