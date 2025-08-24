"""
Agent Manager - Gerenciador de Agentes
=====================================

Este componente é responsável por:
- Gerenciamento do ciclo de vida dos agentes
- Registro e descoberta de agentes
- Monitoramento de saúde e performance
- Balanceamento de carga entre agentes
- Configuração dinâmica de agentes
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Type, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import json

from .base_agent import BaseAgent, AgentTask, TaskPriority, AgentStatus


class AgentManager:
    """
    Gerenciador central para todos os agentes do sistema.
    
    Responsabilidades:
    - Registro e ciclo de vida dos agentes
    - Monitoramento de saúde e performance
    - Distribuição de tarefas
    - Configuração dinâmica
    - Coleta de métricas
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o gerenciador de agentes.
        
        Args:
            config: Configurações do gerenciador
        """
        self.config = config or {}
        
        # Registry de agentes
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_types: Dict[str, Type[BaseAgent]] = {}
        
        # Configurações de gerenciamento
        self.health_check_interval = self.config.get("health_check_interval", 30)
        self.max_retry_attempts = self.config.get("max_retry_attempts", 3)
        self.task_timeout = self.config.get("task_timeout", 300)
        
        # Métricas e monitoramento
        self.metrics = defaultdict(lambda: defaultdict(int))
        self.performance_history = defaultdict(list)
        self.health_status = {}
        
        # Tasks de gerenciamento
        self.management_tasks = set()
        self.is_running = False
        
        # Logger
        self.logger = logging.getLogger(__name__)
        self.logger.info("AgentManager inicializado")
    
    async def start(self) -> None:
        """Inicia o gerenciador de agentes."""
        if self.is_running:
            self.logger.warning("AgentManager já está rodando")
            return
        
        self.is_running = True
        self.logger.info("Iniciando AgentManager")
        
        # Iniciar tasks de gerenciamento
        await self._start_management_tasks()
        
        # Inicializar agentes registrados
        await self._initialize_registered_agents()
        
        self.logger.info("AgentManager iniciado com sucesso")
    
    async def stop(self) -> None:
        """Para o gerenciador e todos os agentes."""
        if not self.is_running:
            return
        
        self.logger.info("Parando AgentManager")
        self.is_running = False
        
        # Parar todos os agentes
        await self._stop_all_agents()
        
        # Cancelar tasks de gerenciamento
        await self._stop_management_tasks()
        
        self.logger.info("AgentManager parado")
    
    def register_agent_type(self, agent_type: Type[BaseAgent], name: Optional[str] = None) -> None:
        """
        Registra um tipo de agente no gerenciador.
        
        Args:
            agent_type: Classe do agente
            name: Nome do tipo (usa nome da classe se não fornecido)
        """
        type_name = name or agent_type.__name__
        self.agent_types[type_name] = agent_type
        self.logger.info(f"Tipo de agente registrado: {type_name}")
    
    async def create_agent(self, agent_type: str, agent_name: str, config: Optional[Dict[str, Any]] = None) -> str:
        """
        Cria uma instância de agente.
        
        Args:
            agent_type: Tipo do agente registrado
            agent_name: Nome único para a instância
            config: Configuração específica do agente
            
        Returns:
            ID do agente criado
        """
        if agent_type not in self.agent_types:
            raise ValueError(f"Tipo de agente não registrado: {agent_type}")
        
        if agent_name in self.agents:
            raise ValueError(f"Agente já existe: {agent_name}")
        
        # Criar instância do agente
        agent_class = self.agent_types[agent_type]
        agent_instance = agent_class(config)
        agent_instance.name = agent_name  # Sobrescrever nome se necessário
        
        # Registrar agente
        self.agents[agent_name] = agent_instance
        
        # Inicializar status de saúde
        self.health_status[agent_name] = {
            "status": "created",
            "last_check": datetime.now(),
            "consecutive_failures": 0
        }
        
        # Inicializar métricas
        self.metrics[agent_name] = defaultdict(int)
        self.performance_history[agent_name] = []
        
        self.logger.info(f"Agente criado: {agent_name} (tipo: {agent_type})")
        return agent_name
    
    async def start_agent(self, agent_name: str) -> None:
        """
        Inicia um agente específico.
        
        Args:
            agent_name: Nome do agente
        """
        if agent_name not in self.agents:
            raise ValueError(f"Agente não encontrado: {agent_name}")
        
        agent = self.agents[agent_name]
        
        try:
            await agent.start()
            self.health_status[agent_name]["status"] = "running"
            self.health_status[agent_name]["last_check"] = datetime.now()
            self.logger.info(f"Agente iniciado: {agent_name}")
        except Exception as e:
            self.health_status[agent_name]["status"] = "failed"
            self.logger.error(f"Erro ao iniciar agente {agent_name}: {e}")
            raise
    
    async def stop_agent(self, agent_name: str) -> None:
        """
        Para um agente específico.
        
        Args:
            agent_name: Nome do agente
        """
        if agent_name not in self.agents:
            raise ValueError(f"Agente não encontrado: {agent_name}")
        
        agent = self.agents[agent_name]
        
        try:
            await agent.stop()
            self.health_status[agent_name]["status"] = "stopped"
            self.health_status[agent_name]["last_check"] = datetime.now()
            self.logger.info(f"Agente parado: {agent_name}")
        except Exception as e:
            self.logger.error(f"Erro ao parar agente {agent_name}: {e}")
            raise
    
    async def remove_agent(self, agent_name: str) -> None:
        """
        Remove um agente do gerenciador.
        
        Args:
            agent_name: Nome do agente
        """
        if agent_name not in self.agents:
            raise ValueError(f"Agente não encontrado: {agent_name}")
        
        # Parar agente se estiver rodando
        agent = self.agents[agent_name]
        if agent.status != AgentStatus.STOPPED:
            await self.stop_agent(agent_name)
        
        # Remover do registry
        del self.agents[agent_name]
        del self.health_status[agent_name]
        del self.metrics[agent_name]
        del self.performance_history[agent_name]
        
        self.logger.info(f"Agente removido: {agent_name}")
    
    async def execute_task(self, agent_name: str, task: AgentTask) -> Dict[str, Any]:
        """
        Executa uma tarefa em um agente específico.
        
        Args:
            agent_name: Nome do agente
            task: Tarefa a ser executada
            
        Returns:
            Resultado da execução
        """
        if agent_name not in self.agents:
            raise ValueError(f"Agente não encontrado: {agent_name}")
        
        agent = self.agents[agent_name]
        
        # Verificar se agente está disponível
        if agent.status != AgentStatus.RUNNING:
            raise RuntimeError(f"Agente {agent_name} não está disponível (status: {agent.status})")
        
        start_time = datetime.now()
        
        try:
            # Executar tarefa com timeout
            result = await asyncio.wait_for(
                agent.process_task(task),
                timeout=self.task_timeout
            )
            
            # Registrar sucesso
            execution_time = (datetime.now() - start_time).total_seconds()
            await self._record_task_success(agent_name, task.type, execution_time)
            
            return result
            
        except asyncio.TimeoutError:
            await self._record_task_timeout(agent_name, task.type)
            raise RuntimeError(f"Timeout na execução da tarefa {task.type} no agente {agent_name}")
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            await self._record_task_failure(agent_name, task.type, execution_time, str(e))
            raise
    
    async def execute_task_with_retry(self, agent_name: str, task: AgentTask, max_retries: Optional[int] = None) -> Dict[str, Any]:
        """
        Executa uma tarefa com retry automático.
        
        Args:
            agent_name: Nome do agente
            task: Tarefa a ser executada
            max_retries: Número máximo de tentativas (usa config padrão se None)
            
        Returns:
            Resultado da execução
        """
        max_retries = max_retries or self.max_retry_attempts
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                result = await self.execute_task(agent_name, task)
                
                if attempt > 0:
                    self.logger.info(f"Tarefa {task.type} executada com sucesso após {attempt} tentativas")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Backoff exponencial
                    self.logger.warning(f"Tentativa {attempt + 1} falhou para {task.type}, tentando novamente em {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"Todas as {max_retries + 1} tentativas falharam para {task.type}")
        
        raise last_exception
    
    def get_agent_info(self, agent_name: str) -> Dict[str, Any]:
        """
        Obtém informações detalhadas de um agente.
        
        Args:
            agent_name: Nome do agente
            
        Returns:
            Informações do agente
        """
        if agent_name not in self.agents:
            raise ValueError(f"Agente não encontrado: {agent_name}")
        
        agent = self.agents[agent_name]
        health = self.health_status[agent_name]
        metrics = self.metrics[agent_name]
        
        return {
            "name": agent_name,
            "type": agent.__class__.__name__,
            "status": agent.status.value,
            "capabilities": agent.get_capabilities(),
            "health": health,
            "metrics": dict(metrics),
            "performance": self._get_performance_summary(agent_name),
            "config": agent.config,
            "created_at": agent.created_at.isoformat() if hasattr(agent, 'created_at') else None
        }
    
    def list_agents(self, status_filter: Optional[AgentStatus] = None) -> List[Dict[str, Any]]:
        """
        Lista todos os agentes registrados.
        
        Args:
            status_filter: Filtrar por status específico
            
        Returns:
            Lista de informações dos agentes
        """
        agents_info = []
        
        for agent_name, agent in self.agents.items():
            if status_filter is None or agent.status == status_filter:
                agents_info.append({
                    "name": agent_name,
                    "type": agent.__class__.__name__,
                    "status": agent.status.value,
                    "health": self.health_status[agent_name]["status"],
                    "tasks_completed": self.metrics[agent_name]["tasks_completed"],
                    "tasks_failed": self.metrics[agent_name]["tasks_failed"]
                })
        
        return agents_info
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Obtém métricas do sistema de agentes.
        
        Returns:
            Métricas consolidadas
        """
        total_agents = len(self.agents)
        running_agents = len([a for a in self.agents.values() if a.status == AgentStatus.RUNNING])
        
        total_tasks = sum(metrics["tasks_completed"] for metrics in self.metrics.values())
        total_failures = sum(metrics["tasks_failed"] for metrics in self.metrics.values())
        
        success_rate = (total_tasks / (total_tasks + total_failures)) * 100 if (total_tasks + total_failures) > 0 else 0
        
        # Calcular tempo médio de resposta
        all_response_times = []
        for agent_name in self.performance_history:
            all_response_times.extend([p["execution_time"] for p in self.performance_history[agent_name]])
        
        avg_response_time = sum(all_response_times) / len(all_response_times) if all_response_times else 0
        
        return {
            "system_overview": {
                "total_agents": total_agents,
                "running_agents": running_agents,
                "agent_types": len(self.agent_types),
                "uptime_percentage": (running_agents / total_agents) * 100 if total_agents > 0 else 0
            },
            "task_metrics": {
                "total_tasks_completed": total_tasks,
                "total_tasks_failed": total_failures,
                "success_rate_percentage": success_rate,
                "average_response_time_seconds": avg_response_time
            },
            "health_summary": self._get_health_summary(),
            "performance_trends": self._get_performance_trends(),
            "timestamp": datetime.now().isoformat()
        }
    
    async def update_agent_config(self, agent_name: str, new_config: Dict[str, Any]) -> None:
        """
        Atualiza configuração de um agente em tempo de execução.
        
        Args:
            agent_name: Nome do agente
            new_config: Nova configuração
        """
        if agent_name not in self.agents:
            raise ValueError(f"Agente não encontrado: {agent_name}")
        
        agent = self.agents[agent_name]
        
        # Validar nova configuração
        await self._validate_agent_config(agent, new_config)
        
        # Aplicar configuração
        agent.config.update(new_config)
        
        # Notificar agente sobre mudança de configuração
        if hasattr(agent, 'on_config_changed'):
            await agent.on_config_changed(new_config)
        
        self.logger.info(f"Configuração atualizada para agente {agent_name}")
    
    # Métodos privados de gerenciamento
    
    async def _start_management_tasks(self) -> None:
        """Inicia tasks de gerenciamento."""
        # Task de monitoramento de saúde
        health_task = asyncio.create_task(self._health_monitoring_loop())
        self.management_tasks.add(health_task)
        
        # Task de coleta de métricas
        metrics_task = asyncio.create_task(self._metrics_collection_loop())
        self.management_tasks.add(metrics_task)
        
        # Task de limpeza de histórico
        cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.management_tasks.add(cleanup_task)
    
    async def _stop_management_tasks(self) -> None:
        """Para todas as tasks de gerenciamento."""
        for task in self.management_tasks:
            task.cancel()
        
        # Aguardar cancelamento
        await asyncio.gather(*self.management_tasks, return_exceptions=True)
        self.management_tasks.clear()
    
    async def _initialize_registered_agents(self) -> None:
        """Inicializa agentes já registrados."""
        for agent_name in list(self.agents.keys()):
            try:
                await self.start_agent(agent_name)
            except Exception as e:
                self.logger.error(f"Erro ao inicializar agente {agent_name}: {e}")
    
    async def _stop_all_agents(self) -> None:
        """Para todos os agentes."""
        for agent_name in list(self.agents.keys()):
            try:
                await self.stop_agent(agent_name)
            except Exception as e:
                self.logger.error(f"Erro ao parar agente {agent_name}: {e}")
    
    async def _health_monitoring_loop(self) -> None:
        """Loop de monitoramento de saúde dos agentes."""
        while self.is_running:
            try:
                await self._check_all_agents_health()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                self.logger.error(f"Erro no monitoramento de saúde: {e}")
                await asyncio.sleep(5)  # Wait antes de tentar novamente
    
    async def _check_all_agents_health(self) -> None:
        """Verifica saúde de todos os agentes."""
        for agent_name, agent in self.agents.items():
            try:
                await self._check_agent_health(agent_name, agent)
            except Exception as e:
                self.logger.error(f"Erro ao verificar saúde do agente {agent_name}: {e}")
    
    async def _check_agent_health(self, agent_name: str, agent: BaseAgent) -> None:
        """Verifica saúde de um agente específico."""
        health_info = self.health_status[agent_name]
        
        try:
            # Verificar se agente responde
            is_healthy = await self._ping_agent(agent)
            
            if is_healthy:
                health_info["status"] = "healthy"
                health_info["consecutive_failures"] = 0
            else:
                health_info["consecutive_failures"] += 1
                
                if health_info["consecutive_failures"] >= 3:
                    health_info["status"] = "unhealthy"
                    await self._handle_unhealthy_agent(agent_name, agent)
                else:
                    health_info["status"] = "degraded"
            
            health_info["last_check"] = datetime.now()
            
        except Exception as e:
            health_info["consecutive_failures"] += 1
            health_info["status"] = "error"
            health_info["last_error"] = str(e)
            health_info["last_check"] = datetime.now()
    
    async def _ping_agent(self, agent: BaseAgent) -> bool:
        """Envia ping para verificar se agente responde."""
        try:
            # Verificar status básico
            if agent.status != AgentStatus.RUNNING:
                return False
            
            # Se agente tem método de health check customizado, usar
            if hasattr(agent, 'health_check'):
                return await agent.health_check()
            
            # Caso contrário, apenas verificar se está rodando
            return True
            
        except Exception:
            return False
    
    async def _handle_unhealthy_agent(self, agent_name: str, agent: BaseAgent) -> None:
        """Lida com agente não saudável."""
        self.logger.warning(f"Agente {agent_name} está não saudável, tentando recuperar")
        
        try:
            # Tentar reiniciar agente
            await self.stop_agent(agent_name)
            await asyncio.sleep(2)
            await self.start_agent(agent_name)
            
            self.logger.info(f"Agente {agent_name} reiniciado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Falha ao recuperar agente {agent_name}: {e}")
    
    async def _metrics_collection_loop(self) -> None:
        """Loop de coleta de métricas."""
        while self.is_running:
            try:
                await self._collect_agent_metrics()
                await asyncio.sleep(60)  # Coletar métricas a cada minuto
            except Exception as e:
                self.logger.error(f"Erro na coleta de métricas: {e}")
                await asyncio.sleep(10)
    
    async def _collect_agent_metrics(self) -> None:
        """Coleta métricas de todos os agentes."""
        for agent_name, agent in self.agents.items():
            try:
                # Coletar métricas básicas
                if hasattr(agent, 'get_metrics'):
                    agent_metrics = await agent.get_metrics()
                    self._update_agent_metrics(agent_name, agent_metrics)
                
            except Exception as e:
                self.logger.error(f"Erro ao coletar métricas do agente {agent_name}: {e}")
    
    def _update_agent_metrics(self, agent_name: str, new_metrics: Dict[str, Any]) -> None:
        """Atualiza métricas de um agente."""
        current_metrics = self.metrics[agent_name]
        
        for key, value in new_metrics.items():
            if isinstance(value, (int, float)):
                current_metrics[key] = value
    
    async def _cleanup_loop(self) -> None:
        """Loop de limpeza de dados antigos."""
        while self.is_running:
            try:
                await self._cleanup_old_data()
                await asyncio.sleep(3600)  # Limpeza a cada hora
            except Exception as e:
                self.logger.error(f"Erro na limpeza: {e}")
                await asyncio.sleep(300)
    
    async def _cleanup_old_data(self) -> None:
        """Remove dados antigos para evitar uso excessivo de memória."""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Limpar histórico de performance antigo
        for agent_name in self.performance_history:
            history = self.performance_history[agent_name]
            self.performance_history[agent_name] = [
                entry for entry in history 
                if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
            ]
    
    async def _record_task_success(self, agent_name: str, task_type: str, execution_time: float) -> None:
        """Registra sucesso de uma tarefa."""
        self.metrics[agent_name]["tasks_completed"] += 1
        self.metrics[agent_name][f"tasks_{task_type}_completed"] += 1
        
        # Adicionar ao histórico de performance
        self.performance_history[agent_name].append({
            "timestamp": datetime.now().isoformat(),
            "task_type": task_type,
            "execution_time": execution_time,
            "status": "success"
        })
    
    async def _record_task_failure(self, agent_name: str, task_type: str, execution_time: float, error: str) -> None:
        """Registra falha de uma tarefa."""
        self.metrics[agent_name]["tasks_failed"] += 1
        self.metrics[agent_name][f"tasks_{task_type}_failed"] += 1
        
        # Adicionar ao histórico de performance
        self.performance_history[agent_name].append({
            "timestamp": datetime.now().isoformat(),
            "task_type": task_type,
            "execution_time": execution_time,
            "status": "failed",
            "error": error
        })
    
    async def _record_task_timeout(self, agent_name: str, task_type: str) -> None:
        """Registra timeout de uma tarefa."""
        self.metrics[agent_name]["tasks_timeout"] += 1
        self.metrics[agent_name][f"tasks_{task_type}_timeout"] += 1
    
    def _get_performance_summary(self, agent_name: str) -> Dict[str, Any]:
        """Gera resumo de performance de um agente."""
        history = self.performance_history[agent_name]
        
        if not history:
            return {"status": "no_data"}
        
        recent_history = [
            entry for entry in history 
            if datetime.fromisoformat(entry["timestamp"]) > datetime.now() - timedelta(hours=1)
        ]
        
        if not recent_history:
            return {"status": "no_recent_data"}
        
        execution_times = [entry["execution_time"] for entry in recent_history]
        success_count = len([entry for entry in recent_history if entry["status"] == "success"])
        
        return {
            "recent_tasks": len(recent_history),
            "success_rate": (success_count / len(recent_history)) * 100,
            "avg_execution_time": sum(execution_times) / len(execution_times),
            "min_execution_time": min(execution_times),
            "max_execution_time": max(execution_times)
        }
    
    def _get_health_summary(self) -> Dict[str, Any]:
        """Gera resumo de saúde do sistema."""
        health_counts = defaultdict(int)
        
        for health_info in self.health_status.values():
            status = health_info["status"]
            health_counts[status] += 1
        
        return dict(health_counts)
    
    def _get_performance_trends(self) -> Dict[str, Any]:
        """Gera tendências de performance."""
        # Implementação simplificada
        return {
            "trend": "stable",
            "analysis": "Performance mantida estável nas últimas horas"
        }
    
    async def _validate_agent_config(self, agent: BaseAgent, config: Dict[str, Any]) -> None:
        """Valida configuração de agente."""
        # Implementação básica - pode ser expandida
        if hasattr(agent, 'validate_config'):
            await agent.validate_config(config)
