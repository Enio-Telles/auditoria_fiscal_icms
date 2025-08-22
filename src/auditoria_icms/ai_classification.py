#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de IA com LLMs para Classificação Automática NCM/CEST
=============================================================

Este módulo implementa diferentes estratégias de IA para classificação
automática de produtos usando modelos de linguagem (LLMs).

Estratégias implementadas:
1. OpenAI GPT (API)
2. Ollama (Local)
3. Hugging Face Transformers
4. Ensemble de múltiplos modelos
5. RAG (Retrieval Augmented Generation) com base de conhecimento NCM/CEST
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """Provedores de LLM disponíveis"""
    OPENAI = "openai"
    OLLAMA = "ollama" 
    HUGGINGFACE = "huggingface"
    ENSEMBLE = "ensemble"

@dataclass
class ClassificationRequest:
    """Request para classificação de produto"""
    produto_id: str
    descricao_produto: str
    categoria: Optional[str] = None
    subcategoria: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    preco: Optional[float] = None
    unidade_medida: Optional[str] = None
    contexto_adicional: Optional[str] = None

@dataclass
class ClassificationResult:
    """Resultado da classificação"""
    produto_id: str
    ncm_sugerido: str
    ncm_descricao: str
    ncm_confianca: float
    cest_sugerido: Optional[str] = None
    cest_descricao: Optional[str] = None
    cest_confianca: Optional[float] = None
    justificativa: str = ""
    modelo_usado: str = ""
    tempo_processamento: float = 0.0
    metadata: Dict[str, Any] = None

class NCMCESTKnowledgeBase:
    """Base de conhecimento NCM/CEST para RAG"""
    
    def __init__(self, data_path: str = "data/raw"):
        self.data_path = data_path
        self.ncm_data = None
        self.cest_data = None
        self.embeddings = None
        self.load_knowledge_base()
    
    def load_knowledge_base(self):
        """Carrega base de conhecimento NCM/CEST"""
        try:
            # Carregar NCM
            ncm_file = os.path.join(self.data_path, "descricoes_ncm.json")
            if os.path.exists(ncm_file):
                with open(ncm_file, 'r', encoding='utf-8') as f:
                    self.ncm_data = json.load(f)
                logger.info(f"Carregados {len(self.ncm_data)} códigos NCM")
            
            # Carregar CEST
            cest_file = os.path.join(self.data_path, "CEST_RO.xlsx")
            if os.path.exists(cest_file):
                self.cest_data = pd.read_excel(cest_file)
                logger.info(f"Carregados {len(self.cest_data)} códigos CEST")
                
        except Exception as e:
            logger.error(f"Erro ao carregar base de conhecimento: {e}")
    
    def search_similar_ncm(self, query: str, top_k: int = 10) -> List[Dict]:
        """Busca NCMs similares usando busca textual simples"""
        if not self.ncm_data:
            return []
        
        query_lower = query.lower()
        matches = []
        
        for item in self.ncm_data:
            descricao = item.get('Descricao_Completa', '').lower()
            if any(word in descricao for word in query_lower.split()):
                score = sum(1 for word in query_lower.split() if word in descricao)
                matches.append({
                    'codigo': item.get('Código'),
                    'descricao': item.get('Descricao_Completa'),
                    'score': score
                })
        
        # Ordenar por score e retornar top_k
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches[:top_k]

class OpenAIClassifier:
    """Classificador usando OpenAI GPT"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = None
        
        if self.api_key:
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
                logger.info("OpenAI client inicializado")
            except ImportError:
                logger.warning("Biblioteca openai não instalada. Use: pip install openai")
        else:
            logger.warning("OPENAI_API_KEY não configurada")
    
    async def classify(self, request: ClassificationRequest, knowledge_base: NCMCESTKnowledgeBase) -> ClassificationResult:
        """Classifica produto usando OpenAI"""
        start_time = datetime.now()
        
        if not self.client:
            return ClassificationResult(
                produto_id=request.produto_id,
                ncm_sugerido="0000.00.00",
                ncm_descricao="Erro: OpenAI não disponível",
                ncm_confianca=0.0,
                justificativa="Cliente OpenAI não configurado",
                modelo_usado="openai-error"
            )
        
        # Buscar NCMs similares para contexto
        similar_ncms = knowledge_base.search_similar_ncm(request.descricao_produto, top_k=5)
        
        # Construir prompt
        prompt = self._build_classification_prompt(request, similar_ncms)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um especialista em classificação fiscal NCM/CEST do Brasil."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content
            parsed_result = self._parse_openai_response(result_text, request.produto_id)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            parsed_result.tempo_processamento = elapsed
            parsed_result.modelo_usado = f"openai-{self.model}"
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Erro na classificação OpenAI: {e}")
            return ClassificationResult(
                produto_id=request.produto_id,
                ncm_sugerido="0000.00.00",
                ncm_descricao=f"Erro OpenAI: {str(e)}",
                ncm_confianca=0.0,
                justificativa=f"Erro durante classificação: {str(e)}",
                modelo_usado="openai-error",
                tempo_processamento=(datetime.now() - start_time).total_seconds()
            )
    
    def _build_classification_prompt(self, request: ClassificationRequest, similar_ncms: List[Dict]) -> str:
        """Constrói prompt para classificação"""
        
        context_ncms = "\n".join([
            f"- {item['codigo']}: {item['descricao']}" 
            for item in similar_ncms[:3]
        ]) if similar_ncms else "Nenhum NCM similar encontrado"
        
        return f"""
Classifique o seguinte produto segundo a nomenclatura NCM brasileira:

PRODUTO:
- Descrição: {request.descricao_produto}
- Categoria: {request.categoria or 'Não informada'}
- Subcategoria: {request.subcategoria or 'Não informada'}
- Marca: {request.marca or 'Não informada'}
- Modelo: {request.modelo or 'Não informado'}
- Preço: {request.preco or 'Não informado'}
- Unidade: {request.unidade_medida or 'Não informada'}

NCMs SIMILARES PARA REFERÊNCIA:
{context_ncms}

Responda EXATAMENTE no formato:
NCM: [código de 8 dígitos]
DESCRIÇÃO: [descrição do NCM]
CONFIANÇA: [número de 0 a 1]
JUSTIFICATIVA: [explicação detalhada da escolha]

Exemplo:
NCM: 8517.12.31
DESCRIÇÃO: Telefones para redes celulares
CONFIANÇA: 0.95
JUSTIFICATIVA: O produto é claramente um dispositivo de telecomunicação móvel...
"""
    
    def _parse_openai_response(self, response_text: str, produto_id: str) -> ClassificationResult:
        """Parseia resposta do OpenAI"""
        try:
            lines = response_text.strip().split('\n')
            ncm_code = ""
            descricao = ""
            confianca = 0.0
            justificativa = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith("NCM:"):
                    ncm_code = line.replace("NCM:", "").strip()
                elif line.startswith("DESCRIÇÃO:"):
                    descricao = line.replace("DESCRIÇÃO:", "").strip()
                elif line.startswith("CONFIANÇA:"):
                    try:
                        confianca = float(line.replace("CONFIANÇA:", "").strip())
                    except:
                        confianca = 0.5
                elif line.startswith("JUSTIFICATIVA:"):
                    justificativa = line.replace("JUSTIFICATIVA:", "").strip()
            
            # Continuar lendo justificativa em múltiplas linhas
            if justificativa and len(lines) > 4:
                justificativa_lines = []
                start_reading = False
                for line in lines:
                    if "JUSTIFICATIVA:" in line:
                        start_reading = True
                        justificativa_lines.append(line.replace("JUSTIFICATIVA:", "").strip())
                    elif start_reading and line.strip():
                        justificativa_lines.append(line.strip())
                justificativa = " ".join(justificativa_lines).strip()
            
            return ClassificationResult(
                produto_id=produto_id,
                ncm_sugerido=ncm_code or "0000.00.00",
                ncm_descricao=descricao or "Não classificado",
                ncm_confianca=confianca,
                justificativa=justificativa or "Classificação automática via OpenAI",
                modelo_usado="openai-gpt"
            )
            
        except Exception as e:
            logger.error(f"Erro ao parsear resposta OpenAI: {e}")
            return ClassificationResult(
                produto_id=produto_id,
                ncm_sugerido="0000.00.00",
                ncm_descricao="Erro no parsing",
                ncm_confianca=0.0,
                justificativa=f"Erro ao interpretar resposta: {str(e)}",
                modelo_usado="openai-parse-error"
            )

class OllamaClassifier:
    """Classificador usando Ollama (local)"""
    
    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.client = None
        
        try:
            import requests
            # Testar conexão com Ollama
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("Ollama conectado com sucesso")
                self.client = True
            else:
                logger.warning("Ollama não está rodando")
        except Exception as e:
            logger.warning(f"Ollama não disponível: {e}")
    
    async def classify(self, request: ClassificationRequest, knowledge_base: NCMCESTKnowledgeBase) -> ClassificationResult:
        """Classifica produto usando Ollama"""
        start_time = datetime.now()
        
        if not self.client:
            return ClassificationResult(
                produto_id=request.produto_id,
                ncm_sugerido="0000.00.00",
                ncm_descricao="Erro: Ollama não disponível",
                ncm_confianca=0.0,
                justificativa="Ollama não está rodando em localhost:11434",
                modelo_usado="ollama-error"
            )
        
        # Buscar NCMs similares
        similar_ncms = knowledge_base.search_similar_ncm(request.descricao_produto, top_k=3)
        
        # Construir prompt simplificado para Ollama
        prompt = self._build_ollama_prompt(request, similar_ncms)
        
        try:
            import requests
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 300
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                parsed_result = self._parse_ollama_response(response_text, request.produto_id)
                elapsed = (datetime.now() - start_time).total_seconds()
                parsed_result.tempo_processamento = elapsed
                parsed_result.modelo_usado = f"ollama-{self.model}"
                
                return parsed_result
            else:
                raise Exception(f"Ollama retornou status {response.status_code}")
                
        except Exception as e:
            logger.error(f"Erro na classificação Ollama: {e}")
            return ClassificationResult(
                produto_id=request.produto_id,
                ncm_sugerido="0000.00.00",
                ncm_descricao=f"Erro Ollama: {str(e)}",
                ncm_confianca=0.0,
                justificativa=f"Erro durante classificação: {str(e)}",
                modelo_usado="ollama-error",
                tempo_processamento=(datetime.now() - start_time).total_seconds()
            )
    
    def _build_ollama_prompt(self, request: ClassificationRequest, similar_ncms: List[Dict]) -> str:
        """Constrói prompt otimizado para Ollama"""
        
        context = "\n".join([
            f"{item['codigo']}: {item['descricao'][:100]}" 
            for item in similar_ncms[:2]
        ]) if similar_ncms else ""
        
        return f"""Você é especialista em classificação NCM. Classifique este produto:

Produto: {request.descricao_produto}
Categoria: {request.categoria or 'N/A'}

NCMs similares:
{context}

Responda apenas:
NCM: [código 8 dígitos]
CONFIANÇA: [0-1]
RAZÃO: [breve explicação]
"""
    
    def _parse_ollama_response(self, response_text: str, produto_id: str) -> ClassificationResult:
        """Parseia resposta do Ollama"""
        try:
            lines = response_text.strip().split('\n')
            ncm_code = ""
            confianca = 0.5
            razao = ""
            
            for line in lines:
                line = line.strip()
                if "NCM:" in line:
                    ncm_code = line.split("NCM:")[-1].strip()
                elif "CONFIANÇA:" in line or "CONFIANCA:" in line:
                    try:
                        conf_text = line.split(":")[-1].strip()
                        confianca = float(conf_text)
                    except:
                        confianca = 0.5
                elif "RAZÃO:" in line or "RAZAO:" in line:
                    razao = line.split(":")[-1].strip()
            
            return ClassificationResult(
                produto_id=produto_id,
                ncm_sugerido=ncm_code or "0000.00.00",
                ncm_descricao="Classificação via Ollama",
                ncm_confianca=confianca,
                justificativa=razao or "Classificação automática via Ollama",
                modelo_usado="ollama"
            )
            
        except Exception as e:
            logger.error(f"Erro ao parsear resposta Ollama: {e}")
            return ClassificationResult(
                produto_id=produto_id,
                ncm_sugerido="0000.00.00",
                ncm_descricao="Erro no parsing Ollama",
                ncm_confianca=0.0,
                justificativa=f"Erro ao interpretar resposta: {str(e)}",
                modelo_usado="ollama-parse-error"
            )

class HuggingFaceClassifier:
    """Classificador usando Hugging Face Transformers"""
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        self.model_name = model_name
        self.pipeline = None
        
        try:
            from transformers import pipeline
            self.pipeline = pipeline("text-generation", 
                                   model=model_name, 
                                   max_length=200, 
                                   do_sample=True, 
                                   temperature=0.1)
            logger.info(f"Modelo Hugging Face {model_name} carregado")
        except ImportError:
            logger.warning("Transformers não instalado. Use: pip install transformers torch")
        except Exception as e:
            logger.warning(f"Erro ao carregar modelo HF: {e}")
    
    async def classify(self, request: ClassificationRequest, knowledge_base: NCMCESTKnowledgeBase) -> ClassificationResult:
        """Classifica produto usando Hugging Face"""
        start_time = datetime.now()
        
        if not self.pipeline:
            return ClassificationResult(
                produto_id=request.produto_id,
                ncm_sugerido="0000.00.00",
                ncm_descricao="Erro: Hugging Face não disponível",
                ncm_confianca=0.0,
                justificativa="Pipeline Hugging Face não carregado",
                modelo_usado="hf-error"
            )
        
        # Para este exemplo, vamos usar uma classificação baseada em regras simples
        # em combinação com busca na base de conhecimento
        similar_ncms = knowledge_base.search_similar_ncm(request.descricao_produto, top_k=1)
        
        if similar_ncms:
            best_match = similar_ncms[0]
            confianca = min(0.8, best_match['score'] / 10.0)  # Normalizar score
            
            return ClassificationResult(
                produto_id=request.produto_id,
                ncm_sugerido=best_match['codigo'],
                ncm_descricao=best_match['descricao'],
                ncm_confianca=confianca,
                justificativa=f"Melhor correspondência encontrada na base NCM (score: {best_match['score']})",
                modelo_usado="hf-rule-based",
                tempo_processamento=(datetime.now() - start_time).total_seconds()
            )
        else:
            return ClassificationResult(
                produto_id=request.produto_id,
                ncm_sugerido="9999.99.99",
                ncm_descricao="Não classificado",
                ncm_confianca=0.1,
                justificativa="Nenhuma correspondência encontrada na base NCM",
                modelo_usado="hf-fallback",
                tempo_processamento=(datetime.now() - start_time).total_seconds()
            )

class AIClassificationEngine:
    """Engine principal de classificação com IA"""
    
    def __init__(self, data_path: str = "data/raw"):
        self.knowledge_base = NCMCESTKnowledgeBase(data_path)
        self.classifiers = {
            LLMProvider.OPENAI: OpenAIClassifier(),
            LLMProvider.OLLAMA: OllamaClassifier(),
            LLMProvider.HUGGINGFACE: HuggingFaceClassifier()
        }
        
        logger.info("AI Classification Engine inicializado")
    
    async def classify_single(self, request: ClassificationRequest, provider: LLMProvider = LLMProvider.OPENAI) -> ClassificationResult:
        """Classifica um único produto"""
        classifier = self.classifiers.get(provider)
        if not classifier:
            raise ValueError(f"Provider {provider} não disponível")
        
        return await classifier.classify(request, self.knowledge_base)
    
    async def classify_ensemble(self, request: ClassificationRequest) -> ClassificationResult:
        """Classifica usando ensemble de múltiplos modelos"""
        start_time = datetime.now()
        
        # Executar classificação com múltiplos modelos em paralelo
        tasks = []
        for provider in [LLMProvider.OPENAI, LLMProvider.OLLAMA, LLMProvider.HUGGINGFACE]:
            classifier = self.classifiers.get(provider)
            if classifier:
                tasks.append(classifier.classify(request, self.knowledge_base))
        
        if not tasks:
            return ClassificationResult(
                produto_id=request.produto_id,
                ncm_sugerido="0000.00.00",
                ncm_descricao="Nenhum classificador disponível",
                ncm_confianca=0.0,
                justificativa="Todos os classificadores falharam",
                modelo_usado="ensemble-error"
            )
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar resultados válidos
        valid_results = [r for r in results if isinstance(r, ClassificationResult) and r.ncm_confianca > 0]
        
        if not valid_results:
            return ClassificationResult(
                produto_id=request.produto_id,
                ncm_sugerido="0000.00.00",
                ncm_descricao="Todos os modelos falharam",
                ncm_confianca=0.0,
                justificativa="Nenhum modelo conseguiu classificar o produto",
                modelo_usado="ensemble-failed"
            )
        
        # Combinar resultados (weighted voting por confiança)
        total_weight = sum(r.ncm_confianca for r in valid_results)
        if total_weight == 0:
            # Fallback para primeiro resultado
            best_result = valid_results[0]
        else:
            # Encontrar resultado com maior confiança
            best_result = max(valid_results, key=lambda x: x.ncm_confianca)
        
        # Criar resultado ensemble
        ensemble_result = ClassificationResult(
            produto_id=request.produto_id,
            ncm_sugerido=best_result.ncm_sugerido,
            ncm_descricao=best_result.ncm_descricao,
            ncm_confianca=best_result.ncm_confianca,
            justificativa=f"Ensemble de {len(valid_results)} modelos. Melhor: {best_result.modelo_usado}. " + best_result.justificativa,
            modelo_usado=f"ensemble-{len(valid_results)}models",
            tempo_processamento=(datetime.now() - start_time).total_seconds(),
            metadata={
                'all_results': [
                    {
                        'modelo': r.modelo_usado,
                        'ncm': r.ncm_sugerido,
                        'confianca': r.ncm_confianca
                    } for r in valid_results
                ],
                'consensus_score': len(set(r.ncm_sugerido for r in valid_results)) / len(valid_results) if valid_results else 0
            }
        )
        
        return ensemble_result
    
    async def classify_batch(self, requests: List[ClassificationRequest], provider: LLMProvider = LLMProvider.ENSEMBLE) -> List[ClassificationResult]:
        """Classifica múltiplos produtos em lote"""
        logger.info(f"Iniciando classificação em lote de {len(requests)} produtos")
        
        tasks = []
        for request in requests:
            if provider == LLMProvider.ENSEMBLE:
                tasks.append(self.classify_ensemble(request))
            else:
                tasks.append(self.classify_single(request, provider))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Converter exceções em resultados de erro
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(ClassificationResult(
                    produto_id=requests[i].produto_id,
                    ncm_sugerido="0000.00.00",
                    ncm_descricao=f"Erro: {str(result)}",
                    ncm_confianca=0.0,
                    justificativa=f"Exceção durante classificação: {str(result)}",
                    modelo_usado="batch-error"
                ))
            else:
                final_results.append(result)
        
        logger.info(f"Classificação em lote concluída: {len(final_results)} resultados")
        return final_results

# Funções de conveniência para uso direto
async def classify_product(descricao: str, provider: str = "openai") -> Dict:
    """Função simples para classificar um produto"""
    engine = AIClassificationEngine()
    
    request = ClassificationRequest(
        produto_id="single",
        descricao_produto=descricao
    )
    
    provider_enum = LLMProvider(provider.lower())
    result = await engine.classify_single(request, provider_enum)
    
    return {
        'ncm': result.ncm_sugerido,
        'descricao': result.ncm_descricao,
        'confianca': result.ncm_confianca,
        'justificativa': result.justificativa,
        'modelo': result.modelo_usado,
        'tempo': result.tempo_processamento
    }

async def classify_products_batch(produtos: List[str], provider: str = "ensemble") -> List[Dict]:
    """Função simples para classificar múltiplos produtos"""
    engine = AIClassificationEngine()
    
    requests = [
        ClassificationRequest(produto_id=str(i), descricao_produto=desc)
        for i, desc in enumerate(produtos)
    ]
    
    if provider == "ensemble":
        results = await engine.classify_batch(requests, LLMProvider.ENSEMBLE)
    else:
        provider_enum = LLMProvider(provider.lower())
        results = await engine.classify_batch(requests, provider_enum)
    
    return [
        {
            'produto': requests[i].descricao_produto,
            'ncm': result.ncm_sugerido,
            'descricao': result.ncm_descricao,
            'confianca': result.ncm_confianca,
            'justificativa': result.justificativa,
            'modelo': result.modelo_usado,
            'tempo': result.tempo_processamento
        }
        for i, result in enumerate(results)
    ]

if __name__ == "__main__":
    # Exemplo de uso
    async def main():
        # Teste simples
        result = await classify_product("Notebook Dell Inspiron 15 3000")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Teste em lote
        produtos_teste = [
            "Smartphone Samsung Galaxy A50",
            "Café torrado e moído 500g",
            "Parafuso sextavado M6 x 20mm aço inox"
        ]
        
        results = await classify_products_batch(produtos_teste)
        for result in results:
            print(f"\nProduto: {result['produto']}")
            print(f"NCM: {result['ncm']} ({result['confianca']:.2f})")
            print(f"Modelo: {result['modelo']}")
    
    # Executar teste apenas se script for executado diretamente
    # asyncio.run(main())
    print("Módulo de IA para classificação NCM/CEST carregado com sucesso!")
    print("Use: from ai_classification import classify_product, classify_products_batch")
