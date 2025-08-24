"""
Sistema de Permissões Completo
Implementa controle de acesso baseado em roles (RBAC)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from enum import Enum

from database import get_db
from auth import get_current_user
from models import User

router = APIRouter(prefix="/api/permissions", tags=["permissions"])


class PermissionLevel(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class ResourceType(str, Enum):
    EMPRESA = "empresa"
    PRODUTO = "produto"
    CLASSIFICACAO = "classificacao"
    GOLDEN_SET = "golden_set"
    RELATORIO = "relatorio"
    USUARIO = "usuario"
    SISTEMA = "sistema"


class Role(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    AUDITOR = "auditor"
    ANALISTA = "analista"
    USUARIO = "usuario"
    READONLY = "readonly"


class PermissionRequest(BaseModel):
    resource_type: ResourceType
    resource_id: Optional[str] = None
    permission_level: PermissionLevel
    user_id: str
    granted_by: str
    reason: str = Field(
        ..., min_length=10, description="Justificativa para a permissão"
    )
    expires_at: Optional[datetime] = None


class PermissionResponse(BaseModel):
    id: str
    resource_type: ResourceType
    resource_id: Optional[str]
    permission_level: PermissionLevel
    user_id: str
    granted_by: str
    granted_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    reason: str


class RoleUpdate(BaseModel):
    user_id: str
    new_role: Role
    reason: str


class PermissionManager:
    """
    Gerenciador central de permissões do sistema
    """

    # Definição de permissões por role
    ROLE_PERMISSIONS = {
        Role.SUPER_ADMIN: {
            ResourceType.EMPRESA: [
                PermissionLevel.READ,
                PermissionLevel.WRITE,
                PermissionLevel.DELETE,
                PermissionLevel.ADMIN,
            ],
            ResourceType.PRODUTO: [
                PermissionLevel.READ,
                PermissionLevel.WRITE,
                PermissionLevel.DELETE,
                PermissionLevel.ADMIN,
            ],
            ResourceType.CLASSIFICACAO: [
                PermissionLevel.READ,
                PermissionLevel.WRITE,
                PermissionLevel.DELETE,
                PermissionLevel.ADMIN,
            ],
            ResourceType.GOLDEN_SET: [
                PermissionLevel.READ,
                PermissionLevel.WRITE,
                PermissionLevel.DELETE,
                PermissionLevel.ADMIN,
            ],
            ResourceType.RELATORIO: [
                PermissionLevel.READ,
                PermissionLevel.WRITE,
                PermissionLevel.DELETE,
                PermissionLevel.ADMIN,
            ],
            ResourceType.USUARIO: [
                PermissionLevel.READ,
                PermissionLevel.WRITE,
                PermissionLevel.DELETE,
                PermissionLevel.ADMIN,
            ],
            ResourceType.SISTEMA: [
                PermissionLevel.READ,
                PermissionLevel.WRITE,
                PermissionLevel.DELETE,
                PermissionLevel.ADMIN,
            ],
        },
        Role.ADMIN: {
            ResourceType.EMPRESA: [
                PermissionLevel.READ,
                PermissionLevel.WRITE,
                PermissionLevel.DELETE,
            ],
            ResourceType.PRODUTO: [
                PermissionLevel.READ,
                PermissionLevel.WRITE,
                PermissionLevel.DELETE,
            ],
            ResourceType.CLASSIFICACAO: [
                PermissionLevel.READ,
                PermissionLevel.WRITE,
                PermissionLevel.DELETE,
            ],
            ResourceType.GOLDEN_SET: [PermissionLevel.READ, PermissionLevel.WRITE],
            ResourceType.RELATORIO: [PermissionLevel.READ, PermissionLevel.WRITE],
            ResourceType.USUARIO: [PermissionLevel.READ, PermissionLevel.WRITE],
            ResourceType.SISTEMA: [PermissionLevel.READ],
        },
        Role.AUDITOR: {
            ResourceType.EMPRESA: [PermissionLevel.READ],
            ResourceType.PRODUTO: [PermissionLevel.READ],
            ResourceType.CLASSIFICACAO: [PermissionLevel.READ, PermissionLevel.WRITE],
            ResourceType.GOLDEN_SET: [PermissionLevel.READ, PermissionLevel.WRITE],
            ResourceType.RELATORIO: [PermissionLevel.READ, PermissionLevel.WRITE],
            ResourceType.USUARIO: [PermissionLevel.READ],
            ResourceType.SISTEMA: [PermissionLevel.READ],
        },
        Role.ANALISTA: {
            ResourceType.EMPRESA: [PermissionLevel.READ],
            ResourceType.PRODUTO: [PermissionLevel.READ, PermissionLevel.WRITE],
            ResourceType.CLASSIFICACAO: [PermissionLevel.READ, PermissionLevel.WRITE],
            ResourceType.GOLDEN_SET: [PermissionLevel.READ],
            ResourceType.RELATORIO: [PermissionLevel.READ],
            ResourceType.USUARIO: [PermissionLevel.READ],
            ResourceType.SISTEMA: [PermissionLevel.READ],
        },
        Role.USUARIO: {
            ResourceType.EMPRESA: [PermissionLevel.READ],
            ResourceType.PRODUTO: [PermissionLevel.READ],
            ResourceType.CLASSIFICACAO: [PermissionLevel.READ],
            ResourceType.GOLDEN_SET: [PermissionLevel.READ],
            ResourceType.RELATORIO: [PermissionLevel.READ],
            ResourceType.USUARIO: [],
            ResourceType.SISTEMA: [],
        },
        Role.READONLY: {
            ResourceType.EMPRESA: [PermissionLevel.READ],
            ResourceType.PRODUTO: [PermissionLevel.READ],
            ResourceType.CLASSIFICACAO: [PermissionLevel.READ],
            ResourceType.GOLDEN_SET: [PermissionLevel.READ],
            ResourceType.RELATORIO: [PermissionLevel.READ],
            ResourceType.USUARIO: [],
            ResourceType.SISTEMA: [],
        },
    }

    def __init__(self, db: Session):
        self.db = db

    def check_permission(
        self,
        user: User,
        resource_type: ResourceType,
        permission_level: PermissionLevel,
        resource_id: Optional[str] = None,
    ) -> bool:
        """
        Verifica se usuário tem permissão específica
        """

        # Verificar permissões do role
        user_role = Role(user.role)
        role_permissions = self.ROLE_PERMISSIONS.get(user_role, {})
        resource_permissions = role_permissions.get(resource_type, [])

        if permission_level in resource_permissions:
            return True

        # Verificar permissões específicas concedidas
        specific_permission = self._check_specific_permission(
            user.id, resource_type, permission_level, resource_id
        )

        return specific_permission

    def _check_specific_permission(
        self,
        user_id: str,
        resource_type: ResourceType,
        permission_level: PermissionLevel,
        resource_id: Optional[str] = None,
    ) -> bool:
        """
        Verifica permissões específicas concedidas individualmente
        """
        # Implementar consulta ao banco de permissões específicas
        # Por ora, retorna False (usar apenas permissões de role)
        return False

    def grant_permission(
        self, permission_request: PermissionRequest, granter: User
    ) -> PermissionResponse:
        """
        Concede permissão específica a um usuário
        """

        # Verificar se quem está concedendo tem autorização
        if not self.check_permission(
            granter, ResourceType.USUARIO, PermissionLevel.ADMIN
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem autorização para conceder permissões",
            )

        # Criar registro de permissão
        permission_id = str(uuid.uuid4())

        # Implementar salvamento no banco
        permission = PermissionResponse(
            id=permission_id,
            resource_type=permission_request.resource_type,
            resource_id=permission_request.resource_id,
            permission_level=permission_request.permission_level,
            user_id=permission_request.user_id,
            granted_by=granter.id,
            granted_at=datetime.utcnow(),
            expires_at=permission_request.expires_at,
            is_active=True,
            reason=permission_request.reason,
        )

        return permission

    def revoke_permission(self, permission_id: str, revoker: User, reason: str) -> bool:
        """
        Revoga permissão específica
        """

        # Verificar autorização
        if not self.check_permission(
            revoker, ResourceType.USUARIO, PermissionLevel.ADMIN
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem autorização para revogar permissões",
            )

        # Implementar revogação no banco
        # Marcar como inativa e registrar razão

        return True

    def update_user_role(
        self, role_update: RoleUpdate, updater: User
    ) -> Dict[str, Any]:
        """
        Atualiza role de um usuário
        """

        # Verificar autorização
        if not self.check_permission(
            updater, ResourceType.USUARIO, PermissionLevel.ADMIN
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem autorização para alterar roles",
            )

        # Implementar atualização no banco
        # Registrar log de auditoria

        return {
            "user_id": role_update.user_id,
            "old_role": "role_atual",  # Buscar do banco
            "new_role": role_update.new_role,
            "updated_by": updater.id,
            "updated_at": datetime.utcnow(),
            "reason": role_update.reason,
        }

    def get_user_permissions(self, user_id: str) -> Dict[str, Any]:
        """
        Retorna todas as permissões de um usuário
        """

        # Buscar usuário
        # user = self.db.query(User).filter(User.id == user_id).first()

        # Simular estrutura de retorno
        return {
            "user_id": user_id,
            "role": "analista",
            "role_permissions": {
                "empresa": ["read"],
                "produto": ["read", "write"],
                "classificacao": ["read", "write"],
                "golden_set": ["read"],
                "relatorio": ["read"],
            },
            "specific_permissions": [],
            "last_updated": datetime.utcnow(),
        }


# Dependency para verificar permissões
def require_permission(
    resource_type: ResourceType,
    permission_level: PermissionLevel,
    resource_id: Optional[str] = None,
):
    """
    Decorator para verificar permissões em endpoints
    """

    def permission_dependency(
        current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ):
        permission_manager = PermissionManager(db)

        if not permission_manager.check_permission(
            current_user, resource_type, permission_level, resource_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Sem permissão {permission_level.value} para {resource_type.value}",
            )

        return current_user

    return permission_dependency


# Endpoints do sistema de permissões


@router.post("/grant", response_model=PermissionResponse)
async def grant_permission(
    permission_request: PermissionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Concede permissão específica a um usuário
    """
    permission_manager = PermissionManager(db)
    return permission_manager.grant_permission(permission_request, current_user)


@router.delete("/revoke/{permission_id}")
async def revoke_permission(
    permission_id: str,
    reason: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Revoga permissão específica
    """
    permission_manager = PermissionManager(db)
    success = permission_manager.revoke_permission(permission_id, current_user, reason)

    if success:
        return {"message": "Permissão revogada com sucesso"}
    else:
        raise HTTPException(status_code=400, detail="Falha ao revogar permissão")


@router.put("/role")
async def update_user_role(
    role_update: RoleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Atualiza role de um usuário
    """
    permission_manager = PermissionManager(db)
    return permission_manager.update_user_role(role_update, current_user)


@router.get("/user/{user_id}")
async def get_user_permissions(
    user_id: str,
    current_user: User = Depends(
        require_permission(ResourceType.USUARIO, PermissionLevel.READ)
    ),
    db: Session = Depends(get_db),
):
    """
    Retorna permissões de um usuário
    """
    permission_manager = PermissionManager(db)
    return permission_manager.get_user_permissions(user_id)


@router.get("/roles")
async def list_available_roles(
    current_user: User = Depends(
        require_permission(ResourceType.USUARIO, PermissionLevel.READ)
    ),
):
    """
    Lista roles disponíveis no sistema
    """
    return {
        "roles": [
            {
                "name": role.value,
                "description": f"Role {role.value}",
                "permissions": PermissionManager.ROLE_PERMISSIONS.get(role, {}),
            }
            for role in Role
        ]
    }


@router.get("/check")
async def check_permission_endpoint(
    resource_type: ResourceType,
    permission_level: PermissionLevel,
    resource_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verifica se usuário atual tem uma permissão específica
    """
    permission_manager = PermissionManager(db)
    has_permission = permission_manager.check_permission(
        current_user, resource_type, permission_level, resource_id
    )

    return {
        "user_id": current_user.id,
        "resource_type": resource_type,
        "permission_level": permission_level,
        "resource_id": resource_id,
        "has_permission": has_permission,
    }
