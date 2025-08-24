"""
Tenant Service
Manages multi-tenant configuration and isolation
"""
from fastapi import FastAPI, HTTPException, Depends, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import sys
import os

# Add the microservices directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
microservices_dir = os.path.dirname(current_dir)
sys.path.insert(0, microservices_dir)

from shared.database import Base, get_db, db_config
from shared.auth import get_current_user, get_current_tenant
from shared.models import BaseResponse, ErrorResponse, TenantInfo
from shared.logging_config import setup_logger
from pydantic import BaseModel

# Initialize logger
logger = setup_logger("tenant-service")

# Database Models
class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, unique=True, index=True, nullable=False)
    tenant_name = Column(String, nullable=False)
    description = Column(Text)
    settings = Column(JSON, default={})
    is_active = Column(String, default="true")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Pydantic Models
class TenantCreate(BaseModel):
    tenant_id: str
    tenant_name: str
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = {}

class TenantUpdate(BaseModel):
    tenant_name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[str] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    engine = db_config.initialize()
    Base.metadata.create_all(bind=engine)
    logger.info("Tenant service started")
    yield
    # Cleanup code (if needed) would go here

# FastAPI App
app = FastAPI(
    title="Tenant Service",
    description="Multi-tenant configuration and isolation management",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return BaseResponse(message="Tenant service is healthy")

@app.post("/tenants", response_model=BaseResponse)
async def create_tenant(
    tenant_data: TenantCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new tenant"""
    try:
        # Check if tenant already exists
        existing_tenant = db.query(Tenant).filter(
            Tenant.tenant_id == tenant_data.tenant_id
        ).first()
        
        if existing_tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant ID already exists"
            )
        
        # Create new tenant
        new_tenant = Tenant(
            tenant_id=tenant_data.tenant_id,
            tenant_name=tenant_data.tenant_name,
            description=tenant_data.description,
            settings=tenant_data.settings or {}
        )
        
        db.add(new_tenant)
        db.commit()
        db.refresh(new_tenant)
        
        # Create tenant schema in database
        try:
            schema_name = db_config.get_tenant_schema(tenant_data.tenant_id)
            db.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
            db.commit()
            logger.info(f"Created schema for tenant: {schema_name}")
        except Exception as schema_error:
            logger.warning(f"Could not create schema: {str(schema_error)}")
        
        logger.info(f"New tenant created: {tenant_data.tenant_id}")
        
        return BaseResponse(
            message="Tenant created successfully",
            data={
                "id": new_tenant.id,
                "tenant_id": new_tenant.tenant_id,
                "tenant_name": new_tenant.tenant_name,
                "description": new_tenant.description,
                "settings": new_tenant.settings,
                "created_at": new_tenant.created_at
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tenant: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/tenants", response_model=BaseResponse)
async def list_tenants(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all tenants (admin only)"""
    try:
        tenants = db.query(Tenant).all()
        
        tenant_list = []
        for tenant in tenants:
            tenant_list.append({
                "id": tenant.id,
                "tenant_id": tenant.tenant_id,
                "tenant_name": tenant.tenant_name,
                "description": tenant.description,
                "is_active": tenant.is_active,
                "created_at": tenant.created_at,
                "updated_at": tenant.updated_at
            })
        
        return BaseResponse(
            message="Tenants retrieved successfully",
            data=tenant_list
        )
        
    except Exception as e:
        logger.error(f"Error listing tenants: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/tenants/{tenant_id}", response_model=BaseResponse)
async def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get tenant information"""
    try:
        # Check access permissions
        user_tenant_id = current_user.get("tenant_id")
        if user_tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to tenant information"
            )
        
        tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        return BaseResponse(
            message="Tenant information retrieved",
            data={
                "id": tenant.id,
                "tenant_id": tenant.tenant_id,
                "tenant_name": tenant.tenant_name,
                "description": tenant.description,
                "settings": tenant.settings,
                "is_active": tenant.is_active,
                "created_at": tenant.created_at,
                "updated_at": tenant.updated_at
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tenant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.put("/tenants/{tenant_id}", response_model=BaseResponse)
async def update_tenant(
    tenant_id: str,
    tenant_data: TenantUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update tenant information"""
    try:
        # Check access permissions
        user_tenant_id = current_user.get("tenant_id")
        if user_tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to update tenant"
            )
        
        tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Update fields
        if tenant_data.tenant_name is not None:
            tenant.tenant_name = tenant_data.tenant_name
        if tenant_data.description is not None:
            tenant.description = tenant_data.description
        if tenant_data.settings is not None:
            tenant.settings = tenant_data.settings
        if tenant_data.is_active is not None:
            tenant.is_active = tenant_data.is_active
        
        tenant.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(tenant)
        
        logger.info(f"Tenant updated: {tenant_id}")
        
        return BaseResponse(
            message="Tenant updated successfully",
            data={
                "id": tenant.id,
                "tenant_id": tenant.tenant_id,
                "tenant_name": tenant.tenant_name,
                "description": tenant.description,
                "settings": tenant.settings,
                "is_active": tenant.is_active,
                "updated_at": tenant.updated_at
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tenant: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/tenants/{tenant_id}/settings", response_model=BaseResponse)
async def get_tenant_settings(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get tenant-specific settings"""
    try:
        # Check access permissions
        user_tenant_id = current_user.get("tenant_id")
        if user_tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to tenant settings"
            )
        
        tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        return BaseResponse(
            message="Tenant settings retrieved",
            data=tenant.settings or {}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tenant settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Incluir rotas de empresas se disponíveis
try:
    from empresa_routes import router as empresa_router
    app.include_router(empresa_router, tags=["empresas"])
    logger.info("Rotas de empresas incluídas com sucesso")
except ImportError as e:
    logger.warning(f"Rotas de empresas não disponíveis: {e}")
except Exception as e:
    logger.error(f"Erro ao incluir rotas de empresas: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
