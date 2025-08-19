"""
Workflow Orchestrator usando LangGraph para Sistema de Auditoria Fiscal ICMS
Implementa grafo de estados para processamento multi-tenant de produtos
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime
import logging
import json
from enum import Enum

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    # Implementação alternativa sem LangGraph
    LANGGRAPH_AVAILABLE = False
    logging.warning("LangGraph não disponível. Usando implementação alternativa.")

from .manager_agent_v2 import ManagerAgent
from .enrichment_agent import EnrichmentAgent
from .ncm_agent import NCMAgent
from .cest_agent import CESTAgent
from .reconciliation_agent import ReconciliationAgent
from ..database.models import ProdutoEmpresa

logger = logging.getLogger(__name__)

class ProcessingState(str, Enum):
    """Estados do workflow de processamento"""
    PENDENTE = "pendente"
    ENRIQUECENDO = "enriquecendo"
    ENRIQUECIDO = "enriquecido"
    CLASSIFICANDO_NCM = "classificando_ncm"
    NCM_CLASSIFICADO = "ncm_classificado"
    CLASSIFICANDO_CEST = "classificando_cest"
    CEST_CLASSIFICADO = "cest_classificado"
    RECONCILIANDO = "reconciliando"
    CONCLUIDO = "concluido"
    ERRO = "erro"
    REVISAO_MANUAL = "revisao_manual"

# Estado do workflow (para LangGraph)
class WorkflowState(TypedDict):
    """Estado compartilhado entre nós do workflow"""
    produto: ProdutoEmpresa
    empresa_id: int
    estado_atual: str
    descricao_enriquecida: Optional[str]
    ncm_sugerido: Optional[str]
    cest_sugerido: Optional[str]
    confianca_ncm: Optional[float]
    confianca_cest: Optional[float]
    justificativa_ncm: Optional[str]
    justificativa_cest: Optional[str]
    logs_processamento: List[Dict[str, Any]]
    erro_detalhes: Optional[str]
    requer_revisao: bool
    confianca_minima: float
    auto_approve_threshold: float

class FiscalAuditWorkflow:
    """
    Orquestrador de workflow para auditoria fiscal usando LangGraph
    """
    
    def __init__(self, 
                 empresa_id: int,
                 config: Optional[Dict[str, Any]] = None):
        
        self.empresa_id = empresa_id
        self.config = config or {}
        
        # Configurações do workflow
        self.workflow_config = {
            'confianca_minima': self.config.get('confianca_minima', 0.7),
            'auto_approve_threshold': self.config.get('auto_approve_threshold', 0.9),
            'max_retries': self.config.get('max_retries', 3),
            'enable_enrichment': self.config.get('enable_enrichment', True),
            'enable_ncm_classification': self.config.get('enable_ncm_classification', True),
            'enable_cest_classification': self.config.get('enable_cest_classification', True),
            'enable_reconciliation': self.config.get('enable_reconciliation', True)
        }
        
        # Inicializa agentes
        self.agents = {
            'enrichment': EnrichmentAgent(config=config),
            'ncm': NCMAgent(config=config),
            'cest': CESTAgent(config=config),
            'reconciliation': ReconciliationAgent(config=config)
        }
        
        # Cria o grafo do workflow
        if LANGGRAPH_AVAILABLE:
            self.workflow = self._create_langgraph_workflow()
        else:
            self.workflow = None
            logger.info("Usando implementação alternativa sem LangGraph")
    
    def _create_langgraph_workflow(self) -> StateGraph:
        """Cria o grafo do workflow usando LangGraph"""
        
        # Define o grafo
        workflow = StateGraph(WorkflowState)
        
        # Adiciona nós do workflow
        workflow.add_node("enriquecimento", self._node_enriquecimento)
        workflow.add_node("classificacao_ncm", self._node_classificacao_ncm)
        workflow.add_node("classificacao_cest", self._node_classificacao_cest)
        workflow.add_node("reconciliacao", self._node_reconciliacao)
        workflow.add_node("finalizacao", self._node_finalizacao)
        workflow.add_node("tratamento_erro", self._node_tratamento_erro)
        
        # Define ponto de entrada
        workflow.set_entry_point("enriquecimento")
        
        # Define transições condicionais
        workflow.add_conditional_edges(
            "enriquecimento",
            self._decide_after_enrichment,
            {
                "ncm": "classificacao_ncm",
                "erro": "tratamento_erro"
            }
        )
        
        workflow.add_conditional_edges(
            "classificacao_ncm",
            self._decide_after_ncm,
            {
                "cest": "classificacao_cest",
                "revisao": "finalizacao",
                "erro": "tratamento_erro"
            }
        )
        
        workflow.add_conditional_edges(
            "classificacao_cest",
            self._decide_after_cest,
            {
                "reconciliacao": "reconciliacao",
                "finalizacao": "finalizacao",
                "erro": "tratamento_erro"
            }
        )
        
        workflow.add_conditional_edges(
            "reconciliacao",
            self._decide_after_reconciliation,
            {
                "finalizacao": "finalizacao",
                "revisao": "finalizacao",
                "erro": "tratamento_erro"
            }
        )
        
        # Nós finais
        workflow.add_edge("finalizacao", END)
        workflow.add_edge("tratamento_erro", END)
        
        # Compila o workflow
        return workflow.compile(checkpointer=MemorySaver())
    
    def processar_produto(self, produto: ProdutoEmpresa) -> Dict[str, Any]:
        """
        Processa um produto através do workflow completo
        
        Args:
            produto: Produto a ser processado
            
        Returns:
            Resultado do processamento
        """
        
        inicio = datetime.utcnow()
        
        try:
            if LANGGRAPH_AVAILABLE and self.workflow:
                return self._processar_com_langgraph(produto)
            else:
                return self._processar_alternativo(produto)
                
        except Exception as e:
            logger.error(f"Erro no processamento do produto {produto.produto_id}: {str(e)}")
            
            fim = datetime.utcnow()
            tempo_execucao = (fim - inicio).total_seconds()
            
            return {
                'produto_id': produto.produto_id,
                'status': 'erro',
                'erro_detalhes': str(e),
                'tempo_execucao': tempo_execucao,
                'timestamp': fim.isoformat()
            }
    
    def _processar_com_langgraph(self, produto: ProdutoEmpresa) -> Dict[str, Any]:
        """Processa produto usando LangGraph"""
        
        # Estado inicial
        initial_state = WorkflowState(
            produto=produto,
            empresa_id=self.empresa_id,
            estado_atual=ProcessingState.PENDENTE.value,
            descricao_enriquecida=None,
            ncm_sugerido=None,
            cest_sugerido=None,
            confianca_ncm=None,
            confianca_cest=None,
            justificativa_ncm=None,
            justificativa_cest=None,
            logs_processamento=[],
            erro_detalhes=None,
            requer_revisao=False,
            confianca_minima=self.workflow_config['confianca_minima'],
            auto_approve_threshold=self.workflow_config['auto_approve_threshold']
        )
        
        # Executa o workflow
        result = self.workflow.invoke(initial_state)
        
        # Converte resultado
        return self._converter_resultado_langgraph(result)
    
    def _processar_alternativo(self, produto: ProdutoEmpresa) -> Dict[str, Any]:
        """Processamento alternativo sem LangGraph"""
        
        inicio = datetime.utcnow()
        logs_processamento = []
        
        try:
            # Estado do produto
            produto_processado = produto
            
            # Etapa 1: Enriquecimento
            if self.workflow_config['enable_enrichment']:
                resultado_enrich = self._executar_enriquecimento(produto_processado)
                logs_processamento.append(resultado_enrich)
                
                if resultado_enrich['status'] == 'sucesso':
                    produto_processado.descricao_enriquecida = resultado_enrich['resultado']['descricao_enriquecida']
            
            # Etapa 2: Classificação NCM
            if self.workflow_config['enable_ncm_classification']:
                resultado_ncm = self._executar_classificacao_ncm(produto_processado)
                logs_processamento.append(resultado_ncm)
                
                if resultado_ncm['status'] == 'sucesso':
                    produto_processado.ncm_sugerido = resultado_ncm['resultado']['ncm']
                    produto_processado.confianca_ncm = resultado_ncm['resultado']['confianca']
                    produto_processado.justificativa_ncm = resultado_ncm['resultado']['justificativa']
            
            # Etapa 3: Classificação CEST
            if self.workflow_config['enable_cest_classification']:
                resultado_cest = self._executar_classificacao_cest(produto_processado)
                logs_processamento.append(resultado_cest)
                
                if resultado_cest['status'] == 'sucesso':
                    produto_processado.cest_sugerido = resultado_cest['resultado']['cest']
                    produto_processado.confianca_cest = resultado_cest['resultado']['confianca']
                    produto_processado.justificativa_cest = resultado_cest['resultado']['justificativa']
            
            # Etapa 4: Reconciliação
            if self.workflow_config['enable_reconciliation']:
                resultado_reconcil = self._executar_reconciliacao(produto_processado)
                logs_processamento.append(resultado_reconcil)
            
            # Determina se requer revisão
            confianca_ncm = getattr(produto_processado, 'confianca_ncm', 0.0) or 0.0
            confianca_cest = getattr(produto_processado, 'confianca_cest', 0.0) or 0.0
            confianca_media = (confianca_ncm + confianca_cest) / 2
            
            requer_revisao = confianca_media < self.workflow_config['confianca_minima']
            
            fim = datetime.utcnow()
            tempo_execucao = (fim - inicio).total_seconds()
            
            return {
                'produto_id': produto.produto_id,
                'status': 'sucesso',
                'produto_processado': produto_processado,
                'requer_revisao': requer_revisao,
                'confianca_media': confianca_media,
                'logs_processamento': logs_processamento,
                'tempo_execucao': tempo_execucao,
                'timestamp': fim.isoformat()
            }
            
        except Exception as e:
            fim = datetime.utcnow()
            tempo_execucao = (fim - inicio).total_seconds()
            
            return {
                'produto_id': produto.produto_id,
                'status': 'erro',
                'erro_detalhes': str(e),
                'logs_processamento': logs_processamento,
                'tempo_execucao': tempo_execucao,
                'timestamp': fim.isoformat()
            }
    
    # Nós do LangGraph
    def _node_enriquecimento(self, state: WorkflowState) -> WorkflowState:
        """Nó de enriquecimento da descrição"""
        
        try:
            if not self.workflow_config['enable_enrichment']:
                state['estado_atual'] = ProcessingState.ENRIQUECIDO.value
                return state
            
            resultado = self._executar_enriquecimento(state['produto'])
            
            if resultado['status'] == 'sucesso':
                state['descricao_enriquecida'] = resultado['resultado']['descricao_enriquecida']
                state['estado_atual'] = ProcessingState.ENRIQUECIDO.value
            else:
                state['estado_atual'] = ProcessingState.ERRO.value
                state['erro_detalhes'] = resultado.get('erro', 'Erro no enriquecimento')
            
            state['logs_processamento'].append(resultado)
            
        except Exception as e:
            state['estado_atual'] = ProcessingState.ERRO.value
            state['erro_detalhes'] = str(e)
        
        return state
    
    def _node_classificacao_ncm(self, state: WorkflowState) -> WorkflowState:
        """Nó de classificação NCM"""
        
        try:
            if not self.workflow_config['enable_ncm_classification']:
                state['estado_atual'] = ProcessingState.NCM_CLASSIFICADO.value
                return state
            
            resultado = self._executar_classificacao_ncm(state['produto'])
            
            if resultado['status'] == 'sucesso':
                state['ncm_sugerido'] = resultado['resultado']['ncm']
                state['confianca_ncm'] = resultado['resultado']['confianca']
                state['justificativa_ncm'] = resultado['resultado']['justificativa']
                state['estado_atual'] = ProcessingState.NCM_CLASSIFICADO.value
                
                # Verifica se confiança é suficiente
                if state['confianca_ncm'] < state['confianca_minima']:
                    state['requer_revisao'] = True
            else:
                state['estado_atual'] = ProcessingState.ERRO.value
                state['erro_detalhes'] = resultado.get('erro', 'Erro na classificação NCM')
            
            state['logs_processamento'].append(resultado)
            
        except Exception as e:
            state['estado_atual'] = ProcessingState.ERRO.value
            state['erro_detalhes'] = str(e)
        
        return state
    
    def _node_classificacao_cest(self, state: WorkflowState) -> WorkflowState:
        """Nó de classificação CEST"""
        
        try:
            if not self.workflow_config['enable_cest_classification']:
                state['estado_atual'] = ProcessingState.CEST_CLASSIFICADO.value
                return state
            
            resultado = self._executar_classificacao_cest(state['produto'])
            
            if resultado['status'] == 'sucesso':
                state['cest_sugerido'] = resultado['resultado']['cest']
                state['confianca_cest'] = resultado['resultado']['confianca']
                state['justificativa_cest'] = resultado['resultado']['justificativa']
                state['estado_atual'] = ProcessingState.CEST_CLASSIFICADO.value
            else:
                state['estado_atual'] = ProcessingState.ERRO.value
                state['erro_detalhes'] = resultado.get('erro', 'Erro na classificação CEST')
            
            state['logs_processamento'].append(resultado)
            
        except Exception as e:
            state['estado_atual'] = ProcessingState.ERRO.value
            state['erro_detalhes'] = str(e)
        
        return state
    
    def _node_reconciliacao(self, state: WorkflowState) -> WorkflowState:
        """Nó de reconciliação e validação"""
        
        try:
            if not self.workflow_config['enable_reconciliation']:
                state['estado_atual'] = ProcessingState.CONCLUIDO.value
                return state
            
            resultado = self._executar_reconciliacao(state['produto'])
            
            if resultado['status'] == 'sucesso':
                state['estado_atual'] = ProcessingState.CONCLUIDO.value
                
                # Calcula confiança final
                confianca_ncm = state.get('confianca_ncm', 0.0) or 0.0
                confianca_cest = state.get('confianca_cest', 0.0) or 0.0
                confianca_media = (confianca_ncm + confianca_cest) / 2
                
                # Determina se precisa de aprovação automática
                if confianca_media >= state['auto_approve_threshold']:
                    state['requer_revisao'] = False
                else:
                    state['requer_revisao'] = True
            else:
                state['estado_atual'] = ProcessingState.ERRO.value
                state['erro_detalhes'] = resultado.get('erro', 'Erro na reconciliação')
            
            state['logs_processamento'].append(resultado)
            
        except Exception as e:
            state['estado_atual'] = ProcessingState.ERRO.value
            state['erro_detalhes'] = str(e)
        
        return state
    
    def _node_finalizacao(self, state: WorkflowState) -> WorkflowState:
        """Nó de finalização do processamento"""
        
        if state['requer_revisao']:
            state['estado_atual'] = ProcessingState.REVISAO_MANUAL.value
        else:
            state['estado_atual'] = ProcessingState.CONCLUIDO.value
        
        return state
    
    def _node_tratamento_erro(self, state: WorkflowState) -> WorkflowState:
        """Nó de tratamento de erros"""
        
        state['estado_atual'] = ProcessingState.ERRO.value
        
        # Log do erro
        log_erro = {
            'etapa': 'tratamento_erro',
            'status': 'erro',
            'erro_detalhes': state.get('erro_detalhes', 'Erro desconhecido'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        state['logs_processamento'].append(log_erro)
        
        return state
    
    # Funções de decisão para LangGraph
    def _decide_after_enrichment(self, state: WorkflowState) -> str:
        """Decide próximo passo após enriquecimento"""
        if state['estado_atual'] == ProcessingState.ERRO.value:
            return "erro"
        return "ncm"
    
    def _decide_after_ncm(self, state: WorkflowState) -> str:
        """Decide próximo passo após classificação NCM"""
        if state['estado_atual'] == ProcessingState.ERRO.value:
            return "erro"
        if state['requer_revisao']:
            return "revisao"
        return "cest"
    
    def _decide_after_cest(self, state: WorkflowState) -> str:
        """Decide próximo passo após classificação CEST"""
        if state['estado_atual'] == ProcessingState.ERRO.value:
            return "erro"
        if self.workflow_config['enable_reconciliation']:
            return "reconciliacao"
        return "finalizacao"
    
    def _decide_after_reconciliation(self, state: WorkflowState) -> str:
        """Decide próximo passo após reconciliação"""
        if state['estado_atual'] == ProcessingState.ERRO.value:
            return "erro"
        if state['requer_revisao']:
            return "revisao"
        return "finalizacao"
    
    # Métodos de execução dos agentes (simulação)
    def _executar_enriquecimento(self, produto: ProdutoEmpresa) -> Dict[str, Any]:
        """Executa enriquecimento da descrição"""
        try:
            # Simula execução do agente de enriquecimento
            descricao_original = getattr(produto, 'descricao_produto', '')
            descricao_enriquecida = f"{descricao_original} - produto enriquecido com análise semântica"
            
            return {
                'etapa': 'enriquecimento',
                'status': 'sucesso',
                'resultado': {
                    'descricao_enriquecida': descricao_enriquecida,
                    'confianca': 0.85
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'etapa': 'enriquecimento',
                'status': 'erro',
                'erro': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _executar_classificacao_ncm(self, produto: ProdutoEmpresa) -> Dict[str, Any]:
        """Executa classificação NCM"""
        try:
            # Simula execução do agente NCM
            return {
                'etapa': 'classificacao_ncm',
                'status': 'sucesso',
                'resultado': {
                    'ncm': '12345678',
                    'confianca': 0.90,
                    'justificativa': 'Classificação baseada em análise da descrição enriquecida'
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'etapa': 'classificacao_ncm',
                'status': 'erro',
                'erro': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _executar_classificacao_cest(self, produto: ProdutoEmpresa) -> Dict[str, Any]:
        """Executa classificação CEST"""
        try:
            # Simula execução do agente CEST
            return {
                'etapa': 'classificacao_cest',
                'status': 'sucesso',
                'resultado': {
                    'cest': '12.345.67',
                    'confianca': 0.85,
                    'justificativa': 'CEST determinado com base no NCM classificado'
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'etapa': 'classificacao_cest',
                'status': 'erro',
                'erro': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _executar_reconciliacao(self, produto: ProdutoEmpresa) -> Dict[str, Any]:
        """Executa reconciliação e validação"""
        try:
            # Simula execução do agente de reconciliação
            return {
                'etapa': 'reconciliacao',
                'status': 'sucesso',
                'resultado': {
                    'validacao_consistencia': True,
                    'observacoes': 'Classificações NCM e CEST consistentes',
                    'confianca': 0.88
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'etapa': 'reconciliacao',
                'status': 'erro',
                'erro': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _converter_resultado_langgraph(self, resultado_langgraph: Dict[str, Any]) -> Dict[str, Any]:
        """Converte resultado do LangGraph para formato padrão"""
        
        return {
            'produto_id': resultado_langgraph['produto'].produto_id,
            'status': 'sucesso' if resultado_langgraph['estado_atual'] == ProcessingState.CONCLUIDO.value else 'erro',
            'estado_final': resultado_langgraph['estado_atual'],
            'descricao_enriquecida': resultado_langgraph.get('descricao_enriquecida'),
            'ncm_sugerido': resultado_langgraph.get('ncm_sugerido'),
            'cest_sugerido': resultado_langgraph.get('cest_sugerido'),
            'confianca_ncm': resultado_langgraph.get('confianca_ncm'),
            'confianca_cest': resultado_langgraph.get('confianca_cest'),
            'justificativa_ncm': resultado_langgraph.get('justificativa_ncm'),
            'justificativa_cest': resultado_langgraph.get('justificativa_cest'),
            'requer_revisao': resultado_langgraph.get('requer_revisao', False),
            'logs_processamento': resultado_langgraph.get('logs_processamento', []),
            'erro_detalhes': resultado_langgraph.get('erro_detalhes'),
            'timestamp': datetime.utcnow().isoformat()
        }

# Função factory para criar workflow
def create_fiscal_workflow(empresa_id: int, 
                          config: Optional[Dict[str, Any]] = None) -> FiscalAuditWorkflow:
    """Cria uma instância do workflow de auditoria fiscal"""
    
    return FiscalAuditWorkflow(empresa_id=empresa_id, config=config)
