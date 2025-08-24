"""
Base Agent - Classe base para todos os agentes especializados
============================================================

Esta classe define a interface comum e funcionalidades base para todos
os agentes do sistema de auditoria fiscal.
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
import json

class AgentStatus(Enum):
    """Status possíveis de um agente"""
    IDLE = "idle"
    WORKING = "working"
    ERROR = "error"
    DISABLED = "disabled"

class TaskPriority(Enum):
    """Prioridades de tarefas"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

@dataclass
class AgentTask:
    """Representa uma tarefa para ser executada por um agente"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3

@dataclass
class AgentMessage:
    """Mensagem entre agentes"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    receiver: str = ""
    type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

class BaseAgent(ABC):
    """
    Classe base para todos os agentes especializados.
    
    Cada agente herda desta classe e implementa seus métodos específicos
    para processamento de dados e tarefas relacionadas à auditoria fiscal.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o agente base.
        
        Args:
            name: Nome único do agente
            config: Configurações específicas do agente
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self.tasks_queue: List[AgentTask] = []
        self.current_task: Optional[AgentTask] = None
        self.completed_tasks: List[AgentTask] = []
        self.messages_inbox: List[AgentMessage] = []
        self.messages_outbox: List[AgentMessage] = []
        
        # Configurar logging
        self.logger = logging.getLogger(f"agents.{self.name}")
        self.logger.setLevel(logging.INFO)
        
        # Estatísticas
        self.stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_processing_time": 0.0,
            "last_activity": None,
            "uptime_start": datetime.now()
        }
        
        self.logger.info(f"Agente {self.name} inicializado com ID {self.id}")
    
    @abstractmethod
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Processa uma tarefa específica do agente.
        
        Este método deve ser implementado por cada agente especializado.
        
        Args:
            task: Tarefa a ser processada
            
        Returns:
            Resultado do processamento
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Retorna lista de capacidades/tipos de tarefas que o agente pode executar.
        
        Returns:
            Lista de strings representando as capacidades
        """
        pass
    
    async def add_task(self, task: AgentTask) -> str:
        """
        Adiciona uma tarefa à fila do agente.
        
        Args:
            task: Tarefa a ser adicionada
            
        Returns:
            ID da tarefa adicionada
        """
        # Ordenar por prioridade
        self.tasks_queue.append(task)
        self.tasks_queue.sort(key=lambda t: t.priority.value, reverse=True)
        
        self.logger.info(f"Tarefa {task.id} adicionada à fila (prioridade: {task.priority.name})")
        return task.id
    
    async def process_next_task(self) -> Optional[Dict[str, Any]]:
        """
        Processa a próxima tarefa da fila.
        
        Returns:
            Resultado do processamento ou None se não houver tarefas
        """
        if not self.tasks_queue:
            return None
        
        task = self.tasks_queue.pop(0)
        self.current_task = task
        self.status = AgentStatus.WORKING
        
        task.started_at = datetime.now()
        
        try:
            self.logger.info(f"Iniciando processamento da tarefa {task.id}")
            
            # Processar tarefa
            result = await self.process_task(task)
            
            # Atualizar tarefa
            task.completed_at = datetime.now()
            task.result = result
            
            # Atualizar estatísticas
            processing_time = (task.completed_at - task.started_at).total_seconds()
            self.stats["tasks_completed"] += 1
            self.stats["total_processing_time"] += processing_time
            self.stats["last_activity"] = datetime.now()
            
            # Mover para concluídas
            self.completed_tasks.append(task)
            
            self.logger.info(f"Tarefa {task.id} concluída em {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            # Tratamento de erro
            task.error = str(e)
            task.retries += 1
            
            self.logger.error(f"Erro ao processar tarefa {task.id}: {e}")
            
            # Retry logic
            if task.retries < task.max_retries:
                self.logger.info(f"Recolocando tarefa {task.id} na fila (tentativa {task.retries + 1})")
                self.tasks_queue.insert(0, task)  # Prioridade alta para retry
            else:
                self.logger.error(f"Tarefa {task.id} falhou após {task.max_retries} tentativas")
                self.stats["tasks_failed"] += 1
                self.completed_tasks.append(task)
            
            self.status = AgentStatus.ERROR
            raise
        
        finally:
            self.current_task = None
            if not self.tasks_queue:
                self.status = AgentStatus.IDLE
    
    async def send_message(self, receiver: str, message_type: str, payload: Dict[str, Any]) -> str:
        """
        Envia mensagem para outro agente.
        
        Args:
            receiver: Nome do agente destinatário
            message_type: Tipo da mensagem
            payload: Dados da mensagem
            
        Returns:
            ID da mensagem enviada
        """
        message = AgentMessage(
            sender=self.name,
            receiver=receiver,
            type=message_type,
            payload=payload
        )
        
        self.messages_outbox.append(message)
        self.logger.info(f"Mensagem {message.id} enviada para {receiver}")
        
        return message.id
    
    async def receive_message(self, message: AgentMessage):
        """
        Recebe uma mensagem de outro agente.
        
        Args:
            message: Mensagem recebida
        """
        self.messages_inbox.append(message)
        self.logger.info(f"Mensagem {message.id} recebida de {message.sender}")
        
        # Processar mensagem se necessário
        await self.handle_message(message)
    
    async def handle_message(self, message: AgentMessage):
        """
        Processa uma mensagem recebida.
        
        Pode ser sobrescrito por agentes específicos para comportamentos customizados.
        
        Args:
            message: Mensagem a ser processada
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retorna status atual do agente.
        
        Returns:
            Dicionário com informações de status
        """
        uptime = (datetime.now() - self.stats["uptime_start"]).total_seconds()
        
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "current_task": self.current_task.id if self.current_task else None,
            "tasks_in_queue": len(self.tasks_queue),
            "capabilities": self.get_capabilities(),
            "stats": {
                **self.stats,
                "uptime_seconds": uptime,
                "avg_processing_time": (
                    self.stats["total_processing_time"] / max(1, self.stats["tasks_completed"])
                )
            }
        }
    
    def get_task_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retorna histórico de tarefas completadas.
        
        Args:
            limit: Número máximo de tarefas a retornar
            
        Returns:
            Lista de tarefas completadas
        """
        recent_tasks = self.completed_tasks[-limit:] if limit > 0 else self.completed_tasks
        
        return [
            {
                "id": task.id,
                "type": task.type,
                "priority": task.priority.name,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "processing_time": (
                    (task.completed_at - task.started_at).total_seconds()
                    if task.completed_at and task.started_at else None
                ),
                "success": task.error is None,
                "error": task.error,
                "retries": task.retries
            }
            for task in recent_tasks
        ]
    
    async def start(self):
        """
        Inicia o loop principal do agente.
        """
        self.logger.info(f"Agente {self.name} iniciado")
        
        while True:
            try:
                if self.status != AgentStatus.DISABLED:
                    await self.process_next_task()
                
                # Pequena pausa para evitar uso excessivo de CPU
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Erro no loop principal: {e}")
                self.status = AgentStatus.ERROR
                await asyncio.sleep(1)  # Pausa maior em caso de erro
    
    async def stop(self):
        """
        Para o agente graciosamente.
        """
        self.status = AgentStatus.DISABLED
        self.logger.info(f"Agente {self.name} parado")
    
    def export_config(self) -> Dict[str, Any]:
        """
        Exporta configuração atual do agente.
        
        Returns:
            Configuração do agente
        """
        return {
            "name": self.name,
            "config": self.config,
            "capabilities": self.get_capabilities()
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', status='{self.status.value}')>"
