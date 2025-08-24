"""
Workflows Module - Sistema de Orquestração LangGraph
Módulo para workflows de classificação fiscal usando LangGraph
"""

from .base_workflow import BaseWorkflow, WorkflowState, WorkflowConfig
from .confirmation_flow import ConfirmationFlow
from .determination_flow import DeterminationFlow
from .workflow_manager import (
    WorkflowManager,
    WorkflowType,
    WorkflowResult,
    workflow_manager,
    classify_product,
    classify_batch,
)

__all__ = [
    # Classes base
    "BaseWorkflow",
    "WorkflowState",
    "WorkflowConfig",
    # Workflows específicos
    "ConfirmationFlow",
    "DeterminationFlow",
    # Gerenciamento
    "WorkflowManager",
    "WorkflowType",
    "WorkflowResult",
    # Instância global e funções de conveniência
    "workflow_manager",
    "classify_product",
    "classify_batch",
]
