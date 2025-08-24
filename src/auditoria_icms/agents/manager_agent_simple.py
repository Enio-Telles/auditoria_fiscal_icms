"""
Manager Agent Simplificado v2.0 para Sistema de Auditoria Fiscal ICMS - Fase 2
Versão independente para demonstração sem dependências externas
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from dataclasses import dataclass, asdict

from .base_agent_simple import (
    BaseAgent,
    EnrichmentAgentBase,
    NCMAgentBase,
    CESTAgentBase,
    ReconciliationAgentBase,
)

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Resultado do processamento de um produto"""

    produto_id: str
    status: str  # sucesso, erro, pendente_revisao
    produto_atualizado: Optional[Any] = None
    erro_detalhes: Optional[str] = None
    tempo_execucao: float = 0.0
    logs_agentes: List[Dict[str, Any]] = None
    confianca_media: float = 0.0

    def to_dict(self):
        """Converte para dicionário"""
        return asdict(self)


@dataclass
class BatchProcessingResult:
    """Resultado do processamento em lote"""

    task_id: str
    empresa_id: int
    total_produtos: int
    produtos_processados: int
    produtos_com_sucesso: int
    produtos_com_erro: int
    produtos_pendente_revisao: int
    tempo_total: float
    resultados_individuais: List[ProcessingResult]

    def to_dict(self):
        """Converte para dicionário"""
        return {
            "task_id": self.task_id,
            "empresa_id": self.empresa_id,
            "total_produtos": self.total_produtos,
            "produtos_processados": self.produtos_processados,
            "produtos_com_sucesso": self.produtos_com_sucesso,
            "produtos_com_erro": self.produtos_com_erro,
            "produtos_pendente_revisao": self.produtos_pendente_revisao,
            "tempo_total": self.tempo_total,
            "resultados_individuais": [
                r.to_dict() for r in self.resultados_individuais
            ],
        }


class ManagerAgent(BaseAgent):
    """
    Agente gerenciador simplificado que orquestra o fluxo de classificação
    """

    def __init__(
        self,
        empresa_id: int,
        data_ingestion: Any,  # Tipagem flexível para evitar dependências
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            name="ManagerAgent",
            description="Orquestra fluxo de classificação fiscal multi-tenant",
            config=config,
        )

        self.empresa_id = empresa_id
        self.data_ingestion = data_ingestion

        # Inicializa agentes especialistas
        self.enrichment_agent = EnrichmentAgentBase(config=config)
        self.ncm_agent = NCMAgentBase(config=config)
        self.cest_agent = CESTAgentBase(config=config)
        self.reconciliation_agent = ReconciliationAgentBase(config=config)

        # Estados do workflow
        self.estados_validos = [
            "PENDENTE",
            "ENRIQUECENDO",
            "ENRIQUECIDO",
            "CLASSIFICANDO_NCM",
            "NCM_CLASSIFICADO",
            "CLASSIFICANDO_CEST",
            "CEST_CLASSIFICADO",
            "RECONCILIANDO",
            "CONCLUIDO",
            "ERRO",
            "REVISAO_MANUAL",
        ]

        # Configurações padrão
        self.config_processamento = {
            "confianca_minima": config.get("confianca_minima", 0.7) if config else 0.7,
            "auto_approve_threshold": (
                config.get("auto_approve_threshold", 0.9) if config else 0.9
            ),
            "max_retries": config.get("max_retries", 3) if config else 3,
            "timeout_agente": config.get("timeout_agente", 300) if config else 300,
            "batch_size": config.get("batch_size", 100) if config else 100,
        }

    def process(
        self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Implementa método abstrato da classe base"""
        produto = self._criar_produto_from_dict(input_data)
        resultado = self._processar_produto_individual(produto)
        return resultado.to_dict()

    def processar_lote(
        self, produtos: List[Any], batch_size: Optional[int] = None
    ) -> BatchProcessingResult:
        """
        Processa um lote de produtos da empresa seguindo o workflow definido
        """

        task_id = str(uuid.uuid4())
        inicio = datetime.utcnow()

        logger.info(f"Iniciando processamento em lote para empresa {self.empresa_id}")
        logger.info(f"Task ID: {task_id}, Total produtos: {len(produtos)}")

        resultados_individuais = []
        produtos_processados = 0
        produtos_com_sucesso = 0
        produtos_com_erro = 0
        produtos_pendente_revisao = 0

        try:
            # Processa produtos individualmente
            for i, produto in enumerate(produtos):
                try:
                    logger.info(
                        f"Processando produto {i+1}/{len(produtos)}: {getattr(produto, 'produto_id', f'produto_{i}')}"
                    )

                    resultado = self._processar_produto_individual(produto)
                    resultados_individuais.append(resultado)

                    produtos_processados += 1

                    if resultado.status == "sucesso":
                        produtos_com_sucesso += 1
                    elif resultado.status == "erro":
                        produtos_com_erro += 1
                    elif resultado.status == "pendente_revisao":
                        produtos_pendente_revisao += 1

                except Exception as e:
                    logger.error(
                        f"Erro ao processar produto {getattr(produto, 'produto_id', f'produto_{i}')}: {str(e)}"
                    )

                    resultado_erro = ProcessingResult(
                        produto_id=getattr(produto, "produto_id", f"produto_{i}"),
                        status="erro",
                        erro_detalhes=str(e),
                    )
                    resultados_individuais.append(resultado_erro)
                    produtos_com_erro += 1

            fim = datetime.utcnow()
            tempo_total = (fim - inicio).total_seconds()

            resultado_batch = BatchProcessingResult(
                task_id=task_id,
                empresa_id=self.empresa_id,
                total_produtos=len(produtos),
                produtos_processados=produtos_processados,
                produtos_com_sucesso=produtos_com_sucesso,
                produtos_com_erro=produtos_com_erro,
                produtos_pendente_revisao=produtos_pendente_revisao,
                tempo_total=tempo_total,
                resultados_individuais=resultados_individuais,
            )

            logger.info(
                f"Processamento concluído. Sucesso: {produtos_com_sucesso}, "
                f"Erro: {produtos_com_erro}, Revisão: {produtos_pendente_revisao}"
            )

            return resultado_batch

        except Exception as e:
            logger.error(f"Erro no processamento em lote: {str(e)}")
            raise

    def _processar_produto_individual(self, produto: Any) -> ProcessingResult:
        """
        Processa um produto individual seguindo o grafo de estados
        """

        inicio = datetime.utcnow()
        logs_agentes = []

        try:
            # Estado inicial
            estado_atual = "PENDENTE"
            produto_processado = produto

            # Workflow de processamento
            while estado_atual not in ["CONCLUIDO", "ERRO", "REVISAO_MANUAL"]:
                if estado_atual == "PENDENTE":
                    estado_atual = "ENRIQUECENDO"

                elif estado_atual == "ENRIQUECENDO":
                    # Etapa 1: Enriquecimento da descrição
                    resultado_enrich = self._executar_agente(
                        self.enrichment_agent,
                        "enriquecer_descricao",
                        produto_processado,
                        logs_agentes,
                    )

                    if resultado_enrich["status"] == "sucesso":
                        produto_processado.descricao_enriquecida = resultado_enrich[
                            "resultado"
                        ].get("descricao_enriquecida", "")
                        estado_atual = "ENRIQUECIDO"
                    else:
                        estado_atual = "ERRO"

                elif estado_atual == "ENRIQUECIDO":
                    estado_atual = "CLASSIFICANDO_NCM"

                elif estado_atual == "CLASSIFICANDO_NCM":
                    # Etapa 2: Classificação NCM
                    resultado_ncm = self._executar_agente(
                        self.ncm_agent,
                        "processar_classificacao",
                        produto_processado,
                        logs_agentes,
                    )

                    if resultado_ncm["status"] == "sucesso":
                        produto_processado.ncm_sugerido = resultado_ncm[
                            "resultado"
                        ].get("ncm", "")
                        produto_processado.confianca_ncm = resultado_ncm[
                            "resultado"
                        ].get("confianca", 0.0)
                        produto_processado.justificativa_ncm = resultado_ncm[
                            "resultado"
                        ].get("justificativa", "")

                        # Verifica se precisa de revisão manual
                        if (
                            produto_processado.confianca_ncm
                            < self.config_processamento["confianca_minima"]
                        ):
                            estado_atual = "REVISAO_MANUAL"
                        else:
                            estado_atual = "NCM_CLASSIFICADO"
                    else:
                        estado_atual = "ERRO"

                elif estado_atual == "NCM_CLASSIFICADO":
                    estado_atual = "CLASSIFICANDO_CEST"

                elif estado_atual == "CLASSIFICANDO_CEST":
                    # Etapa 3: Classificação CEST
                    resultado_cest = self._executar_agente(
                        self.cest_agent,
                        "processar_classificacao",
                        produto_processado,
                        logs_agentes,
                    )

                    if resultado_cest["status"] == "sucesso":
                        produto_processado.cest_sugerido = resultado_cest[
                            "resultado"
                        ].get("cest", "")
                        produto_processado.confianca_cest = resultado_cest[
                            "resultado"
                        ].get("confianca", 0.0)
                        produto_processado.justificativa_cest = resultado_cest[
                            "resultado"
                        ].get("justificativa", "")
                        estado_atual = "CEST_CLASSIFICADO"
                    else:
                        estado_atual = "ERRO"

                elif estado_atual == "CEST_CLASSIFICADO":
                    estado_atual = "RECONCILIANDO"

                elif estado_atual == "RECONCILIANDO":
                    # Etapa 4: Reconciliação e validação final
                    resultado_reconcil = self._executar_agente(
                        self.reconciliation_agent,
                        "validar_consistencia",
                        produto_processado,
                        logs_agentes,
                    )

                    if resultado_reconcil["status"] == "sucesso":
                        # Verifica aprovação automática
                        confianca_ncm = (
                            getattr(produto_processado, "confianca_ncm", 0.0) or 0.0
                        )
                        confianca_cest = (
                            getattr(produto_processado, "confianca_cest", 0.0) or 0.0
                        )
                        confianca_media = (confianca_ncm + confianca_cest) / 2

                        if (
                            confianca_media
                            >= self.config_processamento["auto_approve_threshold"]
                        ):
                            produto_processado.status_processamento = "PROCESSADO"
                        else:
                            produto_processado.status_processamento = "REVISAO_PENDENTE"
                            produto_processado.revisao_manual = True

                        estado_atual = "CONCLUIDO"
                    else:
                        estado_atual = "ERRO"

            # Define status final
            fim = datetime.utcnow()
            tempo_execucao = (fim - inicio).total_seconds()

            if estado_atual == "CONCLUIDO":
                produto_processado.data_processamento = datetime.utcnow()

                # Calcula confiança média
                confianca_ncm = getattr(produto_processado, "confianca_ncm", 0.0) or 0.0
                confianca_cest = (
                    getattr(produto_processado, "confianca_cest", 0.0) or 0.0
                )
                confianca_media = (confianca_ncm + confianca_cest) / 2

                return ProcessingResult(
                    produto_id=getattr(produto, "produto_id", "unknown"),
                    status="sucesso",
                    produto_atualizado=produto_processado,
                    tempo_execucao=tempo_execucao,
                    logs_agentes=logs_agentes,
                    confianca_media=confianca_media,
                )

            elif estado_atual == "REVISAO_MANUAL":
                produto_processado.status_processamento = "REVISAO_PENDENTE"
                produto_processado.revisao_manual = True

                return ProcessingResult(
                    produto_id=getattr(produto, "produto_id", "unknown"),
                    status="pendente_revisao",
                    produto_atualizado=produto_processado,
                    tempo_execucao=tempo_execucao,
                    logs_agentes=logs_agentes,
                )

            else:  # ERRO
                return ProcessingResult(
                    produto_id=getattr(produto, "produto_id", "unknown"),
                    status="erro",
                    erro_detalhes=f"Falha no estado: {estado_atual}",
                    tempo_execucao=tempo_execucao,
                    logs_agentes=logs_agentes,
                )

        except Exception as e:
            fim = datetime.utcnow()
            tempo_execucao = (fim - inicio).total_seconds()

            return ProcessingResult(
                produto_id=getattr(produto, "produto_id", "unknown"),
                status="erro",
                erro_detalhes=str(e),
                tempo_execucao=tempo_execucao,
                logs_agentes=logs_agentes,
            )

    def _executar_agente(
        self,
        agente: BaseAgent,
        acao: str,
        produto: Any,
        logs_agentes: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Executa um agente específico e registra log de auditoria
        """

        inicio = datetime.utcnow()

        try:
            # Prepara entrada para o agente
            dados_entrada = {
                "produto_id": getattr(produto, "produto_id", "unknown"),
                "descricao_produto": getattr(produto, "descricao_produto", ""),
                "descricao_enriquecida": getattr(
                    produto, "descricao_enriquecida", None
                ),
                "ncm": getattr(produto, "ncm", None),
                "cest": getattr(produto, "cest", None),
                "codigo_produto": getattr(produto, "codigo_produto", ""),
                "codigo_barra": getattr(produto, "codigo_barra", None),
                "acao": acao,
            }

            # Executa o agente
            if acao == "enriquecer_descricao":
                descricao = dados_entrada.get("descricao_produto", "")
                resultado = agente.enriquecer_descricao(descricao)
            elif acao == "processar_classificacao":
                resultado = agente.processar_classificacao(dados_entrada)
            elif acao == "validar_consistencia":
                resultado = agente.validar_consistencia(dados_entrada)
            else:
                raise ValueError(f"Ação não reconhecida: {acao}")

            fim = datetime.utcnow()
            tempo_execucao = (fim - inicio).total_seconds()

            # Registra log de auditoria
            log_auditoria = {
                "empresa_id": self.empresa_id,
                "produto_id_origem": dados_entrada["produto_id"],
                "agente_nome": agente.name,
                "timestamp": inicio,
                "acao_realizada": acao,
                "dados_entrada": dados_entrada,
                "dados_saida": resultado,
                "justificativa_rag": resultado.get("justificativa", ""),
                "confianca": resultado.get("confianca", 0.0),
                "status": "sucesso",
                "tempo_execucao": tempo_execucao,
            }

            logs_agentes.append(log_auditoria)

            return {
                "status": "sucesso",
                "resultado": resultado,
                "tempo_execucao": tempo_execucao,
            }

        except Exception as e:
            fim = datetime.utcnow()
            tempo_execucao = (fim - inicio).total_seconds()

            # Registra log de erro
            log_erro = {
                "empresa_id": self.empresa_id,
                "produto_id_origem": getattr(produto, "produto_id", "unknown"),
                "agente_nome": agente.name,
                "timestamp": inicio,
                "acao_realizada": acao,
                "status": "erro",
                "tempo_execucao": tempo_execucao,
                "erro_detalhes": str(e),
            }

            logs_agentes.append(log_erro)

            return {"status": "erro", "erro": str(e), "tempo_execucao": tempo_execucao}

    def _criar_produto_from_dict(self, produto_data: Dict[str, Any]) -> Any:
        """Cria objeto produto a partir de dicionário"""

        class ProdutoSimulado:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

                # Campos que serão preenchidos durante processamento
                if not hasattr(self, "descricao_enriquecida"):
                    self.descricao_enriquecida = None
                if not hasattr(self, "ncm_sugerido"):
                    self.ncm_sugerido = None
                if not hasattr(self, "cest_sugerido"):
                    self.cest_sugerido = None
                if not hasattr(self, "confianca_ncm"):
                    self.confianca_ncm = None
                if not hasattr(self, "confianca_cest"):
                    self.confianca_cest = None
                if not hasattr(self, "justificativa_ncm"):
                    self.justificativa_ncm = None
                if not hasattr(self, "justificativa_cest"):
                    self.justificativa_cest = None
                if not hasattr(self, "status_processamento"):
                    self.status_processamento = None
                if not hasattr(self, "revisao_manual"):
                    self.revisao_manual = False
                if not hasattr(self, "data_processamento"):
                    self.data_processamento = None

        return ProdutoSimulado(produto_data)

    def obter_configuracao_empresa(self) -> Dict[str, Any]:
        """Obtém configuração específica da empresa"""
        return {
            "empresa_id": self.empresa_id,
            "configuracao_processamento": self.config_processamento,
            "agentes_registrados": [
                self.enrichment_agent.name,
                self.ncm_agent.name,
                self.cest_agent.name,
                self.reconciliation_agent.name,
            ],
        }


# Função utilitária para criar ManagerAgent
def create_manager_agent(
    empresa_id: int,
    data_ingestion: Any,
    processing_config: Optional[Dict[str, Any]] = None,
) -> ManagerAgent:
    """Cria uma instância do ManagerAgent para uma empresa específica"""

    return ManagerAgent(
        empresa_id=empresa_id, data_ingestion=data_ingestion, config=processing_config
    )
