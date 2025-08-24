#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Endpoints de IA para Classificação Automática NCM/CEST
=====================================================

Integração do sistema de IA com a API FastAPI existente.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

# Imports do sistema de IA
try:
    from src.auditoria_icms.ai_classification import (
        AIClassificationEngine,
        ClassificationRequest,
        ClassificationResult,
        LLMProvider,
        classify_product,
    )

    AI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Sistema de IA não disponível: {e}")
    AI_AVAILABLE = False

# Router para endpoints de IA
ai_router = APIRouter(prefix="/api/ai", tags=["IA Classification"])


# Modelos Pydantic para API
class ProdutoClassificacao(BaseModel):
    """Modelo para requisição de classificação"""

    produto_id: str = Field(..., description="ID único do produto")
    descricao_produto: str = Field(..., description="Descrição completa do produto")
    categoria: Optional[str] = Field(None, description="Categoria do produto")
    subcategoria: Optional[str] = Field(None, description="Subcategoria do produto")
    marca: Optional[str] = Field(None, description="Marca do produto")
    modelo: Optional[str] = Field(None, description="Modelo do produto")
    preco: Optional[float] = Field(None, description="Preço do produto")
    unidade_medida: Optional[str] = Field(None, description="Unidade de medida")
    contexto_adicional: Optional[str] = Field(
        None, description="Informações adicionais"
    )


class ResultadoClassificacao(BaseModel):
    """Modelo para resultado de classificação"""

    produto_id: str
    ncm_sugerido: str
    ncm_descricao: str
    ncm_confianca: float
    cest_sugerido: Optional[str] = None
    cest_descricao: Optional[str] = None
    cest_confianca: Optional[float] = None
    justificativa: str
    modelo_usado: str
    tempo_processamento: float
    metadata: Optional[Dict[str, Any]] = None


class ClassificacaoLote(BaseModel):
    """Modelo para classificação em lote"""

    produtos: List[ProdutoClassificacao]
    provider: Optional[str] = Field(
        "ensemble", description="Provedor de IA: openai, ollama, huggingface, ensemble"
    )
    usar_cache: bool = Field(True, description="Usar cache de resultados")


class StatusIA(BaseModel):
    """Status do sistema de IA"""

    disponivel: bool
    provedores_ativos: List[str]
    base_conhecimento: Dict[str, int]
    versao: str = "2.1"


# Cache simples em memória
classification_cache = {}

# Instância global do engine
ai_engine = None


async def get_ai_engine():
    """Dependency para obter engine de IA"""
    global ai_engine
    if not AI_AVAILABLE:
        raise HTTPException(status_code=503, detail="Sistema de IA não disponível")

    if ai_engine is None:
        ai_engine = AIClassificationEngine()

    return ai_engine


def convert_to_classification_request(
    produto: ProdutoClassificacao,
) -> ClassificationRequest:
    """Converte modelo Pydantic para ClassificationRequest"""
    return ClassificationRequest(
        produto_id=produto.produto_id,
        descricao_produto=produto.descricao_produto,
        categoria=produto.categoria,
        subcategoria=produto.subcategoria,
        marca=produto.marca,
        modelo=produto.modelo,
        preco=produto.preco,
        unidade_medida=produto.unidade_medida,
        contexto_adicional=produto.contexto_adicional,
    )


def convert_from_classification_result(
    result: ClassificationResult,
) -> ResultadoClassificacao:
    """Converte ClassificationResult para modelo Pydantic"""
    return ResultadoClassificacao(
        produto_id=result.produto_id,
        ncm_sugerido=result.ncm_sugerido,
        ncm_descricao=result.ncm_descricao,
        ncm_confianca=result.ncm_confianca,
        cest_sugerido=result.cest_sugerido,
        cest_descricao=result.cest_descricao,
        cest_confianca=result.cest_confianca,
        justificativa=result.justificativa,
        modelo_usado=result.modelo_usado,
        tempo_processamento=result.tempo_processamento,
        metadata=result.metadata,
    )


@ai_router.get("/status", response_model=StatusIA)
async def get_ai_status():
    """Retorna status do sistema de IA"""
    if not AI_AVAILABLE:
        return StatusIA(disponivel=False, provedores_ativos=[], base_conhecimento={})

    try:
        engine = await get_ai_engine()

        # Verificar provedores disponíveis
        provedores_ativos = []

        # Verificar OpenAI
        try:
            import os

            if os.getenv("OPENAI_API_KEY"):
                provedores_ativos.append("openai")
        except Exception:
            pass

        # Verificar Ollama
        try:
            import requests

            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                provedores_ativos.append("ollama")
        except Exception:
            pass

        # Verificar Hugging Face
        try:
            provedores_ativos.append("huggingface")
        except Exception:
            pass

        # Base de conhecimento
        base_info = {}
        if hasattr(engine, "knowledge_base"):
            kb = engine.knowledge_base
            if kb.ncm_data:
                base_info["ncm_codes"] = len(kb.ncm_data)
            if hasattr(kb, "cest_data") and kb.cest_data is not None:
                base_info["cest_codes"] = len(kb.cest_data)

        return StatusIA(
            disponivel=True,
            provedores_ativos=provedores_ativos,
            base_conhecimento=base_info,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao verificar status da IA: {str(e)}"
        )


@ai_router.post("/classify", response_model=ResultadoClassificacao)
async def classify_single_product(
    produto: ProdutoClassificacao,
    provider: Optional[str] = "ensemble",
    engine: AIClassificationEngine = Depends(get_ai_engine),
):
    """Classifica um único produto usando IA"""

    # Verificar cache
    cache_key = f"{produto.descricao_produto}_{provider}"
    if cache_key in classification_cache:
        logging.info(
            f"Resultado encontrado no cache para: {produto.descricao_produto[:50]}"
        )
        return classification_cache[cache_key]

    try:
        # Converter para formato interno
        request = convert_to_classification_request(produto)

        # Classificar
        if provider == "ensemble":
            result = await engine.classify_ensemble(request)
        else:
            provider_enum = LLMProvider(provider.lower())
            result = await engine.classify_single(request, provider_enum)

        # Converter resposta
        response = convert_from_classification_result(result)

        # Armazenar no cache
        classification_cache[cache_key] = response

        logging.info(
            f"Produto classificado: {produto.descricao_produto[:50]} -> NCM {result.ncm_sugerido}"
        )
        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Provedor inválido: {str(e)}")
    except Exception as e:
        logging.error(f"Erro na classificação: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na classificação: {str(e)}")


@ai_router.post("/classify-batch", response_model=List[ResultadoClassificacao])
async def classify_products_batch_endpoint(
    request: ClassificacaoLote,
    background_tasks: BackgroundTasks,
    engine: AIClassificationEngine = Depends(get_ai_engine),
):
    """Classifica múltiplos produtos em lote"""

    if len(request.produtos) > 100:
        raise HTTPException(status_code=400, detail="Máximo de 100 produtos por lote")

    try:
        # Converter produtos
        classification_requests = [
            convert_to_classification_request(produto) for produto in request.produtos
        ]

        # Verificar cache se solicitado
        cached_results = {}
        pending_requests = []

        if request.usar_cache:
            for i, req in enumerate(classification_requests):
                cache_key = f"{req.descricao_produto}_{request.provider}"
                if cache_key in classification_cache:
                    cached_results[i] = classification_cache[cache_key]
                else:
                    pending_requests.append((i, req))
        else:
            pending_requests = list(enumerate(classification_requests))

        logging.info(
            "Lote de %s produtos: %s no cache, %s para processar",
            len(request.produtos),
            len(cached_results),
            len(pending_requests),
        )

        # Processar produtos pendentes
        new_results = {}
        if pending_requests:
            pending_reqs = [req for _, req in pending_requests]

            if request.provider == "ensemble":
                results = await engine.classify_batch(
                    pending_reqs, LLMProvider.ENSEMBLE
                )
            else:
                provider_enum = LLMProvider(request.provider.lower())
                results = await engine.classify_batch(pending_reqs, provider_enum)

            # Mapear resultados
            for (original_index, _), result in zip(pending_requests, results):
                converted_result = convert_from_classification_result(result)
                new_results[original_index] = converted_result

                # Adicionar ao cache
                if request.usar_cache:
                    cache_key = f"{result.ncm_sugerido}_{request.provider}"
                    classification_cache[cache_key] = converted_result

        # Combinar resultados na ordem original
        final_results = []
        for i in range(len(request.produtos)):
            if i in cached_results:
                final_results.append(cached_results[i])
            elif i in new_results:
                final_results.append(new_results[i])
            else:
                # Fallback em caso de erro
                final_results.append(
                    ResultadoClassificacao(
                        produto_id=request.produtos[i].produto_id,
                        ncm_sugerido="0000.00.00",
                        ncm_descricao="Erro no processamento",
                        ncm_confianca=0.0,
                        justificativa="Produto não foi processado",
                        modelo_usado="error",
                        tempo_processamento=0.0,
                    )
                )

        logging.info(f"Lote processado: {len(final_results)} resultados retornados")
        return final_results

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Provedor inválido: {str(e)}")
    except Exception as e:
        logging.error(f"Erro na classificação em lote: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro na classificação em lote: {str(e)}"
        )


@ai_router.get("/classify-simple")
async def classify_simple(descricao: str, provider: str = "ensemble"):
    """Endpoint simples para classificação rápida"""

    if not AI_AVAILABLE:
        return {
            "error": "Sistema de IA não disponível",
            "ncm": "0000.00.00",
            "confianca": 0.0,
        }

    try:
        result = await classify_product(descricao, provider)
        return {
            "descricao": descricao,
            "ncm": result["ncm"],
            "descricao_ncm": result["descricao"],
            "confianca": result["confianca"],
            "justificativa": result["justificativa"],
            "modelo": result["modelo"],
            "tempo": result["tempo"],
        }
    except Exception as e:
        return {"error": str(e), "ncm": "0000.00.00", "confianca": 0.0}


@ai_router.get("/search-ncm")
async def search_ncm_knowledge(
    query: str, limit: int = 10, engine: AIClassificationEngine = Depends(get_ai_engine)
):
    """Busca na base de conhecimento NCM"""

    try:
        results = engine.knowledge_base.search_similar_ncm(query, top_k=limit)

        return {
            "query": query,
            "total_found": len(results),
            "results": [
                {
                    "codigo": result["codigo"],
                    "descricao": result["descricao"],
                    "relevancia": result["score"],
                }
                for result in results
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")


@ai_router.delete("/cache")
async def clear_classification_cache():
    """Limpa o cache de classificações"""
    global classification_cache
    cache_size = len(classification_cache)
    classification_cache.clear()

    return {
        "message": f"Cache limpo. {cache_size} entradas removidas.",
        "timestamp": datetime.now().isoformat(),
    }


@ai_router.get("/cache/stats")
async def get_cache_stats():
    """Retorna estatísticas do cache"""
    return {
        "total_entries": len(classification_cache),
        "cache_keys": list(classification_cache.keys())[:10],  # Primeiras 10 chaves
        "memory_usage": f"{len(str(classification_cache))} caracteres",
    }


# Endpoints de demonstração e teste
@ai_router.get("/demo")
async def ai_demo():
    """Demonstração do sistema de IA"""

    produtos_demo = [
        "Smartphone Samsung Galaxy S23",
        "Café torrado e moído 500g",
        "Notebook Dell Inspiron 15",
        "Parafuso sextavado M8 aço inox",
    ]

    results = []

    for produto in produtos_demo:
        try:
            result = await classify_product(
                produto, "huggingface"
            )  # Usar HF por ser mais rápido
            results.append(
                {
                    "produto": produto,
                    "ncm": result["ncm"],
                    "confianca": result["confianca"],
                    "modelo": result["modelo"],
                }
            )
        except Exception as e:
            results.append({"produto": produto, "erro": str(e), "ncm": "0000.00.00"})

    return {
        "demo_classification": results,
        "sistema": "IA para Classificação NCM/CEST v2.1",
        "status": "Funcional" if AI_AVAILABLE else "Indisponível",
    }


# Middleware de logging será adicionado na aplicação principal
# @ai_router.middleware("http")
# async def log_ai_requests(request, call_next):
#     start_time = datetime.now()
#     response = await call_next(request)
#     process_time = (datetime.now() - start_time).total_seconds()
#
#     logging.info(f"AI Request: {request.method} {request.url.path} - {process_time:.2f}s")
#     return response
