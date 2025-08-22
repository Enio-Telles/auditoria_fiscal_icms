#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API FastAPI com Sistema de IA Local Integrado
============================================

API completa com classificação de produtos usando LLMs locais via Ollama
"""

import json
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Importar nossos módulos
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from auditoria_icms.ai.local_llm_classifier import LocalLLMClassifier, ClassificationResult, OllamaConfig

# Modelos Pydantic para API
class ProductClassificationRequest(BaseModel):
    produto_id: str
    descricao: str
    modelo: Optional[str] = "llama3.1"

class BatchClassificationRequest(BaseModel):
    produtos: List[Dict[str, str]]
    modelo: Optional[str] = "llama3.1"
    salvar_resultados: bool = True

class AIConfigUpdate(BaseModel):
    modelo_principal: Optional[str] = None
    modelo_backup: Optional[str] = None
    timeout: Optional[int] = None

class AIStatusResponse(BaseModel):
    ollama_disponivel: bool
    modelos_instalados: List[str]
    modelo_ativo: str
    tempo_resposta: float
    configuracao: Dict[str, Any]

# Configuração da aplicação
app = FastAPI(
    title="Sistema de Auditoria Fiscal ICMS - IA Local",
    description="API com classificação automática NCM/CEST usando LLMs locais via Ollama",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instância global do classificador
classifier = None

def get_classifier() -> LocalLLMClassifier:
    """Dependency para obter instância do classificador"""
    global classifier
    if classifier is None:
        classifier = LocalLLMClassifier()
    return classifier

@app.on_event("startup")
async def startup_event():
    """Inicialização da aplicação"""
    global classifier
    classifier = LocalLLMClassifier()
    print("🤖 Sistema de IA Local inicializado!")
    print(f"✅ Ollama disponível: {classifier.check_ollama_connection()}")
    print(f"📋 Modelos: {classifier.get_available_models()}")

# ==========================================
# ENDPOINTS DE SISTEMA E STATUS
# ==========================================

@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "sistema": "Auditoria Fiscal ICMS v3.0",
        "ia": "Sistema Local com Ollama",
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Verificação de saúde do sistema"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0",
        "ai_system": "local_ollama"
    }

@app.get("/ai/status", response_model=AIStatusResponse)
async def ai_status(classifier: LocalLLMClassifier = Depends(get_classifier)):
    """Status detalhado do sistema de IA"""
    start_time = time.time()
    
    ollama_disponivel = classifier.check_ollama_connection()
    modelos_instalados = classifier.get_available_models() if ollama_disponivel else []
    
    tempo_resposta = time.time() - start_time
    
    return AIStatusResponse(
        ollama_disponivel=ollama_disponivel,
        modelos_instalados=modelos_instalados,
        modelo_ativo=classifier.config.modelo_principal,
        tempo_resposta=tempo_resposta,
        configuracao={
            "base_url": classifier.config.base_url,
            "timeout": classifier.config.timeout,
            "max_retries": classifier.config.max_retries,
            "modelo_principal": classifier.config.modelo_principal,
            "modelo_backup": classifier.config.modelo_backup
        }
    )

@app.get("/ai/models")
async def list_models(classifier: LocalLLMClassifier = Depends(get_classifier)):
    """Lista modelos disponíveis no Ollama"""
    if not classifier.check_ollama_connection():
        raise HTTPException(status_code=503, detail="Ollama não disponível")
    
    models = classifier.get_available_models()
    return {
        "models": models,
        "total": len(models),
        "recommended": ["llama3.1:8b", "llama2:7b", "mistral:7b"]
    }

@app.post("/ai/config")
async def update_config(
    config: AIConfigUpdate,
    classifier: LocalLLMClassifier = Depends(get_classifier)
):
    """Atualiza configuração da IA"""
    updates = {}
    
    if config.modelo_principal:
        classifier.config.modelo_principal = config.modelo_principal
        updates["modelo_principal"] = config.modelo_principal
    
    if config.modelo_backup:
        classifier.config.modelo_backup = config.modelo_backup
        updates["modelo_backup"] = config.modelo_backup
    
    if config.timeout:
        classifier.config.timeout = config.timeout
        updates["timeout"] = config.timeout
    
    return {
        "message": "Configuração atualizada",
        "updates": updates,
        "config_atual": {
            "modelo_principal": classifier.config.modelo_principal,
            "modelo_backup": classifier.config.modelo_backup,
            "timeout": classifier.config.timeout
        }
    }

# ==========================================
# ENDPOINTS DE CLASSIFICAÇÃO
# ==========================================

@app.post("/ai/classify")
async def classify_product(
    request: ProductClassificationRequest,
    classifier: LocalLLMClassifier = Depends(get_classifier)
):
    """Classifica um produto usando IA local"""
    if not classifier.check_ollama_connection():
        raise HTTPException(status_code=503, detail="Sistema de IA não disponível")
    
    try:
        # Atualizar modelo se especificado
        if request.modelo:
            classifier.config.modelo_principal = request.modelo
        
        # Classificar produto
        result = classifier.classify_product(request.produto_id, request.descricao)
        
        # Converter para dict para resposta JSON
        return {
            "success": True,
            "produto_id": result.produto_id,
            "descricao": result.descricao,
            "classificacao": {
                "ncm": {
                    "codigo": result.ncm_sugerido,
                    "confianca": result.ncm_confianca
                },
                "cest": {
                    "codigo": result.cest_sugerido,
                    "confianca": result.cest_confianca
                }
            },
            "analise": {
                "justificativa": result.justificativa,
                "categorias": result.categorias_identificadas,
                "palavras_chave": result.palavras_chave
            },
            "metadados": {
                "modelo_usado": result.modelo_usado,
                "tempo_processamento": result.tempo_processamento,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na classificação: {str(e)}")

@app.get("/ai/classify-simple")
async def classify_simple(
    descricao: str = Query(..., description="Descrição do produto"),
    modelo: str = Query("llama3.1", description="Modelo a usar"),
    classifier: LocalLLMClassifier = Depends(get_classifier)
):
    """Classificação simplificada via GET"""
    if not classifier.check_ollama_connection():
        raise HTTPException(status_code=503, detail="Sistema de IA não disponível")
    
    try:
        # Atualizar modelo
        classifier.config.modelo_principal = modelo
        
        # Classificar
        result = classifier.classify_product("simple", descricao)
        
        return {
            "descricao": descricao,
            "ncm": result.ncm_sugerido,
            "ncm_confianca": result.ncm_confianca,
            "cest": result.cest_sugerido,
            "cest_confianca": result.cest_confianca,
            "justificativa": result.justificativa,
            "modelo": result.modelo_usado,
            "tempo": f"{result.tempo_processamento:.2f}s"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@app.post("/ai/classify-batch")
async def classify_batch(
    request: BatchClassificationRequest,
    background_tasks: BackgroundTasks,
    classifier: LocalLLMClassifier = Depends(get_classifier)
):
    """Classificação em lote com processamento em background"""
    if not classifier.check_ollama_connection():
        raise HTTPException(status_code=503, detail="Sistema de IA não disponível")
    
    if len(request.produtos) > 100:
        raise HTTPException(status_code=400, detail="Máximo 100 produtos por lote")
    
    try:
        # Processar em background para lotes grandes
        if len(request.produtos) > 10:
            # Criar ID do job
            job_id = f"batch_{int(time.time())}"
            
            # Adicionar tarefa em background
            background_tasks.add_task(
                process_batch_background,
                job_id,
                request.produtos,
                request.modelo,
                request.salvar_resultados,
                classifier
            )
            
            return {
                "job_id": job_id,
                "status": "processing",
                "total_produtos": len(request.produtos),
                "message": "Processamento iniciado em background"
            }
        
        else:
            # Processar diretamente para lotes pequenos
            if request.modelo:
                classifier.config.modelo_principal = request.modelo
            
            results = classifier.batch_classify(request.produtos)
            
            # Salvar se solicitado
            if request.salvar_resultados:
                filename = classifier.export_results(results)
            else:
                filename = None
            
            return {
                "success": True,
                "total_processados": len(results),
                "resultados": [
                    {
                        "produto_id": r.produto_id,
                        "descricao": r.descricao,
                        "ncm": r.ncm_sugerido,
                        "ncm_confianca": r.ncm_confianca,
                        "cest": r.cest_sugerido,
                        "cest_confianca": r.cest_confianca,
                        "justificativa": r.justificativa,
                        "tempo": r.tempo_processamento
                    }
                    for r in results
                ],
                "arquivo_exportado": filename,
                "tempo_total": sum(r.tempo_processamento for r in results)
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no lote: {str(e)}")

async def process_batch_background(
    job_id: str,
    produtos: List[Dict[str, str]], 
    modelo: str,
    salvar: bool,
    classifier: LocalLLMClassifier
):
    """Processa lote em background"""
    try:
        if modelo:
            classifier.config.modelo_principal = modelo
        
        results = classifier.batch_classify(produtos)
        
        if salvar:
            filename = classifier.export_results(results, f"data/processed/batch_{job_id}.json")
        
        # Salvar status do job
        job_status = {
            "job_id": job_id,
            "status": "completed",
            "total_processados": len(results),
            "tempo_total": sum(r.tempo_processamento for r in results),
            "arquivo": filename if salvar else None,
            "completed_at": datetime.now().isoformat()
        }
        
        job_file = Path(f"data/processed/job_{job_id}.json")
        job_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(job_file, 'w') as f:
            json.dump(job_status, f, indent=2)
            
    except Exception as e:
        # Salvar erro do job
        job_status = {
            "job_id": job_id,
            "status": "error",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        }
        
        job_file = Path(f"data/processed/job_{job_id}.json")
        job_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(job_file, 'w') as f:
            json.dump(job_status, f, indent=2)

@app.get("/ai/job/{job_id}")
async def get_job_status(job_id: str):
    """Verifica status de um job de classificação em lote"""
    job_file = Path(f"data/processed/job_{job_id}.json")
    
    if not job_file.exists():
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    with open(job_file, 'r') as f:
        job_status = json.load(f)
    
    return job_status

# ==========================================
# ENDPOINTS DE DADOS E ANÁLISE
# ==========================================

@app.get("/ai/analytics")
async def get_analytics():
    """Estatísticas de uso do sistema de IA"""
    try:
        # Buscar arquivos de resultados
        results_dir = Path("data/processed")
        
        if not results_dir.exists():
            return {
                "total_classificacoes": 0,
                "arquivos_processados": 0,
                "periodo": None
            }
        
        # Contar arquivos de classificação
        classification_files = list(results_dir.glob("classificacao_ia_local_*.json"))
        batch_files = list(results_dir.glob("batch_*.json"))
        
        total_classificacoes = 0
        tempo_total = 0
        modelos_usados = {}
        
        # Analisar arquivos
        for file in classification_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    
                resultados = data.get("resultados", [])
                total_classificacoes += len(resultados)
                
                for resultado in resultados:
                    tempo_total += resultado.get("tempo_processamento", 0)
                    modelo = resultado.get("modelo_usado", "unknown")
                    modelos_usados[modelo] = modelos_usados.get(modelo, 0) + 1
                    
            except:
                continue
        
        return {
            "total_classificacoes": total_classificacoes,
            "arquivos_processados": len(classification_files),
            "tempo_total_processamento": tempo_total,
            "tempo_medio_por_produto": tempo_total / max(total_classificacoes, 1),
            "modelos_utilizados": modelos_usados,
            "jobs_em_batch": len(batch_files)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro nas analytics: {str(e)}")

# ==========================================
# ENDPOINT DE DEMONSTRAÇÃO
# ==========================================

@app.get("/ai/demo")
async def demo_classification(classifier: LocalLLMClassifier = Depends(get_classifier)):
    """Demonstração rápida do sistema de IA"""
    if not classifier.check_ollama_connection():
        return {
            "status": "error",
            "message": "Ollama não disponível",
            "instrucoes": [
                "1. Instale Ollama: https://ollama.ai",
                "2. Execute: ollama serve",
                "3. Execute: ollama pull llama3.1:8b"
            ]
        }
    
    produtos_demo = [
        "Notebook Dell Inspiron 15 Intel Core i5",
        "Smartphone Samsung Galaxy A54 5G",
        "Televisão LED 55 polegadas LG",
        "Mouse óptico USB Logitech",
        "Teclado mecânico Razer"
    ]
    
    resultados = []
    tempo_total = 0
    
    for i, produto in enumerate(produtos_demo):
        start_time = time.time()
        result = classifier.classify_product(f"demo_{i+1}", produto)
        tempo_produto = time.time() - start_time
        tempo_total += tempo_produto
        
        resultados.append({
            "produto": produto,
            "ncm": result.ncm_sugerido,
            "confianca": result.ncm_confianca,
            "justificativa": result.justificativa[:100] + "...",
            "tempo": f"{tempo_produto:.2f}s"
        })
    
    return {
        "status": "success",
        "demo_executada": True,
        "produtos_testados": len(produtos_demo),
        "tempo_total": f"{tempo_total:.2f}s",
        "tempo_medio": f"{tempo_total/len(produtos_demo):.2f}s",
        "modelo_usado": classifier.config.modelo_principal,
        "resultados": resultados
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Iniciando API com Sistema de IA Local...")
    print("📋 Endpoints principais:")
    print("   GET  /ai/status - Status do sistema de IA")
    print("   GET  /ai/demo - Demonstração rápida")
    print("   POST /ai/classify - Classificar produto")
    print("   GET  /ai/classify-simple - Classificação simples")
    print("   POST /ai/classify-batch - Classificação em lote")
    print("   GET  /docs - Documentação completa")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8005,
        log_level="info"
    )
