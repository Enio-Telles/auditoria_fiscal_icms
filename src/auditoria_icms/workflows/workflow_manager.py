"""
Workflow Manager - Orquestrador Principal dos Workflows LangGraph
Gerencia a seleção e execução dos workflows de confirmação e determinação
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
import asyncio
from datetime import datetime

from .base_workflow import WorkflowConfig, WorkflowState
from .confirmation_flow import ConfirmationFlow
from .determination_flow import DeterminationFlow
from ..core.config import get_workflow_config


class WorkflowType(Enum):
    """Tipos de workflow disponíveis"""
    CONFIRMATION = "confirmation"
    DETERMINATION = "determination"
    HYBRID = "hybrid"


@dataclass
class WorkflowResult:
    """Resultado da execução do workflow"""
    workflow_type: WorkflowType
    status: str
    final_result: Dict[str, Any]
    confidence: float
    requires_review: bool
    execution_time: float
    audit_trail: List[Dict[str, Any]]
    error: Optional[str] = None


class WorkflowManager:
    """
    Gerenciador principal dos workflows de classificação fiscal
    
    Responsabilidades:
    - Analisar produto e decidir qual workflow usar
    - Executar workflows de forma assíncrona
    - Gerenciar configurações e thresholds
    - Consolidar resultados e métricas
    """
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        self.config = config or get_workflow_config()
        self.confirmation_flow = ConfirmationFlow(self.config)
        self.determination_flow = DeterminationFlow(self.config)
        
        # Estatísticas de execução
        self.execution_stats = {
            "total_executions": 0,
            "confirmation_count": 0,
            "determination_count": 0,
            "hybrid_count": 0,
            "manual_review_count": 0,
            "success_rate": 0.0,
            "average_confidence": 0.0
        }
    
    async def process_product(
        self, 
        produto_dados: Dict[str, Any], 
        empresa_id: Optional[str] = None,
        force_workflow: Optional[WorkflowType] = None
    ) -> WorkflowResult:
        """
        Processa um produto através do workflow apropriado
        
        Args:
            produto_dados: Dados do produto a ser classificado
            empresa_id: ID da empresa (para contexto multi-tenant)
            force_workflow: Força uso de workflow específico (para testes)
            
        Returns:
            WorkflowResult com resultado da classificação
        """
        start_time = datetime.now()
        
        try:
            # Determinar tipo de workflow
            if force_workflow:
                workflow_type = force_workflow
            else:
                workflow_type = self._determine_workflow_type(produto_dados)
            
            # Preparar estado inicial
            initial_state = self._prepare_initial_state(produto_dados, empresa_id)
            
            # Executar workflow apropriado
            if workflow_type == WorkflowType.CONFIRMATION:
                final_state = await self._execute_confirmation_workflow(initial_state)
            elif workflow_type == WorkflowType.DETERMINATION:
                final_state = await self._execute_determination_workflow(initial_state)
            else:  # HYBRID
                final_state = await self._execute_hybrid_workflow(initial_state)
            
            # Calcular tempo de execução
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Criar resultado
            result = self._create_workflow_result(
                workflow_type, 
                final_state, 
                execution_time
            )
            
            # Atualizar estatísticas
            self._update_statistics(workflow_type, result)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return WorkflowResult(
                workflow_type=force_workflow or WorkflowType.DETERMINATION,
                status="ERROR",
                final_result={},
                confidence=0.0,
                requires_review=True,
                execution_time=execution_time,
                audit_trail=[],
                error=str(e)
            )
    
    async def process_batch(
        self, 
        produtos_list: List[Dict[str, Any]], 
        empresa_id: Optional[str] = None,
        max_concurrent: int = 5
    ) -> List[WorkflowResult]:
        """
        Processa múltiplos produtos em lote com controle de concorrência
        
        Args:
            produtos_list: Lista de produtos para classificar
            empresa_id: ID da empresa
            max_concurrent: Máximo de workflows concorrentes
            
        Returns:
            Lista de resultados de workflow
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single(produto_dados):
            async with semaphore:
                return await self.process_product(produto_dados, empresa_id)
        
        # Executar processamento concorrente
        tasks = [process_single(produto) for produto in produtos_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Converter exceções em resultados de erro
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(WorkflowResult(
                    workflow_type=WorkflowType.DETERMINATION,
                    status="ERROR",
                    final_result={},
                    confidence=0.0,
                    requires_review=True,
                    execution_time=0.0,
                    audit_trail=[],
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _determine_workflow_type(self, produto_dados: Dict[str, Any]) -> WorkflowType:
        """
        Determina qual tipo de workflow usar baseado nos dados do produto
        
        Lógica:
        - CONFIRMATION: Se NCM está presente e parece válido
        - DETERMINATION: Se NCM ausente ou claramente inadequado
        - HYBRID: Se situação ambígua que requer validação + determinação
        """
        ncm_informado = produto_dados.get("ncm_informado")
        cest_informado = produto_dados.get("cest_informado")
        
        # Verificar se NCM está presente e bem formado
        ncm_valid_format = self._is_valid_ncm_format(ncm_informado)
        
        # Análise heurística da qualidade da descrição
        description_quality = self._assess_description_quality(produto_dados)
        
        # Decisão baseada em múltiplos fatores
        if ncm_informado and ncm_valid_format:
            # NCM presente e válido - usar confirmação
            if description_quality > 0.7:
                return WorkflowType.CONFIRMATION
            else:
                # Descrição ruim pode indicar necessidade de re-determinação
                return WorkflowType.HYBRID
        else:
            # NCM ausente ou inválido - usar determinação
            return WorkflowType.DETERMINATION
    
    def _is_valid_ncm_format(self, ncm: Optional[str]) -> bool:
        """Verifica se NCM tem formato válido"""
        if not ncm:
            return False
        
        # Remover pontos e espaços
        ncm_clean = str(ncm).replace(".", "").replace(" ", "")
        
        # Verificar se tem 8 dígitos
        if len(ncm_clean) != 8:
            return False
        
        # Verificar se são todos números
        if not ncm_clean.isdigit():
            return False
        
        # Verificações básicas de estrutura hierárquica
        chapter = ncm_clean[:2]
        if chapter == "00":
            return False
        
        return True
    
    def _assess_description_quality(self, produto_dados: Dict[str, Any]) -> float:
        """Avalia qualidade da descrição do produto (0.0 a 1.0)"""
        score = 0.0
        
        descricao = produto_dados.get("descricao_original", "")
        if not descricao:
            return 0.0
        
        # Comprimento da descrição
        if len(descricao) > 10:
            score += 0.2
        if len(descricao) > 30:
            score += 0.2
        
        # Presença de palavras técnicas/específicas
        technical_indicators = [
            "mg", "ml", "kg", "g", "comprimido", "cápsula", "solução",
            "xarope", "pomada", "creme", "gel", "spray", "ampola"
        ]
        for indicator in technical_indicators:
            if indicator.lower() in descricao.lower():
                score += 0.1
                break
        
        # Presença de marca/fabricante
        if produto_dados.get("fabricante") or produto_dados.get("laboratorio"):
            score += 0.2
        
        # Presença de dosagem/concentração
        dosage_indicators = ["mg", "ml", "%", "ui", "mcg"]
        for indicator in dosage_indicators:
            if indicator in descricao.lower():
                score += 0.2
                break
        
        # Ausência de indicadores de qualidade ruim
        bad_indicators = ["diversos", "vários", "etc", "...", "s/d"]
        for indicator in bad_indicators:
            if indicator.lower() in descricao.lower():
                score -= 0.3
                break
        
        return min(1.0, max(0.0, score))
    
    def _prepare_initial_state(
        self, 
        produto_dados: Dict[str, Any], 
        empresa_id: Optional[str]
    ) -> Dict[str, Any]:
        """Prepara estado inicial do workflow"""
        return {
            "produto_dados": produto_dados.copy(),
            "empresa_id": empresa_id,
            "status": "INICIADO",
            "workflow_completed": False,
            "requires_human_review": False,
            "final_result": {},
            "final_confidence": 0.0,
            "audit_trail": [],
            "error": None,
            "timestamp": datetime.now().isoformat(),
            "workflow_id": f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "workflow_version": self.config.version
        }
    
    async def _execute_confirmation_workflow(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Executa workflow de confirmação"""
        graph = self.confirmation_flow.build_graph()
        
        # Executar workflow
        final_state = await graph.ainvoke(state)
        
        return final_state
    
    async def _execute_determination_workflow(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Executa workflow de determinação"""
        graph = self.determination_flow.build_graph()
        
        # Executar workflow
        final_state = await graph.ainvoke(state)
        
        return final_state
    
    async def _execute_hybrid_workflow(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa workflow híbrido: primeiro tenta confirmação, 
        se falhar executa determinação
        """
        try:
            # Tentar confirmação primeiro
            confirmation_state = await self._execute_confirmation_workflow(state.copy())
            
            # Se confirmação foi bem-sucedida e confiável, usar resultado
            if (confirmation_state.get("status") == "CONFIRMADO" and 
                confirmation_state.get("final_confidence", 0.0) >= self.config.confidence_threshold):
                return confirmation_state
            
            # Caso contrário, executar determinação
            state["hybrid_confirmation_attempted"] = True
            state["confirmation_result"] = confirmation_state.get("final_result", {})
            
            determination_state = await self._execute_determination_workflow(state)
            determination_state["workflow_type"] = "hybrid"
            
            return determination_state
            
        except Exception as e:
            # Em caso de erro, cair para determinação
            state["hybrid_error"] = str(e)
            return await self._execute_determination_workflow(state)
    
    def _create_workflow_result(
        self, 
        workflow_type: WorkflowType, 
        final_state: Dict[str, Any], 
        execution_time: float
    ) -> WorkflowResult:
        """Cria resultado do workflow"""
        return WorkflowResult(
            workflow_type=workflow_type,
            status=final_state.get("status", "UNKNOWN"),
            final_result=final_state.get("final_result", {}),
            confidence=final_state.get("final_confidence", 0.0),
            requires_review=final_state.get("requires_human_review", False),
            execution_time=execution_time,
            audit_trail=final_state.get("audit_trail", []),
            error=final_state.get("error")
        )
    
    def _update_statistics(self, workflow_type: WorkflowType, result: WorkflowResult):
        """Atualiza estatísticas de execução"""
        self.execution_stats["total_executions"] += 1
        
        if workflow_type == WorkflowType.CONFIRMATION:
            self.execution_stats["confirmation_count"] += 1
        elif workflow_type == WorkflowType.DETERMINATION:
            self.execution_stats["determination_count"] += 1
        else:
            self.execution_stats["hybrid_count"] += 1
        
        if result.requires_review:
            self.execution_stats["manual_review_count"] += 1
        
        # Calcular taxa de sucesso (sem erro e não requer revisão)
        success_count = (self.execution_stats["total_executions"] - 
                        self.execution_stats["manual_review_count"])
        self.execution_stats["success_rate"] = (
            success_count / self.execution_stats["total_executions"] if 
            self.execution_stats["total_executions"] > 0 else 0.0
        )
        
        # Calcular confiança média (média móvel simples)
        current_avg = self.execution_stats["average_confidence"]
        total = self.execution_stats["total_executions"]
        self.execution_stats["average_confidence"] = (
            (current_avg * (total - 1) + result.confidence) / total
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas de execução"""
        return self.execution_stats.copy()
    
    def reset_statistics(self):
        """Reseta estatísticas de execução"""
        self.execution_stats = {
            "total_executions": 0,
            "confirmation_count": 0,
            "determination_count": 0,
            "hybrid_count": 0,
            "manual_review_count": 0,
            "success_rate": 0.0,
            "average_confidence": 0.0
        }


# Instância global do workflow manager
workflow_manager = WorkflowManager()


async def classify_product(
    produto_dados: Dict[str, Any], 
    empresa_id: Optional[str] = None,
    force_workflow: Optional[str] = None
) -> WorkflowResult:
    """
    Função de conveniência para classificar um produto
    
    Args:
        produto_dados: Dados do produto
        empresa_id: ID da empresa
        force_workflow: Força workflow específico ("confirmation", "determination", "hybrid")
        
    Returns:
        Resultado da classificação
    """
    workflow_type = None
    if force_workflow:
        workflow_type = WorkflowType(force_workflow)
    
    return await workflow_manager.process_product(
        produto_dados, 
        empresa_id, 
        workflow_type
    )


async def classify_batch(
    produtos_list: List[Dict[str, Any]], 
    empresa_id: Optional[str] = None,
    max_concurrent: int = 5
) -> List[WorkflowResult]:
    """
    Função de conveniência para classificar múltiplos produtos
    
    Args:
        produtos_list: Lista de produtos
        empresa_id: ID da empresa
        max_concurrent: Máximo de workflows concorrentes
        
    Returns:
        Lista de resultados de classificação
    """
    return await workflow_manager.process_batch(
        produtos_list, 
        empresa_id, 
        max_concurrent
    )
