"""
Reconciler Agent - Agente Especialista em Reconciliação de Dados
===============================================================

Este agente é responsável por:
- Reconciliação de dados entre diferentes fontes
- Validação de consistência de dados
- Identificação de divergências e conflitos
- Sugestão de correções e padronizações
- Auditoria de qualidade de dados
"""

import json
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from difflib import SequenceMatcher
from collections import defaultdict
import statistics

from .base_agent import BaseAgent, AgentTask


class ReconcilerAgent(BaseAgent):
    """
    Agente especializado em reconciliação e validação de dados.

    Capacidades:
    - Reconciliação entre fontes de dados
    - Detecção de inconsistências
    - Validação de integridade referencial
    - Análise de qualidade de dados
    - Sugestão de correções automáticas
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o agente de reconciliação.

        Args:
            config: Configurações específicas do agente
        """
        default_config = {
            "similarity_threshold": 0.85,
            "max_suggestions": 10,
            "enable_auto_correction": True,
            "validation_strictness": "high",
            "batch_size": 1000,
            "confidence_threshold": 0.8,
            "data_quality_weights": {
                "completeness": 0.25,
                "accuracy": 0.30,
                "consistency": 0.25,
                "timeliness": 0.20,
            },
        }

        # Merge configurações
        agent_config = {**default_config, **(config or {})}

        super().__init__(name="ReconcilerAgent", config=agent_config)

        # Caches para otimização
        self.reconciliation_cache = {}
        self.validation_rules_cache = {}
        self.correction_patterns = {}

        # Métricas de qualidade
        self.quality_metrics = defaultdict(list)

        self.logger.info("ReconcilerAgent inicializado para reconciliação de dados")

    def get_capabilities(self) -> List[str]:
        """
        Retorna capacidades do agente de reconciliação.

        Returns:
            Lista de capacidades
        """
        return [
            "reconcile_datasets",
            "detect_inconsistencies",
            "validate_data_integrity",
            "analyze_data_quality",
            "suggest_corrections",
            "merge_duplicate_records",
            "validate_referential_integrity",
            "audit_data_changes",
            "standardize_data_formats",
            "compare_data_sources",
        ]

    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Processa tarefa de reconciliação de dados.

        Args:
            task: Tarefa contendo dados para reconciliação

        Returns:
            Resultado da reconciliação
        """
        task_type = task.type
        data = task.data

        self.logger.info(f"Processando tarefa de reconciliação: {task_type}")

        if task_type == "reconcile_datasets":
            return await self._reconcile_datasets(data)
        elif task_type == "detect_inconsistencies":
            return await self._detect_inconsistencies(data)
        elif task_type == "validate_data_integrity":
            return await self._validate_data_integrity(data)
        elif task_type == "analyze_data_quality":
            return await self._analyze_data_quality(data)
        elif task_type == "suggest_corrections":
            return await self._suggest_corrections(data)
        elif task_type == "merge_duplicate_records":
            return await self._merge_duplicate_records(data)
        elif task_type == "validate_referential_integrity":
            return await self._validate_referential_integrity(data)
        elif task_type == "audit_data_changes":
            return await self._audit_data_changes(data)
        elif task_type == "standardize_data_formats":
            return await self._standardize_data_formats(data)
        elif task_type == "compare_data_sources":
            return await self._compare_data_sources(data)
        else:
            raise ValueError(
                f"Tipo de tarefa de reconciliação não suportado: {task_type}"
            )

    async def _reconcile_datasets(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reconcilia múltiplos datasets identificando correspondências e divergências.

        Args:
            data: Datasets para reconciliação

        Returns:
            Resultado da reconciliação
        """
        datasets = data.get("datasets", [])
        reconciliation_keys = data.get("keys", ["id"])
        comparison_fields = data.get("fields", [])

        self.logger.info(f"Reconciliando {len(datasets)} datasets")

        if len(datasets) < 2:
            return {"error": "Pelo menos 2 datasets são necessários para reconciliação"}

        # 1. Preparar dados para reconciliação
        prepared_datasets = self._prepare_datasets_for_reconciliation(
            datasets, reconciliation_keys
        )

        # 2. Identificar registros correspondentes
        matches = self._find_record_matches(prepared_datasets, reconciliation_keys)

        # 3. Detectar discrepâncias
        discrepancies = self._detect_field_discrepancies(matches, comparison_fields)

        # 4. Calcular estatísticas de reconciliação
        reconciliation_stats = self._calculate_reconciliation_statistics(
            prepared_datasets, matches, discrepancies
        )

        # 5. Gerar relatório de reconciliação
        reconciliation_report = self._generate_reconciliation_report(
            prepared_datasets, matches, discrepancies, reconciliation_stats
        )

        # 6. Sugerir ações corretivas
        corrective_actions = self._suggest_reconciliation_actions(
            discrepancies, reconciliation_stats
        )

        result = {
            "reconciliation_summary": {
                "total_datasets": len(datasets),
                "reconciliation_keys": reconciliation_keys,
                "comparison_fields": comparison_fields,
                "processing_timestamp": datetime.now().isoformat(),
            },
            "matches": matches,
            "discrepancies": discrepancies,
            "statistics": reconciliation_stats,
            "report": reconciliation_report,
            "corrective_actions": corrective_actions,
            "data_quality_score": self._calculate_overall_quality_score(
                reconciliation_stats
            ),
        }

        self.logger.info(
            f"Reconciliação concluída: {len(matches)} correspondências, {len(discrepancies)} discrepâncias"
        )
        return result

    async def _detect_inconsistencies(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detecta inconsistências em um dataset.

        Args:
            data: Dataset para análise de inconsistências

        Returns:
            Inconsistências detectadas
        """
        dataset = data.get("dataset", [])
        validation_rules = data.get("rules", {})

        self.logger.info(f"Detectando inconsistências em {len(dataset)} registros")

        inconsistencies = {
            "format_inconsistencies": [],
            "value_inconsistencies": [],
            "logical_inconsistencies": [],
            "reference_inconsistencies": [],
        }

        # 1. Inconsistências de formato
        format_inconsistencies = self._detect_format_inconsistencies(dataset)
        inconsistencies["format_inconsistencies"] = format_inconsistencies

        # 2. Inconsistências de valor
        value_inconsistencies = self._detect_value_inconsistencies(
            dataset, validation_rules
        )
        inconsistencies["value_inconsistencies"] = value_inconsistencies

        # 3. Inconsistências lógicas
        logical_inconsistencies = self._detect_logical_inconsistencies(dataset)
        inconsistencies["logical_inconsistencies"] = logical_inconsistencies

        # 4. Inconsistências de referência
        reference_inconsistencies = self._detect_reference_inconsistencies(dataset)
        inconsistencies["reference_inconsistencies"] = reference_inconsistencies

        # 5. Calcular severidade
        severity_analysis = self._analyze_inconsistency_severity(inconsistencies)

        # 6. Priorizar correções
        correction_priorities = self._prioritize_corrections(
            inconsistencies, severity_analysis
        )

        result = {
            "dataset_summary": {
                "total_records": len(dataset),
                "analysis_timestamp": datetime.now().isoformat(),
            },
            "inconsistencies": inconsistencies,
            "severity_analysis": severity_analysis,
            "correction_priorities": correction_priorities,
            "impact_assessment": self._assess_inconsistency_impact(inconsistencies),
            "recommendations": self._generate_inconsistency_recommendations(
                inconsistencies, severity_analysis
            ),
        }

        total_inconsistencies = sum(
            len(inconsistencies[key]) for key in inconsistencies
        )
        self.logger.info(f"Detectadas {total_inconsistencies} inconsistências")

        return result

    async def _validate_data_integrity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida integridade de dados incluindo constraints e relacionamentos.

        Args:
            data: Dados para validação de integridade

        Returns:
            Resultado da validação
        """
        dataset = data.get("dataset", [])
        constraints = data.get("constraints", {})
        relationships = data.get("relationships", [])

        self.logger.info(f"Validando integridade de {len(dataset)} registros")

        validation_results = {
            "constraint_violations": [],
            "relationship_violations": [],
            "unique_violations": [],
            "null_violations": [],
            "range_violations": [],
        }

        # 1. Validar constraints de unicidade
        unique_violations = self._validate_unique_constraints(
            dataset, constraints.get("unique", [])
        )
        validation_results["unique_violations"] = unique_violations

        # 2. Validar constraints de nulidade
        null_violations = self._validate_null_constraints(
            dataset, constraints.get("not_null", [])
        )
        validation_results["null_violations"] = null_violations

        # 3. Validar constraints de range/domínio
        range_violations = self._validate_range_constraints(
            dataset, constraints.get("ranges", {})
        )
        validation_results["range_violations"] = range_violations

        # 4. Validar relacionamentos (integridade referencial)
        relationship_violations = self._validate_relationships(dataset, relationships)
        validation_results["relationship_violations"] = relationship_violations

        # 5. Validar constraints customizadas
        if "custom" in constraints:
            custom_violations = self._validate_custom_constraints(
                dataset, constraints["custom"]
            )
            validation_results["constraint_violations"] = custom_violations

        # 6. Calcular score de integridade
        integrity_score = self._calculate_integrity_score(
            validation_results, len(dataset)
        )

        # 7. Gerar recomendações de correção
        integrity_recommendations = self._generate_integrity_recommendations(
            validation_results
        )

        result = {
            "validation_summary": {
                "total_records": len(dataset),
                "constraints_checked": len(constraints),
                "relationships_checked": len(relationships),
                "validation_timestamp": datetime.now().isoformat(),
            },
            "validation_results": validation_results,
            "integrity_score": integrity_score,
            "pass_rate": self._calculate_pass_rate(validation_results, len(dataset)),
            "recommendations": integrity_recommendations,
            "critical_issues": self._identify_critical_integrity_issues(
                validation_results
            ),
        }

        total_violations = sum(
            len(validation_results[key]) for key in validation_results
        )
        self.logger.info(
            f"Validação concluída: {total_violations} violações encontradas"
        )

        return result

    async def _analyze_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa qualidade geral dos dados usando múltiplas dimensões.

        Args:
            data: Dataset para análise de qualidade

        Returns:
            Análise de qualidade de dados
        """
        dataset = data.get("dataset", [])
        quality_dimensions = data.get(
            "dimensions", ["completeness", "accuracy", "consistency", "timeliness"]
        )

        self.logger.info(f"Analisando qualidade de {len(dataset)} registros")

        quality_analysis = {}

        # 1. Completude (completeness)
        if "completeness" in quality_dimensions:
            quality_analysis["completeness"] = self._analyze_completeness(dataset)

        # 2. Precisão (accuracy)
        if "accuracy" in quality_dimensions:
            quality_analysis["accuracy"] = self._analyze_accuracy(dataset)

        # 3. Consistência (consistency)
        if "consistency" in quality_dimensions:
            quality_analysis["consistency"] = self._analyze_consistency(dataset)

        # 4. Atualidade (timeliness)
        if "timeliness" in quality_dimensions:
            quality_analysis["timeliness"] = self._analyze_timeliness(dataset)

        # 5. Validade (validity)
        if "validity" in quality_dimensions:
            quality_analysis["validity"] = self._analyze_validity(dataset)

        # 6. Unicidade (uniqueness)
        if "uniqueness" in quality_dimensions:
            quality_analysis["uniqueness"] = self._analyze_uniqueness(dataset)

        # 7. Calcular score geral de qualidade
        overall_quality_score = self._calculate_weighted_quality_score(quality_analysis)

        # 8. Identificar áreas problemáticas
        problem_areas = self._identify_quality_problem_areas(quality_analysis)

        # 9. Gerar plano de melhoria
        improvement_plan = self._generate_quality_improvement_plan(
            quality_analysis, problem_areas
        )

        result = {
            "quality_summary": {
                "total_records": len(dataset),
                "dimensions_analyzed": quality_dimensions,
                "analysis_timestamp": datetime.now().isoformat(),
            },
            "quality_analysis": quality_analysis,
            "overall_quality_score": overall_quality_score,
            "quality_grade": self._assign_quality_grade(overall_quality_score),
            "problem_areas": problem_areas,
            "improvement_plan": improvement_plan,
            "trending": self._analyze_quality_trends(),
        }

        self.logger.info(
            f"Análise de qualidade concluída: score {overall_quality_score:.2f}"
        )
        return result

    async def _suggest_corrections(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sugere correções automáticas para problemas de dados identificados.

        Args:
            data: Problemas de dados para correção

        Returns:
            Sugestões de correção
        """
        issues = data.get("issues", [])
        dataset = data.get("dataset", [])
        correction_confidence_threshold = data.get("confidence_threshold", 0.8)

        self.logger.info(f"Sugerindo correções para {len(issues)} problemas")

        correction_suggestions = {
            "automatic_corrections": [],
            "manual_review_required": [],
            "pattern_based_corrections": [],
            "reference_based_corrections": [],
        }

        for issue in issues:
            issue_type = issue.get("type", "unknown")
            suggestions = []

            if issue_type == "format_inconsistency":
                suggestions = self._suggest_format_corrections(issue, dataset)
            elif issue_type == "value_inconsistency":
                suggestions = self._suggest_value_corrections(issue, dataset)
            elif issue_type == "missing_value":
                suggestions = self._suggest_missing_value_corrections(issue, dataset)
            elif issue_type == "duplicate_record":
                suggestions = self._suggest_duplicate_resolution(issue, dataset)
            elif issue_type == "reference_integrity":
                suggestions = self._suggest_reference_corrections(issue, dataset)

            # Classificar sugestões por confiança
            for suggestion in suggestions:
                confidence = suggestion.get("confidence", 0.0)

                if confidence >= correction_confidence_threshold:
                    correction_suggestions["automatic_corrections"].append(suggestion)
                elif confidence >= 0.5:
                    correction_suggestions["manual_review_required"].append(suggestion)
                else:
                    # Tentar correções baseadas em padrões
                    pattern_corrections = self._apply_pattern_corrections(
                        issue, dataset
                    )
                    correction_suggestions["pattern_based_corrections"].extend(
                        pattern_corrections
                    )

        # Aplicar correções de referência cruzada
        reference_corrections = self._suggest_cross_reference_corrections(
            issues, dataset
        )
        correction_suggestions["reference_based_corrections"] = reference_corrections

        # Priorizar correções
        prioritized_corrections = self._prioritize_corrections_by_impact(
            correction_suggestions
        )

        # Estimar esforço de correção
        effort_estimation = self._estimate_correction_effort(correction_suggestions)

        result = {
            "correction_summary": {
                "total_issues": len(issues),
                "suggestions_generated": sum(
                    len(correction_suggestions[key]) for key in correction_suggestions
                ),
                "suggestion_timestamp": datetime.now().isoformat(),
            },
            "suggestions": correction_suggestions,
            "prioritized_corrections": prioritized_corrections,
            "effort_estimation": effort_estimation,
            "automation_potential": self._calculate_automation_potential(
                correction_suggestions
            ),
            "risk_assessment": self._assess_correction_risks(correction_suggestions),
        }

        self.logger.info(
            f"Sugestões geradas: {result['correction_summary']['suggestions_generated']}"
        )
        return result

    async def _merge_duplicate_records(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identifica e mescla registros duplicados.

        Args:
            data: Dataset com potenciais duplicatas

        Returns:
            Resultado da fusão de duplicatas
        """
        dataset = data.get("dataset", [])
        similarity_threshold = data.get(
            "similarity_threshold", self.config["similarity_threshold"]
        )
        merge_strategy = data.get("strategy", "conservative")

        self.logger.info(f"Identificando duplicatas em {len(dataset)} registros")

        # 1. Detectar grupos de duplicatas
        duplicate_groups = self._detect_duplicate_groups(dataset, similarity_threshold)

        # 2. Aplicar estratégia de fusão
        merge_results = []

        for group in duplicate_groups:
            if merge_strategy == "conservative":
                merged_record = self._conservative_merge(group)
            elif merge_strategy == "aggressive":
                merged_record = self._aggressive_merge(group)
            else:  # intelligent
                merged_record = self._intelligent_merge(group)

            merge_results.append(
                {
                    "original_records": group,
                    "merged_record": merged_record,
                    "confidence": self._calculate_merge_confidence(
                        group, merged_record
                    ),
                    "conflicts_resolved": self._identify_resolved_conflicts(
                        group, merged_record
                    ),
                }
            )

        # 3. Calcular estatísticas de fusão
        merge_statistics = self._calculate_merge_statistics(
            dataset, duplicate_groups, merge_results
        )

        # 4. Gerar dataset limpo
        clean_dataset = self._generate_clean_dataset(
            dataset, duplicate_groups, merge_results
        )

        result = {
            "merge_summary": {
                "original_records": len(dataset),
                "duplicate_groups_found": len(duplicate_groups),
                "records_merged": sum(len(group) for group in duplicate_groups),
                "final_record_count": len(clean_dataset),
                "merge_timestamp": datetime.now().isoformat(),
            },
            "duplicate_groups": duplicate_groups,
            "merge_results": merge_results,
            "statistics": merge_statistics,
            "clean_dataset": clean_dataset,
            "quality_improvement": self._calculate_quality_improvement(
                dataset, clean_dataset
            ),
        }

        self.logger.info(f"Fusão concluída: {len(duplicate_groups)} grupos processados")
        return result

    # Métodos auxiliares principais

    def _prepare_datasets_for_reconciliation(
        self, datasets: List[List[Dict]], keys: List[str]
    ) -> List[Dict]:
        """Prepara datasets para reconciliação."""
        prepared = []

        for i, dataset in enumerate(datasets):
            prepared.append(
                {
                    "id": f"dataset_{i}",
                    "data": dataset,
                    "indexed_data": self._create_index(dataset, keys),
                    "record_count": len(dataset),
                }
            )

        return prepared

    def _create_index(self, dataset: List[Dict], keys: List[str]) -> Dict:
        """Cria índice para otimizar comparações."""
        index = {}

        for record in dataset:
            # Criar chave composta
            key_values = []
            for key in keys:
                value = record.get(key, "")
                key_values.append(str(value).strip().lower())

            composite_key = "|".join(key_values)

            if composite_key not in index:
                index[composite_key] = []
            index[composite_key].append(record)

        return index

    def _find_record_matches(
        self, prepared_datasets: List[Dict], keys: List[str]
    ) -> List[Dict]:
        """Encontra correspondências entre registros."""
        matches = []

        if len(prepared_datasets) < 2:
            return matches

        # Comparar primeiro dataset com os demais
        base_dataset = prepared_datasets[0]

        for base_key, base_records in base_dataset["indexed_data"].items():
            match_group = {
                "key": base_key,
                "records": {base_dataset["id"]: base_records},
            }

            # Procurar correspondências nos outros datasets
            for other_dataset in prepared_datasets[1:]:
                if base_key in other_dataset["indexed_data"]:
                    match_group["records"][other_dataset["id"]] = other_dataset[
                        "indexed_data"
                    ][base_key]

            # Só adicionar se há correspondência em pelo menos 2 datasets
            if len(match_group["records"]) >= 2:
                matches.append(match_group)

        return matches

    def _detect_format_inconsistencies(self, dataset: List[Dict]) -> List[Dict]:
        """Detecta inconsistências de formato."""
        inconsistencies = []

        # Analisar padrões por campo
        field_patterns = defaultdict(set)

        for record in dataset:
            for field, value in record.items():
                if value is not None:
                    # Analisar padrão do valor
                    pattern = self._extract_value_pattern(str(value))
                    field_patterns[field].add(pattern)

        # Identificar campos com múltiplos padrões
        for field, patterns in field_patterns.items():
            if len(patterns) > 1:
                inconsistencies.append(
                    {
                        "type": "format_inconsistency",
                        "field": field,
                        "patterns_found": list(patterns),
                        "severity": "medium" if len(patterns) <= 3 else "high",
                        "affected_records": self._count_records_by_pattern(
                            dataset, field, patterns
                        ),
                    }
                )

        return inconsistencies

    def _extract_value_pattern(self, value: str) -> str:
        """Extrai padrão de um valor."""
        import re

        # Substituir dígitos por 'D' e letras por 'L'
        pattern = re.sub(r"\d", "D", value)
        pattern = re.sub(r"[a-zA-Z]", "L", pattern)

        return pattern

    def _analyze_completeness(self, dataset: List[Dict]) -> Dict[str, Any]:
        """Analisa completude dos dados."""
        if not dataset:
            return {"score": 0.0, "analysis": "Dataset vazio"}

        total_fields = 0
        filled_fields = 0
        field_completeness = {}

        # Obter todos os campos possíveis
        all_fields = set()
        for record in dataset:
            all_fields.update(record.keys())

        # Calcular completude por campo
        for field in all_fields:
            field_total = len(dataset)
            field_filled = sum(
                1
                for record in dataset
                if record.get(field) is not None
                and str(record.get(field)).strip() != ""
            )

            field_completeness[field] = {
                "filled": field_filled,
                "total": field_total,
                "percentage": (
                    (field_filled / field_total) * 100 if field_total > 0 else 0
                ),
            }

            total_fields += field_total
            filled_fields += field_filled

        overall_completeness = (
            (filled_fields / total_fields) * 100 if total_fields > 0 else 0
        )

        return {
            "score": overall_completeness / 100,
            "percentage": overall_completeness,
            "field_analysis": field_completeness,
            "critical_missing_fields": [
                field
                for field, stats in field_completeness.items()
                if stats["percentage"] < 50
            ],
            "analysis": f"Completude geral: {overall_completeness:.1f}%",
        }

    def _analyze_consistency(self, dataset: List[Dict]) -> Dict[str, Any]:
        """Analisa consistência dos dados."""
        consistency_issues = []

        # Verificar consistência de formatos por campo
        for field in self._get_all_fields(dataset):
            field_values = [
                record.get(field) for record in dataset if record.get(field) is not None
            ]

            if field_values:
                patterns = set(
                    self._extract_value_pattern(str(value)) for value in field_values
                )

                if len(patterns) > 1:
                    consistency_issues.append(
                        {
                            "field": field,
                            "issue": "format_inconsistency",
                            "patterns": list(patterns),
                            "severity": len(patterns),
                        }
                    )

        # Calcular score de consistência
        total_fields = len(self._get_all_fields(dataset))
        consistent_fields = total_fields - len(consistency_issues)
        consistency_score = (
            (consistent_fields / total_fields) if total_fields > 0 else 1.0
        )

        return {
            "score": consistency_score,
            "percentage": consistency_score * 100,
            "issues": consistency_issues,
            "consistent_fields": consistent_fields,
            "total_fields": total_fields,
            "analysis": f"Consistência: {consistency_score * 100:.1f}%",
        }

    def _analyze_accuracy(self, dataset: List[Dict]) -> Dict[str, Any]:
        """Analisa precisão dos dados."""
        accuracy_issues = []

        # Verificar valores válidos para campos conhecidos
        validation_rules = {
            "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "phone": r"^\+?[\d\s\-\(\)]{10,}$",
            "cpf": r"^\d{3}\.\d{3}\.\d{3}-\d{2}$|^\d{11}$",
            "cnpj": r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$|^\d{14}$",
        }

        import re

        for field in self._get_all_fields(dataset):
            field_lower = field.lower()

            # Identificar tipo de campo e aplicar validação
            for field_type, pattern in validation_rules.items():
                if field_type in field_lower:
                    invalid_count = 0
                    total_count = 0

                    for record in dataset:
                        value = record.get(field)
                        if value is not None and str(value).strip():
                            total_count += 1
                            if not re.match(pattern, str(value).strip()):
                                invalid_count += 1

                    if total_count > 0:
                        accuracy_rate = (
                            (total_count - invalid_count) / total_count
                        ) * 100

                        if accuracy_rate < 90:  # Threshold para problemas de precisão
                            accuracy_issues.append(
                                {
                                    "field": field,
                                    "field_type": field_type,
                                    "invalid_count": invalid_count,
                                    "total_count": total_count,
                                    "accuracy_rate": accuracy_rate,
                                }
                            )

        # Calcular score geral de precisão
        if accuracy_issues:
            avg_accuracy = statistics.mean(
                [issue["accuracy_rate"] for issue in accuracy_issues]
            )
            accuracy_score = avg_accuracy / 100
        else:
            accuracy_score = 1.0  # Assume alta precisão se não há regras violadas

        return {
            "score": accuracy_score,
            "percentage": accuracy_score * 100,
            "issues": accuracy_issues,
            "validation_rules_applied": len(validation_rules),
            "analysis": f"Precisão: {accuracy_score * 100:.1f}%",
        }

    def _analyze_timeliness(self, dataset: List[Dict]) -> Dict[str, Any]:
        """Analisa atualidade dos dados."""
        timeliness_issues = []
        current_time = datetime.now()

        # Procurar campos de data/timestamp
        date_fields = []
        for field in self._get_all_fields(dataset):
            field_lower = field.lower()
            if any(
                keyword in field_lower
                for keyword in ["date", "time", "created", "updated", "modified"]
            ):
                date_fields.append(field)

        for field in date_fields:
            old_records = 0
            total_records = 0

            for record in dataset:
                value = record.get(field)
                if value:
                    try:
                        # Tentar parsear data
                        if isinstance(value, str):
                            record_date = datetime.fromisoformat(
                                value.replace("Z", "+00:00")
                            )
                        else:
                            record_date = value

                        total_records += 1
                        days_old = (current_time - record_date).days

                        # Considerar "antigo" se > 365 dias (configurável)
                        if days_old > 365:
                            old_records += 1

                    except (ValueError, TypeError):
                        continue

            if total_records > 0:
                timeliness_rate = ((total_records - old_records) / total_records) * 100

                if timeliness_rate < 80:  # Threshold
                    timeliness_issues.append(
                        {
                            "field": field,
                            "old_records": old_records,
                            "total_records": total_records,
                            "timeliness_rate": timeliness_rate,
                        }
                    )

        # Calcular score de atualidade
        if timeliness_issues:
            avg_timeliness = statistics.mean(
                [issue["timeliness_rate"] for issue in timeliness_issues]
            )
            timeliness_score = avg_timeliness / 100
        else:
            timeliness_score = 0.8  # Score neutro se não há campos de data

        return {
            "score": timeliness_score,
            "percentage": timeliness_score * 100,
            "issues": timeliness_issues,
            "date_fields_analyzed": len(date_fields),
            "analysis": f"Atualidade: {timeliness_score * 100:.1f}%",
        }

    def _analyze_validity(self, dataset: List[Dict]) -> Dict[str, Any]:
        """Analisa validade dos dados."""
        validity_issues = []

        # Verificar valores em branco, nulos ou inválidos
        for field in self._get_all_fields(dataset):
            invalid_count = 0
            total_count = len(dataset)

            for record in dataset:
                value = record.get(field)

                # Verificar se valor é inválido
                if self._is_invalid_value(value):
                    invalid_count += 1

            validity_rate = (
                ((total_count - invalid_count) / total_count) * 100
                if total_count > 0
                else 100
            )

            if validity_rate < 95:  # Threshold para validade
                validity_issues.append(
                    {
                        "field": field,
                        "invalid_count": invalid_count,
                        "total_count": total_count,
                        "validity_rate": validity_rate,
                    }
                )

        # Calcular score de validade
        if validity_issues:
            avg_validity = statistics.mean(
                [issue["validity_rate"] for issue in validity_issues]
            )
            validity_score = avg_validity / 100
        else:
            validity_score = 1.0

        return {
            "score": validity_score,
            "percentage": validity_score * 100,
            "issues": validity_issues,
            "analysis": f"Validade: {validity_score * 100:.1f}%",
        }

    def _analyze_uniqueness(self, dataset: List[Dict]) -> Dict[str, Any]:
        """Analisa unicidade dos dados."""
        uniqueness_issues = []

        # Verificar duplicatas por campo
        for field in self._get_all_fields(dataset):
            values = []
            for record in dataset:
                value = record.get(field)
                if value is not None and str(value).strip():
                    values.append(str(value).strip().lower())

            if values:
                unique_values = len(set(values))
                total_values = len(values)
                uniqueness_rate = (unique_values / total_values) * 100

                if uniqueness_rate < 95 and field.lower() in [
                    "id",
                    "codigo",
                    "cpf",
                    "cnpj",
                    "email",
                ]:
                    uniqueness_issues.append(
                        {
                            "field": field,
                            "unique_count": unique_values,
                            "total_count": total_values,
                            "duplicate_count": total_values - unique_values,
                            "uniqueness_rate": uniqueness_rate,
                        }
                    )

        # Calcular score de unicidade
        if uniqueness_issues:
            avg_uniqueness = statistics.mean(
                [issue["uniqueness_rate"] for issue in uniqueness_issues]
            )
            uniqueness_score = avg_uniqueness / 100
        else:
            uniqueness_score = 1.0

        return {
            "score": uniqueness_score,
            "percentage": uniqueness_score * 100,
            "issues": uniqueness_issues,
            "analysis": f"Unicidade: {uniqueness_score * 100:.1f}%",
        }

    def _get_all_fields(self, dataset: List[Dict]) -> Set[str]:
        """Obtém todos os campos únicos do dataset."""
        all_fields = set()
        for record in dataset:
            all_fields.update(record.keys())
        return all_fields

    def _is_invalid_value(self, value: Any) -> bool:
        """Verifica se um valor é considerado inválido."""
        if value is None:
            return True

        str_value = str(value).strip().lower()

        # Valores considerados inválidos
        invalid_values = {
            "",
            "null",
            "none",
            "undefined",
            "n/a",
            "na",
            "#n/a",
            "missing",
            "unknown",
            "tbd",
            "tmp",
            "test",
            "???",
        }

        return str_value in invalid_values

    def _calculate_weighted_quality_score(
        self, quality_analysis: Dict[str, Any]
    ) -> float:
        """Calcula score ponderado de qualidade."""
        weights = self.config["data_quality_weights"]
        total_score = 0.0
        total_weight = 0.0

        for dimension, analysis in quality_analysis.items():
            if dimension in weights:
                score = analysis.get("score", 0.0)
                weight = weights[dimension]
                total_score += score * weight
                total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def _assign_quality_grade(self, score: float) -> str:
        """Atribui nota à qualidade dos dados."""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"

    def _identify_quality_problem_areas(
        self, quality_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identifica áreas problemáticas na qualidade."""
        problems = []

        for dimension, analysis in quality_analysis.items():
            score = analysis.get("score", 1.0)

            if score < 0.7:  # Threshold para problemas
                problems.append(
                    {
                        "dimension": dimension,
                        "score": score,
                        "severity": (
                            "critical"
                            if score < 0.5
                            else "high" if score < 0.6 else "medium"
                        ),
                        "issues": analysis.get("issues", []),
                        "recommendations": self._get_dimension_recommendations(
                            dimension, score
                        ),
                    }
                )

        return sorted(problems, key=lambda x: x["score"])

    def _get_dimension_recommendations(self, dimension: str, score: float) -> List[str]:
        """Gera recomendações específicas por dimensão."""
        recommendations = []

        if dimension == "completeness":
            if score < 0.5:
                recommendations.append(
                    "Implementar validação obrigatória para campos críticos"
                )
                recommendations.append("Revisar processo de coleta de dados")
            else:
                recommendations.append("Melhorar preenchimento de campos opcionais")

        elif dimension == "accuracy":
            recommendations.append("Implementar validação de formato em tempo real")
            recommendations.append("Criar regras de negócio para validação")

        elif dimension == "consistency":
            recommendations.append("Padronizar formatos de entrada")
            recommendations.append("Implementar normalização automática")

        elif dimension == "timeliness":
            recommendations.append("Estabelecer políticas de atualização de dados")
            recommendations.append("Implementar notificações para dados antigos")

        return recommendations

    def _generate_quality_improvement_plan(
        self, quality_analysis: Dict[str, Any], problems: List[Dict]
    ) -> Dict[str, Any]:
        """Gera plano de melhoria da qualidade."""
        plan = {
            "priority_actions": [],
            "short_term_goals": [],
            "long_term_goals": [],
            "estimated_effort": {},
            "expected_improvements": {},
        }

        # Ações prioritárias baseadas em problemas críticos
        critical_problems = [p for p in problems if p["severity"] == "critical"]

        for problem in critical_problems:
            plan["priority_actions"].extend(problem["recommendations"])

        # Metas de curto prazo
        if quality_analysis.get("completeness", {}).get("score", 1.0) < 0.8:
            plan["short_term_goals"].append("Aumentar completude para 90%")

        if quality_analysis.get("accuracy", {}).get("score", 1.0) < 0.8:
            plan["short_term_goals"].append("Implementar validação de dados")

        # Metas de longo prazo
        plan["long_term_goals"] = [
            "Atingir qualidade geral A (>90%)",
            "Automatizar 80% das validações",
            "Reduzir inconsistências em 95%",
        ]

        return plan

    def _analyze_quality_trends(self) -> Dict[str, Any]:
        """Analisa tendências de qualidade ao longo do tempo."""
        # Placeholder - em produção usaria dados históricos
        return {
            "trend": "stable",
            "improvements": [],
            "degradations": [],
            "recommendations": ["Estabelecer monitoramento contínuo de qualidade"],
        }

    def _detect_duplicate_groups(
        self, dataset: List[Dict], threshold: float
    ) -> List[List[Dict]]:
        """Detecta grupos de registros duplicados."""
        duplicate_groups = []
        processed_indices = set()

        for i, record1 in enumerate(dataset):
            if i in processed_indices:
                continue

            group = [record1]
            processed_indices.add(i)

            for j, record2 in enumerate(dataset[i + 1 :], i + 1):
                if j in processed_indices:
                    continue

                similarity = self._calculate_record_similarity(record1, record2)

                if similarity >= threshold:
                    group.append(record2)
                    processed_indices.add(j)

            # Só adicionar se há duplicatas
            if len(group) > 1:
                duplicate_groups.append(group)

        return duplicate_groups

    def _calculate_record_similarity(self, record1: Dict, record2: Dict) -> float:
        """Calcula similaridade entre dois registros."""
        all_fields = set(record1.keys()) | set(record2.keys())

        if not all_fields:
            return 0.0

        similarity_scores = []

        for field in all_fields:
            value1 = str(record1.get(field, "")).strip().lower()
            value2 = str(record2.get(field, "")).strip().lower()

            if value1 == "" and value2 == "":
                continue  # Não considerar campos vazios

            # Usar SequenceMatcher para calcular similaridade
            similarity = SequenceMatcher(None, value1, value2).ratio()
            similarity_scores.append(similarity)

        return statistics.mean(similarity_scores) if similarity_scores else 0.0

    def _conservative_merge(self, group: List[Dict]) -> Dict[str, Any]:
        """Estratégia conservadora de fusão - preserva dados existentes."""
        merged = {}

        all_fields = set()
        for record in group:
            all_fields.update(record.keys())

        for field in all_fields:
            values = []
            for record in group:
                value = record.get(field)
                if value is not None and str(value).strip():
                    values.append(value)

            if values:
                # Usar o primeiro valor não vazio
                merged[field] = values[0]
            else:
                merged[field] = None

        # Adicionar metadados da fusão
        merged["_merge_info"] = {
            "strategy": "conservative",
            "source_count": len(group),
            "merge_timestamp": datetime.now().isoformat(),
        }

        return merged

    def _aggressive_merge(self, group: List[Dict]) -> Dict[str, Any]:
        """Estratégia agressiva - usa valor mais comum ou mais recente."""
        merged = {}

        all_fields = set()
        for record in group:
            all_fields.update(record.keys())

        for field in all_fields:
            values = []
            for record in group:
                value = record.get(field)
                if value is not None and str(value).strip():
                    values.append(value)

            if values:
                # Usar valor mais comum
                from collections import Counter

                most_common = Counter(values).most_common(1)[0][0]
                merged[field] = most_common
            else:
                merged[field] = None

        merged["_merge_info"] = {
            "strategy": "aggressive",
            "source_count": len(group),
            "merge_timestamp": datetime.now().isoformat(),
        }

        return merged

    def _intelligent_merge(self, group: List[Dict]) -> Dict[str, Any]:
        """Estratégia inteligente - usa heurísticas específicas por campo."""
        merged = {}

        all_fields = set()
        for record in group:
            all_fields.update(record.keys())

        for field in all_fields:
            values = []
            for record in group:
                value = record.get(field)
                if value is not None and str(value).strip():
                    values.append(value)

            if values:
                # Aplicar heurística específica
                merged[field] = self._apply_field_merge_heuristic(field, values)
            else:
                merged[field] = None

        merged["_merge_info"] = {
            "strategy": "intelligent",
            "source_count": len(group),
            "merge_timestamp": datetime.now().isoformat(),
        }

        return merged

    def _apply_field_merge_heuristic(self, field: str, values: List[Any]) -> Any:
        """Aplica heurística específica para fusão de campo."""
        field_lower = field.lower()

        # Para campos de data, usar o mais recente
        if any(
            keyword in field_lower for keyword in ["date", "time", "created", "updated"]
        ):
            try:
                dates = []
                for value in values:
                    if isinstance(value, str):
                        dates.append(
                            datetime.fromisoformat(value.replace("Z", "+00:00"))
                        )
                    else:
                        dates.append(value)
                return max(dates).isoformat()
            except Exception:
                pass

        # Para emails, usar o mais completo (com @)
        if "email" in field_lower:
            emails = [v for v in values if "@" in str(v)]
            if emails:
                return max(emails, key=len)

        # Para valores numéricos, usar a média
        if field_lower in ["price", "valor", "amount", "quantidade"]:
            try:
                numbers = [float(v) for v in values]
                return statistics.mean(numbers)
            except Exception:
                pass

        # Para nomes, usar o mais completo
        if any(
            keyword in field_lower
            for keyword in ["name", "nome", "description", "descricao"]
        ):
            return max(values, key=len)

        # Default: usar valor mais comum
        from collections import Counter

        return Counter(values).most_common(1)[0][0]

    def _calculate_merge_confidence(self, group: List[Dict], merged: Dict) -> float:
        """Calcula confiança da fusão."""
        total_fields = len(merged) - 1  # Excluir _merge_info
        consistent_fields = 0

        for field, merged_value in merged.items():
            if field == "_merge_info":
                continue

            # Verificar quantos registros têm o mesmo valor
            matching_count = 0
            for record in group:
                if record.get(field) == merged_value:
                    matching_count += 1

            # Campo é consistente se pelo menos 50% dos registros concordam
            if matching_count >= len(group) * 0.5:
                consistent_fields += 1

        return consistent_fields / total_fields if total_fields > 0 else 1.0

    def _identify_resolved_conflicts(
        self, group: List[Dict], merged: Dict
    ) -> List[Dict]:
        """Identifica conflitos resolvidos na fusão."""
        conflicts = []

        for field in merged.keys():
            if field == "_merge_info":
                continue

            values = set()
            for record in group:
                value = record.get(field)
                if value is not None:
                    values.add(str(value))

            if len(values) > 1:
                conflicts.append(
                    {
                        "field": field,
                        "conflicting_values": list(values),
                        "resolved_value": merged[field],
                        "conflict_count": len(values),
                    }
                )

        return conflicts

    def _calculate_merge_statistics(
        self,
        original_dataset: List[Dict],
        duplicate_groups: List[List[Dict]],
        merge_results: List[Dict],
    ) -> Dict[str, Any]:
        """Calcula estatísticas da fusão."""
        total_duplicates = sum(len(group) for group in duplicate_groups)
        records_removed = total_duplicates - len(duplicate_groups)

        # Calcular confiança média
        confidences = [result["confidence"] for result in merge_results]
        avg_confidence = statistics.mean(confidences) if confidences else 0.0

        # Calcular conflitos totais
        total_conflicts = sum(
            len(result["conflicts_resolved"]) for result in merge_results
        )

        return {
            "original_record_count": len(original_dataset),
            "duplicate_groups": len(duplicate_groups),
            "total_duplicates": total_duplicates,
            "records_removed": records_removed,
            "reduction_percentage": (
                (records_removed / len(original_dataset)) * 100
                if original_dataset
                else 0
            ),
            "average_merge_confidence": avg_confidence,
            "total_conflicts_resolved": total_conflicts,
            "merge_efficiency": (
                (records_removed / total_duplicates) if total_duplicates > 0 else 0
            ),
        }

    def _generate_clean_dataset(
        self,
        original_dataset: List[Dict],
        duplicate_groups: List[List[Dict]],
        merge_results: List[Dict],
    ) -> List[Dict]:
        """Gera dataset limpo após fusão."""
        # Criar set de registros a serem removidos
        records_to_remove = set()

        for group in duplicate_groups:
            for record in group:
                # Usar hash do record como identificador
                record_hash = hash(json.dumps(record, sort_keys=True, default=str))
                records_to_remove.add(record_hash)

        # Criar dataset limpo
        clean_dataset = []

        # Adicionar registros não duplicados
        for record in original_dataset:
            record_hash = hash(json.dumps(record, sort_keys=True, default=str))
            if record_hash not in records_to_remove:
                clean_dataset.append(record)

        # Adicionar registros mesclados
        for result in merge_results:
            clean_dataset.append(result["merged_record"])

        return clean_dataset

    def _calculate_quality_improvement(
        self, original_dataset: List[Dict], clean_dataset: List[Dict]
    ) -> Dict[str, Any]:
        """Calcula melhoria de qualidade após limpeza."""
        # Calcular métricas antes e depois
        original_metrics = {
            "record_count": len(original_dataset),
            "uniqueness": self._calculate_dataset_uniqueness(original_dataset),
        }

        clean_metrics = {
            "record_count": len(clean_dataset),
            "uniqueness": self._calculate_dataset_uniqueness(clean_dataset),
        }

        improvement = {
            "size_reduction": {
                "absolute": original_metrics["record_count"]
                - clean_metrics["record_count"],
                "percentage": (
                    (
                        (
                            original_metrics["record_count"]
                            - clean_metrics["record_count"]
                        )
                        / original_metrics["record_count"]
                    )
                    * 100
                    if original_metrics["record_count"] > 0
                    else 0
                ),
            },
            "uniqueness_improvement": {
                "before": original_metrics["uniqueness"],
                "after": clean_metrics["uniqueness"],
                "improvement": clean_metrics["uniqueness"]
                - original_metrics["uniqueness"],
            },
        }

        return improvement

    def _calculate_dataset_uniqueness(self, dataset: List[Dict]) -> float:
        """Calcula score de unicidade do dataset."""
        if not dataset:
            return 1.0

        # Usar combinação de campos chave para determinar unicidade
        key_fields = ["id", "codigo", "cpf", "cnpj", "email"]

        for field in key_fields:
            if field in dataset[0]:  # Verificar se campo existe
                values = [record.get(field) for record in dataset if record.get(field)]
                if values:
                    unique_values = len(set(values))
                    return unique_values / len(values)

        # Se não há campos chave, usar hash dos registros completos
        hashes = set()
        for record in dataset:
            record_hash = hash(json.dumps(record, sort_keys=True, default=str))
            hashes.add(record_hash)

        return len(hashes) / len(dataset)

    # Métodos auxiliares adicionais (implementação simplificada)

    def _detect_field_discrepancies(
        self, matches: List[Dict], fields: List[str]
    ) -> List[Dict]:
        """Detecta discrepâncias entre campos correspondentes."""
        discrepancies = []
        # Implementação simplificada
        return discrepancies

    def _calculate_reconciliation_statistics(
        self, datasets: List[Dict], matches: List[Dict], discrepancies: List[Dict]
    ) -> Dict:
        """Calcula estatísticas de reconciliação."""
        return {
            "total_matches": len(matches),
            "total_discrepancies": len(discrepancies),
            "match_rate": len(matches)
            / max(sum(d["record_count"] for d in datasets), 1),
        }

    def _generate_reconciliation_report(
        self,
        datasets: List[Dict],
        matches: List[Dict],
        discrepancies: List[Dict],
        stats: Dict,
    ) -> Dict:
        """Gera relatório de reconciliação."""
        return {
            "summary": f"Reconciliação de {len(datasets)} datasets concluída",
            "details": stats,
        }

    def _suggest_reconciliation_actions(
        self, discrepancies: List[Dict], stats: Dict
    ) -> List[str]:
        """Sugere ações corretivas para reconciliação."""
        return ["Revisar discrepâncias identificadas", "Padronizar formatos de dados"]

    def _calculate_overall_quality_score(self, stats: Dict) -> float:
        """Calcula score geral de qualidade."""
        return stats.get("match_rate", 0.0)
