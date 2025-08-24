"""
Endpoints de Autenticação
Implementa login, logout e gestão de tokens JWT
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt
import bcrypt
import logging

from ...database.connection import get_db_session
from ...database.models import Usuario
from ...core.config import get_settings
from ..schemas import UserLogin, TokenResponse, MessageResponse

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Instância das configurações
settings = get_settings()


def hash_password(password: str) -> str:
    """Gera hash da senha"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verifica se a senha confere com o hash"""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria token JWT de acesso"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.jwt["access_token_expire_minutes"]
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt["secret_key"], algorithm=settings.jwt["algorithm"]
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decodifica e valida token JWT"""
    try:
        payload = jwt.decode(
            token, settings.jwt["secret_key"], algorithms=[settings.jwt["algorithm"]]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session),
) -> Usuario:
    """Dependency para obter usuário atual a partir do token"""

    token = credentials.credentials
    payload = decode_access_token(token)

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


@router.post("/token", response_model=TokenResponse, summary="Login de usuário")
async def login(user_data: UserLogin, db: Session = Depends(get_db_session)):
    """
    Endpoint para autenticação de usuário

    Retorna token JWT para acesso às APIs protegidas
    """
    logger.info(f"🔐 Tentativa de login para: {user_data.email}")

    # Buscar usuário pelo email
    user = db.query(Usuario).filter(Usuario.email == user_data.email).first()

    if not user:
        logger.warning(f"❌ Login falhou - usuário não encontrado: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha incorretos"
        )

    if not user.ativo:
        logger.warning(f"❌ Login falhou - usuário inativo: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo"
        )

    # Verificar senha
    if not verify_password(user_data.password, user.senha_hash):
        logger.warning(f"❌ Login falhou - senha incorreta: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha incorretos"
        )

    # Criar token de acesso
    access_token_expires = timedelta(
        minutes=settings.jwt["access_token_expire_minutes"]
    )
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires,
    )

    logger.info(f"✅ Login bem-sucedido: {user_data.email}")

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt["access_token_expire_minutes"] * 60,
        user_info={
            "id": user.id,
            "nome": user.nome,
            "email": user.email,
            "cargo": user.cargo,
        },
    )


@router.post("/logout", response_model=MessageResponse, summary="Logout de usuário")
async def logout(current_user: Usuario = Depends(get_current_user)):
    """
    Endpoint para logout de usuário

    Nota: Como estamos usando JWT stateless, o logout é apenas uma confirmação.
    O cliente deve descartar o token.
    """
    logger.info(f"🚪 Logout do usuário: {current_user.email}")

    return MessageResponse(message="Logout realizado com sucesso", success=True)


@router.get("/me", response_model=dict, summary="Informações do usuário atual")
async def get_user_info(current_user: Usuario = Depends(get_current_user)):
    """
    Retorna informações do usuário atualmente autenticado
    """
    return {
        "id": current_user.id,
        "nome": current_user.nome,
        "email": current_user.email,
        "cargo": current_user.cargo,
        "identificacao": current_user.identificacao,
        "ativo": current_user.ativo,
        "criado_em": current_user.criado_em,
    }


@router.post("/refresh", response_model=TokenResponse, summary="Renovar token")
async def refresh_token(current_user: Usuario = Depends(get_current_user)):
    """
    Renova o token de acesso de um usuário autenticado
    """
    logger.info(f"🔄 Renovando token para: {current_user.email}")

    # Criar novo token
    access_token_expires = timedelta(
        minutes=settings.jwt["access_token_expire_minutes"]
    )
    access_token = create_access_token(
        data={"sub": str(current_user.id), "email": current_user.email},
        expires_delta=access_token_expires,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt["access_token_expire_minutes"] * 60,
        user_info={
            "id": current_user.id,
            "nome": current_user.nome,
            "email": current_user.email,
            "cargo": current_user.cargo,
        },
    )
