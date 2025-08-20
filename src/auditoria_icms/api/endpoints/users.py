"""
Endpoints de Gestão de Usuários
CRUD completo para usuários do sistema
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
import logging

from ...database.connection import get_db_session
from ...database.models import Usuario
from ..schemas import UserCreate, UserResponse, UserUpdate, MessageResponse
from .auth import get_current_user, hash_password
from ..middleware.error_handler import APIError, BusinessLogicError

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[UserResponse], summary="Listar usuários")
async def list_users(
    page: int = Query(default=1, ge=1, description="Página (iniciando em 1)"),
    page_size: int = Query(default=50, ge=1, le=500, description="Itens por página"),
    search: Optional[str] = Query(None, description="Buscar por nome ou email"),
    ativo: Optional[bool] = Query(None, description="Filtrar por status ativo"),
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista todos os usuários do sistema com paginação e filtros
    """
    logger.info(f"👥 Listando usuários - Página {page}, Usuário: {current_user.email}")
    
    # Query base
    query = db.query(Usuario)
    
    # Aplicar filtros
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Usuario.nome.ilike(search_term),
                Usuario.email.ilike(search_term)
            )
        )
    
    if ativo is not None:
        query = query.filter(Usuario.ativo == ativo)
    
    # Contar total
    total = query.count()
    
    # Aplicar paginação
    offset = (page - 1) * page_size
    users = query.offset(offset).limit(page_size).all()
    
    logger.info(f"✅ Retornando {len(users)} usuários de {total} total")
    
    return users

@router.get("/{user_id}", response_model=UserResponse, summary="Buscar usuário por ID")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna informações de um usuário específico
    """
    logger.info(f"👤 Buscando usuário ID {user_id} - Solicitado por: {current_user.email}")
    
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    
    if not user:
        logger.warning(f"❌ Usuário {user_id} não encontrado")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    return user

@router.post("/", response_model=UserResponse, summary="Criar novo usuário")
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Cria um novo usuário no sistema
    """
    logger.info(f"➕ Criando usuário {user_data.email} - Por: {current_user.email}")
    
    # Verificar se email já existe
    existing_user = db.query(Usuario).filter(Usuario.email == user_data.email).first()
    if existing_user:
        logger.warning(f"❌ Email já cadastrado: {user_data.email}")
        raise BusinessLogicError(
            "Email já cadastrado no sistema",
            {"email": user_data.email}
        )
    
    # Criar hash da senha
    password_hash = hash_password(user_data.password)
    
    # Criar novo usuário
    new_user = Usuario(
        nome=user_data.nome,
        email=user_data.email,
        cargo=user_data.cargo,
        identificacao=user_data.identificacao,
        senha_hash=password_hash,
        ativo=True
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"✅ Usuário criado com sucesso: {new_user.email} (ID: {new_user.id})")
        return new_user
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao criar usuário: {e}")
        raise APIError("Erro ao criar usuário", 500, {"error": str(e)})

@router.put("/{user_id}", response_model=UserResponse, summary="Atualizar usuário")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Atualiza informações de um usuário existente
    """
    logger.info(f"✏️ Atualizando usuário {user_id} - Por: {current_user.email}")
    
    # Buscar usuário
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        logger.warning(f"❌ Usuário {user_id} não encontrado para atualização")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Aplicar atualizações (apenas campos não nulos)
    update_data = user_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    try:
        db.commit()
        db.refresh(user)
        
        logger.info(f"✅ Usuário {user_id} atualizado com sucesso")
        return user
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao atualizar usuário {user_id}: {e}")
        raise APIError("Erro ao atualizar usuário", 500, {"error": str(e)})

@router.delete("/{user_id}", response_model=MessageResponse, summary="Desativar usuário")
async def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Desativa um usuário (soft delete)
    """
    logger.info(f"🗑️ Desativando usuário {user_id} - Por: {current_user.email}")
    
    # Verificar se não está tentando desativar a si mesmo
    if user_id == current_user.id:
        logger.warning(f"❌ Usuário {current_user.email} tentou desativar a si mesmo")
        raise BusinessLogicError("Não é possível desativar sua própria conta")
    
    # Buscar usuário
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        logger.warning(f"❌ Usuário {user_id} não encontrado para desativação")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Desativar usuário
    user.ativo = False
    
    try:
        db.commit()
        logger.info(f"✅ Usuário {user_id} ({user.email}) desativado com sucesso")
        
        return MessageResponse(
            message=f"Usuário {user.nome} desativado com sucesso",
            success=True,
            data={"user_id": user_id, "email": user.email}
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao desativar usuário {user_id}: {e}")
        raise APIError("Erro ao desativar usuário", 500, {"error": str(e)})

@router.post("/{user_id}/activate", response_model=MessageResponse, summary="Reativar usuário")
async def activate_user(
    user_id: int,
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Reativa um usuário desativado
    """
    logger.info(f"🔄 Reativando usuário {user_id} - Por: {current_user.email}")
    
    # Buscar usuário
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        logger.warning(f"❌ Usuário {user_id} não encontrado para reativação")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Reativar usuário
    user.ativo = True
    
    try:
        db.commit()
        logger.info(f"✅ Usuário {user_id} ({user.email}) reativado com sucesso")
        
        return MessageResponse(
            message=f"Usuário {user.nome} reativado com sucesso",
            success=True,
            data={"user_id": user_id, "email": user.email}
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao reativar usuário {user_id}: {e}")
        raise APIError("Erro ao reativar usuário", 500, {"error": str(e)})
