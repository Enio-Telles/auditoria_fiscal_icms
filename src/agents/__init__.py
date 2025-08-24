"""
Sistema de Agentes para Auditoria Fiscal ICMS
=============================================

Este módulo implementa um sistema completo de agentes especializados para auditoria fiscal,
incluindo classificação NCM/CEST, expansão de dados, agregação, reconciliação e orquestração.

Agentes Disponíveis:
- BaseAgent: Classe base para todos os agentes
- ExpansionAgent: Especialista em expansão e enriquecimento de dados
- AggregationAgent: Especialista em agregação e análise estatística
- NCMAgent: Especialista em classificação NCM
- CESTAgent: Especialista em classificação CEST
- ReconcilerAgent: Especialista em reconciliação de dados

Componentes de Gerenciamento:
- AgentManager: Gerenciador de ciclo de vida dos agentes
- AgentCoordinator: Coordenador de workflows multi-agente

Classes de Dados:
- AgentTask: Representa uma tarefa para execução
- AgentMessage: Representa uma mensagem entre agentes
- AgentStatus: Enum com status dos agentes
- TaskPriority: Enum com prioridades de tarefas
- WorkflowStatus: Enum com status de workflows
- Workflow: Representa um workflow completo
- WorkflowStep: Representa um step de workflow
"""

# Importações das classes base
from .base_agent import (
    BaseAgent,
    AgentTask,
    AgentMessage,
    AgentStatus,
    TaskPriority
)

# Importações dos agentes especializados
from .expansion_agent import ExpansionAgent
from .aggregation_agent import AggregationAgent
from .ncm_agent import NCMAgent
from .cest_agent import CESTAgent
from .reconciler_agent import ReconcilerAgent

# Importações dos componentes de gerenciamento
from .agent_manager import AgentManager
from .agent_coordinator import (
    AgentCoordinator,
    Workflow,
    WorkflowStep,
    WorkflowStatus,
    StepStatus
)

# Lista de exportações públicas
__all__ = [
    # Classes base
    "BaseAgent",
    "AgentTask", 
    "AgentMessage",
    "AgentStatus",
    "TaskPriority",
    
    # Agentes especializados
    "ExpansionAgent",
    "AggregationAgent", 
    "NCMAgent",
    "CESTAgent",
    "ReconcilerAgent",
    
    # Gerenciamento
    "AgentManager",
    "AgentCoordinator",
    
    # Workflows
    "Workflow",
    "WorkflowStep", 
    "WorkflowStatus",
    "StepStatus"
]

# Metadados do módulo
__version__ = "1.0.0"
__author__ = "Sistema de Auditoria Fiscal ICMS"
__description__ = "Sistema completo de agentes especializados para auditoria fiscal"

# Configurações padrão para agentes
DEFAULT_AGENT_CONFIG = {
    "log_level": "INFO",
    "task_timeout": 300,
    "max_retries": 3,
    "cache_size": 1000,
    "enable_metrics": True
}

# Configurações padrão para o gerenciador
DEFAULT_MANAGER_CONFIG = {
    "health_check_interval": 30,
    "max_retry_attempts": 3,
    "task_timeout": 300
}

# Configurações padrão para o coordenador
DEFAULT_COORDINATOR_CONFIG = {
    "max_concurrent_workflows": 10,
    "default_step_timeout": 300,
    "monitoring_interval": 5
}


def create_audit_agent_system(config: dict = None) -> tuple:
    """
    Cria um sistema completo de agentes para auditoria fiscal.
    
    Args:
        config: Configurações customizadas para o sistema
        
    Returns:
        Tupla contendo (agent_manager, agent_coordinator, agents_dict)
    """
    config = config or {}
    
    # Criar gerenciador de agentes
    manager_config = {**DEFAULT_MANAGER_CONFIG, **config.get("manager", {})}
    agent_manager = AgentManager(manager_config)
    
    # Registrar tipos de agentes
    agent_manager.register_agent_type(ExpansionAgent, "ExpansionAgent")
    agent_manager.register_agent_type(AggregationAgent, "AggregationAgent") 
    agent_manager.register_agent_type(NCMAgent, "NCMAgent")
    agent_manager.register_agent_type(CESTAgent, "CESTAgent")
    agent_manager.register_agent_type(ReconcilerAgent, "ReconcilerAgent")
    
    # Criar coordenador
    coordinator_config = {**DEFAULT_COORDINATOR_CONFIG, **config.get("coordinator", {})}
    agent_coordinator = AgentCoordinator(agent_manager, coordinator_config)
    
    # Registrar templates de workflow comuns
    _register_default_workflow_templates(agent_coordinator)
    
    return agent_manager, agent_coordinator


def _register_default_workflow_templates(coordinator: AgentCoordinator) -> None:
    """Registra templates de workflow padrão."""
    
    # Template para classificação completa de produto
    product_classification_template = {
        "name": "Classificação Completa de Produto",
        "description": "Workflow para classificação NCM/CEST e enriquecimento de dados de produto",
        "steps": [
            {
                "id": "expand_product_data",
                "agent_name": "expansion_agent",
                "task_type": "expand_description",
                "task_data": {
                    "description": "${product_description}",
                    "additional_info": "${additional_info}"
                },
                "dependencies": []
            },
            {
                "id": "classify_ncm",
                "agent_name": "ncm_agent", 
                "task_type": "classify_ncm",
                "task_data": {
                    "description": "${step_expand_product_data_result.expanded_description}",
                    "technical_specs": "${step_expand_product_data_result.technical_specs}"
                },
                "dependencies": ["expand_product_data"]
            },
            {
                "id": "classify_cest",
                "agent_name": "cest_agent",
                "task_type": "classify_cest", 
                "task_data": {
                    "description": "${step_expand_product_data_result.expanded_description}",
                    "ncm_code": "${step_classify_ncm_result.ncm_code}",
                    "state": "${state}"
                },
                "dependencies": ["expand_product_data", "classify_ncm"]
            },
            {
                "id": "aggregate_results",
                "agent_name": "aggregation_agent",
                "task_type": "consolidate_data",
                "task_data": {
                    "sources": [
                        "${step_expand_product_data_result}",
                        "${step_classify_ncm_result}",
                        "${step_classify_cest_result}"
                    ]
                },
                "dependencies": ["expand_product_data", "classify_ncm", "classify_cest"]
            }
        ],
        "max_parallel_steps": 3,
        "failure_strategy": "stop"
    }
    
    coordinator.register_workflow_template("product_classification", product_classification_template)
    
    # Template para reconciliação de dados
    data_reconciliation_template = {
        "name": "Reconciliação de Dados",
        "description": "Workflow para reconciliação e validação de qualidade de dados",
        "steps": [
            {
                "id": "detect_inconsistencies",
                "agent_name": "reconciler_agent",
                "task_type": "detect_inconsistencies",
                "task_data": {
                    "dataset": "${dataset}",
                    "rules": "${validation_rules}"
                },
                "dependencies": []
            },
            {
                "id": "analyze_quality",
                "agent_name": "reconciler_agent",
                "task_type": "analyze_data_quality",
                "task_data": {
                    "dataset": "${dataset}",
                    "dimensions": ["completeness", "accuracy", "consistency"]
                },
                "dependencies": []
            },
            {
                "id": "suggest_corrections",
                "agent_name": "reconciler_agent",
                "task_type": "suggest_corrections",
                "task_data": {
                    "issues": "${step_detect_inconsistencies_result.inconsistencies}",
                    "dataset": "${dataset}"
                },
                "dependencies": ["detect_inconsistencies"]
            },
            {
                "id": "aggregate_quality_report",
                "agent_name": "aggregation_agent",
                "task_type": "generate_report",
                "task_data": {
                    "data_sources": [
                        "${step_detect_inconsistencies_result}",
                        "${step_analyze_quality_result}",
                        "${step_suggest_corrections_result}"
                    ],
                    "report_type": "data_quality"
                },
                "dependencies": ["detect_inconsistencies", "analyze_quality", "suggest_corrections"]
            }
        ],
        "max_parallel_steps": 2,
        "failure_strategy": "continue"
    }
    
    coordinator.register_workflow_template("data_reconciliation", data_reconciliation_template)


# Funções utilitárias

async def quick_classify_product(product_description: str, state: str = None) -> dict:
    """
    Função utilitária para classificação rápida de produto.
    
    Args:
        product_description: Descrição do produto
        state: Estado para classificação CEST (opcional)
        
    Returns:
        Resultado da classificação
    """
    # Criar agentes temporários
    expansion_agent = ExpansionAgent()
    ncm_agent = NCMAgent()
    cest_agent = CESTAgent() if state else None
    
    results = {}
    
    try:
        # Expandir descrição
        expansion_task = AgentTask(
            type="expand_description",
            data={"description": product_description}
        )
        results["expansion"] = await expansion_agent.process_task(expansion_task)
        
        # Classificar NCM
        ncm_task = AgentTask(
            type="classify_ncm",
            data={"description": results["expansion"]["expanded_description"]}
        )
        results["ncm"] = await ncm_agent.process_task(ncm_task)
        
        # Classificar CEST se estado fornecido
        if cest_agent and state:
            cest_task = AgentTask(
                type="classify_cest",
                data={
                    "description": results["expansion"]["expanded_description"],
                    "ncm_code": results["ncm"]["ncm_code"],
                    "state": state
                }
            )
            results["cest"] = await cest_agent.process_task(cest_task)
        
        return {
            "success": True,
            "results": results,
            "summary": {
                "product_description": product_description,
                "expanded_description": results["expansion"]["expanded_description"],
                "ncm_code": results["ncm"]["ncm_code"],
                "ncm_confidence": results["ncm"]["confidence"],
                "cest_code": results.get("cest", {}).get("cest_code"),
                "cest_confidence": results.get("cest", {}).get("confidence")
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "partial_results": results
        }


def get_agent_capabilities_summary() -> dict:
    """
    Retorna resumo das capacidades de todos os agentes.
    
    Returns:
        Dicionário com capacidades por agente
    """
    return {
        "ExpansionAgent": [
            "expand_description",
            "normalize_text", 
            "extract_features",
            "enrich_product_data",
            "identify_technical_specs",
            "suggest_synonyms"
        ],
        "AggregationAgent": [
            "consolidate_data",
            "aggregate_statistics",
            "detect_patterns", 
            "generate_report",
            "analyze_trends",
            "detect_anomalies"
        ],
        "NCMAgent": [
            "classify_ncm",
            "validate_ncm",
            "suggest_alternatives",
            "detect_inconsistencies",
            "explain_classification",
            "compare_ncm_codes"
        ],
        "CESTAgent": [
            "classify_cest",
            "validate_cest",
            "map_ncm_to_cest",
            "analyze_st_requirement",
            "suggest_alternatives",
            "detect_inconsistencies"
        ],
        "ReconcilerAgent": [
            "reconcile_datasets",
            "detect_inconsistencies",
            "validate_data_integrity", 
            "analyze_data_quality",
            "suggest_corrections",
            "merge_duplicate_records"
        ]
    }
