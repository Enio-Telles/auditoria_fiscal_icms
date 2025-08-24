"""
Aggregation Agent - Agente de Agregação e Consolidação
=====================================================

Este agente é responsável por:
- Consolidar dados de múltiplas fontes
- Agregar estatísticas e métricas
- Combinar resultados de outros agentes
- Gerar relatórios consolidados
- Detectar padrões em conjuntos de dados
"""

import asyncio
import statistics
from collections import defaultdict, Counter
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from .base_agent import BaseAgent, AgentTask, TaskPriority


class AggregationAgent(BaseAgent):
    """
    Agente especializado em agregação e consolidação de dados.
    
    Capacidades:
    - Consolidação de dados multi-fonte
    - Agregação estatística
    - Detecção de padrões
    - Geração de relatórios
    - Análise de tendências
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o agente de agregação.
        
        Args:
            config: Configurações específicas do agente
        """
        default_config = {
            "max_data_points": 10000,
            "aggregation_timeout": 300,  # 5 minutos
            "pattern_detection_threshold": 0.8,
            "statistical_confidence": 0.95,
            "enable_trend_analysis": True,
            "enable_anomaly_detection": True
        }
        
        # Merge configurações
        agent_config = {**default_config, **(config or {})}
        
        super().__init__(name="AggregationAgent", config=agent_config)
        
        # Cache para dados agregados
        self.aggregation_cache = {}
        self.pattern_cache = {}
        
        # Contadores estatísticos
        self.stats_counters = defaultdict(Counter)
        
        self.logger.info("AggregationAgent inicializado com capacidades de consolidação")
    
    def get_capabilities(self) -> List[str]:
        """
        Retorna capacidades do agente de agregação.
        
        Returns:
            Lista de capacidades
        """
        return [
            "consolidate_data",
            "aggregate_statistics",
            "detect_patterns",
            "generate_report",
            "analyze_trends",
            "detect_anomalies",
            "combine_results",
            "calculate_metrics"
        ]
    
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Processa tarefa de agregação/consolidação.
        
        Args:
            task: Tarefa contendo dados para agregação
            
        Returns:
            Dados agregados e consolidados
        """
        task_type = task.type
        data = task.data
        
        self.logger.info(f"Processando tarefa de {task_type}")
        
        if task_type == "consolidate_data":
            return await self._consolidate_data(data)
        elif task_type == "aggregate_statistics":
            return await self._aggregate_statistics(data)
        elif task_type == "detect_patterns":
            return await self._detect_patterns(data)
        elif task_type == "generate_report":
            return await self._generate_report(data)
        elif task_type == "analyze_trends":
            return await self._analyze_trends(data)
        elif task_type == "detect_anomalies":
            return await self._detect_anomalies(data)
        elif task_type == "combine_results":
            return await self._combine_results(data)
        elif task_type == "calculate_metrics":
            return await self._calculate_metrics(data)
        else:
            raise ValueError(f"Tipo de tarefa não suportado: {task_type}")
    
    async def _consolidate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Consolida dados de múltiplas fontes.
        
        Args:
            data: Dados de múltiplas fontes para consolidação
            
        Returns:
            Dados consolidados
        """
        sources = data.get("sources", [])
        consolidation_strategy = data.get("strategy", "merge")
        
        self.logger.info(f"Consolidando {len(sources)} fontes com estratégia '{consolidation_strategy}'")
        
        if consolidation_strategy == "merge":
            consolidated = await self._merge_sources(sources)
        elif consolidation_strategy == "union":
            consolidated = await self._union_sources(sources)
        elif consolidation_strategy == "intersection":
            consolidated = await self._intersection_sources(sources)
        else:
            raise ValueError(f"Estratégia de consolidação não suportada: {consolidation_strategy}")
        
        # Calcular estatísticas de consolidação
        consolidation_stats = self._calculate_consolidation_stats(sources, consolidated)
        
        result = {
            "consolidated_data": consolidated,
            "source_count": len(sources),
            "consolidation_strategy": consolidation_strategy,
            "consolidation_stats": consolidation_stats,
            "data_quality_metrics": self._assess_data_quality(consolidated),
            "processing_metadata": {
                "agent": self.name,
                "timestamp": datetime.now().isoformat(),
                "total_records": len(consolidated) if isinstance(consolidated, list) else 1
            }
        }
        
        self.logger.info(f"Consolidação concluída: {len(consolidated) if isinstance(consolidated, list) else 1} registros")
        return result
    
    async def _aggregate_statistics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agrega estatísticas de um conjunto de dados.
        
        Args:
            data: Dados para agregação estatística
            
        Returns:
            Estatísticas agregadas
        """
        dataset = data.get("dataset", [])
        metrics = data.get("metrics", ["count", "mean", "median", "std"])
        group_by = data.get("group_by", None)
        
        self.logger.info(f"Agregando estatísticas para {len(dataset)} registros")
        
        if group_by:
            stats = await self._grouped_statistics(dataset, metrics, group_by)
        else:
            stats = await self._overall_statistics(dataset, metrics)
        
        # Calcular métricas adicionais
        additional_metrics = self._calculate_additional_metrics(dataset)
        
        result = {
            "statistics": stats,
            "additional_metrics": additional_metrics,
            "dataset_summary": {
                "total_records": len(dataset),
                "data_types": self._analyze_data_types(dataset),
                "completeness": self._calculate_completeness(dataset)
            },
            "confidence_level": self.config["statistical_confidence"]
        }
        
        return result
    
    async def _detect_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detecta padrões nos dados.
        
        Args:
            data: Dados para detecção de padrões
            
        Returns:
            Padrões detectados
        """
        dataset = data.get("dataset", [])
        pattern_types = data.get("pattern_types", ["frequency", "sequence", "correlation"])
        
        self.logger.info(f"Detectando padrões em {len(dataset)} registros")
        
        detected_patterns = {}
        
        for pattern_type in pattern_types:
            if pattern_type == "frequency":
                patterns = self._detect_frequency_patterns(dataset)
            elif pattern_type == "sequence":
                patterns = self._detect_sequence_patterns(dataset)
            elif pattern_type == "correlation":
                patterns = self._detect_correlation_patterns(dataset)
            else:
                continue
            
            if patterns:
                detected_patterns[pattern_type] = patterns
        
        # Calcular confiança dos padrões
        pattern_confidence = self._calculate_pattern_confidence(detected_patterns)
        
        result = {
            "detected_patterns": detected_patterns,
            "pattern_confidence": pattern_confidence,
            "pattern_summary": {
                "total_patterns": sum(len(p) for p in detected_patterns.values()),
                "pattern_types": list(detected_patterns.keys()),
                "strongest_pattern": self._find_strongest_pattern(detected_patterns)
            }
        }
        
        return result
    
    async def _generate_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera relatório consolidado.
        
        Args:
            data: Dados e configuração do relatório
            
        Returns:
            Relatório gerado
        """
        report_type = data.get("report_type", "summary")
        dataset = data.get("dataset", [])
        include_charts = data.get("include_charts", False)
        
        self.logger.info(f"Gerando relatório do tipo '{report_type}'")
        
        # Componentes do relatório
        report_sections = {}
        
        # Seção de resumo executivo
        report_sections["executive_summary"] = self._generate_executive_summary(dataset)
        
        # Estatísticas descritivas
        report_sections["descriptive_statistics"] = await self._aggregate_statistics({
            "dataset": dataset,
            "metrics": ["count", "mean", "median", "std", "min", "max"]
        })
        
        # Padrões detectados
        report_sections["patterns"] = await self._detect_patterns({
            "dataset": dataset,
            "pattern_types": ["frequency", "correlation"]
        })
        
        # Análise de tendências (se habilitada)
        if self.config["enable_trend_analysis"]:
            report_sections["trends"] = await self._analyze_trends({"dataset": dataset})
        
        # Detecção de anomalias (se habilitada)
        if self.config["enable_anomaly_detection"]:
            report_sections["anomalies"] = await self._detect_anomalies({"dataset": dataset})
        
        # Recomendações
        report_sections["recommendations"] = self._generate_recommendations(dataset)
        
        # Metadados do relatório
        report_metadata = {
            "report_type": report_type,
            "generation_time": datetime.now().isoformat(),
            "data_period": self._determine_data_period(dataset),
            "total_records_analyzed": len(dataset),
            "agent": self.name
        }
        
        result = {
            "report": report_sections,
            "metadata": report_metadata,
            "data_quality_assessment": self._assess_data_quality(dataset)
        }
        
        return result
    
    async def _analyze_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa tendências nos dados.
        
        Args:
            data: Dados para análise de tendências
            
        Returns:
            Análise de tendências
        """
        dataset = data.get("dataset", [])
        time_field = data.get("time_field", "timestamp")
        value_fields = data.get("value_fields", [])
        
        self.logger.info(f"Analisando tendências em {len(value_fields) or 'todos os campos'} campos")
        
        trends = {}
        
        # Agrupar dados por período
        time_series = self._create_time_series(dataset, time_field, value_fields)
        
        for field, series in time_series.items():
            trend_analysis = self._calculate_trend(series)
            trends[field] = trend_analysis
        
        # Identificar tendências globais
        global_trends = self._identify_global_trends(trends)
        
        result = {
            "field_trends": trends,
            "global_trends": global_trends,
            "trend_summary": {
                "trending_up": [f for f, t in trends.items() if t.get("direction") == "up"],
                "trending_down": [f for f, t in trends.items() if t.get("direction") == "down"],
                "stable": [f for f, t in trends.items() if t.get("direction") == "stable"]
            }
        }
        
        return result
    
    async def _detect_anomalies(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detecta anomalias nos dados.
        
        Args:
            data: Dados para detecção de anomalias
            
        Returns:
            Anomalias detectadas
        """
        dataset = data.get("dataset", [])
        threshold = data.get("threshold", 2.0)  # Z-score threshold
        
        self.logger.info(f"Detectando anomalias em {len(dataset)} registros")
        
        anomalies = []
        
        # Detectar anomalias numéricas
        numeric_anomalies = self._detect_numeric_anomalies(dataset, threshold)
        anomalies.extend(numeric_anomalies)
        
        # Detectar anomalias categóricas
        categorical_anomalies = self._detect_categorical_anomalies(dataset)
        anomalies.extend(categorical_anomalies)
        
        # Detectar anomalias temporais
        temporal_anomalies = self._detect_temporal_anomalies(dataset)
        anomalies.extend(temporal_anomalies)
        
        # Classificar anomalias por severidade
        classified_anomalies = self._classify_anomalies(anomalies)
        
        result = {
            "anomalies": classified_anomalies,
            "anomaly_summary": {
                "total_anomalies": len(anomalies),
                "by_type": Counter(a.get("type") for a in anomalies),
                "by_severity": Counter(a.get("severity") for a in classified_anomalies)
            },
            "anomaly_rate": len(anomalies) / max(1, len(dataset))
        }
        
        return result
    
    async def _combine_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combina resultados de múltiplos agentes.
        
        Args:
            data: Resultados de diferentes agentes
            
        Returns:
            Resultados combinados
        """
        agent_results = data.get("agent_results", {})
        combination_strategy = data.get("strategy", "weighted_merge")
        
        self.logger.info(f"Combinando resultados de {len(agent_results)} agentes")
        
        if combination_strategy == "weighted_merge":
            combined = self._weighted_merge(agent_results, data.get("weights", {}))
        elif combination_strategy == "consensus":
            combined = self._consensus_merge(agent_results)
        elif combination_strategy == "best_score":
            combined = self._best_score_merge(agent_results)
        else:
            combined = self._simple_merge(agent_results)
        
        # Calcular métricas de combinação
        combination_metrics = self._calculate_combination_metrics(agent_results, combined)
        
        result = {
            "combined_results": combined,
            "combination_strategy": combination_strategy,
            "agent_contributions": {
                agent: len(results) if isinstance(results, list) else 1
                for agent, results in agent_results.items()
            },
            "combination_metrics": combination_metrics
        }
        
        return result
    
    async def _calculate_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula métricas específicas.
        
        Args:
            data: Dados e configuração de métricas
            
        Returns:
            Métricas calculadas
        """
        dataset = data.get("dataset", [])
        metric_types = data.get("metrics", ["accuracy", "completeness", "consistency"])
        
        self.logger.info(f"Calculando {len(metric_types)} métricas")
        
        calculated_metrics = {}
        
        for metric_type in metric_types:
            if metric_type == "accuracy":
                calculated_metrics[metric_type] = self._calculate_accuracy_metrics(dataset)
            elif metric_type == "completeness":
                calculated_metrics[metric_type] = self._calculate_completeness(dataset)
            elif metric_type == "consistency":
                calculated_metrics[metric_type] = self._calculate_consistency_metrics(dataset)
            elif metric_type == "diversity":
                calculated_metrics[metric_type] = self._calculate_diversity_metrics(dataset)
            elif metric_type == "distribution":
                calculated_metrics[metric_type] = self._calculate_distribution_metrics(dataset)
        
        # Calcular score geral de qualidade
        quality_score = self._calculate_overall_quality_score(calculated_metrics)
        
        result = {
            "metrics": calculated_metrics,
            "overall_quality_score": quality_score,
            "recommendations": self._generate_metric_recommendations(calculated_metrics)
        }
        
        return result
    
    # Métodos auxiliares
    
    async def _merge_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge de fontes de dados."""
        merged = []
        seen_keys = set()
        
        for source in sources:
            source_data = source.get("data", [])
            key_field = source.get("key_field", "id")
            
            for item in source_data:
                key = item.get(key_field)
                if key not in seen_keys:
                    merged.append(item)
                    seen_keys.add(key)
        
        return merged
    
    async def _union_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """União de todas as fontes."""
        union = []
        for source in sources:
            union.extend(source.get("data", []))
        return union
    
    async def _intersection_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Interseção de fontes."""
        if not sources:
            return []
        
        # Usar primeira fonte como base
        base_data = sources[0].get("data", [])
        key_field = sources[0].get("key_field", "id")
        
        # Encontrar interseção
        intersection = []
        for item in base_data:
            key = item.get(key_field)
            
            # Verificar se existe em todas as outras fontes
            exists_in_all = True
            for source in sources[1:]:
                source_keys = {i.get(key_field) for i in source.get("data", [])}
                if key not in source_keys:
                    exists_in_all = False
                    break
            
            if exists_in_all:
                intersection.append(item)
        
        return intersection
    
    def _calculate_consolidation_stats(self, sources: List[Dict[str, Any]], consolidated: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula estatísticas de consolidação."""
        total_input = sum(len(source.get("data", [])) for source in sources)
        total_output = len(consolidated)
        
        return {
            "input_records": total_input,
            "output_records": total_output,
            "deduplication_rate": 1 - (total_output / max(1, total_input)),
            "sources_used": len(sources)
        }
    
    async def _grouped_statistics(self, dataset: List[Dict[str, Any]], metrics: List[str], group_by: str) -> Dict[str, Any]:
        """Calcula estatísticas agrupadas."""
        groups = defaultdict(list)
        
        # Agrupar dados
        for item in dataset:
            group_value = item.get(group_by)
            if group_value is not None:
                groups[group_value].append(item)
        
        # Calcular estatísticas para cada grupo
        grouped_stats = {}
        for group, items in groups.items():
            grouped_stats[group] = await self._overall_statistics(items, metrics)
        
        return grouped_stats
    
    async def _overall_statistics(self, dataset: List[Dict[str, Any]], metrics: List[str]) -> Dict[str, Any]:
        """Calcula estatísticas gerais."""
        stats = {}
        
        if "count" in metrics:
            stats["count"] = len(dataset)
        
        # Encontrar campos numéricos
        numeric_fields = self._find_numeric_fields(dataset)
        
        for field in numeric_fields:
            values = [item.get(field) for item in dataset if item.get(field) is not None]
            
            if not values:
                continue
            
            field_stats = {}
            
            if "mean" in metrics:
                field_stats["mean"] = statistics.mean(values)
            if "median" in metrics:
                field_stats["median"] = statistics.median(values)
            if "std" in metrics and len(values) > 1:
                field_stats["std"] = statistics.stdev(values)
            if "min" in metrics:
                field_stats["min"] = min(values)
            if "max" in metrics:
                field_stats["max"] = max(values)
            
            stats[field] = field_stats
        
        return stats
    
    def _find_numeric_fields(self, dataset: List[Dict[str, Any]]) -> List[str]:
        """Encontra campos numéricos no dataset."""
        if not dataset:
            return []
        
        sample = dataset[0]
        numeric_fields = []
        
        for field, value in sample.items():
            if isinstance(value, (int, float)):
                numeric_fields.append(field)
        
        return numeric_fields
    
    def _calculate_additional_metrics(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula métricas adicionais."""
        return {
            "unique_records": len(set(str(item) for item in dataset)),
            "duplicate_rate": 1 - (len(set(str(item) for item in dataset)) / max(1, len(dataset))),
            "field_coverage": self._calculate_field_coverage(dataset),
            "data_freshness": self._calculate_data_freshness(dataset)
        }
    
    def _calculate_field_coverage(self, dataset: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calcula cobertura de campos."""
        if not dataset:
            return {}
        
        field_counts = defaultdict(int)
        total_records = len(dataset)
        
        for item in dataset:
            for field, value in item.items():
                if value is not None and value != "":
                    field_counts[field] += 1
        
        return {field: count / total_records for field, count in field_counts.items()}
    
    def _calculate_data_freshness(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula frescor dos dados."""
        timestamps = []
        
        for item in dataset:
            for field, value in item.items():
                if "time" in field.lower() or "date" in field.lower():
                    try:
                        if isinstance(value, str):
                            timestamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            timestamps.append(timestamp)
                    except:
                        continue
        
        if not timestamps:
            return {"status": "no_timestamps"}
        
        now = datetime.now()
        ages = [(now - ts).total_seconds() / 86400 for ts in timestamps]  # Days
        
        return {
            "newest_days": min(ages),
            "oldest_days": max(ages),
            "average_age_days": sum(ages) / len(ages),
            "records_with_timestamps": len(timestamps)
        }
    
    def _detect_frequency_patterns(self, dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detecta padrões de frequência."""
        patterns = []
        
        # Analisar cada campo categórico
        for field in self._find_categorical_fields(dataset):
            values = [item.get(field) for item in dataset if item.get(field)]
            counter = Counter(values)
            
            # Identificar valores mais frequentes
            most_common = counter.most_common(5)
            
            if most_common:
                pattern = {
                    "field": field,
                    "type": "frequency",
                    "most_common_values": most_common,
                    "total_unique": len(counter),
                    "concentration": most_common[0][1] / len(values) if values else 0
                }
                patterns.append(pattern)
        
        return patterns
    
    def _find_categorical_fields(self, dataset: List[Dict[str, Any]]) -> List[str]:
        """Encontra campos categóricos."""
        if not dataset:
            return []
        
        sample = dataset[0]
        categorical_fields = []
        
        for field, value in sample.items():
            if isinstance(value, str) and field not in ["id", "description"]:
                categorical_fields.append(field)
        
        return categorical_fields
    
    def _detect_sequence_patterns(self, dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detecta padrões de sequência."""
        # Implementação básica para detecção de sequências
        patterns = []
        
        # Procurar por campos que podem ter sequências
        sequence_fields = ["code", "id", "number"]
        
        for field in sequence_fields:
            values = [item.get(field) for item in dataset if item.get(field)]
            
            if values and len(values) > 2:
                # Verificar se há padrão numérico sequencial
                try:
                    numeric_values = [int(str(v).replace('-', '').replace('_', '')) for v in values if str(v).isdigit()]
                    if len(numeric_values) > 2:
                        differences = [numeric_values[i+1] - numeric_values[i] for i in range(len(numeric_values)-1)]
                        
                        if len(set(differences)) == 1:  # Diferença constante
                            pattern = {
                                "field": field,
                                "type": "arithmetic_sequence",
                                "difference": differences[0],
                                "sequence_length": len(numeric_values)
                            }
                            patterns.append(pattern)
                except:
                    continue
        
        return patterns
    
    def _detect_correlation_patterns(self, dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detecta padrões de correlação."""
        patterns = []
        numeric_fields = self._find_numeric_fields(dataset)
        
        # Verificar correlações entre campos numéricos
        for i, field1 in enumerate(numeric_fields):
            for field2 in numeric_fields[i+1:]:
                values1 = [item.get(field1) for item in dataset if item.get(field1) is not None]
                values2 = [item.get(field2) for item in dataset if item.get(field2) is not None]
                
                if len(values1) > 2 and len(values2) > 2:
                    correlation = self._calculate_correlation(values1, values2)
                    
                    if abs(correlation) > 0.7:  # Correlação forte
                        pattern = {
                            "field1": field1,
                            "field2": field2,
                            "type": "correlation",
                            "correlation_coefficient": correlation,
                            "strength": "strong" if abs(correlation) > 0.8 else "moderate"
                        }
                        patterns.append(pattern)
        
        return patterns
    
    def _calculate_correlation(self, values1: List[float], values2: List[float]) -> float:
        """Calcula correlação simples entre duas listas."""
        if len(values1) != len(values2) or len(values1) < 2:
            return 0.0
        
        mean1 = sum(values1) / len(values1)
        mean2 = sum(values2) / len(values2)
        
        numerator = sum((x - mean1) * (y - mean2) for x, y in zip(values1, values2))
        
        sum_sq1 = sum((x - mean1) ** 2 for x in values1)
        sum_sq2 = sum((y - mean2) ** 2 for y in values2)
        
        denominator = (sum_sq1 * sum_sq2) ** 0.5
        
        return numerator / denominator if denominator != 0 else 0
    
    def _calculate_pattern_confidence(self, patterns: Dict[str, List[Dict[str, Any]]]) -> Dict[str, float]:
        """Calcula confiança dos padrões detectados."""
        confidence_scores = {}
        
        for pattern_type, pattern_list in patterns.items():
            if pattern_type == "frequency":
                # Confiança baseada na concentração
                scores = [p.get("concentration", 0) for p in pattern_list]
            elif pattern_type == "correlation":
                # Confiança baseada no coeficiente
                scores = [abs(p.get("correlation_coefficient", 0)) for p in pattern_list]
            else:
                scores = [0.8] * len(pattern_list)  # Confiança padrão
            
            confidence_scores[pattern_type] = sum(scores) / len(scores) if scores else 0
        
        return confidence_scores
    
    def _find_strongest_pattern(self, patterns: Dict[str, List[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
        """Encontra o padrão mais forte."""
        strongest = None
        max_strength = 0
        
        for pattern_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                strength = 0
                
                if pattern_type == "frequency":
                    strength = pattern.get("concentration", 0)
                elif pattern_type == "correlation":
                    strength = abs(pattern.get("correlation_coefficient", 0))
                
                if strength > max_strength:
                    max_strength = strength
                    strongest = {**pattern, "pattern_type": pattern_type}
        
        return strongest
    
    def _assess_data_quality(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Avalia qualidade dos dados."""
        if not dataset:
            return {"status": "no_data"}
        
        # Calcular métricas de qualidade
        completeness = self._calculate_completeness(dataset)
        consistency = self._calculate_consistency_metrics(dataset)
        
        # Score geral de qualidade
        quality_score = (completeness + consistency.get("overall", 0)) / 2
        
        return {
            "completeness": completeness,
            "consistency": consistency,
            "overall_quality_score": quality_score,
            "quality_level": self._classify_quality_level(quality_score)
        }
    
    def _calculate_completeness(self, dataset: List[Dict[str, Any]]) -> float:
        """Calcula completude dos dados."""
        if not dataset:
            return 0.0
        
        total_fields = 0
        filled_fields = 0
        
        for item in dataset:
            for field, value in item.items():
                total_fields += 1
                if value is not None and value != "":
                    filled_fields += 1
        
        return filled_fields / max(1, total_fields)
    
    def _calculate_consistency_metrics(self, dataset: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calcula métricas de consistência."""
        if not dataset:
            return {"overall": 0.0}
        
        # Verificar consistência de tipos
        field_types = defaultdict(set)
        
        for item in dataset:
            for field, value in item.items():
                if value is not None:
                    field_types[field].add(type(value).__name__)
        
        # Calcular score de consistência
        consistency_scores = {}
        for field, types in field_types.items():
            consistency_scores[field] = 1.0 if len(types) == 1 else 0.5
        
        overall = sum(consistency_scores.values()) / len(consistency_scores) if consistency_scores else 0
        
        return {
            **consistency_scores,
            "overall": overall
        }
    
    def _classify_quality_level(self, score: float) -> str:
        """Classifica nível de qualidade."""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.7:
            return "good"
        elif score >= 0.5:
            return "fair"
        else:
            return "poor"
    
    def _generate_executive_summary(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Gera resumo executivo."""
        return {
            "total_records": len(dataset),
            "data_period": self._determine_data_period(dataset),
            "key_insights": self._extract_key_insights(dataset),
            "data_health": self._assess_data_health(dataset)
        }
    
    def _determine_data_period(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Determina período dos dados."""
        # Implementação básica
        return {
            "status": "analysis_period",
            "records_analyzed": len(dataset)
        }
    
    def _extract_key_insights(self, dataset: List[Dict[str, Any]]) -> List[str]:
        """Extrai insights principais."""
        insights = []
        
        if len(dataset) > 1000:
            insights.append("Dataset de grande volume com mais de 1000 registros")
        
        # Verificar diversidade
        if self._has_high_diversity(dataset):
            insights.append("Dados apresentam alta diversidade de valores")
        
        return insights
    
    def _has_high_diversity(self, dataset: List[Dict[str, Any]]) -> bool:
        """Verifica se dados têm alta diversidade."""
        if not dataset:
            return False
        
        # Calcular diversidade baseada em campos únicos
        unique_values = defaultdict(set)
        
        for item in dataset:
            for field, value in item.items():
                if value is not None:
                    unique_values[field].add(str(value))
        
        # Se algum campo tem alta diversidade
        for field, values in unique_values.items():
            diversity_ratio = len(values) / len(dataset)
            if diversity_ratio > 0.8:
                return True
        
        return False
    
    def _assess_data_health(self, dataset: List[Dict[str, Any]]) -> str:
        """Avalia saúde geral dos dados."""
        quality = self._assess_data_quality(dataset)
        score = quality.get("overall_quality_score", 0)
        
        if score >= 0.8:
            return "healthy"
        elif score >= 0.6:
            return "moderate"
        else:
            return "needs_attention"
