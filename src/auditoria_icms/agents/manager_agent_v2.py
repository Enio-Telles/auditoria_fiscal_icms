"""
Manager Agent v2.0 para Sistema de Auditoria Fiscal ICMS - Fase 2
Orquestra o fluxo de trabalho multi-tenant com auditoria completa
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from dataclasses import dataclass, asdict

from .base_agent import BaseAgent
from .enrichment_agent import EnrichmentAgent
from .ncm_agent import NCMAgent
from .cest_agent import CESTAgent
from .reconciliation_agent import ReconciliationAgent
from ..database.models import ProdutoEmpresa
from ..data_processing.empresa_data_ingestion import EmpresaDataIngestion

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Resultado do processamento de um produto"""

    produto_id: str
    status: str  # sucesso, erro, pendente_revisao
    produto_atualizado: Optional[ProdutoEmpresa] = None
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
    Agente gerenciador que orquestra todo o fluxo de classificação
    Implementa padrão de estados LangGraph para auditoria completa
    """

    def __init__(
        self,
        empresa_id: int,
        data_ingestion: EmpresaDataIngestion,
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
        self.enrichment_agent = EnrichmentAgent(config=config)
        self.ncm_agent = NCMAgent(config=config)
        self.cest_agent = CESTAgent(config=config)
        self.reconciliation_agent = ReconciliationAgent(config=config)

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

    def processar_lote(
        self, produtos: List[ProdutoEmpresa], batch_size: Optional[int] = None
    ) -> BatchProcessingResult:
        """
        Processa um lote de produtos da empresa seguindo o workflow definido

        Args:
            produtos: Lista de produtos para processar
            batch_size: Tamanho do lote (se None, processa todos)

        Returns:
            Resultado do processamento em lote
        """

        task_id = str(uuid.uuid4())
        inicio = datetime.utcnow()

        logger.info(f"Iniciando processamento em lote para empresa {self.empresa_id}")
        logger.info(f"Task ID: {task_id}, Total produtos: {len(produtos)}")

        # Registra início do processamento
        self._registrar_status_processamento(task_id, len(produtos), "iniciado")

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
                        f"Processando produto {i+1}/{len(produtos)}: {produto.produto_id}"
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

                    # Atualiza status do processamento
                    self._atualizar_status_processamento(
                        task_id, produtos_processados, "em_progresso"
                    )

                except Exception as e:
                    logger.error(
                        f"Erro ao processar produto {produto.produto_id}: {str(e)}"
                    )

                    resultado_erro = ProcessingResult(
                        produto_id=produto.produto_id,
                        status="erro",
                        erro_detalhes=str(e),
                    )
                    resultados_individuais.append(resultado_erro)
                    produtos_com_erro += 1

            # Atualiza produtos no banco da empresa
            self._atualizar_produtos_empresa(resultados_individuais)

            fim = datetime.utcnow()
            tempo_total = (fim - inicio).total_seconds()

            # Finaliza status do processamento
            self._finalizar_status_processamento(task_id, "concluido")

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
            self._finalizar_status_processamento(task_id, "erro")
            raise

    def _processar_produto_individual(
        self, produto: ProdutoEmpresa
    ) -> ProcessingResult:
        """
        Processa um produto individual seguindo o grafo de estados

        Args:
            produto: Produto a ser processado

        Returns:
            Resultado do processamento
        """

        inicio = datetime.utcnow()
        logs_agentes = []

        try:
            # Estado inicial
            estado_atual = "PENDENTE"
            produto_processado = produto.copy() if hasattr(produto, "copy") else produto

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
                    acao = (
                        "confirmar_ncm"
                        if hasattr(produto_processado, "ncm") and produto_processado.ncm
                        else "determinar_ncm"
                    )

                    resultado_ncm = self._executar_agente(
                        self.ncm_agent, acao, produto_processado, logs_agentes
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
                    acao = (
                        "confirmar_cest"
                        if hasattr(produto_processado, "cest")
                        and produto_processado.cest
                        else "determinar_cest"
                    )

                    resultado_cest = self._executar_agente(
                        self.cest_agent, acao, produto_processado, logs_agentes
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
                    produto_id=produto.produto_id,
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
                    produto_id=produto.produto_id,
                    status="pendente_revisao",
                    produto_atualizado=produto_processado,
                    tempo_execucao=tempo_execucao,
                    logs_agentes=logs_agentes,
                )

            else:  # ERRO
                return ProcessingResult(
                    produto_id=produto.produto_id,
                    status="erro",
                    erro_detalhes=f"Falha no estado: {estado_atual}",
                    tempo_execucao=tempo_execucao,
                    logs_agentes=logs_agentes,
                )

        except Exception as e:
            fim = datetime.utcnow()
            tempo_execucao = (fim - inicio).total_seconds()

            return ProcessingResult(
                produto_id=produto.produto_id,
                status="erro",
                erro_detalhes=str(e),
                tempo_execucao=tempo_execucao,
                logs_agentes=logs_agentes,
            )

    def _executar_agente(
        self,
        agente: BaseAgent,
        acao: str,
        produto: ProdutoEmpresa,
        logs_agentes: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Executa um agente específico e registra log de auditoria

        Args:
            agente: Agente a ser executado
            acao: Ação a ser realizada
            produto: Produto sendo processado
            logs_agentes: Lista para armazenar logs

        Returns:
            Resultado da execução do agente
        """

        inicio = datetime.utcnow()

        try:
            # Prepara entrada para o agente
            dados_entrada = {
                "produto_id": produto.produto_id,
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

            # Executa o agente (simulação - deve ser implementado nos agentes reais)
            if acao == "enriquecer_descricao":
                resultado = self._simular_enriquecimento(dados_entrada)
            elif acao in ["confirmar_ncm", "determinar_ncm"]:
                resultado = self._simular_classificacao_ncm(dados_entrada)
            elif acao in ["confirmar_cest", "determinar_cest"]:
                resultado = self._simular_classificacao_cest(dados_entrada)
            elif acao == "validar_consistencia":
                resultado = self._simular_validacao(dados_entrada)
            else:
                raise ValueError(f"Ação não reconhecida: {acao}")

            fim = datetime.utcnow()
            tempo_execucao = (fim - inicio).total_seconds()

            # Registra log de auditoria
            log_auditoria = {
                "empresa_id": self.empresa_id,
                "produto_id_origem": produto.produto_id,
                "agente_nome": agente.name,
                "timestamp": inicio,
                "acao_realizada": acao,
                "dados_entrada": dados_entrada,
                "dados_saida": resultado,
                "justificativa_rag": resultado.get("justificativa", ""),
                "query_rag": resultado.get("query_rag", ""),
                "contexto_rag": resultado.get("contexto_rag", {}),
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
                "produto_id_origem": produto.produto_id,
                "agente_nome": agente.name,
                "timestamp": inicio,
                "acao_realizada": acao,
                "dados_entrada": dados_entrada,
                "dados_saida": None,
                "status": "erro",
                "tempo_execucao": tempo_execucao,
                "erro_detalhes": str(e),
            }

            logs_agentes.append(log_erro)

            return {"status": "erro", "erro": str(e), "tempo_execucao": tempo_execucao}

    def _simular_enriquecimento(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Simula enriquecimento da descrição"""
        descricao_original = dados.get("descricao_produto", "")
        return {
            "descricao_enriquecida": f"{descricao_original} - produto enriquecido",
            "confianca": 0.85,
            "justificativa": "Enriquecimento baseado em análise semântica",
        }

    def _simular_classificacao_ncm(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Simula classificação NCM"""
        return {
            "ncm": "12345678",
            "confianca": 0.90,
            "justificativa": "Classificação baseada em descrição e padrões similares",
        }

    def _simular_classificacao_cest(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Simula classificação CEST"""
        return {
            "cest": "12.345.67",
            "confianca": 0.85,
            "justificativa": "CEST determinado com base no NCM",
        }

    def _simular_validacao(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Simula validação de consistência"""
        return {
            "validacao": True,
            "confianca": 0.88,
            "justificativa": "Classificações consistentes entre NCM e CEST",
        }

    def _atualizar_produtos_empresa(self, resultados: List[ProcessingResult]):
        """Atualiza produtos no banco da empresa com os resultados"""

        produtos_para_atualizar = []

        for resultado in resultados:
            if resultado.produto_atualizado:
                produto_dict = {
                    "produto_id": resultado.produto_id,
                    "descricao_enriquecida": getattr(
                        resultado.produto_atualizado, "descricao_enriquecida", None
                    ),
                    "ncm_sugerido": getattr(
                        resultado.produto_atualizado, "ncm_sugerido", None
                    ),
                    "cest_sugerido": getattr(
                        resultado.produto_atualizado, "cest_sugerido", None
                    ),
                    "status_processamento": getattr(
                        resultado.produto_atualizado, "status_processamento", None
                    ),
                    "confianca_ncm": getattr(
                        resultado.produto_atualizado, "confianca_ncm", None
                    ),
                    "confianca_cest": getattr(
                        resultado.produto_atualizado, "confianca_cest", None
                    ),
                    "justificativa_ncm": getattr(
                        resultado.produto_atualizado, "justificativa_ncm", None
                    ),
                    "justificativa_cest": getattr(
                        resultado.produto_atualizado, "justificativa_cest", None
                    ),
                    "revisao_manual": getattr(
                        resultado.produto_atualizado, "revisao_manual", False
                    ),
                }
                produtos_para_atualizar.append(produto_dict)

        if produtos_para_atualizar:
            sucesso = self.data_ingestion.update_produtos_processados(
                produtos_para_atualizar
            )

            if sucesso:
                logger.info(
                    f"Atualizados {len(produtos_para_atualizar)} produtos no banco da empresa"
                )
            else:
                logger.error("Erro ao atualizar produtos no banco da empresa")

    def _registrar_status_processamento(
        self, task_id: str, total_produtos: int, status: str
    ):
        """Registra início do processamento"""
        logger.info(
            f"Iniciando processamento {task_id} - {total_produtos} produtos - Status: {status}"
        )

    def _atualizar_status_processamento(
        self, task_id: str, produtos_processados: int, status: str
    ):
        """Atualiza status do processamento"""
        logger.info(
            f"Processamento {task_id} - {produtos_processados} produtos processados - Status: {status}"
        )

    def _finalizar_status_processamento(self, task_id: str, status_final: str):
        """Finaliza status do processamento"""
        logger.info(f"Processamento {task_id} finalizado - Status: {status_final}")

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

    def obter_estatisticas_processamento(self) -> Dict[str, Any]:
        """Obtém estatísticas de processamento da empresa"""
        # Implementar consulta ao banco de dados para estatísticas
        return {
            "empresa_id": self.empresa_id,
            "total_produtos_processados": 0,
            "taxa_sucesso": 0.0,
            "tempo_medio_processamento": 0.0,
            "produtos_pendente_revisao": 0,
        }


# Função utilitária para criar ManagerAgent
def create_manager_agent(
    empresa_id: int,
    db_config: Dict[str, Any],
    processing_config: Optional[Dict[str, Any]] = None,
) -> ManagerAgent:
    """Cria uma instância do ManagerAgent para uma empresa específica"""

    # Cria instância de ingestão de dados
    data_ingestion = EmpresaDataIngestion(empresa_id, db_config)

    # Cria e retorna o manager agent
    return ManagerAgent(
        empresa_id=empresa_id, data_ingestion=data_ingestion, config=processing_config
    )
