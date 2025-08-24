"""
Endpoints do Golden Set
Gestão da base de conhecimento curada por humanos
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from datetime import datetime
import logging

from ...database.connection import get_db_session
from ...database.models import Usuario, GoldenSet
from ..schemas import GoldenSetCreate, GoldenSetResponse, MessageResponse
from .auth import get_current_user
from ..middleware.error_handler import APIError, BusinessLogicError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[GoldenSetResponse], summary="Listar Golden Set")
async def list_golden_set(
    page: int = Query(default=1, ge=1, description="Página (iniciando em 1)"),
    page_size: int = Query(default=50, ge=1, le=500, description="Itens por página"),
    search: Optional[str] = Query(None, description="Buscar na descrição"),
    ncm_filter: Optional[str] = Query(None, description="Filtrar por NCM"),
    cest_filter: Optional[str] = Query(None, description="Filtrar por CEST"),
    empresa_filter: Optional[int] = Query(
        None, description="Filtrar por empresa fonte"
    ),
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Lista entradas do Golden Set com filtros e paginação
    """
    logger.info(f"📚 Listando Golden Set - Usuário: {current_user.email}")

    # Query base
    query = db.query(GoldenSet)

    # Aplicar filtros
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                GoldenSet.descricao_produto.ilike(search_pattern),
                GoldenSet.descricao_enriquecida.ilike(search_pattern),
            )
        )

    if ncm_filter:
        query = query.filter(GoldenSet.ncm_correto.ilike(f"%{ncm_filter}%"))

    if cest_filter:
        query = query.filter(GoldenSet.cest_correto.ilike(f"%{cest_filter}%"))

    if empresa_filter:
        query = query.filter(GoldenSet.fonte_empresa_id == empresa_filter)

    # Ordenar por mais recentes
    query = query.order_by(desc(GoldenSet.data_confirmacao))

    # Aplicar paginação
    offset = (page - 1) * page_size
    golden_entries = query.offset(offset).limit(page_size).all()

    logger.info(f"✅ Retornando {len(golden_entries)} entradas do Golden Set")

    return golden_entries


@router.get(
    "/{golden_id}",
    response_model=GoldenSetResponse,
    summary="Buscar entrada do Golden Set",
)
async def get_golden_set_entry(
    golden_id: int,
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Retorna uma entrada específica do Golden Set
    """
    logger.info(f"📖 Buscando entrada Golden Set {golden_id}")

    entry = db.query(GoldenSet).filter(GoldenSet.id == golden_id).first()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entrada do Golden Set não encontrada",
        )

    return entry


@router.post(
    "/", response_model=GoldenSetResponse, summary="Criar entrada no Golden Set"
)
async def create_golden_set_entry(
    golden_data: GoldenSetCreate,
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Cria uma nova entrada no Golden Set

    O Golden Set é a base de conhecimento mais valiosa do sistema,
    contendo classificações validadas por especialistas humanos.
    """
    logger.info(f"➕ Criando entrada Golden Set - Por: {current_user.email}")

    # Verificar se já existe entrada similar
    existing_entry = (
        db.query(GoldenSet)
        .filter(GoldenSet.descricao_produto == golden_data.descricao_produto)
        .first()
    )

    if existing_entry:
        logger.warning("⚠️ Entrada similar já existe no Golden Set")
        raise BusinessLogicError(
            "Já existe uma entrada com descrição similar no Golden Set",
            {
                "existing_id": existing_entry.id,
                "existing_description": existing_entry.descricao_produto,
            },
        )

    # Validar NCM (formato AAAA.AA.AA)
    if len(golden_data.ncm_correto.replace(".", "")) != 8:
        raise BusinessLogicError("NCM deve ter 8 dígitos no formato AAAA.AA.AA")

    # Validar CEST se fornecido (formato AA.AAA.AA)
    if golden_data.cest_correto and len(golden_data.cest_correto.replace(".", "")) != 7:
        raise BusinessLogicError("CEST deve ter 7 dígitos no formato AA.AAA.AA")

    # Criar nova entrada
    new_entry = GoldenSet(
        descricao_produto=golden_data.descricao_produto,
        descricao_enriquecida=golden_data.descricao_enriquecida,
        gtin=golden_data.gtin,
        ncm_correto=golden_data.ncm_correto,
        cest_correto=golden_data.cest_correto,
        fonte_usuario=current_user.email,
        fonte_empresa_id=golden_data.fonte_empresa_id,
        data_confirmacao=datetime.utcnow(),
        observacoes=golden_data.observacoes,
    )

    try:
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)

        logger.info(f"✅ Entrada Golden Set criada: ID {new_entry.id}")
        return new_entry

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao criar entrada Golden Set: {e}")
        raise APIError("Erro ao criar entrada no Golden Set", 500, {"error": str(e)})


@router.put(
    "/{golden_id}",
    response_model=GoldenSetResponse,
    summary="Atualizar entrada do Golden Set",
)
async def update_golden_set_entry(
    golden_id: int,
    golden_data: dict,  # Permite atualizações parciais
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Atualiza uma entrada existente do Golden Set
    """
    logger.info(
        f"✏️ Atualizando entrada Golden Set {golden_id} - Por: {current_user.email}"
    )

    # Buscar entrada
    entry = db.query(GoldenSet).filter(GoldenSet.id == golden_id).first()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entrada do Golden Set não encontrada",
        )

    # Aplicar atualizações
    for field, value in golden_data.items():
        if hasattr(entry, field) and value is not None:
            # Validações específicas
            if field == "ncm_correto" and len(value.replace(".", "")) != 8:
                raise BusinessLogicError("NCM deve ter 8 dígitos")

            if field == "cest_correto" and value and len(value.replace(".", "")) != 7:
                raise BusinessLogicError("CEST deve ter 7 dígitos")

            setattr(entry, field, value)

    # Atualizar metadados
    entry.fonte_usuario = current_user.email
    entry.data_confirmacao = datetime.utcnow()

    try:
        db.commit()
        db.refresh(entry)

        logger.info(f"✅ Entrada Golden Set {golden_id} atualizada")
        return entry

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao atualizar entrada Golden Set: {e}")
        raise APIError(
            "Erro ao atualizar entrada do Golden Set", 500, {"error": str(e)}
        )


@router.delete(
    "/{golden_id}",
    response_model=MessageResponse,
    summary="Remover entrada do Golden Set",
)
async def delete_golden_set_entry(
    golden_id: int,
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Remove uma entrada do Golden Set

    Atenção: Esta operação é irreversível e afeta a base de conhecimento do sistema.
    """
    logger.info(
        f"🗑️ Removendo entrada Golden Set {golden_id} - Por: {current_user.email}"
    )

    # Buscar entrada
    entry = db.query(GoldenSet).filter(GoldenSet.id == golden_id).first()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entrada do Golden Set não encontrada",
        )

    # Salvar informações para log
    descricao = entry.descricao_produto
    ncm = entry.ncm_correto

    try:
        db.delete(entry)
        db.commit()

        logger.info(f"✅ Entrada Golden Set removida: {descricao} (NCM: {ncm})")

        return MessageResponse(
            message="Entrada do Golden Set removida com sucesso",
            success=True,
            data={"golden_id": golden_id, "descricao": descricao, "ncm": ncm},
        )

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao remover entrada Golden Set: {e}")
        raise APIError("Erro ao remover entrada do Golden Set", 500, {"error": str(e)})


@router.post(
    "/from-classification/{mercadoria_id}",
    response_model=GoldenSetResponse,
    summary="Criar Golden Set a partir de classificação",
)
async def create_from_classification(
    mercadoria_id: int,
    ncm_correto: str = Query(..., description="NCM correto validado"),
    cest_correto: Optional[str] = Query(None, description="CEST correto validado"),
    observacoes: Optional[str] = Query(
        None, description="Observações sobre a correção"
    ),
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Cria entrada no Golden Set a partir de uma classificação revisada

    Este é o principal mecanismo de feedback humano para o sistema.
    """
    logger.info(f"🎯 Criando Golden Set a partir da mercadoria {mercadoria_id}")

    # Buscar mercadoria com classificação
    from ...database.models import (
        MercadoriaAClassificar,
        Classificacao,
        UsuarioEmpresaAcesso,
    )

    mercadoria = (
        db.query(MercadoriaAClassificar)
        .filter(MercadoriaAClassificar.id == mercadoria_id)
        .first()
    )

    if not mercadoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mercadoria não encontrada"
        )

    # Verificar acesso à empresa
    access = (
        db.query(UsuarioEmpresaAcesso)
        .filter(
            UsuarioEmpresaAcesso.usuario_id == current_user.id,
            UsuarioEmpresaAcesso.empresa_id == mercadoria.empresa_id,
        )
        .first()
    )

    if not access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado à empresa"
        )

    # Buscar classificação existente
    classificacao = (
        db.query(Classificacao)
        .filter(Classificacao.mercadoria_id == mercadoria_id)
        .first()
    )

    # Preparar dados para Golden Set
    golden_data = GoldenSetCreate(
        descricao_produto=mercadoria.descricao_original,
        descricao_enriquecida=mercadoria.descricao_enriquecida,
        gtin=mercadoria.codigo_barra,
        ncm_correto=ncm_correto,
        cest_correto=cest_correto,
        fonte_empresa_id=mercadoria.empresa_id,
        observacoes=(
            observacoes
            or (
                "Correção humana da classificação automática. Original: "
                f"NCM={classificacao.ncm_determinado if classificacao else 'N/A'}, "
                f"CEST={classificacao.cest_determinado if classificacao else 'N/A'}"
            )
        ),
    )

    # Criar entrada usando endpoint existente
    return await create_golden_set_entry(golden_data, db, current_user)


@router.get("/search/similar", summary="Buscar entradas similares no Golden Set")
async def search_similar_in_golden_set(
    description: str = Query(
        ..., min_length=5, description="Descrição para buscar similaridade"
    ),
    threshold: float = Query(
        default=0.8, ge=0.1, le=1.0, description="Limiar de similaridade"
    ),
    limit: int = Query(default=10, ge=1, le=50, description="Limite de resultados"),
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Busca entradas similares no Golden Set usando similaridade de texto

    Útil para verificar se já existe classificação similar antes de criar nova entrada.
    """
    logger.info(f"🔍 Buscando similaridade no Golden Set para: {description[:50]}...")

    # Busca simples por palavras-chave (em produção, usar embeddings)
    search_terms = description.lower().split()

    # Query que busca por termos na descrição
    query = db.query(GoldenSet)

    for term in search_terms[:5]:  # Limitar a 5 termos principais
        if len(term) > 3:  # Ignorar palavras muito pequenas
            query = query.filter(
                or_(
                    GoldenSet.descricao_produto.ilike(f"%{term}%"),
                    GoldenSet.descricao_enriquecida.ilike(f"%{term}%"),
                )
            )

    # Buscar e limitar resultados
    similar_entries = query.limit(limit).all()

    # Em uma implementação completa, calcular similaridade semântica real
    results = []
    for entry in similar_entries:
        # Simulação de score de similaridade baseado em palavras comuns
        entry_terms = (entry.descricao_produto or "").lower().split()
        common_terms = set(search_terms) & set(entry_terms)
        similarity_score = len(common_terms) / max(len(search_terms), len(entry_terms))

        if similarity_score >= threshold:
            results.append(
                {
                    "golden_set_entry": entry,
                    "similarity_score": similarity_score,
                    "matching_terms": list(common_terms),
                }
            )

    # Ordenar por similaridade
    results.sort(key=lambda x: x["similarity_score"], reverse=True)

    logger.info(f"✅ Encontradas {len(results)} entradas similares")

    return {
        "query": description,
        "threshold": threshold,
        "total_found": len(results),
        "results": results,
    }


@router.get("/stats", summary="Estatísticas do Golden Set")
async def get_golden_set_stats(
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Retorna estatísticas do Golden Set
    """
    logger.info("📊 Gerando estatísticas do Golden Set")

    # Estatísticas básicas
    total_entries = db.query(GoldenSet).count()

    # Por fonte de usuário
    user_contributions = (
        db.query(GoldenSet.fonte_usuario, db.func.count(GoldenSet.id).label("count"))
        .group_by(GoldenSet.fonte_usuario)
        .all()
    )

    # Por empresa fonte
    company_contributions = (
        db.query(GoldenSet.fonte_empresa_id, db.func.count(GoldenSet.id).label("count"))
        .group_by(GoldenSet.fonte_empresa_id)
        .all()
    )

    # Entradas com CEST vs sem CEST
    with_cest = db.query(GoldenSet).filter(GoldenSet.cest_correto.isnot(None)).count()
    without_cest = total_entries - with_cest

    return {
        "total_entries": total_entries,
        "with_cest": with_cest,
        "without_cest": without_cest,
        "by_user": [
            {"user": contrib[0], "count": contrib[1]} for contrib in user_contributions
        ],
        "by_company": [
            {"company_id": contrib[0], "count": contrib[1]}
            for contrib in company_contributions
        ],
        "quality_metrics": {
            "coverage_percentage": (
                (with_cest / total_entries * 100) if total_entries > 0 else 0
            ),
            "avg_description_length": db.query(
                db.func.avg(db.func.length(GoldenSet.descricao_produto))
            ).scalar()
            or 0,
        },
    }
