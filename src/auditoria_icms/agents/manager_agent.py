"""
Agente Gerenciador (Manager Agent) - Orquestrador Principal
Responsável por coordenar todos os outros agentes e tomar decisões finais.
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_agent import BaseAgent, AgentDecision, AuditTrail


class ManagerAgent(BaseAgent):
    """
    Agente Gerenciador que orquestra todo o fluxo de classificação fiscal.
    Coordena os agentes especializados e toma decisões de nível superior.
    """
    
    def __init__(self, llm, config: Dict[str, Any], logger=None):
        super().__init__("ManagerAgent", llm, config, logger)
        self.specialist_agents = {}
        self.workflow_patterns = {
            "confirmation": ["enrichment", "ncm_classifier", "cest_classifier", "reconciliation"],
            "determination": ["enrichment", "ncm_classifier", "cest_classifier", "reconciliation"],
            "validation": ["ncm_classifier", "cest_classifier", "reconciliation"]
        }
        
    def register_agent(self, agent_type: str, agent: BaseAgent):
        """Registra um agente especialista no sistema."""
        self.specialist_agents[agent_type] = agent
        self.logger.info(f"Agente {agent_type} registrado: {agent.name}")
        
    async def process(
        self, 
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processa uma solicitação de classificação fiscal coordenando todos os agentes.
        
        Args:
            input_data: Dados do produto para classificação
            context: Contexto da empresa e usuário
            
        Returns:
            Resultado completo da classificação com trilha de auditoria
        """
        start_time = time.time()
        
        # Validação de entrada
        if not self.validate_input(input_data):
            raise ValueError("Dados de entrada inválidos para o ManagerAgent")
        
        # Determinar tipo de workflow baseado no contexto
        workflow_type = self._determine_workflow_type(input_data, context)
        
        # Inicializar trilha de auditoria
        audit_trail = AuditTrail(
            session_id=context.get('session_id', 'unknown'),
            product_id=input_data.get('produto_id', 'unknown'),
            empresa_id=context.get('empresa_id', 0),
            agent_decisions=[],
            final_classification={},
            human_review_required=False,
            created_at=datetime.now()
        )
        
        # Executar workflow de agentes
        workflow_result = await self._execute_workflow(
            workflow_type, 
            input_data, 
            context, 
            audit_trail
        )
        
        # Análise de consenso e decisão final
        final_decision = await self._make_final_decision(workflow_result, audit_trail)
        
        # Determinar se requer revisão humana
        requires_review = self._requires_human_review(final_decision, audit_trail)
        audit_trail.human_review_required = requires_review
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Criar registro de decisão do manager
        manager_decision = self.create_decision_record(
            input_data=input_data,
            output_data=final_decision,
            reasoning=self._generate_reasoning(workflow_result, final_decision),
            confidence_score=final_decision.get('confidence_score', 0.0),
            sources_used=self._aggregate_sources(audit_trail),
            processing_time_ms=processing_time
        )
        
        audit_trail.agent_decisions.append(manager_decision)
        audit_trail.final_classification = final_decision
        
        return {
            "classification": final_decision,
            "audit_trail": audit_trail,
            "requires_human_review": requires_review,
            "processing_time_ms": processing_time,
            "workflow_type": workflow_type
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Valida se os dados de entrada contêm informações mínimas necessárias."""
        required_fields = ['descricao_produto']
        
        for field in required_fields:
            if field not in input_data or not input_data[field]:
                self.logger.error(f"Campo obrigatório ausente: {field}")
                return False
                
        return True
    
    def _determine_workflow_type(
        self, 
        input_data: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Determina qual tipo de workflow executar baseado nos dados disponíveis."""
        
        # Se já tem NCM/CEST, é confirmação
        if input_data.get('ncm_atual') or input_data.get('cest_atual'):
            return "confirmation"
        
        # Se tem GTIN, pode usar busca em exemplos
        if input_data.get('gtin'):
            return "determination"
            
        # Caso padrão: determinação completa
        return "determination"
    
    async def _execute_workflow(
        self, 
        workflow_type: str, 
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        audit_trail: AuditTrail
    ) -> Dict[str, Any]:
        """Executa o workflow de agentes na sequência apropriada."""
        
        workflow_steps = self.workflow_patterns.get(workflow_type, [])
        results = {}
        current_data = input_data.copy()
        
        for step in workflow_steps:
            if step not in self.specialist_agents:
                self.logger.warning(f"Agente {step} não registrado, pulando...")
                continue
                
            agent = self.specialist_agents[step]
            
            try:
                step_result = await agent.process(current_data, context)
                results[step] = step_result
                
                # Enriquecer dados para próximo agente
                if step == "enrichment" and step_result.get('enriched_description'):
                    current_data['descricao_enriquecida'] = step_result['enriched_description']
                    
                # Adicionar decisão à trilha de auditoria
                if hasattr(agent, 'decisions_history') and agent.decisions_history:
                    latest_decision = agent.decisions_history[-1]
                    audit_trail.agent_decisions.append(latest_decision)
                    
            except Exception as e:
                self.logger.error(f"Erro no agente {step}: {str(e)}")
                results[step] = {"error": str(e), "success": False}
        
        return results
    
    async def _make_final_decision(
        self, 
        workflow_result: Dict[str, Any],
        audit_trail: AuditTrail
    ) -> Dict[str, Any]:
        """Toma a decisão final baseada nos resultados de todos os agentes."""
        
        # Extrair classificações dos agentes especializados
        ncm_result = workflow_result.get('ncm_classifier', {})
        cest_result = workflow_result.get('cest_classifier', {})
        reconciliation_result = workflow_result.get('reconciliation', {})
        
        # Usar resultado da reconciliação se disponível
        if reconciliation_result.get('success'):
            return {
                "ncm_final": reconciliation_result.get('ncm_final'),
                "cest_final": reconciliation_result.get('cest_final'),
                "justificativa_ncm": reconciliation_result.get('justificativa_ncm'),
                "justificativa_cest": reconciliation_result.get('justificativa_cest'),
                "confidence_score": reconciliation_result.get('confidence_score', 0.0),
                "sources": reconciliation_result.get('sources', []),
                "method": "reconciliation"
            }
        
        # Caso contrário, usar consenso simples
        ncm_confidence = ncm_result.get('confidence_score', 0.0)
        cest_confidence = cest_result.get('confidence_score', 0.0)
        
        return {
            "ncm_final": ncm_result.get('ncm_classificado'),
            "cest_final": cest_result.get('cest_classificado'),
            "justificativa_ncm": ncm_result.get('justificativa'),
            "justificativa_cest": cest_result.get('justificativa'),
            "confidence_score": min(ncm_confidence, cest_confidence),
            "sources": list(set(
                ncm_result.get('sources', []) + cest_result.get('sources', [])
            )),
            "method": "individual_consensus"
        }
    
    def _requires_human_review(
        self, 
        final_decision: Dict[str, Any],
        audit_trail: AuditTrail
    ) -> bool:
        """Determina se a classificação requer revisão humana."""
        
        # Verifica limiar de confiança
        confidence = final_decision.get('confidence_score', 0.0)
        if confidence < self.get_confidence_threshold():
            return True
        
        # Verifica se há classificações conflitantes
        agent_decisions = audit_trail.agent_decisions
        ncm_classifications = [
            d.output_data.get('ncm_classificado') 
            for d in agent_decisions 
            if d.agent_name.endswith('_classifier') and d.output_data.get('ncm_classificado')
        ]
        
        if len(set(ncm_classifications)) > 1:
            return True
        
        # Verifica regras de negócio específicas
        business_rules = self.config.get('business_rules', {})
        
        if business_rules.get('require_human_validation', {}).get('conflicting_classifications'):
            return len(set(ncm_classifications)) > 1
            
        return False
    
    def _generate_reasoning(
        self, 
        workflow_result: Dict[str, Any],
        final_decision: Dict[str, Any]
    ) -> str:
        """Gera uma explicação do raciocínio para a decisão final."""
        
        reasoning_parts = [
            f"Decisão final baseada no método: {final_decision.get('method', 'unknown')}"
        ]
        
        for agent_type, result in workflow_result.items():
            if result.get('success', True):
                reasoning_parts.append(
                    f"- {agent_type}: {result.get('summary', 'Processado com sucesso')}"
                )
            else:
                reasoning_parts.append(
                    f"- {agent_type}: ERRO - {result.get('error', 'Erro desconhecido')}"
                )
        
        confidence = final_decision.get('confidence_score', 0.0)
        reasoning_parts.append(f"Confiança final: {confidence:.2%}")
        
        return "\n".join(reasoning_parts)
    
    def _aggregate_sources(self, audit_trail: AuditTrail) -> List[str]:
        """Agrega todas as fontes consultadas pelos agentes."""
        all_sources = []
        
        for decision in audit_trail.agent_decisions:
            all_sources.extend(decision.sources_used)
        
        return list(set(all_sources))  # Remove duplicatas
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas dos workflows executados."""
        
        # Análise baseada no histórico de decisões
        decisions = self.decisions_history
        
        if not decisions:
            return {"total_workflows": 0}
        
        workflow_types = [
            d.output_data.get('workflow_type', 'unknown') 
            for d in decisions
        ]
        
        human_reviews = sum(
            1 for d in decisions 
            if d.output_data.get('requires_human_review', False)
        )
        
        return {
            "total_workflows": len(decisions),
            "workflow_type_distribution": {
                wt: workflow_types.count(wt) for wt in set(workflow_types)
            },
            "human_review_rate": human_reviews / len(decisions) if decisions else 0,
            "average_processing_time_ms": sum(d.processing_time_ms for d in decisions) / len(decisions)
        }
