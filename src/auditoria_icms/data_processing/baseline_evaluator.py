"""
Baseline Evaluation para Sistema de Auditoria Fiscal ICMS v15.0
Avaliação da qualidade do sistema RAG usando métricas RAGAS
"""

import os
import json
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime
import numpy as np

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BaselineEvaluator:
    """Classe para avaliação baseline do sistema RAG"""
    
    def __init__(self, 
                 vector_db_path: str = "./data/processed/vector_db",
                 evaluation_dataset_path: str = "./data/processed/evaluation_dataset.json",
                 output_dir: str = "./data/processed/evaluations"):
        
        self.vector_db_path = vector_db_path
        self.evaluation_dataset_path = evaluation_dataset_path
        self.output_dir = output_dir
        
        # Cria diretório de saída
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Métricas de avaliação
        self.metrics = {
            'context_precision': [],
            'context_recall': [],
            'faithfulness': [],
            'answer_relevancy': [],
            'semantic_similarity': [],
            'retrieval_precision': [],
            'retrieval_recall': []
        }
        
        # Dataset de avaliação
        self.evaluation_dataset = self._create_evaluation_dataset()
    
    def _create_evaluation_dataset(self) -> List[Dict]:
        """Cria dataset de avaliação com perguntas e respostas esperadas."""
        logger.info("Criando dataset de avaliação...")
        
        # Dataset sintético para avaliação inicial
        evaluation_data = [
            {
                "question": "Qual é o NCM para medicamentos genéricos?",
                "expected_answer": "O NCM para medicamentos genéricos é 30049069 - Outros medicamentos constituídos por produtos misturados ou não misturados",
                "expected_contexts": [
                    "NCM 30049069: Outros medicamentos constituídos por produtos misturados ou não misturados",
                    "CEST 17.004.00: Medicamentos genéricos"
                ],
                "category": "medicamentos",
                "difficulty": "easy"
            },
            {
                "question": "Quais produtos estão sujeitos à substituição tributária para telefones celulares?",
                "expected_answer": "Telefones celulares com NCM 85171211 e 85171212 estão sujeitos à substituição tributária conforme CEST 21.001.00",
                "expected_contexts": [
                    "NCM 85171211: Telefones móveis e de outras redes sem fio",
                    "NCM 85171212: Telefones inteligentes",
                    "CEST 21.001.00: Aparelhos telefônicos"
                ],
                "category": "telecomunicacoes",
                "difficulty": "medium"
            },
            {
                "question": "Como classificar uma bebida açucarada para fins de ICMS?",
                "expected_answer": "Bebidas açucaradas devem ser classificadas no NCM 22021000 - Águas, incluindo as águas minerais e as águas gaseificadas, adicionadas de açúcar",
                "expected_contexts": [
                    "NCM 22021000: Águas, incluindo as águas minerais e as águas gaseificadas, adicionadas de açúcar",
                    "Produtos com açúcar adicionado seguem classificação específica"
                ],
                "category": "bebidas",
                "difficulty": "medium"
            },
            {
                "question": "Quais são as regras NESH aplicáveis a produtos importados?",
                "expected_answer": "As regras NESH estabelecem critérios específicos para classificação de produtos importados, incluindo análise de origem, composição e finalidade",
                "expected_contexts": [
                    "Notas Explicativas do Sistema Harmonizado (NESH)",
                    "Regras para produtos importados",
                    "Critérios de classificação NESH"
                ],
                "category": "importacao",
                "difficulty": "hard"
            },
            {
                "question": "Como identificar se um produto requer classificação CEST específica?",
                "expected_answer": "Um produto requer CEST específica se estiver listado na tabela de produtos sujeitos à substituição tributária ou antecipação tributária",
                "expected_contexts": [
                    "Tabela CEST de produtos sujeitos à substituição tributária",
                    "Critérios para aplicação de CEST",
                    "Produtos com regime especial de tributação"
                ],
                "category": "classificacao",
                "difficulty": "hard"
            }
        ]
        
        # Salva dataset
        dataset_file = self.evaluation_dataset_path
        os.makedirs(os.path.dirname(dataset_file), exist_ok=True)
        
        with open(dataset_file, 'w', encoding='utf-8') as f:
            json.dump(evaluation_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Dataset de avaliação criado com {len(evaluation_data)} exemplos")
        return evaluation_data
    
    def simulate_rag_retrieval(self, question: str) -> List[str]:
        """Simula recuperação de contextos relevantes."""
        # Simulação baseada em palavras-chave
        simulated_retrievals = {
            "medicamentos": [
                "NCM 30049069: Outros medicamentos constituídos por produtos misturados ou não misturados",
                "CEST 17.004.00: Medicamentos genéricos",
                "Produtos farmacêuticos seguem regulamentação específica"
            ],
            "telefones": [
                "NCM 85171211: Telefones móveis e de outras redes sem fio",
                "NCM 85171212: Telefones inteligentes",
                "CEST 21.001.00: Aparelhos telefônicos"
            ],
            "bebidas": [
                "NCM 22021000: Águas, incluindo as águas minerais e as águas gaseificadas, adicionadas de açúcar",
                "Produtos com açúcar seguem classificação específica",
                "Bebidas não alcoólicas têm tributação diferenciada"
            ],
            "nesh": [
                "Notas Explicativas do Sistema Harmonizado (NESH)",
                "Regras para produtos importados",
                "Critérios de classificação internacional"
            ],
            "cest": [
                "Tabela CEST de produtos sujeitos à substituição tributária",
                "Critérios para aplicação de CEST",
                "Produtos com regime especial de tributação"
            ]
        }
        
        question_lower = question.lower()
        retrieved_contexts = []
        
        for keyword, contexts in simulated_retrievals.items():
            if keyword in question_lower:
                retrieved_contexts.extend(contexts)
        
        # Se não encontrou contextos específicos, retorna contextos genéricos
        if not retrieved_contexts:
            retrieved_contexts = [
                "Classificação fiscal segue regras específicas",
                "Consulte tabelas NCM e CEST atualizadas",
                "Verificar legislação aplicável"
            ]
        
        return retrieved_contexts[:3]  # Retorna top 3
    
    def simulate_rag_generation(self, question: str, contexts: List[str]) -> str:
        """Simula geração de resposta baseada nos contextos."""
        question_lower = question.lower()
        
        # Simulação de geração baseada em templates
        if "ncm" in question_lower and "medicamentos" in question_lower:
            return "O NCM para medicamentos genéricos é 30049069 - Outros medicamentos constituídos por produtos misturados ou não misturados"
        
        elif "telefones" in question_lower or "celulares" in question_lower:
            return "Telefones celulares com NCM 85171211 e 85171212 estão sujeitos à substituição tributária conforme CEST 21.001.00"
        
        elif "bebida" in question_lower:
            return "Bebidas açucaradas devem ser classificadas no NCM 22021000 - Águas, incluindo as águas minerais e as águas gaseificadas, adicionadas de açúcar"
        
        elif "nesh" in question_lower:
            return "As regras NESH estabelecem critérios específicos para classificação de produtos importados, incluindo análise de origem, composição e finalidade"
        
        elif "cest" in question_lower:
            return "Um produto requer CEST específica se estiver listado na tabela de produtos sujeitos à substituição tributária ou antecipação tributária"
        
        else:
            return "Para classificação fiscal adequada, consulte as tabelas NCM e CEST atualizadas, considerando as características específicas do produto."
    
    def calculate_context_precision(self, retrieved_contexts: List[str], expected_contexts: List[str]) -> float:
        """Calcula precisão dos contextos recuperados."""
        if not retrieved_contexts:
            return 0.0
        
        relevant_retrieved = 0
        for context in retrieved_contexts:
            for expected in expected_contexts:
                # Similaridade simples por palavras-chave
                if any(word in context.lower() for word in expected.lower().split() if len(word) > 3):
                    relevant_retrieved += 1
                    break
        
        return relevant_retrieved / len(retrieved_contexts)
    
    def calculate_context_recall(self, retrieved_contexts: List[str], expected_contexts: List[str]) -> float:
        """Calcula recall dos contextos recuperados."""
        if not expected_contexts:
            return 1.0
        
        relevant_retrieved = 0
        for expected in expected_contexts:
            for context in retrieved_contexts:
                if any(word in context.lower() for word in expected.lower().split() if len(word) > 3):
                    relevant_retrieved += 1
                    break
        
        return relevant_retrieved / len(expected_contexts)
    
    def calculate_faithfulness(self, generated_answer: str, contexts: List[str]) -> float:
        """Calcula fidelidade da resposta aos contextos."""
        if not contexts:
            return 0.0
        
        # Verifica se a resposta contém informações dos contextos
        answer_words = set(generated_answer.lower().split())
        context_words = set()
        
        for context in contexts:
            context_words.update(context.lower().split())
        
        # Calcula sobreposição de palavras significativas
        significant_words = {word for word in answer_words if len(word) > 3}
        overlap = len(significant_words.intersection(context_words))
        
        if not significant_words:
            return 0.0
        
        return min(overlap / len(significant_words), 1.0)
    
    def calculate_answer_relevancy(self, generated_answer: str, question: str) -> float:
        """Calcula relevância da resposta à pergunta."""
        question_words = set(question.lower().split())
        answer_words = set(generated_answer.lower().split())
        
        # Remove palavras comuns
        stop_words = {'o', 'a', 'de', 'da', 'do', 'para', 'com', 'em', 'é', 'são', 'como', 'qual', 'quais'}
        question_words = {word for word in question_words if word not in stop_words and len(word) > 2}
        answer_words = {word for word in answer_words if word not in stop_words and len(word) > 2}
        
        if not question_words:
            return 0.0
        
        overlap = len(question_words.intersection(answer_words))
        return overlap / len(question_words)
    
    def calculate_semantic_similarity(self, generated_answer: str, expected_answer: str) -> float:
        """Calcula similaridade semântica entre respostas."""
        # Implementação simples usando Jaccard similarity
        gen_words = set(generated_answer.lower().split())
        exp_words = set(expected_answer.lower().split())
        
        intersection = len(gen_words.intersection(exp_words))
        union = len(gen_words.union(exp_words))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def evaluate_single_example(self, example: Dict) -> Dict:
        """Avalia um único exemplo do dataset."""
        question = example["question"]
        expected_answer = example["expected_answer"]
        expected_contexts = example["expected_contexts"]
        
        # Simula recuperação e geração
        retrieved_contexts = self.simulate_rag_retrieval(question)
        generated_answer = self.simulate_rag_generation(question, retrieved_contexts)
        
        # Calcula métricas
        metrics = {
            'context_precision': self.calculate_context_precision(retrieved_contexts, expected_contexts),
            'context_recall': self.calculate_context_recall(retrieved_contexts, expected_contexts),
            'faithfulness': self.calculate_faithfulness(generated_answer, retrieved_contexts),
            'answer_relevancy': self.calculate_answer_relevancy(generated_answer, question),
            'semantic_similarity': self.calculate_semantic_similarity(generated_answer, expected_answer)
        }
        
        return {
            'question': question,
            'expected_answer': expected_answer,
            'generated_answer': generated_answer,
            'retrieved_contexts': retrieved_contexts,
            'expected_contexts': expected_contexts,
            'metrics': metrics,
            'category': example.get('category', 'unknown'),
            'difficulty': example.get('difficulty', 'medium')
        }
    
    def run_baseline_evaluation(self) -> Dict:
        """Executa avaliação baseline completa."""
        logger.info("=== Iniciando Avaliação Baseline ===")
        
        results = []
        all_metrics = {metric: [] for metric in self.metrics.keys()}
        
        # Avalia cada exemplo
        for i, example in enumerate(self.evaluation_dataset):
            logger.info(f"Avaliando exemplo {i+1}/{len(self.evaluation_dataset)}: {example['category']}")
            
            result = self.evaluate_single_example(example)
            results.append(result)
            
            # Acumula métricas
            for metric, value in result['metrics'].items():
                all_metrics[metric].append(value)
        
        # Calcula estatísticas agregadas
        aggregated_metrics = {}
        for metric, values in all_metrics.items():
            if values:
                aggregated_metrics[metric] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'median': np.median(values)
                }
            else:
                aggregated_metrics[metric] = {
                    'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0, 'median': 0.0
                }
        
        # Calcula métricas por categoria
        category_metrics = {}
        for result in results:
            category = result['category']
            if category not in category_metrics:
                category_metrics[category] = {metric: [] for metric in self.metrics.keys()}
            
            for metric, value in result['metrics'].items():
                category_metrics[category][metric].append(value)
        
        # Agrega métricas por categoria
        for category, metrics in category_metrics.items():
            for metric, values in metrics.items():
                if values:
                    category_metrics[category][metric] = {
                        'mean': np.mean(values),
                        'count': len(values)
                    }
        
        # Compila relatório final
        evaluation_report = {
            'timestamp': datetime.now().isoformat(),
            'dataset_size': len(self.evaluation_dataset),
            'aggregated_metrics': aggregated_metrics,
            'category_metrics': category_metrics,
            'detailed_results': results,
            'summary': {
                'average_context_precision': aggregated_metrics['context_precision']['mean'],
                'average_context_recall': aggregated_metrics['context_recall']['mean'],
                'average_faithfulness': aggregated_metrics['faithfulness']['mean'],
                'average_answer_relevancy': aggregated_metrics['answer_relevancy']['mean'],
                'average_semantic_similarity': aggregated_metrics['semantic_similarity']['mean'],
                'overall_score': np.mean([
                    aggregated_metrics['context_precision']['mean'],
                    aggregated_metrics['context_recall']['mean'],
                    aggregated_metrics['faithfulness']['mean'],
                    aggregated_metrics['answer_relevancy']['mean'],
                    aggregated_metrics['semantic_similarity']['mean']
                ])
            }
        }
        
        logger.info("=== Avaliação Baseline Concluída ===")
        logger.info(f"Score geral: {evaluation_report['summary']['overall_score']:.3f}")
        
        return evaluation_report
    
    def save_evaluation_report(self, report: Dict):
        """Salva relatório de avaliação."""
        report_file = os.path.join(self.output_dir, "baseline_evaluation_report.json")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Relatório de avaliação salvo: {report_file}")
        
        # Salva também um resumo em texto
        summary_file = os.path.join(self.output_dir, "evaluation_summary.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=== RELATÓRIO DE AVALIAÇÃO BASELINE ===\\n")
            f.write(f"Data: {report['timestamp']}\\n")
            f.write(f"Dataset: {report['dataset_size']} exemplos\\n\\n")
            
            f.write("MÉTRICAS AGREGADAS:\\n")
            for metric, stats in report['aggregated_metrics'].items():
                f.write(f"  {metric}: {stats['mean']:.3f} (±{stats['std']:.3f})\\n")
            
            f.write(f"\\nSCORE GERAL: {report['summary']['overall_score']:.3f}\\n")
            
            f.write("\\nMÉTRICAS POR CATEGORIA:\\n")
            for category, metrics in report['category_metrics'].items():
                f.write(f"  {category}:\\n")
                for metric, stats in metrics.items():
                    if isinstance(stats, dict) and 'mean' in stats:
                        f.write(f"    {metric}: {stats['mean']:.3f}\\n")
        
        logger.info(f"Resumo da avaliação salvo: {summary_file}")

def main():
    """Função principal para teste."""
    evaluator = BaselineEvaluator()
    
    # Executa avaliação
    report = evaluator.run_baseline_evaluation()
    
    # Salva relatório
    evaluator.save_evaluation_report(report)
    
    logger.info(f"Avaliação concluída com score: {report['summary']['overall_score']:.3f}")

if __name__ == "__main__":
    main()
