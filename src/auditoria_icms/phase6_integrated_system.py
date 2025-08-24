"""
Sistema Integrado Fase 6 - Auditoria ICMS
Orquestração completa do sistema com agentes reais e PostgreSQL
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
from dataclasses import dataclass, asdict

from ..core.config import get_settings
from ..database.postgresql_setup import PostgreSQLSetup
from ..data_processing.database_importer import DatabaseImporter
from ..agents.real_agents import NCMAgent, CESTAgent
from ..agents.data_agents import EnrichmentAgent, ReconciliationAgent
from ..workflows.workflow_manager import WorkflowManager


@dataclass
class SystemStatus:
    """Status do sistema integrado"""

    database_ready: bool
    agents_ready: bool
    workflows_ready: bool
    data_imported: bool
    last_check: datetime
    errors: List[str]
    warnings: List[str]


@dataclass
class ProcessingResult:
    """Resultado do processamento completo"""

    success: bool
    products_processed: int
    products_enriched: int
    conflicts_resolved: int
    errors: List[str]
    processing_time_seconds: float
    confidence_average: float
    manual_review_required: int


class IntegratedSystem:
    """Sistema integrado completo da Fase 6"""

    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)

        # Componentes do sistema
        self.db_setup = PostgreSQLSetup()
        self.db_importer = DatabaseImporter()
        self.ncm_agent = NCMAgent()
        self.cest_agent = CESTAgent()
        self.enrichment_agent = EnrichmentAgent()
        self.reconciliation_agent = ReconciliationAgent()
        self.workflow_manager = WorkflowManager()

        # Status do sistema
        self.system_status = None
        self._initialize_system()

    def _initialize_system(self):
        """Inicializa o sistema"""
        try:
            self.logger.info("Inicializando sistema integrado...")
            self.system_status = self.check_system_status()

            if not self.system_status.database_ready:
                self.logger.warning("Base de dados não está pronta")

            if not self.system_status.agents_ready:
                self.logger.warning("Agentes não estão prontos")

        except Exception as e:
            self.logger.error(f"Erro na inicialização: {e}")

    def check_system_status(self) -> SystemStatus:
        """Verifica status de todos os componentes"""
        errors = []
        warnings = []

        # Verificar PostgreSQL
        database_ready = self.db_setup.test_connection()
        if not database_ready:
            errors.append("PostgreSQL não está acessível")

        # Verificar agentes
        agents_ready = True
        try:
            # Testar agentes com dados básicos
            test_result = self.ncm_agent.validate_ncm("12345678", "produto teste")
            if "error" in str(test_result):
                agents_ready = False
                warnings.append("Agente NCM pode estar com problemas")
        except Exception as e:
            agents_ready = False
            errors.append(f"Erro nos agentes: {e}")

        # Verificar workflows
        workflows_ready = True
        try:
            workflow_status = self.workflow_manager.get_available_workflows()
            if not workflow_status:
                workflows_ready = False
                warnings.append("Workflows não disponíveis")
        except Exception as e:
            workflows_ready = False
            errors.append(f"Erro nos workflows: {e}")

        # Verificar dados importados
        data_imported = False
        try:
            stats = self.db_setup.get_database_stats()
            if stats.get("total_ncm_classificacoes", 0) > 0:
                data_imported = True
        except Exception:
            warnings.append("Não foi possível verificar dados importados")

        return SystemStatus(
            database_ready=database_ready,
            agents_ready=agents_ready,
            workflows_ready=workflows_ready,
            data_imported=data_imported,
            last_check=datetime.now(),
            errors=errors,
            warnings=warnings,
        )

    def setup_complete_system(self) -> bool:
        """Configura sistema completo do zero"""
        try:
            self.logger.info("🚀 Iniciando configuração completa do sistema...")

            # 1. Configurar PostgreSQL
            self.logger.info("📊 Configurando PostgreSQL...")
            if not self.db_setup.setup_database():
                self.logger.error("❌ Falha na configuração do PostgreSQL")
                return False

            # 2. Importar dados externos
            self.logger.info("📥 Importando dados externos...")
            if not self._import_external_data():
                self.logger.warning(
                    "⚠️ Falha na importação de dados externos (continuando)"
                )

            # 3. Verificar agentes
            self.logger.info("🤖 Verificando agentes...")
            if not self._validate_agents():
                self.logger.error("❌ Falha na validação dos agentes")
                return False

            # 4. Configurar workflows
            self.logger.info("🔄 Configurando workflows...")
            if not self._setup_workflows():
                self.logger.error("❌ Falha na configuração dos workflows")
                return False

            # 5. Verificação final
            self.system_status = self.check_system_status()

            if all(
                [
                    self.system_status.database_ready,
                    self.system_status.agents_ready,
                    self.system_status.workflows_ready,
                ]
            ):
                self.logger.info("✅ Sistema configurado com sucesso!")
                return True
            else:
                self.logger.error("❌ Sistema não está completamente funcional")
                return False

        except Exception as e:
            self.logger.error(f"Erro na configuração do sistema: {e}")
            return False

    def _import_external_data(self) -> bool:
        """Importa dados de fontes externas"""
        try:
            # Configuração de exemplo para base externa
            external_config = {
                "db_04565289005297": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "empresa_04565289005297",
                    "username": "readonly_user",
                    "password": "readonly_pass",
                }
            }

            for db_name, config in external_config.items():
                try:
                    import_result = self.db_importer.import_from_external_database(
                        config_name=db_name, custom_config=config
                    )

                    if import_result["success"]:
                        self.logger.info(
                            f"✅ Dados importados de {db_name}: {import_result['products_imported']} produtos"
                        )
                    else:
                        self.logger.warning(
                            f"⚠️ Falha na importação de {db_name}: {import_result['error']}"
                        )

                except Exception as e:
                    self.logger.warning(f"⚠️ Erro ao importar de {db_name}: {e}")

            return True

        except Exception as e:
            self.logger.error(f"Erro na importação de dados externos: {e}")
            return False

    def _validate_agents(self) -> bool:
        """Valida funcionamento dos agentes"""
        try:
            # Teste do agente NCM
            ncm_test = self.ncm_agent.validate_ncm("84713012", "Processador Intel")
            if not isinstance(ncm_test, dict):
                return False

            # Teste do agente CEST
            cest_test = self.cest_agent.validate_cest(
                "2800100", "84713012", "Processador"
            )
            if not isinstance(cest_test, dict):
                return False

            # Teste do agente de enriquecimento
            test_product = {
                "codigo_produto": "TEST001",
                "descricao": "Produto de teste",
                "ncm": "84713012",
                "empresa_id": 1,
            }

            enrichment_test = self.enrichment_agent.enrich_product_data(test_product)
            if not enrichment_test.success and enrichment_test.confidence < 0.5:
                return False

            return True

        except Exception as e:
            self.logger.error(f"Erro na validação dos agentes: {e}")
            return False

    def _setup_workflows(self) -> bool:
        """Configura workflows"""
        try:
            # Verificar workflows disponíveis
            workflows = self.workflow_manager.get_available_workflows()

            required_workflows = ["ConfirmationFlow", "DeterminationFlow"]
            available_workflows = [w["name"] for w in workflows]

            for required in required_workflows:
                if required not in available_workflows:
                    self.logger.error(
                        f"Workflow obrigatório não disponível: {required}"
                    )
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Erro na configuração dos workflows: {e}")
            return False

    async def process_company_products(
        self, empresa_id: int, batch_size: int = 100
    ) -> ProcessingResult:
        """Processa produtos de uma empresa específica"""
        start_time = datetime.now()

        try:
            self.logger.info(f"📋 Iniciando processamento da empresa {empresa_id}")

            # 1. Obter produtos da empresa
            products = await self._get_company_products(empresa_id)
            if not products:
                return ProcessingResult(
                    success=False,
                    products_processed=0,
                    products_enriched=0,
                    conflicts_resolved=0,
                    errors=["Nenhum produto encontrado para a empresa"],
                    processing_time_seconds=0,
                    confidence_average=0,
                    manual_review_required=0,
                )

            # 2. Obter informações da empresa
            empresa_info = await self._get_company_info(empresa_id)

            # 3. Processar em lotes
            results = []
            errors = []

            for i in range(0, len(products), batch_size):
                batch = products[i : i + batch_size]
                self.logger.info(
                    f"🔄 Processando lote {i//batch_size + 1}/{(len(products)-1)//batch_size + 1}"
                )

                try:
                    batch_result = await self._process_product_batch(
                        batch, empresa_info
                    )
                    results.extend(batch_result)
                except Exception as e:
                    error_msg = f"Erro no lote {i//batch_size + 1}: {e}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)

            # 4. Compilar resultados
            processing_time = (datetime.now() - start_time).total_seconds()

            successful_results = [r for r in results if r.success]
            confidence_values = [
                r.confidence for r in successful_results if r.confidence > 0
            ]

            return ProcessingResult(
                success=len(errors) == 0,
                products_processed=len(products),
                products_enriched=len(successful_results),
                conflicts_resolved=sum(1 for r in results if len(r.changes) > 0),
                errors=errors,
                processing_time_seconds=processing_time,
                confidence_average=(
                    sum(confidence_values) / len(confidence_values)
                    if confidence_values
                    else 0
                ),
                manual_review_required=sum(
                    1
                    for r in results
                    if any(w for w in r.warnings if "manual" in w.lower())
                ),
            )

        except Exception as e:
            self.logger.error(f"Erro no processamento da empresa: {e}")
            return ProcessingResult(
                success=False,
                products_processed=0,
                products_enriched=0,
                conflicts_resolved=0,
                errors=[str(e)],
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
                confidence_average=0,
                manual_review_required=0,
            )

    async def _get_company_products(self, empresa_id: int) -> List[Dict[str, Any]]:
        """Obtém produtos da empresa do banco de dados"""
        try:
            engine = self.db_setup._get_engine()

            query = """
                SELECT id, codigo_produto, descricao, ncm, cest, unidade, categoria, preco
                FROM produtos
                WHERE empresa_id = %s AND ativo = true
            """

            df = pd.read_sql(query, engine, params=[empresa_id])
            return df.to_dict("records")

        except Exception as e:
            self.logger.error(f"Erro ao obter produtos da empresa: {e}")
            return []

    async def _get_company_info(self, empresa_id: int) -> Dict[str, Any]:
        """Obtém informações da empresa"""
        try:
            engine = self.db_setup._get_engine()

            query = """
                SELECT cnpj, razao_social, atividade_principal, regime_tributario
                FROM empresas
                WHERE id = %s
            """

            df = pd.read_sql(query, engine, params=[empresa_id])
            if not df.empty:
                return {
                    "cnpj": df.iloc[0]["cnpj"],
                    "razao_social": df.iloc[0]["razao_social"],
                    "atividade": df.iloc[0]["atividade_principal"],
                    "regime_tributario": df.iloc[0]["regime_tributario"],
                }

            return {}

        except Exception as e:
            self.logger.error(f"Erro ao obter informações da empresa: {e}")
            return {}

    async def _process_product_batch(
        self, products: List[Dict[str, Any]], empresa_info: Dict[str, Any]
    ) -> List:
        """Processa um lote de produtos"""
        results = []

        for product in products:
            try:
                # Enriquecer dados do produto
                enrichment_result = self.enrichment_agent.enrich_product_data(
                    product, empresa_info
                )
                results.append(enrichment_result)

                # Salvar resultado se bem-sucedido
                if enrichment_result.success:
                    await self._save_enriched_product(product["id"], enrichment_result)

            except Exception as e:
                self.logger.error(
                    f"Erro ao processar produto {product.get('id', 'unknown')}: {e}"
                )

        return results

    async def _save_enriched_product(self, product_id: int, enrichment_result) -> bool:
        """Salva produto enriquecido no banco"""
        try:
            engine = self.db_setup._get_engine()

            # Preparar dados para atualização
            update_data = {}
            enriched_data = enrichment_result.enriched_data

            if "ncm" in enriched_data:
                update_data["ncm"] = enriched_data["ncm"]
            if "cest" in enriched_data:
                update_data["cest"] = enriched_data["cest"]
            if "categoria_automatica" in enriched_data:
                update_data["categoria"] = enriched_data["categoria_automatica"]

            update_data["confianca_ncm"] = enrichment_result.confidence
            update_data["atualizado_em"] = datetime.now()

            # Determinar se requer revisão manual
            manual_review = any(
                "manual" in w.lower() for w in enrichment_result.warnings
            )
            update_data["revisao_manual"] = manual_review

            # Executar atualização
            if update_data:
                with engine.connect() as conn:
                    set_clause = ", ".join([f"{k} = %s" for k in update_data.keys()])
                    query = f"UPDATE produtos SET {set_clause} WHERE id = %s"

                    conn.execute(query, list(update_data.values()) + [product_id])
                    conn.commit()

            # Registrar auditoria
            await self._log_audit_changes(product_id, enrichment_result.changes)

            return True

        except Exception as e:
            self.logger.error(f"Erro ao salvar produto enriquecido: {e}")
            return False

    async def _log_audit_changes(
        self, product_id: int, changes: List[Dict[str, Any]]
    ) -> bool:
        """Registra mudanças na auditoria"""
        try:
            if not changes:
                return True

            engine = self.db_setup._get_engine()

            with engine.connect() as conn:
                for change in changes:
                    audit_query = """
                        INSERT INTO auditoria_classificacoes
                        (produto_id, campo_alterado, valor_anterior, valor_novo, motivo, confianca, origem)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """

                    conn.execute(
                        audit_query,
                        [
                            product_id,
                            change.get("field"),
                            str(change.get("old_value", "")),
                            str(change.get("new_value", "")),
                            change.get("action", ""),
                            change.get("confidence", 0),
                            "sistema_automatico",
                        ],
                    )

                conn.commit()

            return True

        except Exception as e:
            self.logger.error(f"Erro ao registrar auditoria: {e}")
            return False

    def generate_system_report(self) -> Dict[str, Any]:
        """Gera relatório completo do sistema"""
        try:
            # Status atual
            current_status = self.check_system_status()

            # Estatísticas do banco
            db_stats = self.db_setup.get_database_stats()

            # Estatísticas de workflows
            workflow_stats = self.workflow_manager.get_execution_statistics()

            return {
                "timestamp": datetime.now().isoformat(),
                "system_status": asdict(current_status),
                "database_statistics": db_stats,
                "workflow_statistics": workflow_stats,
                "summary": {
                    "system_health": (
                        "healthy"
                        if all(
                            [
                                current_status.database_ready,
                                current_status.agents_ready,
                                current_status.workflows_ready,
                            ]
                        )
                        else "degraded"
                    ),
                    "total_errors": len(current_status.errors),
                    "total_warnings": len(current_status.warnings),
                    "data_completeness": db_stats.get("classificacao_stats", {}).get(
                        "com_ncm", 0
                    )
                    / max(
                        db_stats.get("classificacao_stats", {}).get(
                            "total_produtos", 1
                        ),
                        1,
                    ),
                },
                "recommendations": self._generate_recommendations(
                    current_status, db_stats
                ),
            }

        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório do sistema: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def _generate_recommendations(
        self, status: SystemStatus, db_stats: Dict[str, Any]
    ) -> List[str]:
        """Gera recomendações baseadas no status do sistema"""
        recommendations = []

        if not status.database_ready:
            recommendations.append("🔧 Verificar conexão e configuração do PostgreSQL")

        if not status.agents_ready:
            recommendations.append(
                "🤖 Verificar configuração e dados dos agentes de classificação"
            )

        if not status.data_imported:
            recommendations.append("📥 Importar dados de referência (NCM/CEST)")

        if status.errors:
            recommendations.append("🚨 Resolver erros críticos do sistema")

        # Recomendações baseadas em estatísticas
        classificacao_stats = db_stats.get("classificacao_stats", {})
        total_produtos = classificacao_stats.get("total_produtos", 0)
        com_ncm = classificacao_stats.get("com_ncm", 0)
        requer_revisao = classificacao_stats.get("requer_revisao", 0)

        if total_produtos > 0:
            ncm_completeness = com_ncm / total_produtos
            if ncm_completeness < 0.8:
                recommendations.append(
                    "📋 Executar processo de classificação automática para produtos sem NCM"
                )

            if requer_revisao > 0:
                recommendations.append(
                    f"👀 Revisar manualmente {requer_revisao} produtos que requerem atenção"
                )

        return recommendations
