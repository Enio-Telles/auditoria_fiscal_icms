"""
Agent Coordinator - Coordenador de Workflows Multi-Agente
=========================================================

Este componente é responsável por:
- Orquestração de workflows complexos entre múltiplos agentes
- Definição e execução de pipelines de processamento
- Coordenação de dependências entre tarefas
- Monitoramento de progresso de workflows
- Recuperação de falhas e retry de workflows
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import json

from .base_agent import BaseAgent, AgentTask, TaskPriority
from .agent_manager import AgentManager


class WorkflowStatus(Enum):
    """Status de um workflow."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepStatus(Enum):
    """Status de um step do workflow."""
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """
    Representa um step em um workflow.
    """
    id: str
    agent_name: str
    task_type: str
    task_data: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    retry_attempts: int = 3
    timeout: Optional[int] = None
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    
    # Estado do step
    status: StepStatus = StepStatus.WAITING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempt_count: int = 0


@dataclass
class Workflow:
    """
    Representa um workflow completo.
    """
    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    
    # Configurações
    max_parallel_steps: int = 5
    global_timeout: Optional[int] = None
    failure_strategy: str = "stop"  # "stop", "continue", "retry_failed"
    
    # Estado do workflow
    status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class AgentCoordinator:
    """
    Coordenador responsável pela orquestração de workflows multi-agente.
    
    Funcionalidades:
    - Definição de workflows complexos
    - Execução paralela e sequencial de steps
    - Gerenciamento de dependências
    - Recuperação de falhas
    - Monitoramento de progresso
    """
    
    def __init__(self, agent_manager: AgentManager, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o coordenador de agentes.
        
        Args:
            agent_manager: Gerenciador de agentes
            config: Configurações do coordenador
        """
        self.agent_manager = agent_manager
        self.config = config or {}
        
        # Registry de workflows
        self.workflows: Dict[str, Workflow] = {}
        self.workflow_templates: Dict[str, Dict[str, Any]] = {}
        
        # Configurações
        self.max_concurrent_workflows = self.config.get("max_concurrent_workflows", 10)
        self.default_step_timeout = self.config.get("default_step_timeout", 300)
        self.monitoring_interval = self.config.get("monitoring_interval", 5)
        
        # Estado de execução
        self.running_workflows: Dict[str, asyncio.Task] = {}
        self.workflow_metrics = defaultdict(lambda: defaultdict(int))
        
        # Tasks de gerenciamento
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Logger
        self.logger = logging.getLogger(__name__)
        self.logger.info("AgentCoordinator inicializado")
    
    async def start(self) -> None:
        """Inicia o coordenador."""
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info("Iniciando AgentCoordinator")
        
        # Iniciar task de monitoramento
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        self.logger.info("AgentCoordinator iniciado")
    
    async def stop(self) -> None:
        """Para o coordenador e todos os workflows."""
        if not self.is_running:
            return
        
        self.logger.info("Parando AgentCoordinator")
        self.is_running = False
        
        # Cancelar todos os workflows em execução
        await self._cancel_all_workflows()
        
        # Parar task de monitoramento
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("AgentCoordinator parado")
    
    def register_workflow_template(self, template_name: str, template_definition: Dict[str, Any]) -> None:
        """
        Registra um template de workflow.
        
        Args:
            template_name: Nome do template
            template_definition: Definição do template
        """
        self.workflow_templates[template_name] = template_definition
        self.logger.info(f"Template de workflow registrado: {template_name}")
    
    async def create_workflow_from_template(self, template_name: str, workflow_id: str, 
                                          context: Dict[str, Any]) -> str:
        """
        Cria um workflow a partir de um template.
        
        Args:
            template_name: Nome do template
            workflow_id: ID único para o workflow
            context: Contexto inicial do workflow
            
        Returns:
            ID do workflow criado
        """
        if template_name not in self.workflow_templates:
            raise ValueError(f"Template não encontrado: {template_name}")
        
        template = self.workflow_templates[template_name]
        
        # Criar workflow a partir do template
        workflow = self._build_workflow_from_template(template, workflow_id, context)
        
        # Registrar workflow
        self.workflows[workflow_id] = workflow
        
        self.logger.info(f"Workflow criado a partir do template {template_name}: {workflow_id}")
        return workflow_id
    
    def create_workflow(self, workflow_id: str, name: str, description: str, 
                       steps: List[Dict[str, Any]], **kwargs) -> str:
        """
        Cria um workflow manualmente.
        
        Args:
            workflow_id: ID único para o workflow
            name: Nome do workflow
            description: Descrição do workflow
            steps: Lista de definições de steps
            **kwargs: Configurações adicionais
            
        Returns:
            ID do workflow criado
        """
        if workflow_id in self.workflows:
            raise ValueError(f"Workflow já existe: {workflow_id}")
        
        # Criar steps
        workflow_steps = []
        for step_def in steps:
            step = WorkflowStep(
                id=step_def["id"],
                agent_name=step_def["agent_name"],
                task_type=step_def["task_type"],
                task_data=step_def.get("task_data", {}),
                dependencies=step_def.get("dependencies", []),
                retry_attempts=step_def.get("retry_attempts", 3),
                timeout=step_def.get("timeout"),
                condition=step_def.get("condition")
            )
            workflow_steps.append(step)
        
        # Criar workflow
        workflow = Workflow(
            id=workflow_id,
            name=name,
            description=description,
            steps=workflow_steps,
            max_parallel_steps=kwargs.get("max_parallel_steps", 5),
            global_timeout=kwargs.get("global_timeout"),
            failure_strategy=kwargs.get("failure_strategy", "stop")
        )
        
        # Registrar workflow
        self.workflows[workflow_id] = workflow
        
        self.logger.info(f"Workflow criado: {workflow_id}")
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str, initial_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Executa um workflow.
        
        Args:
            workflow_id: ID do workflow
            initial_context: Contexto inicial adicional
            
        Returns:
            ID da execução
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow não encontrado: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        
        # Verificar se já está em execução
        if workflow_id in self.running_workflows:
            raise RuntimeError(f"Workflow já está em execução: {workflow_id}")
        
        # Verificar limite de workflows concorrentes
        if len(self.running_workflows) >= self.max_concurrent_workflows:
            raise RuntimeError("Limite de workflows concorrentes atingido")
        
        # Preparar contexto inicial
        if initial_context:
            workflow.context.update(initial_context)
        
        # Criar task de execução
        execution_task = asyncio.create_task(self._execute_workflow_internal(workflow))
        self.running_workflows[workflow_id] = execution_task
        
        self.logger.info(f"Execução de workflow iniciada: {workflow_id}")
        return workflow_id
    
    async def cancel_workflow(self, workflow_id: str) -> None:
        """
        Cancela a execução de um workflow.
        
        Args:
            workflow_id: ID do workflow
        """
        if workflow_id not in self.running_workflows:
            raise ValueError(f"Workflow não está em execução: {workflow_id}")
        
        # Cancelar task
        task = self.running_workflows[workflow_id]
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Atualizar status
        if workflow_id in self.workflows:
            self.workflows[workflow_id].status = WorkflowStatus.CANCELLED
            self.workflows[workflow_id].completed_at = datetime.now()
        
        # Remover do registry de execução
        del self.running_workflows[workflow_id]
        
        self.logger.info(f"Workflow cancelado: {workflow_id}")
    
    async def pause_workflow(self, workflow_id: str) -> None:
        """
        Pausa a execução de um workflow.
        
        Args:
            workflow_id: ID do workflow
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow não encontrado: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.PAUSED
        
        self.logger.info(f"Workflow pausado: {workflow_id}")
    
    async def resume_workflow(self, workflow_id: str) -> None:
        """
        Resume a execução de um workflow pausado.
        
        Args:
            workflow_id: ID do workflow
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow não encontrado: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        
        if workflow.status != WorkflowStatus.PAUSED:
            raise RuntimeError(f"Workflow não está pausado: {workflow_id}")
        
        workflow.status = WorkflowStatus.RUNNING
        
        self.logger.info(f"Workflow resumido: {workflow_id}")
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Obtém status detalhado de um workflow.
        
        Args:
            workflow_id: ID do workflow
            
        Returns:
            Status do workflow
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow não encontrado: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        
        # Calcular progresso
        total_steps = len(workflow.steps)
        completed_steps = len([s for s in workflow.steps if s.status == StepStatus.COMPLETED])
        progress = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
        
        # Calcular tempo decorrido
        elapsed_time = None
        if workflow.started_at:
            end_time = workflow.completed_at or datetime.now()
            elapsed_time = (end_time - workflow.started_at).total_seconds()
        
        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "progress_percentage": progress,
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "elapsed_time_seconds": elapsed_time,
            "error": workflow.error,
            "is_running": workflow_id in self.running_workflows,
            "steps": [self._get_step_status(step) for step in workflow.steps]
        }
    
    def list_workflows(self, status_filter: Optional[WorkflowStatus] = None) -> List[Dict[str, Any]]:
        """
        Lista todos os workflows.
        
        Args:
            status_filter: Filtrar por status específico
            
        Returns:
            Lista de workflows
        """
        workflows_info = []
        
        for workflow_id, workflow in self.workflows.items():
            if status_filter is None or workflow.status == status_filter:
                workflows_info.append({
                    "workflow_id": workflow_id,
                    "name": workflow.name,
                    "status": workflow.status.value,
                    "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
                    "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
                    "is_running": workflow_id in self.running_workflows,
                    "step_count": len(workflow.steps)
                })
        
        return workflows_info
    
    def get_workflow_metrics(self) -> Dict[str, Any]:
        """
        Obtém métricas dos workflows.
        
        Returns:
            Métricas consolidadas
        """
        total_workflows = len(self.workflows)
        running_workflows = len(self.running_workflows)
        
        status_counts = defaultdict(int)
        for workflow in self.workflows.values():
            status_counts[workflow.status.value] += 1
        
        # Calcular tempo médio de execução
        completed_workflows = [w for w in self.workflows.values() if w.status == WorkflowStatus.COMPLETED]
        
        avg_execution_time = 0
        if completed_workflows:
            execution_times = []
            for workflow in completed_workflows:
                if workflow.started_at and workflow.completed_at:
                    duration = (workflow.completed_at - workflow.started_at).total_seconds()
                    execution_times.append(duration)
            
            if execution_times:
                avg_execution_time = sum(execution_times) / len(execution_times)
        
        return {
            "overview": {
                "total_workflows": total_workflows,
                "running_workflows": running_workflows,
                "templates_registered": len(self.workflow_templates)
            },
            "status_distribution": dict(status_counts),
            "performance": {
                "average_execution_time_seconds": avg_execution_time,
                "completed_workflows": len(completed_workflows),
                "success_rate": (status_counts["completed"] / total_workflows) * 100 if total_workflows > 0 else 0
            },
            "resource_usage": {
                "concurrent_limit": self.max_concurrent_workflows,
                "current_usage": running_workflows,
                "usage_percentage": (running_workflows / self.max_concurrent_workflows) * 100
            }
        }
    
    # Métodos privados de execução
    
    async def _execute_workflow_internal(self, workflow: Workflow) -> None:
        """Execução interna de um workflow."""
        try:
            workflow.status = WorkflowStatus.RUNNING
            workflow.started_at = datetime.now()
            
            self.logger.info(f"Iniciando execução do workflow: {workflow.id}")
            
            # Executar steps
            await self._execute_workflow_steps(workflow)
            
            # Verificar se todos os steps foram completados
            failed_steps = [s for s in workflow.steps if s.status == StepStatus.FAILED]
            
            if failed_steps and workflow.failure_strategy == "stop":
                workflow.status = WorkflowStatus.FAILED
                workflow.error = f"Workflow falhou devido a {len(failed_steps)} steps com falha"
            else:
                workflow.status = WorkflowStatus.COMPLETED
            
            workflow.completed_at = datetime.now()
            
            self.logger.info(f"Workflow concluído: {workflow.id} (status: {workflow.status.value})")
            
        except asyncio.CancelledError:
            workflow.status = WorkflowStatus.CANCELLED
            workflow.completed_at = datetime.now()
            self.logger.info(f"Workflow cancelado: {workflow.id}")
            raise
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.error = str(e)
            workflow.completed_at = datetime.now()
            self.logger.error(f"Erro na execução do workflow {workflow.id}: {e}")
            
        finally:
            # Remover do registry de execução
            if workflow.id in self.running_workflows:
                del self.running_workflows[workflow.id]
    
    async def _execute_workflow_steps(self, workflow: Workflow) -> None:
        """Executa os steps do workflow."""
        completed_steps = set()
        semaphore = asyncio.Semaphore(workflow.max_parallel_steps)
        
        while True:
            # Verificar se workflow foi pausado
            if workflow.status == WorkflowStatus.PAUSED:
                await asyncio.sleep(1)
                continue
            
            # Encontrar steps prontos para execução
            ready_steps = self._find_ready_steps(workflow, completed_steps)
            
            if not ready_steps:
                # Verificar se todos os steps foram processados
                pending_steps = [s for s in workflow.steps if s.status in [StepStatus.WAITING, StepStatus.RUNNING]]
                if not pending_steps:
                    break
                
                # Aguardar um pouco antes de verificar novamente
                await asyncio.sleep(0.1)
                continue
            
            # Executar steps em paralelo
            tasks = []
            for step in ready_steps:
                task = asyncio.create_task(self._execute_step_with_semaphore(semaphore, workflow, step))
                tasks.append(task)
            
            # Aguardar conclusão dos steps
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # Atualizar lista de steps completados
            for step in workflow.steps:
                if step.status in [StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED]:
                    completed_steps.add(step.id)
    
    def _find_ready_steps(self, workflow: Workflow, completed_steps: set) -> List[WorkflowStep]:
        """Encontra steps prontos para execução."""
        ready_steps = []
        
        for step in workflow.steps:
            if step.status != StepStatus.WAITING:
                continue
            
            # Verificar se todas as dependências foram completadas
            dependencies_met = all(dep in completed_steps for dep in step.dependencies)
            
            if dependencies_met:
                # Verificar condição se especificada
                if step.condition and not step.condition(workflow.context):
                    step.status = StepStatus.SKIPPED
                    continue
                
                ready_steps.append(step)
        
        return ready_steps
    
    async def _execute_step_with_semaphore(self, semaphore: asyncio.Semaphore, 
                                         workflow: Workflow, step: WorkflowStep) -> None:
        """Executa um step com controle de concorrência."""
        async with semaphore:
            await self._execute_step(workflow, step)
    
    async def _execute_step(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Executa um step individual."""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()
        
        self.logger.info(f"Executando step {step.id} no agente {step.agent_name}")
        
        for attempt in range(step.retry_attempts + 1):
            step.attempt_count = attempt + 1
            
            try:
                # Preparar dados da tarefa com contexto
                task_data = self._prepare_task_data(step.task_data, workflow.context)
                
                # Criar tarefa
                task = AgentTask(
                    type=step.task_type,
                    data=task_data,
                    priority=TaskPriority.NORMAL
                )
                
                # Executar tarefa no agente
                if step.timeout:
                    result = await asyncio.wait_for(
                        self.agent_manager.execute_task(step.agent_name, task),
                        timeout=step.timeout
                    )
                else:
                    result = await self.agent_manager.execute_task(step.agent_name, task)
                
                # Sucesso
                step.result = result
                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.now()
                
                # Atualizar contexto do workflow com resultado
                self._update_workflow_context(workflow, step, result)
                
                self.logger.info(f"Step {step.id} completado com sucesso")
                return
                
            except asyncio.TimeoutError:
                error_msg = f"Timeout na execução do step {step.id}"
                step.error = error_msg
                self.logger.warning(f"{error_msg} (tentativa {attempt + 1})")
                
            except Exception as e:
                error_msg = f"Erro na execução do step {step.id}: {str(e)}"
                step.error = error_msg
                self.logger.warning(f"{error_msg} (tentativa {attempt + 1})")
            
            # Se não é a última tentativa, aguardar antes de tentar novamente
            if attempt < step.retry_attempts:
                await asyncio.sleep(2 ** attempt)  # Backoff exponencial
        
        # Todas as tentativas falharam
        step.status = StepStatus.FAILED
        step.completed_at = datetime.now()
        self.logger.error(f"Step {step.id} falhou após {step.retry_attempts + 1} tentativas")
    
    def _prepare_task_data(self, task_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara dados da tarefa substituindo variáveis do contexto."""
        prepared_data = {}
        
        for key, value in task_data.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # Substituir variável do contexto
                var_name = value[2:-1]
                if var_name in context:
                    prepared_data[key] = context[var_name]
                else:
                    prepared_data[key] = value  # Manter original se não encontrado
            else:
                prepared_data[key] = value
        
        return prepared_data
    
    def _update_workflow_context(self, workflow: Workflow, step: WorkflowStep, result: Dict[str, Any]) -> None:
        """Atualiza contexto do workflow com resultado do step."""
        # Adicionar resultado do step ao contexto
        workflow.context[f"step_{step.id}_result"] = result
        
        # Se resultado tem campos específicos, adicionar diretamente
        if isinstance(result, dict):
            for key, value in result.items():
                if not key.startswith("_"):  # Ignorar campos privados
                    workflow.context[key] = value
    
    def _get_step_status(self, step: WorkflowStep) -> Dict[str, Any]:
        """Obtém status detalhado de um step."""
        elapsed_time = None
        if step.started_at:
            end_time = step.completed_at or datetime.now()
            elapsed_time = (end_time - step.started_at).total_seconds()
        
        return {
            "id": step.id,
            "agent_name": step.agent_name,
            "task_type": step.task_type,
            "status": step.status.value,
            "dependencies": step.dependencies,
            "started_at": step.started_at.isoformat() if step.started_at else None,
            "completed_at": step.completed_at.isoformat() if step.completed_at else None,
            "elapsed_time_seconds": elapsed_time,
            "attempt_count": step.attempt_count,
            "retry_attempts": step.retry_attempts,
            "error": step.error
        }
    
    def _build_workflow_from_template(self, template: Dict[str, Any], workflow_id: str, 
                                    context: Dict[str, Any]) -> Workflow:
        """Constrói um workflow a partir de um template."""
        # Implementação simplificada - pode ser expandida para templates mais complexos
        
        steps_def = template.get("steps", [])
        workflow_steps = []
        
        for step_def in steps_def:
            step = WorkflowStep(
                id=step_def["id"],
                agent_name=step_def["agent_name"],
                task_type=step_def["task_type"],
                task_data=step_def.get("task_data", {}),
                dependencies=step_def.get("dependencies", []),
                retry_attempts=step_def.get("retry_attempts", 3),
                timeout=step_def.get("timeout")
            )
            workflow_steps.append(step)
        
        workflow = Workflow(
            id=workflow_id,
            name=template.get("name", workflow_id),
            description=template.get("description", ""),
            steps=workflow_steps,
            max_parallel_steps=template.get("max_parallel_steps", 5),
            global_timeout=template.get("global_timeout"),
            failure_strategy=template.get("failure_strategy", "stop"),
            context=context.copy()
        )
        
        return workflow
    
    async def _monitoring_loop(self) -> None:
        """Loop de monitoramento dos workflows."""
        while self.is_running:
            try:
                await self._monitor_workflows()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                self.logger.error(f"Erro no monitoramento de workflows: {e}")
                await asyncio.sleep(5)
    
    async def _monitor_workflows(self) -> None:
        """Monitora workflows em execução."""
        # Verificar workflows que podem ter travado
        current_time = datetime.now()
        
        for workflow_id, workflow in self.workflows.items():
            if workflow.status == WorkflowStatus.RUNNING:
                # Verificar timeout global
                if workflow.global_timeout and workflow.started_at:
                    elapsed = (current_time - workflow.started_at).total_seconds()
                    if elapsed > workflow.global_timeout:
                        self.logger.warning(f"Workflow {workflow_id} excedeu timeout global")
                        await self.cancel_workflow(workflow_id)
    
    async def _cancel_all_workflows(self) -> None:
        """Cancela todos os workflows em execução."""
        workflow_ids = list(self.running_workflows.keys())
        
        for workflow_id in workflow_ids:
            try:
                await self.cancel_workflow(workflow_id)
            except Exception as e:
                self.logger.error(f"Erro ao cancelar workflow {workflow_id}: {e}")
