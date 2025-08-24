"""
Base Agent Simplificado - Sistema de Auditoria Fiscal ICMS
Versão independente sem dependências externas
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentDecision:
    """Representa uma decisão tomada por um agente"""

    agent_name: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    reasoning: str
    confidence_score: float
    sources_used: List[str] = field(default_factory=list)
    processing_time_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "agent_name": self.agent_name,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "reasoning": self.reasoning,
            "confidence_score": self.confidence_score,
            "sources_used": self.sources_used,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AuditTrail:
    """Trilha de auditoria para um processo completo"""

    session_id: str
    product_id: str
    empresa_id: int
    agent_decisions: List[AgentDecision]
    final_classification: Dict[str, Any]
    human_review_required: bool
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "session_id": self.session_id,
            "product_id": self.product_id,
            "empresa_id": self.empresa_id,
            "agent_decisions": [d.to_dict() for d in self.agent_decisions],
            "final_classification": self.final_classification,
            "human_review_required": self.human_review_required,
            "created_at": self.created_at.isoformat(),
        }


class BaseAgent(ABC):
    """
    Classe base para todos os agentes do sistema de auditoria fiscal
    Versão simplificada sem dependências externas
    """

    def __init__(
        self, name: str, description: str = "", config: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.description = description
        self.config = config or {}
        self.logger = logging.getLogger(f"agent.{name}")

        # Histórico de decisões
        self.decisions_history: List[AgentDecision] = []

        # Configurações padrão
        self.default_config = {
            "confidence_threshold": 0.7,
            "max_retries": 3,
            "timeout_seconds": 300,
            "enable_logging": True,
        }

        # Merge configurações
        self.effective_config = {**self.default_config, **self.config}

        self.logger.info(f"Agente {self.name} inicializado")

    @abstractmethod
    def process(
        self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Método principal de processamento do agente

        Args:
            input_data: Dados de entrada para processamento
            context: Contexto adicional (empresa, usuário, etc.)

        Returns:
            Resultado do processamento
        """
        pass

    def create_decision_record(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        reasoning: str,
        confidence_score: float,
        sources_used: List[str] = None,
        processing_time_ms: int = 0,
    ) -> AgentDecision:
        """Cria registro de decisão do agente"""

        decision = AgentDecision(
            agent_name=self.name,
            input_data=input_data,
            output_data=output_data,
            reasoning=reasoning,
            confidence_score=confidence_score,
            sources_used=sources_used or [],
            processing_time_ms=processing_time_ms,
        )

        self.decisions_history.append(decision)

        if self.effective_config.get("enable_logging", True):
            self.logger.info(f"Decisão registrada: confiança={confidence_score:.2%}")

        return decision

    def get_confidence_threshold(self) -> float:
        """Retorna o limiar de confiança configurado"""
        return self.effective_config.get("confidence_threshold", 0.7)

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Valida dados de entrada básicos

        Args:
            input_data: Dados para validar

        Returns:
            True se válidos, False caso contrário
        """
        if not isinstance(input_data, dict):
            self.logger.error("Dados de entrada devem ser um dicionário")
            return False

        required_fields = self.get_required_fields()
        for (
            required_field
        ) in required_fields:  # rename to avoid shadowing imported 'field'
            if required_field not in input_data:
                self.logger.error(f"Campo obrigatório ausente: {required_field}")
                return False

        return True

    def get_required_fields(self) -> List[str]:
        """
        Retorna lista de campos obrigatórios para este agente
        Subclasses podem sobrescrever
        """
        return []

    def handle_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """
        Trata erros de forma padronizada

        Args:
            error: Exceção ocorrida
            context: Contexto do erro

        Returns:
            Dicionário com informações do erro
        """
        error_info = {
            "success": False,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "agent_name": self.name,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.logger.error(f"Erro no agente {self.name}: {error_info}")

        return error_info

    def log_performance(self, operation: str, duration_ms: int, **kwargs):
        """Registra métricas de performance"""

        if self.effective_config.get("enable_logging", True):
            self.logger.info(f"Performance {operation}: {duration_ms}ms", extra=kwargs)

    def get_agent_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o agente"""

        return {
            "name": self.name,
            "description": self.description,
            "config": self.effective_config,
            "decisions_count": len(self.decisions_history),
            "last_activity": (
                self.decisions_history[-1].timestamp.isoformat()
                if self.decisions_history
                else None
            ),
        }

    def reset_history(self):
        """Limpa histórico de decisões"""
        self.decisions_history.clear()
        self.logger.info(f"Histórico do agente {self.name} limpo")


class MockLLMAgent(BaseAgent):
    """
    Agente simulado para testes sem dependências externas
    """

    def __init__(
        self, name: str, description: str = "", config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(name, description, config)

    def process(
        self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Processamento simulado"""

        if not self.validate_input(input_data):
            return self.handle_error(ValueError("Dados de entrada inválidos"))

        try:
            # Simula processamento
            descricao = input_data.get("descricao_produto", "")

            # Resposta simulada baseada na descrição
            resultado = {
                "success": True,
                "processed_description": descricao,
                "agent_response": f"Processado por {self.name}: {descricao[:50]}...",
                "confidence": 0.85,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Registra decisão
            self.create_decision_record(
                input_data=input_data,
                output_data=resultado,
                reasoning=f"Processamento simulado pelo agente {self.name}",
                confidence_score=0.85,
                sources_used=["simulacao"],
                processing_time_ms=100,
            )

            return resultado

        except Exception as e:
            return self.handle_error(e, "Erro no processamento simulado")

    def get_required_fields(self) -> List[str]:
        """Campos obrigatórios para o agente simulado"""
        return ["descricao_produto"]


# Classes de agentes especializados simplificadas
class EnrichmentAgentBase(BaseAgent):
    """Agente de enriquecimento de descrições"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="EnrichmentAgent",
            description="Enriquece descrições de produtos",
            config=config,
        )

    def enriquecer_descricao(self, descricao: str) -> Dict[str, Any]:
        """Simula enriquecimento de descrição"""

        resultado = {
            "descricao_enriquecida": f"{descricao} - produto enriquecido com análise semântica",
            "confianca": 0.85,
            "justificativa": "Enriquecimento baseado em análise de padrões textuais",
        }

        return resultado


class NCMAgentBase(BaseAgent):
    """Agente de classificação NCM"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="NCMAgent",
            description="Classifica produtos com código NCM",
            config=config,
        )

    def processar_classificacao(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Simula classificação NCM"""

        resultado = {
            "ncm": "12345678",
            "confianca": 0.90,
            "justificativa": "Classificação baseada em descrição e padrões similares",
        }

        return resultado


class CESTAgentBase(BaseAgent):
    """Agente de classificação CEST"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="CESTAgent",
            description="Classifica produtos com código CEST",
            config=config,
        )

    def processar_classificacao(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Simula classificação CEST"""

        resultado = {
            "cest": "12.345.67",
            "confianca": 0.85,
            "justificativa": "CEST determinado com base no NCM",
        }

        return resultado


class ReconciliationAgentBase(BaseAgent):
    """Agente de reconciliação e validação"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="ReconciliationAgent",
            description="Valida e reconcilia classificações",
            config=config,
        )

    def validar_consistencia(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Simula validação de consistência"""

        resultado = {
            "validacao": True,
            "confianca": 0.88,
            "justificativa": "Classificações consistentes entre NCM e CEST",
        }

        return resultado


# Função utilitária para criar agentes simulados
def create_mock_agents(config: Optional[Dict[str, Any]] = None) -> Dict[str, BaseAgent]:
    """Cria conjunto de agentes simulados para teste"""

    return {
        "enrichment": EnrichmentAgentBase(config),
        "ncm": NCMAgentBase(config),
        "cest": CESTAgentBase(config),
        "reconciliation": ReconciliationAgentBase(config),
    }
