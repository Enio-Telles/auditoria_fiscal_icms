"""
Endpoints de Resultados e Visualização
Permite consultar e revisar classificações realizadas
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc
import logging

from ...database.connection import get_db_session
from ...database.models import (
    Usuario, ProdutoEmpresa as MercadoriaAClassificar, Classificacao, 
    UsuarioEmpresaAcesso, Empresa
)
from ..schemas import (
    ProductClassificationResult, ClassificationDetailResponse,
    ResultsListRequest, ResultsListResponse, MessageResponse
)
from .auth import get_current_user
from ..middleware.error_handler import APIError, BusinessLogicError

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=ResultsListResponse, summary="Listar resultados de classificação")
async def list_classification_results(
    empresa_id: int = Query(..., description="ID da empresa"),
    page: int = Query(default=1, ge=1, description="Página (iniciando em 1)"),
    page_size: int = Query(default=50, ge=1, le=500, description="Itens por página"),
    status_filter: Optional[str] = Query(None, description="Filtrar por status"),
    ncm_filter: Optional[str] = Query(None, description="Filtrar por NCM"),
    search_term: Optional[str] = Query(None, description="Buscar na descrição"),
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista resultados de classificação com filtros e paginação
    """
    logger.info(f"📋 Listando resultados da empresa {empresa_id} - Usuário: {current_user.email}")
    
    # Verificar acesso à empresa
    access = db.query(UsuarioEmpresaAcesso).filter(
        UsuarioEmpresaAcesso.usuario_id == current_user.id,
        UsuarioEmpresaAcesso.empresa_id == empresa_id
    ).first()
    
    if not access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado à empresa"
        )
    
    # Query base com join
    query = db.query(MercadoriaAClassificar).outerjoin(
        Classificacao,
        MercadoriaAClassificar.id == Classificacao.mercadoria_id
    ).filter(
        MercadoriaAClassificar.empresa_id == empresa_id
    ).options(
        joinedload(MercadoriaAClassificar.classificacao)
    )
    
    # Aplicar filtros
    if status_filter:
        query = query.filter(MercadoriaAClassificar.status == status_filter)
    
    if ncm_filter:
        query = query.filter(
            or_(
                MercadoriaAClassificar.ncm_informado.ilike(f"%{ncm_filter}%"),
                Classificacao.ncm_determinado.ilike(f"%{ncm_filter}%")
            )
        )
    
    if search_term:
        search_pattern = f"%{search_term}%"
        query = query.filter(
            or_(
                MercadoriaAClassificar.descricao_original.ilike(search_pattern),
                MercadoriaAClassificar.descricao_enriquecida.ilike(search_pattern)
            )
        )
    
    # Ordenar por mais recentes
    query = query.order_by(desc(MercadoriaAClassificar.id))
    
    # Contar total
    total = query.count()
    
    # Aplicar paginação
    offset = (page - 1) * page_size
    mercadorias = query.offset(offset).limit(page_size).all()
    
    # Converter para schema de resposta
    items = []
    for mercadoria in mercadorias:
        classificacao = mercadoria.classificacao[0] if mercadoria.classificacao else None
        
        item = ProductClassificationResult(
            mercadoria_id=mercadoria.id,
            produto_id=mercadoria.produto_id_origem,
            descricao_original=mercadoria.descricao_original,
            descricao_enriquecida=mercadoria.descricao_enriquecida,
            ncm_informado=mercadoria.ncm_informado,
            cest_informado=mercadoria.cest_informado,
            ncm_determinado=classificacao.ncm_determinado if classificacao else None,
            cest_determinado=classificacao.cest_determinado if classificacao else None,
            confianca_ncm=classificacao.confianca_ncm if classificacao else None,
            confianca_cest=classificacao.confianca_cest if classificacao else None,
            status=mercadoria.status,
            justificativa_ncm=classificacao.justificativa_ncm if classificacao else None,
            contexto_ncm=classificacao.contexto_ncm if classificacao else None,
            justificativa_cest=classificacao.justificativa_cest if classificacao else None,
            contexto_cest=classificacao.contexto_cest if classificacao else None,
            processado_em=classificacao.processado_em if classificacao else None
        )
        items.append(item)
    
    # Calcular total de páginas
    total_pages = (total + page_size - 1) // page_size
    
    logger.info(f"✅ Retornando {len(items)} resultados de {total} total")
    
    return ResultsListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/details/{mercadoria_id}", response_model=ClassificationDetailResponse, summary="Detalhes da classificação")
async def get_classification_details(
    mercadoria_id: int,
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna detalhes completos de uma classificação incluindo trilha de auditoria
    """
    logger.info(f"🔍 Buscando detalhes da classificação {mercadoria_id}")
    
    # Buscar mercadoria com classificação
    mercadoria = db.query(MercadoriaAClassificar).options(
        joinedload(MercadoriaAClassificar.classificacao)
    ).filter(MercadoriaAClassificar.id == mercadoria_id).first()
    
    if not mercadoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mercadoria não encontrada"
        )
    
    # Verificar acesso à empresa
    access = db.query(UsuarioEmpresaAcesso).filter(
        UsuarioEmpresaAcesso.usuario_id == current_user.id,
        UsuarioEmpresaAcesso.empresa_id == mercadoria.empresa_id
    ).first()
    
    if not access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado à empresa"
        )
    
    # Obter classificação
    classificacao = mercadoria.classificacao[0] if mercadoria.classificacao else None
    
    # Montar resultado principal
    classification_result = ProductClassificationResult(
        mercadoria_id=mercadoria.id,
        produto_id=mercadoria.produto_id_origem,
        descricao_original=mercadoria.descricao_original,
        descricao_enriquecida=mercadoria.descricao_enriquecida,
        ncm_informado=mercadoria.ncm_informado,
        cest_informado=mercadoria.cest_informado,
        ncm_determinado=classificacao.ncm_determinado if classificacao else None,
        cest_determinado=classificacao.cest_determinado if classificacao else None,
        confianca_ncm=classificacao.confianca_ncm if classificacao else None,
        confianca_cest=classificacao.confianca_cest if classificacao else None,
        status=mercadoria.status,
        justificativa_ncm=classificacao.justificativa_ncm if classificacao else None,
        contexto_ncm=classificacao.contexto_ncm if classificacao else None,
        justificativa_cest=classificacao.justificativa_cest if classificacao else None,
        contexto_cest=classificacao.contexto_cest if classificacao else None,
        processado_em=classificacao.processado_em if classificacao else None
    )
    
    # Extrair trilha de auditoria
    audit_trail = []
    rag_contexts = []
    
    if classificacao and classificacao.trilha_auditoria:
        trilha = classificacao.trilha_auditoria
        
        # Processar trilha de agentes
        if "agents" in trilha:
            for agent_name, agent_data in trilha["agents"].items():
                audit_trail.append({
                    "agent": agent_name,
                    "action": agent_data.get("action", "unknown"),
                    "decision": agent_data.get("decision"),
                    "confidence": agent_data.get("confidence"),
                    "reasoning": agent_data.get("reasoning"),
                    "timestamp": agent_data.get("timestamp"),
                    "duration": agent_data.get("duration_ms")
                })
        
        # Processar contextos RAG
        if "rag_contexts" in trilha:
            for context in trilha["rag_contexts"]:
                rag_contexts.append({
                    "query": context.get("query"),
                    "source": context.get("source"),
                    "content": context.get("content"),
                    "score": context.get("score"),
                    "metadata": context.get("metadata", {})
                })
    
    # Buscar produtos similares (mesmo id_agregados)
    similar_products = []
    if mercadoria.id_agregados:
        similar_mercadorias = db.query(MercadoriaAClassificar).options(
            joinedload(MercadoriaAClassificar.classificacao)
        ).filter(
            and_(
                MercadoriaAClassificar.id_agregados == mercadoria.id_agregados,
                MercadoriaAClassificar.id != mercadoria.id,
                MercadoriaAClassificar.empresa_id == mercadoria.empresa_id
            )
        ).limit(10).all()
        
        for similar in similar_mercadorias:
            similar_classificacao = similar.classificacao[0] if similar.classificacao else None
            
            similar_result = ProductClassificationResult(
                mercadoria_id=similar.id,
                produto_id=similar.produto_id_origem,
                descricao_original=similar.descricao_original,
                descricao_enriquecida=similar.descricao_enriquecida,
                ncm_informado=similar.ncm_informado,
                cest_informado=similar.cest_informado,
                ncm_determinado=similar_classificacao.ncm_determinado if similar_classificacao else None,
                cest_determinado=similar_classificacao.cest_determinado if similar_classificacao else None,
                confianca_ncm=similar_classificacao.confianca_ncm if similar_classificacao else None,
                confianca_cest=similar_classificacao.confianca_cest if similar_classificacao else None,
                status=similar.status,
                justificativa_ncm=similar_classificacao.justificativa_ncm if similar_classificacao else None,
                contexto_ncm=similar_classificacao.contexto_ncm if similar_classificacao else None,
                justificativa_cest=similar_classificacao.justificativa_cest if similar_classificacao else None,
                contexto_cest=similar_classificacao.contexto_cest if similar_classificacao else None,
                processado_em=similar_classificacao.processado_em if similar_classificacao else None
            )
            similar_products.append(similar_result)
    
    return ClassificationDetailResponse(
        classification=classification_result,
        audit_trail=audit_trail,
        rag_contexts=rag_contexts,
        similar_products=similar_products if similar_products else None
    )

@router.put("/{mercadoria_id}/status", response_model=MessageResponse, summary="Atualizar status da classificação")
async def update_classification_status(
    mercadoria_id: int,
    new_status: str = Query(..., regex="^(PENDENTE|PROCESSANDO|CONCLUIDA|REVISAO_MANUAL|ERRO)$"),
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Atualiza o status de uma classificação
    """
    logger.info(f"📝 Atualizando status da mercadoria {mercadoria_id} para {new_status}")
    
    # Buscar mercadoria
    mercadoria = db.query(MercadoriaAClassificar).filter(
        MercadoriaAClassificar.id == mercadoria_id
    ).first()
    
    if not mercadoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mercadoria não encontrada"
        )
    
    # Verificar acesso
    access = db.query(UsuarioEmpresaAcesso).filter(
        UsuarioEmpresaAcesso.usuario_id == current_user.id,
        UsuarioEmpresaAcesso.empresa_id == mercadoria.empresa_id,
        UsuarioEmpresaAcesso.nivel_acesso.in_(["admin", "editor"])
    ).first()
    
    if not access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão insuficiente para atualizar status"
        )
    
    # Atualizar status
    old_status = mercadoria.status
    mercadoria.status = new_status
    
    try:
        db.commit()
        logger.info(f"✅ Status atualizado: {old_status} → {new_status}")
        
        return MessageResponse(
            message=f"Status atualizado de {old_status} para {new_status}",
            success=True,
            data={
                "mercadoria_id": mercadoria_id,
                "old_status": old_status,
                "new_status": new_status
            }
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao atualizar status: {e}")
        raise APIError("Erro ao atualizar status", 500, {"error": str(e)})

@router.get("/stats/{empresa_id}", summary="Estatísticas de classificação")
async def get_classification_stats(
    empresa_id: int,
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna estatísticas de classificação para uma empresa
    """
    logger.info(f"📊 Gerando estatísticas para empresa {empresa_id}")
    
    # Verificar acesso
    access = db.query(UsuarioEmpresaAcesso).filter(
        UsuarioEmpresaAcesso.usuario_id == current_user.id,
        UsuarioEmpresaAcesso.empresa_id == empresa_id
    ).first()
    
    if not access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado à empresa"
        )
    
    # Estatísticas básicas
    total_produtos = db.query(MercadoriaAClassificar).filter(
        MercadoriaAClassificar.empresa_id == empresa_id
    ).count()
    
    # Por status
    stats_by_status = {}
    status_list = ["PENDENTE", "PROCESSANDO", "CONCLUIDA", "REVISAO_MANUAL", "ERRO"]
    
    for status in status_list:
        count = db.query(MercadoriaAClassificar).filter(
            MercadoriaAClassificar.empresa_id == empresa_id,
            MercadoriaAClassificar.status == status
        ).count()
        stats_by_status[status] = count
    
    # Estatísticas de confiança (apenas produtos classificados)
    classificacoes = db.query(Classificacao).join(
        MercadoriaAClassificar,
        Classificacao.mercadoria_id == MercadoriaAClassificar.id
    ).filter(
        MercadoriaAClassificar.empresa_id == empresa_id,
        Classificacao.confianca_ncm.isnot(None)
    ).all()
    
    confidence_stats = {
        "total_classified": len(classificacoes),
        "avg_confidence_ncm": 0,
        "avg_confidence_cest": 0,
        "high_confidence": 0,  # > 0.8
        "medium_confidence": 0,  # 0.6 - 0.8
        "low_confidence": 0  # < 0.6
    }
    
    if classificacoes:
        ncm_confidences = [c.confianca_ncm for c in classificacoes if c.confianca_ncm]
        cest_confidences = [c.confianca_cest for c in classificacoes if c.confianca_cest]
        
        if ncm_confidences:
            confidence_stats["avg_confidence_ncm"] = sum(ncm_confidences) / len(ncm_confidences)
        
        if cest_confidences:
            confidence_stats["avg_confidence_cest"] = sum(cest_confidences) / len(cest_confidences)
        
        # Categorizar por confiança (usando NCM como referência)
        for confidence in ncm_confidences:
            if confidence > 0.8:
                confidence_stats["high_confidence"] += 1
            elif confidence >= 0.6:
                confidence_stats["medium_confidence"] += 1
            else:
                confidence_stats["low_confidence"] += 1
    
    return {
        "empresa_id": empresa_id,
        "total_produtos": total_produtos,
        "by_status": stats_by_status,
        "confidence": confidence_stats,
        "processing_rate": {
            "completed": stats_by_status["CONCLUIDA"],
            "pending": stats_by_status["PENDENTE"],
            "needs_review": stats_by_status["REVISAO_MANUAL"],
            "percentage_completed": (stats_by_status["CONCLUIDA"] / total_produtos * 100) if total_produtos > 0 else 0
        }
    }
