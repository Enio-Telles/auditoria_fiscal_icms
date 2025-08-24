"""
Agentes de Enriquecimento e Reconciliação - Fase 6
Implementa processamento de dados e reconciliação de informações
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass

from ..core.config import get_settings
from .real_agents import NCMAgent, CESTAgent


@dataclass
class EnrichmentResult:
    """Resultado do enriquecimento de dados"""

    success: bool
    original_data: Dict[str, Any]
    enriched_data: Dict[str, Any]
    confidence: float
    changes: List[Dict[str, Any]]
    warnings: List[str]
    timestamp: datetime


@dataclass
class ReconciliationResult:
    """Resultado da reconciliação de dados"""

    success: bool
    conflicts: List[Dict[str, Any]]
    resolutions: List[Dict[str, Any]]
    final_data: Dict[str, Any]
    confidence: float
    manual_review_required: bool
    timestamp: datetime


class EnrichmentAgent:
    """Agente para enriquecimento de dados de produtos"""

    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.ncm_agent = NCMAgent()
        self.cest_agent = CESTAgent()
        self.enrichment_rules = self._load_enrichment_rules()

    def _load_enrichment_rules(self) -> Dict[str, Any]:
        """Carrega regras de enriquecimento"""
        return {
            "required_fields": ["codigo_produto", "descricao", "ncm", "empresa_id"],
            "optional_fields": [
                "cest",
                "unidade",
                "preco",
                "categoria",
                "atividade_empresa",
            ],
            "validation_rules": {
                "ncm": {"length": 8, "numeric": True, "required": True},
                "cest": {
                    "length": [7, 9],  # XX.XXX.XX ou XX.XXX.XX.X
                    "numeric": True,
                    "required": False,
                },
                "preco": {"type": "numeric", "min_value": 0, "required": False},
            },
            "enrichment_priority": [
                "validate_ncm",
                "determine_missing_ncm",
                "validate_cest",
                "determine_missing_cest",
                "enrich_metadata",
                "validate_business_rules",
            ],
        }

    def enrich_product_data(
        self, product_data: Dict[str, Any], empresa_info: Dict[str, Any] = None
    ) -> EnrichmentResult:
        """Enriquece dados de um produto"""
        try:
            original_data = product_data.copy()
            enriched_data = product_data.copy()
            changes = []
            warnings = []
            overall_confidence = 1.0

            # Validar campos obrigatórios
            missing_fields = self._validate_required_fields(enriched_data)
            if missing_fields:
                warnings.append(f"Campos obrigatórios ausentes: {missing_fields}")
                overall_confidence *= 0.5

            # Executar enriquecimento por prioridade
            for step in self.enrichment_rules["enrichment_priority"]:
                step_result = self._execute_enrichment_step(
                    step, enriched_data, empresa_info
                )

                if step_result:
                    enriched_data.update(step_result.get("data", {}))
                    changes.extend(step_result.get("changes", []))
                    warnings.extend(step_result.get("warnings", []))
                    overall_confidence *= step_result.get("confidence", 1.0)

            # Determinar sucesso
            success = len(missing_fields) == 0 and overall_confidence > 0.6

            return EnrichmentResult(
                success=success,
                original_data=original_data,
                enriched_data=enriched_data,
                confidence=overall_confidence,
                changes=changes,
                warnings=warnings,
                timestamp=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Erro no enriquecimento: {e}")
            return EnrichmentResult(
                success=False,
                original_data=product_data,
                enriched_data=product_data,
                confidence=0.0,
                changes=[],
                warnings=[f"Erro no enriquecimento: {str(e)}"],
                timestamp=datetime.now(),
            )

    def enrich_batch_data(
        self, products_data: List[Dict[str, Any]], empresa_info: Dict[str, Any] = None
    ) -> List[EnrichmentResult]:
        """Enriquece dados de múltiplos produtos"""
        results = []

        for i, product_data in enumerate(products_data):
            self.logger.info(f"Enriquecendo produto {i+1}/{len(products_data)}")
            result = self.enrich_product_data(product_data, empresa_info)
            results.append(result)

        return results

    def _validate_required_fields(self, data: Dict[str, Any]) -> List[str]:
        """Valida campos obrigatórios"""
        missing = []
        for field in self.enrichment_rules["required_fields"]:
            if field not in data or not data[field]:
                missing.append(field)
        return missing

    def _execute_enrichment_step(
        self, step: str, data: Dict[str, Any], empresa_info: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Executa um passo específico do enriquecimento"""
        try:
            if step == "validate_ncm":
                return self._validate_ncm_step(data, empresa_info)
            elif step == "determine_missing_ncm":
                return self._determine_missing_ncm_step(data, empresa_info)
            elif step == "validate_cest":
                return self._validate_cest_step(data, empresa_info)
            elif step == "determine_missing_cest":
                return self._determine_missing_cest_step(data, empresa_info)
            elif step == "enrich_metadata":
                return self._enrich_metadata_step(data, empresa_info)
            elif step == "validate_business_rules":
                return self._validate_business_rules_step(data, empresa_info)

            return None

        except Exception as e:
            self.logger.error(f"Erro no passo {step}: {e}")
            return {
                "data": {},
                "changes": [],
                "warnings": [f"Erro no passo {step}: {str(e)}"],
                "confidence": 0.5,
            }

    def _validate_ncm_step(
        self, data: Dict[str, Any], empresa_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Valida NCM existente"""
        if not data.get("ncm"):
            return {"data": {}, "changes": [], "warnings": [], "confidence": 1.0}

        atividade = empresa_info.get("atividade") if empresa_info else None
        result = self.ncm_agent.validate_ncm(
            ncm_code=data["ncm"],
            description=data.get("descricao", ""),
            empresa_atividade=atividade,
        )

        changes = []
        warnings = []
        enriched_data = {}

        if result["valid"]:
            enriched_data["ncm_validado"] = result["ncm_validado"]
            enriched_data["ncm_info"] = result.get("ncm_info")
            changes.append(
                {
                    "field": "ncm",
                    "action": "validated",
                    "old_value": data["ncm"],
                    "new_value": result["ncm_validado"],
                    "confidence": result["confidence"],
                }
            )
        else:
            warnings.append(f"NCM inválido: {result['reason']}")

        return {
            "data": enriched_data,
            "changes": changes,
            "warnings": warnings,
            "confidence": result["confidence"],
        }

    def _determine_missing_ncm_step(
        self, data: Dict[str, Any], empresa_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determina NCM ausente"""
        if data.get("ncm"):  # Já possui NCM
            return {"data": {}, "changes": [], "warnings": [], "confidence": 1.0}

        if not data.get("descricao"):
            return {
                "data": {},
                "changes": [],
                "warnings": ["Não é possível determinar NCM sem descrição"],
                "confidence": 0.0,
            }

        atividade = empresa_info.get("atividade") if empresa_info else None
        result = self.ncm_agent.determine_ncm(
            description=data["descricao"], empresa_atividade=atividade
        )

        changes = []
        warnings = []
        enriched_data = {}

        if result["success"] and result["ncm_determinado"]:
            enriched_data["ncm"] = result["ncm_determinado"]
            enriched_data["ncm_info"] = result.get("ncm_info")
            enriched_data["ncm_determinado_automaticamente"] = True
            changes.append(
                {
                    "field": "ncm",
                    "action": "determined",
                    "old_value": None,
                    "new_value": result["ncm_determinado"],
                    "confidence": result["confidence"],
                }
            )
        else:
            warnings.append(
                f"NCM não determinado: {result.get('reason', 'Razão desconhecida')}"
            )

        return {
            "data": enriched_data,
            "changes": changes,
            "warnings": warnings,
            "confidence": result["confidence"],
        }

    def _validate_cest_step(
        self, data: Dict[str, Any], empresa_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Valida CEST existente"""
        if not data.get("cest"):
            return {"data": {}, "changes": [], "warnings": [], "confidence": 1.0}

        ncm_code = data.get("ncm") or data.get("ncm_determinado", "")
        atividade = empresa_info.get("atividade") if empresa_info else None

        result = self.cest_agent.validate_cest(
            cest_code=data["cest"],
            ncm_code=ncm_code,
            description=data.get("descricao", ""),
            empresa_atividade=atividade,
        )

        changes = []
        warnings = []
        enriched_data = {}

        if result["valid"]:
            enriched_data["cest_validado"] = result["cest_validado"]
            enriched_data["cest_info"] = result.get("cest_info")
            changes.append(
                {
                    "field": "cest",
                    "action": "validated",
                    "old_value": data["cest"],
                    "new_value": result["cest_validado"],
                    "confidence": result["confidence"],
                }
            )
        else:
            warnings.append(f"CEST inválido: {result['reason']}")

        return {
            "data": enriched_data,
            "changes": changes,
            "warnings": warnings,
            "confidence": result["confidence"],
        }

    def _determine_missing_cest_step(
        self, data: Dict[str, Any], empresa_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determina CEST ausente"""
        if data.get("cest"):  # Já possui CEST
            return {"data": {}, "changes": [], "warnings": [], "confidence": 1.0}

        ncm_code = data.get("ncm") or data.get("ncm_determinado", "")
        if not ncm_code:
            return {
                "data": {},
                "changes": [],
                "warnings": ["Não é possível determinar CEST sem NCM"],
                "confidence": 0.0,
            }

        atividade = empresa_info.get("atividade") if empresa_info else None
        result = self.cest_agent.determine_cest(
            ncm_code=ncm_code,
            description=data.get("descricao", ""),
            empresa_atividade=atividade,
        )

        changes = []
        warnings = []
        enriched_data = {}

        if result["success"]:
            if result["cest_determinado"]:
                enriched_data["cest"] = result["cest_determinado"]
                enriched_data["cest_info"] = result.get("cest_info")
                enriched_data["cest_determinado_automaticamente"] = True
                changes.append(
                    {
                        "field": "cest",
                        "action": "determined",
                        "old_value": None,
                        "new_value": result["cest_determinado"],
                        "confidence": result["confidence"],
                    }
                )
            else:
                enriched_data["cest"] = None
                enriched_data["cest_nao_aplicavel"] = True
                changes.append(
                    {
                        "field": "cest",
                        "action": "determined_not_applicable",
                        "old_value": None,
                        "new_value": None,
                        "confidence": result["confidence"],
                    }
                )
        else:
            warnings.append(
                f"CEST não determinado: {result.get('reason', 'Razão desconhecida')}"
            )

        return {
            "data": enriched_data,
            "changes": changes,
            "warnings": warnings,
            "confidence": result["confidence"],
        }

    def _enrich_metadata_step(
        self, data: Dict[str, Any], empresa_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enriquece metadados do produto"""
        enriched_data = {}
        changes = []

        # Adicionar timestamp de processamento
        enriched_data["processado_em"] = datetime.now().isoformat()

        # Adicionar informações da empresa se disponível
        if empresa_info:
            enriched_data["empresa_atividade"] = empresa_info.get("atividade")
            enriched_data["empresa_regime_tributario"] = empresa_info.get(
                "regime_tributario"
            )

        # Determinar categoria baseada no NCM
        ncm_code = data.get("ncm") or data.get("ncm_determinado")
        if ncm_code:
            category = self._determine_category_from_ncm(ncm_code)
            if category:
                enriched_data["categoria_automatica"] = category
                changes.append(
                    {
                        "field": "categoria",
                        "action": "determined",
                        "old_value": data.get("categoria"),
                        "new_value": category,
                        "confidence": 0.8,
                    }
                )

        # Normalizar unidade
        if data.get("unidade"):
            normalized_unit = self._normalize_unit(data["unidade"])
            if normalized_unit != data["unidade"]:
                enriched_data["unidade"] = normalized_unit
                changes.append(
                    {
                        "field": "unidade",
                        "action": "normalized",
                        "old_value": data["unidade"],
                        "new_value": normalized_unit,
                        "confidence": 1.0,
                    }
                )

        return {
            "data": enriched_data,
            "changes": changes,
            "warnings": [],
            "confidence": 0.9,
        }

    def _validate_business_rules_step(
        self, data: Dict[str, Any], empresa_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Valida regras de negócio"""
        warnings = []

        # Verificar preço
        if data.get("preco") and float(data["preco"]) <= 0:
            warnings.append("Preço deve ser maior que zero")

        # Verificar compatibilidade CEST-empresa
        cest = data.get("cest") or data.get("cest_determinado")
        if cest and empresa_info:
            regime = empresa_info.get("regime_tributario", "").lower()
            if "simples" in regime and cest:
                warnings.append(
                    "Empresas do Simples Nacional podem não precisar de CEST"
                )

        # Verificar completude dos dados
        completeness_score = self._calculate_completeness_score(data)
        if completeness_score < 0.7:
            warnings.append(f"Dados incompletos (score: {completeness_score:.1%})")

        return {
            "data": {"completeness_score": completeness_score},
            "changes": [],
            "warnings": warnings,
            "confidence": completeness_score,
        }

    def _determine_category_from_ncm(self, ncm_code: str) -> Optional[str]:
        """Determina categoria baseada no NCM"""
        if not ncm_code or len(ncm_code) < 2:
            return None

        chapter = ncm_code[:2]

        category_mapping = {
            "01": "Animais vivos",
            "02": "Carnes e miudezas",
            "03": "Peixes e crustáceos",
            "04": "Laticínios",
            "05": "Produtos de origem animal",
            "06": "Plantas vivas",
            "07": "Produtos hortícolas",
            "08": "Frutas",
            "09": "Café, chá, especiarias",
            "10": "Cereais",
            # ... adicionar mais mapeamentos conforme necessário
        }

        return category_mapping.get(chapter)

    def _normalize_unit(self, unit: str) -> str:
        """Normaliza unidade de medida"""
        if not unit:
            return unit

        unit_mapping = {
            "un": "UN",
            "und": "UN",
            "unidade": "UN",
            "pc": "PC",
            "peca": "PC",
            "peça": "PC",
            "kg": "KG",
            "kilo": "KG",
            "quilograma": "KG",
            "l": "L",
            "litro": "L",
            "m": "M",
            "metro": "M",
        }

        return unit_mapping.get(unit.lower(), unit.upper())

    def _calculate_completeness_score(self, data: Dict[str, Any]) -> float:
        """Calcula score de completude dos dados"""
        required_weight = 0.7
        optional_weight = 0.3

        # Campos obrigatórios
        required_present = sum(
            1 for field in self.enrichment_rules["required_fields"] if data.get(field)
        )
        required_score = required_present / len(
            self.enrichment_rules["required_fields"]
        )

        # Campos opcionais
        optional_present = sum(
            1 for field in self.enrichment_rules["optional_fields"] if data.get(field)
        )
        optional_score = optional_present / len(
            self.enrichment_rules["optional_fields"]
        )

        return required_score * required_weight + optional_score * optional_weight


class ReconciliationAgent:
    """Agente para reconciliação de dados entre diferentes fontes"""

    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.reconciliation_rules = self._load_reconciliation_rules()

    def _load_reconciliation_rules(self) -> Dict[str, Any]:
        """Carrega regras de reconciliação"""
        return {
            "conflict_resolution": {
                "ncm": {
                    "priority": [
                        "manual",
                        "agent_high_confidence",
                        "database",
                        "default",
                    ],
                    "confidence_threshold": 0.8,
                },
                "cest": {
                    "priority": [
                        "manual",
                        "agent_high_confidence",
                        "database",
                        "default",
                    ],
                    "confidence_threshold": 0.7,
                },
                "preco": {
                    "priority": ["manual", "most_recent", "database", "default"],
                    "variance_threshold": 0.1,  # 10% de variação
                },
            },
            "merge_strategies": {
                "concatenate": ["descricao", "observacoes"],
                "take_highest": ["preco", "confidence"],
                "take_most_recent": ["data_atualizacao"],
                "manual_review": ["ncm", "cest"],
            },
        }

    def reconcile_product_data(
        self, sources: List[Dict[str, Any]], source_names: List[str] = None
    ) -> ReconciliationResult:
        """Reconcilia dados de produto de múltiplas fontes"""
        try:
            if not sources:
                return ReconciliationResult(
                    success=False,
                    conflicts=[],
                    resolutions=[],
                    final_data={},
                    confidence=0.0,
                    manual_review_required=True,
                    timestamp=datetime.now(),
                )

            if not source_names:
                source_names = [f"fonte_{i+1}" for i in range(len(sources))]

            # Identificar conflitos
            conflicts = self._identify_conflicts(sources, source_names)

            # Resolver conflitos
            resolutions = []
            final_data = {}
            overall_confidence = 1.0
            manual_review_required = False

            # Combinar todos os campos únicos
            all_fields = set()
            for source in sources:
                all_fields.update(source.keys())

            # Processar cada campo
            for field in all_fields:
                field_values = [
                    (source.get(field), name)
                    for source, name in zip(sources, source_names)
                    if source.get(field) is not None
                ]

                if not field_values:
                    continue

                if len(field_values) == 1:
                    # Sem conflito
                    final_data[field] = field_values[0][0]
                else:
                    # Resolver conflito
                    resolution = self._resolve_field_conflict(
                        field, field_values, conflicts
                    )
                    final_data[field] = resolution["value"]
                    resolutions.append(resolution)
                    overall_confidence *= resolution["confidence"]

                    if resolution["manual_review_required"]:
                        manual_review_required = True

            # Adicionar metadados da reconciliação
            final_data["reconciliacao"] = {
                "fontes": source_names,
                "timestamp": datetime.now().isoformat(),
                "conflitos_resolvidos": len(resolutions),
                "revisao_manual_necessaria": manual_review_required,
            }

            success = overall_confidence > 0.5 and not any(
                c["severity"] == "critical" for c in conflicts
            )

            return ReconciliationResult(
                success=success,
                conflicts=conflicts,
                resolutions=resolutions,
                final_data=final_data,
                confidence=overall_confidence,
                manual_review_required=manual_review_required,
                timestamp=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Erro na reconciliação: {e}")
            return ReconciliationResult(
                success=False,
                conflicts=[],
                resolutions=[],
                final_data={},
                confidence=0.0,
                manual_review_required=True,
                timestamp=datetime.now(),
            )

    def _identify_conflicts(
        self, sources: List[Dict[str, Any]], source_names: List[str]
    ) -> List[Dict[str, Any]]:
        """Identifica conflitos entre as fontes"""
        conflicts = []

        # Campos para verificar conflitos
        conflict_fields = ["ncm", "cest", "preco", "unidade", "categoria"]

        for field in conflict_fields:
            values = {}
            for i, source in enumerate(sources):
                if field in source and source[field] is not None:
                    value = str(source[field]).strip()
                    if value not in values:
                        values[value] = []
                    values[value].append(source_names[i])

            if len(values) > 1:
                severity = self._determine_conflict_severity(field, list(values.keys()))
                conflicts.append(
                    {
                        "field": field,
                        "values": values,
                        "severity": severity,
                        "description": f"Conflito no campo {field}: {list(values.keys())}",
                    }
                )

        return conflicts

    def _determine_conflict_severity(self, field: str, values: List[str]) -> str:
        """Determina severidade do conflito"""
        if field in ["ncm", "cest"]:
            return "critical"
        elif field in ["preco"]:
            # Verificar se a diferença é significativa
            try:
                numeric_values = [
                    float(v)
                    for v in values
                    if v.replace(".", "").replace(",", "").isdigit()
                ]
                if len(numeric_values) > 1:
                    max_val = max(numeric_values)
                    min_val = min(numeric_values)
                    variance = (max_val - min_val) / max_val if max_val > 0 else 0
                    return "critical" if variance > 0.2 else "medium"
            except Exception:
                pass
            return "medium"
        else:
            return "low"

    def _resolve_field_conflict(
        self,
        field: str,
        field_values: List[Tuple[Any, str]],
        conflicts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Resolve conflito em um campo específico"""
        if len(field_values) == 1:
            return {
                "field": field,
                "value": field_values[0][0],
                "source": field_values[0][1],
                "strategy": "no_conflict",
                "confidence": 1.0,
                "manual_review_required": False,
            }

        # Obter regras para o campo
        field_rules = self.reconciliation_rules["conflict_resolution"].get(field, {})
        priority = field_rules.get("priority", ["manual"])

        # Aplicar estratégia de resolução
        for strategy in priority:
            if strategy == "manual":
                continue
            elif strategy == "agent_high_confidence":
                # Procurar valor com alta confiança
                for value, source in field_values:
                    if isinstance(value, dict) and value.get(
                        "confidence", 0
                    ) > field_rules.get("confidence_threshold", 0.8):
                        return {
                            "field": field,
                            "value": value,
                            "source": source,
                            "strategy": "agent_high_confidence",
                            "confidence": value.get("confidence", 0.8),
                            "manual_review_required": False,
                        }
            elif strategy == "most_recent":
                # Implementar lógica de mais recente se timestamps disponíveis
                pass
            elif strategy == "database":
                # Preferir fonte que parece ser de base de dados
                for value, source in field_values:
                    if "database" in source.lower() or "db" in source.lower():
                        return {
                            "field": field,
                            "value": value,
                            "source": source,
                            "strategy": "database_priority",
                            "confidence": 0.8,
                            "manual_review_required": False,
                        }

        # Fallback: primeiro valor, mas requer revisão manual
        return {
            "field": field,
            "value": field_values[0][0],
            "source": field_values[0][1],
            "strategy": "manual_review_required",
            "confidence": 0.5,
            "manual_review_required": True,
            "conflict_values": [(v, s) for v, s in field_values],
        }

    def generate_reconciliation_report(
        self, results: List[ReconciliationResult]
    ) -> Dict[str, Any]:
        """Gera relatório de reconciliação"""
        total_products = len(results)
        successful_reconciliations = sum(1 for r in results if r.success)
        manual_reviews_required = sum(1 for r in results if r.manual_review_required)

        # Agregar conflitos por tipo
        conflict_summary = {}
        resolution_summary = {}

        for result in results:
            for conflict in result.conflicts:
                field = conflict["field"]
                severity = conflict["severity"]
                key = f"{field}_{severity}"
                conflict_summary[key] = conflict_summary.get(key, 0) + 1

            for resolution in result.resolutions:
                strategy = resolution["strategy"]
                resolution_summary[strategy] = resolution_summary.get(strategy, 0) + 1

        return {
            "summary": {
                "total_products": total_products,
                "successful_reconciliations": successful_reconciliations,
                "success_rate": (
                    successful_reconciliations / total_products
                    if total_products > 0
                    else 0
                ),
                "manual_reviews_required": manual_reviews_required,
                "manual_review_rate": (
                    manual_reviews_required / total_products
                    if total_products > 0
                    else 0
                ),
            },
            "conflict_analysis": conflict_summary,
            "resolution_strategies": resolution_summary,
            "recommendations": self._generate_reconciliation_recommendations(results),
            "timestamp": datetime.now().isoformat(),
        }
