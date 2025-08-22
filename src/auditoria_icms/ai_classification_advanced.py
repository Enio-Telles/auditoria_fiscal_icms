#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de IA com LLMs para Classificação Automática NCM/CEST - Versão Avançada
===============================================================================

Este módulo implementa um sistema completo de IA com LLMs reais para classificação
automática de produtos usando múltiplos provedores e estratégias avançadas.

Características principais:
- Integração com OpenAI, Ollama, Anthropic e Hugging Face
- Sistema RAG avançado com base de conhecimento NCM/CEST
- Ensemble de múltiplos modelos
- Validação cruzada e aprendizado contínuo
- Auditoria completa de decisões
- Otimizações para performance e custo

Autor: Sistema de IA Auditoria Fiscal
Data: 2025-08-22
"""

import os
import json
import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import hashlib
import sqlite3
from pathlib import Path

# Configurações de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """Provedores de LLM disponíveis"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    ENSEMBLE = "ensemble"

class ClassificationStrategy(Enum):
    """Estratégias de classificação"""
    DIRECT = "direct"           # Classificação direta
    RAG = "rag"                # RAG com base de conhecimento
    HIERARCHICAL = "hierarchical"  # Classificação hierárquica
    ENSEMBLE = "ensemble"       # Ensemble de múltiplas estratégias
    HYBRID = "hybrid"          # Híbrido adaptativo

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
    ncm_atual: Optional[str] = None
    cest_atual: Optional[str] = None
    gtin: Optional[str] = None
    estado: str = "RO"
    empresa_id: Optional[str] = None
    # Metadados para auditoria
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ClassificationResult:
    """Resultado da classificação com auditoria completa"""
    produto_id: str
    ncm_sugerido: str
    ncm_descricao: str
    ncm_confianca: float
    cest_sugerido: Optional[str] = None
    cest_descricao: Optional[str] = None
    cest_confianca: Optional[float] = None
    justificativa: str = ""
    modelos_usados: List[str] = field(default_factory=list)
    tempo_processamento: float = 0.0
    custo_estimado: float = 0.0
    estrategia_usada: str = ""
    
    # Detalhes da auditoria
    audit_trail: Dict[str, Any] = field(default_factory=dict)
    confidence_breakdown: Dict[str, float] = field(default_factory=dict)
    alternative_suggestions: List[Dict] = field(default_factory=list)
    validation_flags: List[str] = field(default_factory=list)
    
    # Metadados
    metadata: Dict[str, Any] = field(default_factory=dict)
    cache_hit: bool = False
    requires_human_review: bool = False

class EnhancedNCMCESTKnowledgeBase:
    """Base de conhecimento avançada NCM/CEST com RAG otimizado"""
    
    def __init__(self, data_path: str = "data/raw", cache_path: str = "data/cache"):
        self.data_path = Path(data_path)
        self.cache_path = Path(cache_path)
        self.cache_path.mkdir(exist_ok=True)
        
        # Dados estruturados
        self.ncm_data = {}
        self.cest_data = {}
        self.ncm_hierarchy = {}
        self.cest_patterns = {}
        
        # Índices para busca rápida
        self.ncm_index = {}
        self.cest_index = {}
        self.keyword_index = {}
        
        # Embeddings para busca semântica
        self.embeddings_model = None
        self.ncm_embeddings = None
        self.cest_embeddings = None
        
        self.load_knowledge_base()
        self.build_search_indices()
    
    def load_knowledge_base(self):
        """Carrega base de conhecimento otimizada"""
        try:
            # Carregar NCM com estrutura hierárquica
            ncm_file = self.data_path / "descricoes_ncm.json"
            if ncm_file.exists():
                with open(ncm_file, 'r', encoding='utf-8') as f:
                    ncm_raw = json.load(f)
                
                # Estruturar hierarquicamente
                for item in ncm_raw:
                    codigo = item.get('Código', '').replace('.', '').replace('-', '')
                    if len(codigo) >= 8:
                        self.ncm_data[codigo] = {
                            'codigo': codigo,
                            'descricao': item.get('Descricao_Completa', ''),
                            'capitulo': codigo[:2],
                            'posicao': codigo[:4],
                            'subposicao': codigo[:6],
                            'item': codigo
                        }
                
                logger.info(f"Carregados {len(self.ncm_data)} códigos NCM")
            
            # Carregar CEST com padrões NCM
            cest_file = self.data_path / "CEST_RO.xlsx"
            if cest_file.exists():
                df = pd.read_excel(cest_file)
                
                for _, row in df.iterrows():
                    cest_code = str(row.get('CEST', '')).replace('.', '')
                    if cest_code and len(cest_code) >= 7:
                        ncm_patterns = str(row.get('NCM', '')).split(',')
                        ncm_patterns = [p.strip().replace('.', '') for p in ncm_patterns if p.strip()]
                        
                        self.cest_data[cest_code] = {
                            'codigo': cest_code,
                            'descricao': str(row.get('Descrição', '')),
                            'ncm_patterns': ncm_patterns,
                            'segmento': str(row.get('Segmento', '')),
                            'anexo': str(row.get('Anexo', ''))
                        }
                
                logger.info(f"Carregados {len(self.cest_data)} códigos CEST")
                
        except Exception as e:
            logger.error(f"Erro ao carregar base de conhecimento: {e}")
    
    def build_search_indices(self):
        """Constrói índices otimizados para busca"""
        # Índice de palavras-chave para NCM
        for codigo, data in self.ncm_data.items():
            descricao = data['descricao'].lower()
            words = descricao.split()
            for word in words:
                if len(word) > 3:  # Palavras significativas
                    if word not in self.keyword_index:
                        self.keyword_index[word] = {'ncm': [], 'cest': []}
                    self.keyword_index[word]['ncm'].append(codigo)
        
        # Índice de palavras-chave para CEST
        for codigo, data in self.cest_data.items():
            descricao = data['descricao'].lower()
            words = descricao.split()
            for word in words:
                if len(word) > 3:
                    if word not in self.keyword_index:
                        self.keyword_index[word] = {'ncm': [], 'cest': []}
                    self.keyword_index[word]['cest'].append(codigo)
        
        logger.info(f"Índice construído com {len(self.keyword_index)} palavras-chave")
    
    def search_ncm_semantic(self, query: str, top_k: int = 10) -> List[Dict]:
        """Busca NCM por similaridade semântica"""
        query_lower = query.lower()
        matches = []
        
        # Busca por palavras-chave
        query_words = query_lower.split()
        candidates = set()
        
        for word in query_words:
            if word in self.keyword_index:
                candidates.update(self.keyword_index[word]['ncm'])
        
        # Calcular scores
        for codigo in candidates:
            if codigo in self.ncm_data:
                data = self.ncm_data[codigo]
                descricao = data['descricao'].lower()
                
                # Score baseado em palavras comuns
                common_words = sum(1 for word in query_words if word in descricao)
                total_words = len(query_words)
                
                if total_words > 0:
                    score = common_words / total_words
                    
                    # Bonus para correspondências exatas
                    if query_lower in descricao:
                        score += 0.3
                    
                    matches.append({
                        'codigo': codigo,
                        'descricao': data['descricao'],
                        'score': score,
                        'nivel': 'item'
                    })
        
        # Ordenar por score
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches[:top_k]
    
    def search_cest_by_ncm(self, ncm: str, estado: str = "RO") -> List[Dict]:
        """Busca CEST compatíveis com NCM"""
        matches = []
        ncm_clean = ncm.replace('.', '').replace('-', '')
        
        for cest_code, data in self.cest_data.items():
            for pattern in data['ncm_patterns']:
                if self._ncm_matches_pattern(ncm_clean, pattern):
                    matches.append({
                        'codigo': cest_code,
                        'descricao': data['descricao'],
                        'ncm_pattern': pattern,
                        'segmento': data['segmento'],
                        'score': self._calculate_pattern_score(ncm_clean, pattern)
                    })
        
        # Ordenar por score de compatibilidade
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches
    
    def _ncm_matches_pattern(self, ncm: str, pattern: str) -> bool:
        """Verifica se NCM corresponde ao padrão CEST"""
        if not pattern or not ncm:
            return False
        
        pattern_clean = pattern.replace('.', '').replace('-', '').strip()
        
        # Correspondência exata
        if ncm == pattern_clean:
            return True
        
        # Correspondência por prefixo
        if ncm.startswith(pattern_clean):
            return True
        
        # Padrões com wildcards (implementação futura)
        if '*' in pattern_clean or 'x' in pattern_clean.lower():
            # Implementar lógica de wildcards
            return self._match_wildcard_pattern(ncm, pattern_clean)
        
        return False
    
    def _match_wildcard_pattern(self, ncm: str, pattern: str) -> bool:
        """Corresponde padrões com wildcards"""
        # Converter pattern para regex simples
        pattern = pattern.lower().replace('x', '.').replace('*', '.*')
        import re
        return bool(re.match(f"^{pattern}", ncm))
    
    def _calculate_pattern_score(self, ncm: str, pattern: str) -> float:
        """Calcula score de compatibilidade entre NCM e padrão"""
        pattern_clean = pattern.replace('.', '').replace('-', '').strip()
        
        if ncm == pattern_clean:
            return 1.0
        
        if ncm.startswith(pattern_clean):
            # Score baseado na especificidade do padrão
            return len(pattern_clean) / 8.0  # NCM tem 8 dígitos
        
        return 0.0

class LLMManager:
    """Gerenciador de múltiplos provedores LLM"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers = {}
        self.cost_tracker = {}
        self.response_cache = {}
        
        self.initialize_providers()
    
    def initialize_providers(self):
        """Inicializa todos os provedores configurados"""
        try:
            # OpenAI
            if self.config.get('openai', {}).get('enabled', False):
                self.providers['openai'] = OpenAIProvider(self.config['openai'])
            
            # Anthropic
            if self.config.get('anthropic', {}).get('enabled', False):
                self.providers['anthropic'] = AnthropicProvider(self.config['anthropic'])
            
            # Ollama (Local)
            if self.config.get('ollama', {}).get('enabled', False):
                self.providers['ollama'] = OllamaProvider(self.config['ollama'])
            
            # Hugging Face
            if self.config.get('huggingface', {}).get('enabled', False):
                self.providers['huggingface'] = HuggingFaceProvider(self.config['huggingface'])
            
            logger.info(f"Inicializados {len(self.providers)} provedores LLM")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar provedores: {e}")
    
    async def generate_response(self, prompt: str, provider: str = "auto", **kwargs) -> Dict[str, Any]:
        """Gera resposta usando provedor especificado ou automático"""
        if provider == "auto":
            provider = self._select_optimal_provider(prompt, **kwargs)
        
        if provider not in self.providers:
            raise ValueError(f"Provedor {provider} não disponível")
        
        # Verificar cache
        cache_key = self._generate_cache_key(prompt, provider, kwargs)
        if cache_key in self.response_cache:
            logger.debug(f"Cache hit para {provider}")
            return self.response_cache[cache_key]
        
        start_time = time.time()
        
        try:
            result = await self.providers[provider].generate(prompt, **kwargs)
            
            # Adicionar metadados
            result.update({
                'provider': provider,
                'processing_time': time.time() - start_time,
                'cache_hit': False
            })
            
            # Atualizar cache
            self.response_cache[cache_key] = result
            
            # Rastreamento de custos
            self._track_usage(provider, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Erro no provedor {provider}: {e}")
            raise
    
    def _select_optimal_provider(self, prompt: str, **kwargs) -> str:
        """Seleciona o provedor ótimo baseado em custo/performance"""
        # Lógica de seleção inteligente
        prompt_length = len(prompt)
        complexity = kwargs.get('complexity', 'medium')
        
        # Para prompts simples, usar modelo local se disponível
        if prompt_length < 500 and complexity == 'low' and 'ollama' in self.providers:
            return 'ollama'
        
        # Para alta complexidade, usar modelos premium
        if complexity == 'high' and 'openai' in self.providers:
            return 'openai'
        
        # Default para primeiro disponível
        return list(self.providers.keys())[0] if self.providers else 'openai'
    
    def _generate_cache_key(self, prompt: str, provider: str, kwargs: Dict) -> str:
        """Gera chave de cache para resposta"""
        content = f"{provider}:{prompt}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _track_usage(self, provider: str, result: Dict):
        """Rastreia uso e custos por provedor"""
        if provider not in self.cost_tracker:
            self.cost_tracker[provider] = {
                'requests': 0,
                'tokens': 0,
                'cost': 0.0
            }
        
        self.cost_tracker[provider]['requests'] += 1
        self.cost_tracker[provider]['tokens'] += result.get('tokens_used', 0)
        self.cost_tracker[provider]['cost'] += result.get('cost', 0.0)

class BaseProvider:
    """Classe base para provedores LLM"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Método abstrato para geração"""
        raise NotImplementedError
    
    def estimate_cost(self, prompt: str, **kwargs) -> float:
        """Estima custo da requisição"""
        return 0.0

class OpenAIProvider(BaseProvider):
    """Provedor OpenAI"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        try:
            import openai
            self.client = openai.AsyncOpenAI(
                api_key=config.get('api_key') or os.getenv('OPENAI_API_KEY')
            )
            logger.info("Cliente OpenAI inicializado")
        except ImportError:
            logger.error("Biblioteca openai não instalada: pip install openai")
            raise
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Gera resposta usando OpenAI"""
        model = kwargs.get('model', self.config.get('model', 'gpt-3.5-turbo'))
        max_tokens = kwargs.get('max_tokens', self.config.get('max_tokens', 1000))
        temperature = kwargs.get('temperature', self.config.get('temperature', 0.1))
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Você é um especialista em classificação fiscal NCM/CEST."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            result = {
                'content': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens,
                'cost': self._calculate_cost(response.usage, model),
                'model': model
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Erro OpenAI: {e}")
            raise
    
    def _calculate_cost(self, usage, model: str) -> float:
        """Calcula custo baseado no uso de tokens"""
        # Preços aproximados (atualizar conforme API)
        pricing = {
            'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002},
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-4-turbo': {'input': 0.01, 'output': 0.03}
        }
        
        if model in pricing:
            input_cost = (usage.prompt_tokens / 1000) * pricing[model]['input']
            output_cost = (usage.completion_tokens / 1000) * pricing[model]['output']
            return input_cost + output_cost
        
        return 0.0

class OllamaProvider(BaseProvider):
    """Provedor Ollama (Local)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'http://localhost:11434')
        
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Gera resposta usando Ollama"""
        import aiohttp
        
        model = kwargs.get('model', self.config.get('model', 'llama3.1:8b'))
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get('temperature', 0.1),
                "top_p": kwargs.get('top_p', 0.9),
                "max_tokens": kwargs.get('max_tokens', 1000)
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'content': data.get('response', ''),
                            'tokens_used': len(prompt.split()) + len(data.get('response', '').split()),
                            'cost': 0.0,  # Local, sem custo
                            'model': model
                        }
                    else:
                        raise Exception(f"Ollama error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Erro Ollama: {e}")
            raise

class AnthropicProvider(BaseProvider):
    """Provedor Anthropic Claude"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(
                api_key=config.get('api_key') or os.getenv('ANTHROPIC_API_KEY')
            )
            logger.info("Cliente Anthropic inicializado")
        except ImportError:
            logger.error("Biblioteca anthropic não instalada: pip install anthropic")
            raise
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Gera resposta usando Claude"""
        model = kwargs.get('model', self.config.get('model', 'claude-3-sonnet-20240229'))
        max_tokens = kwargs.get('max_tokens', self.config.get('max_tokens', 1000))
        
        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return {
                'content': response.content[0].text,
                'tokens_used': response.usage.input_tokens + response.usage.output_tokens,
                'cost': self._calculate_cost(response.usage, model),
                'model': model
            }
            
        except Exception as e:
            logger.error(f"Erro Anthropic: {e}")
            raise
    
    def _calculate_cost(self, usage, model: str) -> float:
        """Calcula custo Anthropic"""
        pricing = {
            'claude-3-sonnet-20240229': {'input': 0.003, 'output': 0.015},
            'claude-3-opus-20240229': {'input': 0.015, 'output': 0.075}
        }
        
        if model in pricing:
            input_cost = (usage.input_tokens / 1000) * pricing[model]['input']
            output_cost = (usage.output_tokens / 1000) * pricing[model]['output']
            return input_cost + output_cost
        
        return 0.0

class HuggingFaceProvider(BaseProvider):
    """Provedor Hugging Face"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = None
        self.tokenizer = None
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            model_name = config.get('model', 'microsoft/DialoGPT-medium')
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            
            # Configurar pad_token se não existir
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            logger.info(f"Modelo HF {model_name} carregado")
            
        except ImportError:
            logger.error("Bibliotecas transformers/torch não instaladas")
            raise
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Gera resposta usando modelo local HF"""
        max_length = kwargs.get('max_tokens', 512)
        temperature = kwargs.get('temperature', 0.7)
        
        try:
            # Tokenizar entrada
            inputs = self.tokenizer.encode(prompt, return_tensors='pt')
            
            # Gerar resposta
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=max_length,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decodificar resposta
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = response[len(prompt):].strip()
            
            return {
                'content': response,
                'tokens_used': len(outputs[0]),
                'cost': 0.0,  # Local, sem custo
                'model': 'huggingface-local'
            }
            
        except Exception as e:
            logger.error(f"Erro HuggingFace: {e}")
            raise

class AdvancedNCMCESTClassifier:
    """Classificador avançado NCM/CEST com IA real"""
    
    def __init__(self, config_path: str = "configs/ai_config.yaml"):
        self.config = self.load_config(config_path)
        self.knowledge_base = EnhancedNCMCESTKnowledgeBase()
        self.llm_manager = LLMManager(self.config.get('llm', {}))
        
        # Cache de resultados
        self.result_cache = {}
        self.performance_metrics = {}
        
        # Auditoria
        self.audit_db_path = "data/cache/audit_trail.sqlite"
        self.init_audit_database()
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Carrega configurações do sistema"""
        default_config = {
            'llm': {
                'openai': {
                    'enabled': True,
                    'model': 'gpt-3.5-turbo',
                    'temperature': 0.1,
                    'max_tokens': 1000
                },
                'ollama': {
                    'enabled': True,
                    'base_url': 'http://localhost:11434',
                    'model': 'llama3.1:8b',
                    'temperature': 0.1
                },
                'anthropic': {
                    'enabled': False,
                    'model': 'claude-3-sonnet-20240229'
                },
                'huggingface': {
                    'enabled': False,
                    'model': 'microsoft/DialoGPT-medium'
                }
            },
            'classification': {
                'default_strategy': 'hybrid',
                'confidence_threshold': 0.8,
                'ensemble_models': ['openai', 'ollama'],
                'fallback_strategy': 'rag'
            },
            'caching': {
                'enabled': True,
                'ttl_hours': 24,
                'max_size': 10000
            }
        }
        
        try:
            if os.path.exists(config_path):
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                
                # Merge configs
                default_config.update(user_config)
                
        except Exception as e:
            logger.warning(f"Erro ao carregar config {config_path}: {e}. Usando padrão.")
        
        return default_config
    
    def init_audit_database(self):
        """Inicializa banco de dados de auditoria"""
        os.makedirs(os.path.dirname(self.audit_db_path), exist_ok=True)
        
        with sqlite3.connect(self.audit_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS classification_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id TEXT,
                    timestamp DATETIME,
                    strategy TEXT,
                    models_used TEXT,
                    ncm_result TEXT,
                    cest_result TEXT,
                    confidence_score REAL,
                    processing_time REAL,
                    cost REAL,
                    user_id TEXT,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_produto_timestamp 
                ON classification_audit(produto_id, timestamp)
            """)
    
    async def classify_product(self, request: ClassificationRequest) -> ClassificationResult:
        """Classifica produto usando IA avançada"""
        start_time = time.time()
        
        try:
            # Verificar cache
            cache_key = self._generate_request_hash(request)
            if cache_key in self.result_cache:
                cached_result = self.result_cache[cache_key]
                cached_result.cache_hit = True
                return cached_result
            
            # Selecionar estratégia
            strategy = self._select_classification_strategy(request)
            
            # Executar classificação
            if strategy == ClassificationStrategy.ENSEMBLE:
                result = await self._classify_ensemble(request)
            elif strategy == ClassificationStrategy.RAG:
                result = await self._classify_rag(request)
            elif strategy == ClassificationStrategy.HIERARCHICAL:
                result = await self._classify_hierarchical(request)
            elif strategy == ClassificationStrategy.HYBRID:
                result = await self._classify_hybrid(request)
            else:
                result = await self._classify_direct(request)
            
            # Finalizar resultado
            result.tempo_processamento = time.time() - start_time
            result.estrategia_usada = strategy.value
            
            # Validação adicional
            result = await self._validate_and_enhance_result(result, request)
            
            # Cache
            self.result_cache[cache_key] = result
            
            # Auditoria
            await self._log_classification(request, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na classificação: {e}")
            return self._create_error_result(request, str(e))
    
    def _select_classification_strategy(self, request: ClassificationRequest) -> ClassificationStrategy:
        """Seleciona estratégia ótima baseada no contexto"""
        # Análise da complexidade do produto
        desc_complexity = len(request.descricao_produto.split())
        has_context = bool(request.contexto_adicional)
        has_current_classification = bool(request.ncm_atual or request.cest_atual)
        
        # Lógica de seleção adaptativa
        if desc_complexity > 20 and has_context:
            return ClassificationStrategy.HYBRID
        elif has_current_classification:
            return ClassificationStrategy.RAG
        elif desc_complexity < 10:
            return ClassificationStrategy.DIRECT
        else:
            return ClassificationStrategy.ENSEMBLE
    
    async def _classify_direct(self, request: ClassificationRequest) -> ClassificationResult:
        """Classificação direta usando LLM"""
        prompt = self._build_direct_prompt(request)
        
        response = await self.llm_manager.generate_response(
            prompt, 
            provider="auto",
            complexity="low"
        )
        
        return self._parse_llm_response(request, response, "direct")
    
    async def _classify_rag(self, request: ClassificationRequest) -> ClassificationResult:
        """Classificação RAG com base de conhecimento"""
        # Buscar contexto relevante
        ncm_candidates = self.knowledge_base.search_ncm_semantic(
            request.descricao_produto, top_k=5
        )
        
        # Construir prompt com contexto
        prompt = self._build_rag_prompt(request, ncm_candidates)
        
        response = await self.llm_manager.generate_response(
            prompt,
            provider="auto",
            complexity="medium"
        )
        
        result = self._parse_llm_response(request, response, "rag")
        
        # Buscar CEST baseado no NCM encontrado
        if result.ncm_sugerido:
            cest_candidates = self.knowledge_base.search_cest_by_ncm(
                result.ncm_sugerido, request.estado
            )
            
            if cest_candidates:
                best_cest = cest_candidates[0]
                result.cest_sugerido = best_cest['codigo']
                result.cest_descricao = best_cest['descricao']
                result.cest_confianca = best_cest['score']
        
        return result
    
    async def _classify_ensemble(self, request: ClassificationRequest) -> ClassificationResult:
        """Classificação usando ensemble de modelos"""
        models = self.config['classification']['ensemble_models']
        results = []
        
        prompt = self._build_ensemble_prompt(request)
        
        # Executar em paralelo
        tasks = []
        for model in models:
            if model in self.llm_manager.providers:
                task = self.llm_manager.generate_response(
                    prompt, provider=model, complexity="medium"
                )
                tasks.append((model, task))
        
        # Coletar resultados
        for model, task in tasks:
            try:
                response = await task
                parsed = self._parse_llm_response(request, response, f"ensemble-{model}")
                results.append(parsed)
            except Exception as e:
                logger.warning(f"Erro no modelo {model}: {e}")
        
        # Consolidar resultados
        return self._consolidate_ensemble_results(request, results)
    
    async def _classify_hierarchical(self, request: ClassificationRequest) -> ClassificationResult:
        """Classificação hierárquica (capítulo → posição → subposição → item)"""
        # Etapa 1: Identificar capítulo
        capitulo_prompt = self._build_hierarchical_prompt(request, "capitulo")
        capitulo_response = await self.llm_manager.generate_response(
            capitulo_prompt, complexity="low"
        )
        
        # Etapa 2: Refinar para posição
        posicao_prompt = self._build_hierarchical_prompt(request, "posicao", capitulo_response)
        posicao_response = await self.llm_manager.generate_response(
            posicao_prompt, complexity="medium"
        )
        
        # Etapa 3: Item específico
        item_prompt = self._build_hierarchical_prompt(request, "item", posicao_response)
        item_response = await self.llm_manager.generate_response(
            item_prompt, complexity="high"
        )
        
        return self._parse_llm_response(request, item_response, "hierarchical")
    
    async def _classify_hybrid(self, request: ClassificationRequest) -> ClassificationResult:
        """Estratégia híbrida adaptativa"""
        # Combinar RAG + Ensemble
        rag_result = await self._classify_rag(request)
        
        # Se confiança baixa, usar ensemble
        if rag_result.ncm_confianca < 0.8:
            ensemble_result = await self._classify_ensemble(request)
            
            # Combinar melhores aspectos
            if ensemble_result.ncm_confianca > rag_result.ncm_confianca:
                result = ensemble_result
                result.alternative_suggestions.append({
                    'ncm': rag_result.ncm_sugerido,
                    'source': 'rag',
                    'confidence': rag_result.ncm_confianca
                })
            else:
                result = rag_result
                result.alternative_suggestions.append({
                    'ncm': ensemble_result.ncm_sugerido,
                    'source': 'ensemble',
                    'confidence': ensemble_result.ncm_confianca
                })
        else:
            result = rag_result
        
        result.estrategia_usada = "hybrid"
        return result
    
    def _build_direct_prompt(self, request: ClassificationRequest) -> str:
        """Constrói prompt para classificação direta"""
        return f"""
Classifique o seguinte produto na tabela NCM (8 dígitos) e CEST quando aplicável:

Produto: {request.descricao_produto}
Categoria: {request.categoria or 'Não informada'}
Marca: {request.marca or 'Não informada'}
Modelo: {request.modelo or 'Não informado'}
Estado: {request.estado}

Responda no formato JSON:
{{
    "ncm": "00000000",
    "ncm_descricao": "Descrição do NCM",
    "ncm_confianca": 0.95,
    "cest": "0000000",
    "cest_descricao": "Descrição do CEST",
    "cest_confianca": 0.90,
    "justificativa": "Explicação da classificação"
}}
"""
    
    def _build_rag_prompt(self, request: ClassificationRequest, ncm_candidates: List[Dict]) -> str:
        """Constrói prompt RAG com contexto"""
        context = "\n".join([
            f"NCM {item['codigo']}: {item['descricao']} (Score: {item['score']:.2f})"
            for item in ncm_candidates[:3]
        ])
        
        return f"""
Baseado nos seguintes NCMs similares da base de conhecimento:

{context}

Classifique o produto:
Descrição: {request.descricao_produto}
Categoria: {request.categoria or 'Não informada'}
Estado: {request.estado}

Considere as similaridades e escolha o NCM mais apropriado.
Justifique sua escolha baseando-se nos exemplos fornecidos.

Responda no formato JSON:
{{
    "ncm": "00000000",
    "ncm_descricao": "Descrição do NCM",
    "ncm_confianca": 0.95,
    "justificativa": "Explicação baseada nos exemplos"
}}
"""
    
    def _build_ensemble_prompt(self, request: ClassificationRequest) -> str:
        """Constrói prompt para ensemble"""
        return f"""
Como especialista em classificação fiscal, analise cuidadosamente o produto:

Descrição: {request.descricao_produto}
Categoria: {request.categoria or 'Não informada'}
Marca: {request.marca or 'Não informada'}
Contexto: {request.contexto_adicional or 'Não informado'}

Forneça sua melhor classificação NCM considerando:
1. Composição e materiais
2. Função e uso do produto
3. Regras NESH aplicáveis
4. Notas do capítulo/posição

Seja preciso e justifique sua escolha.

Formato da resposta:
NCM: 00000000
Descrição: [descrição do código]
Confiança: 0.XX
Justificativa: [explicação detalhada]
"""
    
    def _build_hierarchical_prompt(self, request: ClassificationRequest, level: str, previous_response: Dict = None) -> str:
        """Constrói prompt para classificação hierárquica"""
        if level == "capitulo":
            return f"""
Identifique o CAPÍTULO NCM (2 dígitos) mais apropriado para:
Produto: {request.descricao_produto}

Considere os principais capítulos da NCM e suas características.
Responda apenas o número do capítulo e uma breve justificativa.
"""
        elif level == "posicao":
            return f"""
Dentro do capítulo identificado, determine a POSIÇÃO NCM (4 dígitos) para:
Produto: {request.descricao_produto}
Capítulo anterior: {previous_response.get('content', '') if previous_response else ''}

Responda a posição de 4 dígitos mais específica.
"""
        else:  # item
            return f"""
Determine o código NCM completo (8 dígitos) final para:
Produto: {request.descricao_produto}
Análise anterior: {previous_response.get('content', '') if previous_response else ''}

Forneça o código NCM de 8 dígitos mais preciso e sua justificativa.
"""
    
    def _parse_llm_response(self, request: ClassificationRequest, response: Dict, strategy: str) -> ClassificationResult:
        """Parseia resposta do LLM para resultado estruturado"""
        content = response.get('content', '')
        
        # Tentar extrair JSON
        try:
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                return ClassificationResult(
                    produto_id=request.produto_id,
                    ncm_sugerido=data.get('ncm', ''),
                    ncm_descricao=data.get('ncm_descricao', ''),
                    ncm_confianca=float(data.get('ncm_confianca', 0.0)),
                    cest_sugerido=data.get('cest'),
                    cest_descricao=data.get('cest_descricao'),
                    cest_confianca=float(data.get('cest_confianca', 0.0)) if data.get('cest_confianca') else None,
                    justificativa=data.get('justificativa', ''),
                    modelos_usados=[response.get('provider', 'unknown')],
                    custo_estimado=response.get('cost', 0.0),
                    estrategia_usada=strategy,
                    audit_trail={'llm_response': content}
                )
        except Exception as e:
            logger.warning(f"Erro ao parsear JSON: {e}")
        
        # Fallback: extração por regex
        return self._extract_by_regex(request, content, response, strategy)
    
    def _extract_by_regex(self, request: ClassificationRequest, content: str, response: Dict, strategy: str) -> ClassificationResult:
        """Extração por regex quando JSON falha"""
        import re
        
        # Procurar padrões NCM
        ncm_pattern = r'NCM:?\s*(\d{8}|\d{4}\.\d{2}\.\d{2})'
        ncm_match = re.search(ncm_pattern, content)
        ncm = ncm_match.group(1).replace('.', '') if ncm_match else '00000000'
        
        # Procurar confiança
        conf_pattern = r'[Cc]onfiança:?\s*(\d+\.?\d*)'
        conf_match = re.search(conf_pattern, content)
        confidence = float(conf_match.group(1)) if conf_match else 0.5
        
        return ClassificationResult(
            produto_id=request.produto_id,
            ncm_sugerido=ncm,
            ncm_descricao="Extraído por regex",
            ncm_confianca=confidence,
            justificativa=content[:500],  # Primeiros 500 chars
            modelos_usados=[response.get('provider', 'unknown')],
            custo_estimado=response.get('cost', 0.0),
            estrategia_usada=strategy,
            audit_trail={'llm_response': content, 'extraction': 'regex'}
        )
    
    def _consolidate_ensemble_results(self, request: ClassificationRequest, results: List[ClassificationResult]) -> ClassificationResult:
        """Consolida resultados do ensemble"""
        if not results:
            return self._create_error_result(request, "Nenhum resultado do ensemble")
        
        # Agrupar por NCM sugerido
        ncm_votes = {}
        for result in results:
            ncm = result.ncm_sugerido
            if ncm not in ncm_votes:
                ncm_votes[ncm] = []
            ncm_votes[ncm].append(result)
        
        # Selecionar NCM com maior consenso
        best_ncm = max(ncm_votes.keys(), key=lambda x: len(ncm_votes[x]))
        best_results = ncm_votes[best_ncm]
        
        # Calcular métricas consolidadas
        avg_confidence = sum(r.ncm_confianca for r in best_results) / len(best_results)
        all_models = []
        for r in results:
            all_models.extend(r.modelos_usados)
        
        # Resultado consolidado
        base_result = best_results[0]
        base_result.ncm_confianca = avg_confidence
        base_result.modelos_usados = list(set(all_models))
        base_result.estrategia_usada = "ensemble"
        
        # Adicionar alternativas
        for ncm, votes in ncm_votes.items():
            if ncm != best_ncm:
                avg_conf = sum(r.ncm_confianca for r in votes) / len(votes)
                base_result.alternative_suggestions.append({
                    'ncm': ncm,
                    'confidence': avg_conf,
                    'votes': len(votes),
                    'source': 'ensemble'
                })
        
        return base_result
    
    async def _validate_and_enhance_result(self, result: ClassificationResult, request: ClassificationRequest) -> ClassificationResult:
        """Valida e aprimora resultado"""
        # Verificar se NCM existe na base
        if result.ncm_sugerido in self.knowledge_base.ncm_data:
            ncm_info = self.knowledge_base.ncm_data[result.ncm_sugerido]
            result.ncm_descricao = ncm_info['descricao']
        else:
            result.validation_flags.append("NCM não encontrado na base")
        
        # Verificar confiança mínima
        min_confidence = self.config['classification']['confidence_threshold']
        if result.ncm_confianca < min_confidence:
            result.requires_human_review = True
            result.validation_flags.append(f"Confiança abaixo do limiar ({min_confidence})")
        
        # Verificar compatibilidade NCM/CEST
        if result.cest_sugerido and result.ncm_sugerido:
            cest_matches = self.knowledge_base.search_cest_by_ncm(result.ncm_sugerido, request.estado)
            if not any(c['codigo'] == result.cest_sugerido for c in cest_matches):
                result.validation_flags.append("Incompatibilidade NCM/CEST detectada")
        
        return result
    
    def _create_error_result(self, request: ClassificationRequest, error: str) -> ClassificationResult:
        """Cria resultado de erro"""
        return ClassificationResult(
            produto_id=request.produto_id,
            ncm_sugerido="00000000",
            ncm_descricao="Erro na classificação",
            ncm_confianca=0.0,
            justificativa=f"Erro: {error}",
            validation_flags=["error"],
            requires_human_review=True
        )
    
    def _generate_request_hash(self, request: ClassificationRequest) -> str:
        """Gera hash para cache do request"""
        content = f"{request.descricao_produto}:{request.categoria}:{request.marca}:{request.estado}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def _log_classification(self, request: ClassificationRequest, result: ClassificationResult):
        """Registra classificação na auditoria"""
        try:
            with sqlite3.connect(self.audit_db_path) as conn:
                conn.execute("""
                    INSERT INTO classification_audit 
                    (produto_id, timestamp, strategy, models_used, ncm_result, cest_result, 
                     confidence_score, processing_time, cost, user_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    request.produto_id,
                    request.timestamp,
                    result.estrategia_usada,
                    ','.join(result.modelos_usados),
                    result.ncm_sugerido,
                    result.cest_sugerido,
                    result.ncm_confianca,
                    result.tempo_processamento,
                    result.custo_estimado,
                    request.user_id,
                    json.dumps(result.metadata)
                ))
        except Exception as e:
            logger.error(f"Erro ao registrar auditoria: {e}")

# Exemplo de uso
async def main():
    """Exemplo de uso do sistema"""
    
    # Configurar classificador
    classifier = AdvancedNCMCESTClassifier()
    
    # Criar request de exemplo
    request = ClassificationRequest(
        produto_id="PROD001",
        descricao_produto="Smartphone Samsung Galaxy A54 5G 128GB Preto",
        categoria="Eletrônicos",
        marca="Samsung",
        modelo="Galaxy A54",
        estado="RO",
        user_id="user123"
    )
    
    # Classificar
    result = await classifier.classify_product(request)
    
    # Exibir resultado
    print(f"NCM: {result.ncm_sugerido}")
    print(f"Descrição: {result.ncm_descricao}")
    print(f"Confiança: {result.ncm_confianca:.2f}")
    print(f"CEST: {result.cest_sugerido}")
    print(f"Estratégia: {result.estrategia_usada}")
    print(f"Modelos: {', '.join(result.modelos_usados)}")
    print(f"Tempo: {result.tempo_processamento:.2f}s")
    print(f"Custo: ${result.custo_estimado:.4f}")
    print(f"Justificativa: {result.justificativa}")
    
    if result.validation_flags:
        print(f"Alertas: {', '.join(result.validation_flags)}")

if __name__ == "__main__":
    asyncio.run(main())
