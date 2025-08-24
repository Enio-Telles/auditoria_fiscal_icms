"""
Endpoints de Gestão de Empresas
CRUD para empresas e configuração de acesso multiempresa
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
import logging

from ...database.connection import get_db_session
from ...database.models import Usuario, Empresa, UsuarioEmpresaAcesso
from ..schemas import CompanyCreate, CompanyResponse, MessageResponse
from .auth import get_current_user
from ..middleware.error_handler import APIError, BusinessLogicError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[CompanyResponse], summary="Listar empresas")
async def list_companies(
    page: int = Query(default=1, ge=1, description="Página (iniciando em 1)"),
    page_size: int = Query(default=50, ge=1, le=500, description="Itens por página"),
    search: Optional[str] = Query(None, description="Buscar por nome ou CNPJ"),
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    ativo: Optional[bool] = Query(None, description="Filtrar por status ativo"),
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Lista empresas acessíveis pelo usuário atual
    """
    logger.info(f"🏢 Listando empresas - Página {page}, Usuário: {current_user.email}")

    # Query base - empresas que o usuário tem acesso
    query = (
        db.query(Empresa)
        .join(UsuarioEmpresaAcesso, Empresa.id == UsuarioEmpresaAcesso.empresa_id)
        .filter(UsuarioEmpresaAcesso.usuario_id == current_user.id)
    )

    # Aplicar filtros
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(Empresa.nome.ilike(search_term), Empresa.cnpj.ilike(search_term))
        )

    if uf:
        query = query.filter(Empresa.uf == uf.upper())

    if ativo is not None:
        query = query.filter(Empresa.ativo == ativo)

    # Contar total
    total = query.count()

    # Aplicar paginação
    offset = (page - 1) * page_size
    companies = query.offset(offset).limit(page_size).all()

    logger.info(f"✅ Retornando {len(companies)} empresas de {total} total")

    return companies


@router.get(
    "/{company_id}", response_model=CompanyResponse, summary="Buscar empresa por ID"
)
async def get_company(
    company_id: int,
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Retorna informações de uma empresa específica
    """
    logger.info(f"🏢 Buscando empresa ID {company_id} - Usuário: {current_user.email}")

    # Verificar se usuário tem acesso à empresa
    access = (
        db.query(UsuarioEmpresaAcesso)
        .filter(
            UsuarioEmpresaAcesso.usuario_id == current_user.id,
            UsuarioEmpresaAcesso.empresa_id == company_id,
        )
        .first()
    )

    if not access:
        logger.warning(
            f"❌ Usuário {current_user.email} sem acesso à empresa {company_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado à empresa"
        )

    company = db.query(Empresa).filter(Empresa.id == company_id).first()

    if not company:
        logger.warning(f"❌ Empresa {company_id} não encontrada")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada"
        )

    return company


@router.post("/", response_model=CompanyResponse, summary="Criar nova empresa")
async def create_company(
    company_data: CompanyCreate,
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Cria uma nova empresa e concede acesso ao usuário criador
    """
    logger.info(f"➕ Criando empresa {company_data.nome} - Por: {current_user.email}")

    # Verificar se CNPJ já existe
    existing_company = (
        db.query(Empresa).filter(Empresa.cnpj == company_data.cnpj).first()
    )
    if existing_company:
        logger.warning(f"❌ CNPJ já cadastrado: {company_data.cnpj}")
        raise BusinessLogicError(
            "CNPJ já cadastrado no sistema", {"cnpj": company_data.cnpj}
        )

    # Criar nova empresa
    new_company = Empresa(
        nome=company_data.nome,
        cnpj=company_data.cnpj,
        uf=company_data.uf,
        atividades=company_data.atividades,
        endereco=company_data.endereco,
        telefone=company_data.telefone,
        email_contato=company_data.email_contato,
        ativo=True,
    )

    try:
        db.add(new_company)
        db.flush()  # Para obter o ID da empresa

        # Conceder acesso ao usuário criador
        acesso = UsuarioEmpresaAcesso(
            usuario_id=current_user.id,
            empresa_id=new_company.id,
            nivel_acesso="admin",
            ativo=True,
        )

        db.add(acesso)
        db.commit()
        db.refresh(new_company)

        logger.info(f"✅ Empresa criada: {new_company.nome} (ID: {new_company.id})")
        return new_company

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao criar empresa: {e}")
        raise APIError("Erro ao criar empresa", 500, {"error": str(e)})


@router.put(
    "/{company_id}", response_model=CompanyResponse, summary="Atualizar empresa"
)
async def update_company(
    company_id: int,
    company_data: dict,  # Usar dict genérico para permitir atualizações parciais
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Atualiza informações de uma empresa
    """
    logger.info(f"✏️ Atualizando empresa {company_id} - Por: {current_user.email}")

    # Verificar acesso
    access = (
        db.query(UsuarioEmpresaAcesso)
        .filter(
            UsuarioEmpresaAcesso.usuario_id == current_user.id,
            UsuarioEmpresaAcesso.empresa_id == company_id,
            UsuarioEmpresaAcesso.nivel_acesso.in_(["admin", "editor"]),
        )
        .first()
    )

    if not access:
        logger.warning(
            f"❌ Usuário {current_user.email} sem permissão para editar empresa {company_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão insuficiente para editar empresa",
        )

    # Buscar empresa
    company = db.query(Empresa).filter(Empresa.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada"
        )

    # Aplicar atualizações
    for field, value in company_data.items():
        if hasattr(company, field) and value is not None:
            setattr(company, field, value)

    try:
        db.commit()
        db.refresh(company)

        logger.info(f"✅ Empresa {company_id} atualizada com sucesso")
        return company

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao atualizar empresa {company_id}: {e}")
        raise APIError("Erro ao atualizar empresa", 500, {"error": str(e)})


@router.delete(
    "/{company_id}", response_model=MessageResponse, summary="Desativar empresa"
)
async def deactivate_company(
    company_id: int,
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Desativa uma empresa (soft delete)
    """
    logger.info(f"🗑️ Desativando empresa {company_id} - Por: {current_user.email}")

    # Verificar acesso admin
    access = (
        db.query(UsuarioEmpresaAcesso)
        .filter(
            UsuarioEmpresaAcesso.usuario_id == current_user.id,
            UsuarioEmpresaAcesso.empresa_id == company_id,
            UsuarioEmpresaAcesso.nivel_acesso == "admin",
        )
        .first()
    )

    if not access:
        logger.warning(
            f"❌ Usuário {current_user.email} sem permissão admin para empresa {company_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão de administrador necessária",
        )

    # Buscar empresa
    company = db.query(Empresa).filter(Empresa.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada"
        )

    # Desativar empresa
    company.ativo = False

    try:
        db.commit()
        logger.info(f"✅ Empresa {company_id} ({company.nome}) desativada")

        return MessageResponse(
            message=f"Empresa {company.nome} desativada com sucesso",
            success=True,
            data={"company_id": company_id, "cnpj": company.cnpj},
        )

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao desativar empresa {company_id}: {e}")
        raise APIError("Erro ao desativar empresa", 500, {"error": str(e)})


@router.post(
    "/{company_id}/users/{user_id}/access",
    response_model=MessageResponse,
    summary="Conceder acesso à empresa",
)
async def grant_company_access(
    company_id: int,
    user_id: int,
    access_level: str = Query(
        ..., regex="^(viewer|editor|admin)$", description="Nível de acesso"
    ),
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Concede acesso de um usuário a uma empresa
    """
    logger.info(
        f"🔑 Concedendo acesso {access_level} ao usuário {user_id} para empresa {company_id}"
    )

    # Verificar se usuário atual é admin da empresa
    admin_access = (
        db.query(UsuarioEmpresaAcesso)
        .filter(
            UsuarioEmpresaAcesso.usuario_id == current_user.id,
            UsuarioEmpresaAcesso.empresa_id == company_id,
            UsuarioEmpresaAcesso.nivel_acesso == "admin",
        )
        .first()
    )

    if not admin_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão de administrador necessária",
        )

    # Verificar se usuário existe
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado"
        )

    # Verificar se empresa existe
    company = db.query(Empresa).filter(Empresa.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada"
        )

    # Verificar se acesso já existe
    existing_access = (
        db.query(UsuarioEmpresaAcesso)
        .filter(
            UsuarioEmpresaAcesso.usuario_id == user_id,
            UsuarioEmpresaAcesso.empresa_id == company_id,
        )
        .first()
    )

    if existing_access:
        # Atualizar nível de acesso
        existing_access.nivel_acesso = access_level
        existing_access.ativo = True
    else:
        # Criar novo acesso
        new_access = UsuarioEmpresaAcesso(
            usuario_id=user_id,
            empresa_id=company_id,
            nivel_acesso=access_level,
            ativo=True,
        )
        db.add(new_access)

    try:
        db.commit()
        logger.info(f"✅ Acesso {access_level} concedido ao usuário {user.email}")

        return MessageResponse(
            message=f"Acesso {access_level} concedido a {user.nome}",
            success=True,
            data={
                "user_id": user_id,
                "company_id": company_id,
                "access_level": access_level,
            },
        )

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao conceder acesso: {e}")
        raise APIError("Erro ao conceder acesso", 500, {"error": str(e)})
