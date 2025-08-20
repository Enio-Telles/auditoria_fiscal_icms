"""
Endpoints de Classificação
Orquestra a execução dos agentes de classificação usando LangGraph
"""

import uuid
import asyncio
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from ...database.connection import get_db_session
from ...database.models import Usuario, ProdutoEmpresa as MercadoriaAClassificar, Classificacao
from ...agents.manager_agent import ManagerAgent
from ...workflows.fiscal_audit_workflow import FiscalAuditWorkflow
from ..schemas import (
    BatchClassificationRequest, BatchClassificationResponse,
    ClassificationJobStatus, MessageResponse
)
from .auth import get_current_user
from ..middleware.error_handler import APIError, BusinessLogicError

logger = logging.getLogger(__name__)
router = APIRouter()

# Cache de jobs de classificação (em produção, usar Redis)
classification_jobs_cache: Dict[str, Dict[str, Any]] = {}

async def execute_batch_classification(
    job_id: str,
    empresa_id: int,
    product_ids: Optional[List[int]] = None,
    limit: Optional[int] = None,
    force_reclassify: bool = False
):
    """
    Executa classificação em lote usando workflow LangGraph
    """
    try:
        logger.info(f"🎯 Iniciando classificação {job_id} para empresa {empresa_id}")
        
        # Atualizar status do job
        classification_jobs_cache[job_id]["status"] = "running"
        classification_jobs_cache[job_id]["message"] = "Preparando produtos para classificação..."
        
        # Conectar ao banco
        from ...database.connection import db_manager
        
        with db_manager.session_scope() as db:
            # Construir query para produtos a classificar
            query = db.query(MercadoriaAClassificar).filter(
                MercadoriaAClassificar.empresa_id == empresa_id
            )
            
            # Filtrar por IDs específicos se fornecido
            if product_ids:
                query = query.filter(MercadoriaAClassificar.id.in_(product_ids))
            elif not force_reclassify:
                # Se não força reclassificação, pegar apenas pendentes
                query = query.filter(MercadoriaAClassificar.status == "PENDENTE")
            
            # Aplicar limite
            if limit:
                query = query.limit(limit)
            
            # Obter produtos
            produtos = query.all()
            
            if not produtos:
                classification_jobs_cache[job_id]["status"] = "completed"
                classification_jobs_cache[job_id]["message"] = "Nenhum produto encontrado para classificação"
                classification_jobs_cache[job_id]["total"] = 0
                return
            
            total_produtos = len(produtos)
            classification_jobs_cache[job_id]["total"] = total_produtos
            classification_jobs_cache[job_id]["message"] = f"Classificando {total_produtos} produtos..."
            
            logger.info(f"🏷️ Classificando {total_produtos} produtos")
            
            # Inicializar workflow e agentes
            workflow = FiscalAuditWorkflow()
            manager_agent = ManagerAgent()
            
            # Contadores de progresso
            processed = 0
            successful = 0
            failed = 0
            
            # Processar produtos em lotes menores
            batch_size = 10  # Processar 10 produtos por vez
            
            for i in range(0, total_produtos, batch_size):
                batch = produtos[i:i + batch_size]
                
                for produto in batch:
                    try:
                        # Atualizar produto atual
                        classification_jobs_cache[job_id]["current_item"] = produto.descricao_original[:50] + "..."
                        classification_jobs_cache[job_id]["message"] = f"Processando: {produto.descricao_original[:30]}..."
                        
                        # Marcar como processando
                        produto.status = "PROCESSANDO"
                        db.commit()
                        
                        # Preparar dados para o workflow
                        product_data = {
                            "mercadoria_id": produto.id,
                            "produto_id": produto.produto_id_origem,
                            "descricao_original": produto.descricao_original,
                            "codigo_barra": produto.codigo_barra,
                            "codigo_produto": produto.codigo_produto,
                            "ncm_informado": produto.ncm_informado,
                            "cest_informado": produto.cest_informado,
                            "empresa_id": empresa_id
                        }
                        
                        # Determinar tipo de workflow baseado no NCM/CEST informado
                        if produto.ncm_informado and produto.cest_informado:
                            workflow_type = "confirmation"
                        else:
                            workflow_type = "determination"
                        
                        logger.info(f"🔄 Executando workflow {workflow_type} para produto {produto.id}")
                        
                        # Executar workflow via ManagerAgent
                        result = await manager_agent.process_product(
                            product_data=product_data,
                            workflow_type=workflow_type,
                            empresa_atividades=[]  # Buscar atividades da empresa se necessário
                        )
                        
                        # Processar resultado
                        if result["success"]:
                            # Salvar classificação
                            classificacao = Classificacao(
                                mercadoria_id=produto.id,
                                ncm_determinado=result.get("ncm_determinado"),
                                cest_determinado=result.get("cest_determinado"),
                                confianca_ncm=result.get("confianca_ncm"),
                                confianca_cest=result.get("confianca_cest"),
                                justificativa_ncm=result.get("justificativa_ncm"),
                                contexto_ncm=result.get("contexto_ncm"),
                                justificativa_cest=result.get("justificativa_cest"),
                                contexto_cest=result.get("contexto_cest"),
                                trilha_auditoria=result.get("trilha_auditoria", {}),
                                processado_em=datetime.utcnow()
                            )
                            
                            db.add(classificacao)
                            
                            # Determinar status final
                            confianca_ncm = result.get("confianca_ncm", 0)
                            confianca_cest = result.get("confianca_cest", 0)
                            
                            if confianca_ncm < 0.7 or (confianca_cest and confianca_cest < 0.7):
                                produto.status = "REVISAO_MANUAL"
                            else:
                                produto.status = "CONCLUIDA"
                            
                            successful += 1
                            
                        else:
                            # Classificação falhou
                            produto.status = "ERRO"
                            
                            # Salvar erro no contexto
                            classificacao = Classificacao(
                                mercadoria_id=produto.id,
                                trilha_auditoria={
                                    "error": result.get("error", "Erro desconhecido"),
                                    "timestamp": datetime.utcnow().isoformat()
                                },
                                processado_em=datetime.utcnow()
                            )
                            
                            db.add(classificacao)
                            failed += 1
                        
                        # Commit das alterações
                        db.commit()
                        processed += 1
                        
                        # Atualizar progresso
                        progress = (processed / total_produtos) * 100
                        classification_jobs_cache[job_id]["processed"] = processed
                        classification_jobs_cache[job_id]["successful"] = successful
                        classification_jobs_cache[job_id]["failed"] = failed
                        classification_jobs_cache[job_id]["progress_percentage"] = progress
                        
                        # Calcular tempo restante estimado
                        if processed > 0:
                            avg_time_per_item = 5  # Estimativa de 5 segundos por item
                            remaining_items = total_produtos - processed
                            estimated_remaining = remaining_items * avg_time_per_item
                            classification_jobs_cache[job_id]["estimated_remaining"] = estimated_remaining
                        
                        logger.info(f"✅ Produto {produto.id} processado: {produto.status}")
                        
                    except Exception as item_error:
                        logger.error(f"❌ Erro ao processar produto {produto.id}: {item_error}")
                        
                        # Marcar produto com erro
                        produto.status = "ERRO"
                        db.commit()
                        
                        processed += 1
                        failed += 1
                        
                        # Atualizar contadores
                        classification_jobs_cache[job_id]["processed"] = processed
                        classification_jobs_cache[job_id]["failed"] = failed
                
                # Pequena pausa entre lotes
                await asyncio.sleep(1)
        
        # Finalizar job
        classification_jobs_cache[job_id]["status"] = "completed"
        classification_jobs_cache[job_id]["progress_percentage"] = 100.0
        classification_jobs_cache[job_id]["current_item"] = None
        classification_jobs_cache[job_id]["message"] = f"Classificação concluída! {successful} sucessos, {failed} falhas."
        
        logger.info(f"🎉 Classificação {job_id} concluída: {successful}/{total_produtos} sucessos")
        
    except Exception as e:
        # Tratar erro geral
        error_message = f"Erro na classificação: {str(e)}"
        logger.error(f"❌ {error_message}")
        
        classification_jobs_cache[job_id]["status"] = "error"
        classification_jobs_cache[job_id]["message"] = error_message
        classification_jobs_cache[job_id]["error"] = str(e)

@router.post("/batch", response_model=BatchClassificationResponse, summary="Classificação em lote")
async def start_batch_classification(
    classification_request: BatchClassificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Inicia classificação de produtos em lote usando sistema multiagente
    
    Executa workflow LangGraph para classificar NCM/CEST de produtos
    """
    logger.info(f"🎯 Solicitação de classificação em lote para empresa {classification_request.empresa_id}")
    
    # Verificar acesso à empresa
    from ...database.models import UsuarioEmpresaAcesso
    access = db.query(UsuarioEmpresaAcesso).filter(
        UsuarioEmpresaAcesso.usuario_id == current_user.id,
        UsuarioEmpresaAcesso.empresa_id == classification_request.empresa_id
    ).first()
    
    if not access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado à empresa"
        )
    
    # Contar produtos disponíveis para classificação
    query = db.query(MercadoriaAClassificar).filter(
        MercadoriaAClassificar.empresa_id == classification_request.empresa_id
    )
    
    # Aplicar filtros
    if classification_request.produto_ids:
        query = query.filter(MercadoriaAClassificar.id.in_(classification_request.produto_ids))
    elif not classification_request.force_reclassify:
        query = query.filter(MercadoriaAClassificar.status == "PENDENTE")
    
    if classification_request.limit:
        query = query.limit(classification_request.limit)
    
    total_products = query.count()
    
    if total_products == 0:
        raise BusinessLogicError(
            "Nenhum produto encontrado para classificação com os filtros especificados"
        )
    
    # Gerar ID único para o job
    job_id = str(uuid.uuid4())
    
    # Inicializar cache do job
    classification_jobs_cache[job_id] = {
        "job_id": job_id,
        "empresa_id": classification_request.empresa_id,
        "status": "initiated",
        "total": total_products,
        "processed": 0,
        "successful": 0,
        "failed": 0,
        "progress_percentage": 0.0,
        "estimated_remaining": None,
        "current_item": None,
        "message": "Classificação iniciada...",
        "started_at": datetime.utcnow().isoformat(),
        "user_email": current_user.email
    }
    
    # Adicionar task em background
    background_tasks.add_task(
        execute_batch_classification,
        job_id=job_id,
        empresa_id=classification_request.empresa_id,
        product_ids=classification_request.produto_ids,
        limit=classification_request.limit,
        force_reclassify=classification_request.force_reclassify
    )
    
    logger.info(f"🚀 Job de classificação {job_id} iniciado para {total_products} produtos")
    
    return BatchClassificationResponse(
        job_id=job_id,
        empresa_id=classification_request.empresa_id,
        total_products=total_products,
        status="initiated",
        estimated_time=total_products * 5  # 5 segundos por produto
    )

@router.get("/status/{job_id}", response_model=ClassificationJobStatus, summary="Status da classificação")
async def get_classification_status(
    job_id: str,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna o status detalhado de um job de classificação
    """
    logger.info(f"📊 Consultando status da classificação {job_id}")
    
    if job_id not in classification_jobs_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job de classificação não encontrado"
        )
    
    job_info = classification_jobs_cache[job_id]
    
    # Verificar acesso à empresa do job
    from ...database.models import UsuarioEmpresaAcesso
    from ...database.connection import db_manager
    
    with db_manager.session_scope() as db:
        access = db.query(UsuarioEmpresaAcesso).filter(
            UsuarioEmpresaAcesso.usuario_id == current_user.id,
            UsuarioEmpresaAcesso.empresa_id == job_info["empresa_id"]
        ).first()
        
        if not access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado ao job de classificação"
            )
    
    return ClassificationJobStatus(
        job_id=job_info["job_id"],
        status=job_info["status"],
        total=job_info["total"],
        processed=job_info["processed"],
        successful=job_info["successful"],
        failed=job_info["failed"],
        progress_percentage=job_info["progress_percentage"],
        estimated_remaining=job_info.get("estimated_remaining"),
        current_item=job_info.get("current_item")
    )

@router.delete("/{job_id}", response_model=MessageResponse, summary="Cancelar classificação")
async def cancel_classification(
    job_id: str,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Cancela um job de classificação em andamento
    """
    logger.info(f"🚫 Cancelando classificação {job_id}")
    
    if job_id not in classification_jobs_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job de classificação não encontrado"
        )
    
    job_info = classification_jobs_cache[job_id]
    
    # Verificar acesso
    from ...database.models import UsuarioEmpresaAcesso
    from ...database.connection import db_manager
    
    with db_manager.session_scope() as db:
        access = db.query(UsuarioEmpresaAcesso).filter(
            UsuarioEmpresaAcesso.usuario_id == current_user.id,
            UsuarioEmpresaAcesso.empresa_id == job_info["empresa_id"]
        ).first()
        
        if not access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado para cancelar classificação"
            )
    
    # Cancelar se possível
    if job_info["status"] in ["initiated", "running"]:
        classification_jobs_cache[job_id]["status"] = "cancelled"
        classification_jobs_cache[job_id]["message"] = "Classificação cancelada pelo usuário"
        
        return MessageResponse(
            message="Classificação cancelada com sucesso",
            success=True,
            data={"job_id": job_id}
        )
    else:
        raise BusinessLogicError(
            f"Job não pode ser cancelado. Status atual: {job_info['status']}"
        )
