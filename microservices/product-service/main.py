"""
Product Service
Manages product CRUD operations with multi-tenant isolation
"""

# Standard Library Imports
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

# Third-party Imports
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Session

# Add the microservices directory to Python path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
microservices_dir = os.path.dirname(current_dir)
sys.path.insert(0, microservices_dir)

# Local Application Imports
from shared.auth import get_current_tenant, get_current_user  # noqa: E402
from shared.database import Base, db_config, get_db  # noqa: E402
from shared.logging_config import setup_logger  # noqa: E402
from shared.models import BaseResponse  # noqa: E402

# Initialize logger
logger = setup_logger("product-service")


# Database Models
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    codigo_produto = Column(String, nullable=False)
    descricao = Column(Text, nullable=False)
    ncm = Column(String)
    cest = Column(String)
    unidade = Column(String)
    valor_unitario = Column(Float)
    categoria_fiscal = Column(String)
    classificacao_ia = Column(String)
    confianca_classificacao = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic Models
class ProductCreate(BaseModel):
    codigo_produto: str
    descricao: str
    ncm: Optional[str] = None
    cest: Optional[str] = None
    unidade: Optional[str] = None
    valor_unitario: Optional[float] = None
    categoria_fiscal: Optional[str] = None


class ProductUpdate(BaseModel):
    codigo_produto: Optional[str] = None
    descricao: Optional[str] = None
    ncm: Optional[str] = None
    cest: Optional[str] = None
    unidade: Optional[str] = None
    valor_unitario: Optional[float] = None
    categoria_fiscal: Optional[str] = None
    classificacao_ia: Optional[str] = None
    confianca_classificacao: Optional[float] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: int
    tenant_id: str
    codigo_produto: str
    descricao: str
    ncm: Optional[str]
    cest: Optional[str]
    unidade: Optional[str]
    valor_unitario: Optional[float]
    categoria_fiscal: Optional[str]
    classificacao_ia: Optional[str]
    confianca_classificacao: Optional[float]
    is_active: bool
    created_at: datetime
    updated_at: datetime


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize on startup"""
    engine = db_config.initialize()
    Base.metadata.create_all(bind=engine)
    logger.info("Product service started")
    yield
    # Cleanup code (if needed) would go here


# FastAPI App
app = FastAPI(
    title="Product Service",
    description="Product management with multi-tenant isolation",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    return BaseResponse(message="Product service is healthy")


@app.post("/products", response_model=BaseResponse)
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """Create a new product"""
    try:
        # Check if product code already exists for this tenant
        existing_product = (
            db.query(Product)
            .filter(
                Product.tenant_id == tenant_id,
                Product.codigo_produto == product_data.codigo_produto,
            )
            .first()
        )

        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product code already exists for this tenant",
            )

        # Create new product
        new_product = Product(
            tenant_id=tenant_id,
            codigo_produto=product_data.codigo_produto,
            descricao=product_data.descricao,
            ncm=product_data.ncm,
            cest=product_data.cest,
            unidade=product_data.unidade,
            valor_unitario=product_data.valor_unitario,
            categoria_fiscal=product_data.categoria_fiscal,
        )

        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        logger.info(
            f"Product created: {product_data.codigo_produto} for tenant {tenant_id}"
        )

        return BaseResponse(
            message="Product created successfully",
            data={
                "id": new_product.id,
                "codigo_produto": new_product.codigo_produto,
                "descricao": new_product.descricao,
                "tenant_id": new_product.tenant_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@app.get("/products", response_model=BaseResponse)
async def list_products(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """List products for current tenant"""
    try:
        query = db.query(Product).filter(Product.tenant_id == tenant_id)

        if search:
            query = query.filter(
                (Product.descricao.ilike(f"%{search}%"))
                | (Product.codigo_produto.ilike(f"%{search}%"))
                | (Product.ncm.ilike(f"%{search}%"))
            )

        total = query.count()
        products = query.offset(skip).limit(limit).all()

        product_list = []
        for product in products:
            product_list.append(
                {
                    "id": product.id,
                    "codigo_produto": product.codigo_produto,
                    "descricao": product.descricao,
                    "ncm": product.ncm,
                    "cest": product.cest,
                    "unidade": product.unidade,
                    "valor_unitario": product.valor_unitario,
                    "categoria_fiscal": product.categoria_fiscal,
                    "classificacao_ia": product.classificacao_ia,
                    "confianca_classificacao": product.confianca_classificacao,
                    "is_active": product.is_active,
                    "created_at": product.created_at,
                    "updated_at": product.updated_at,
                }
            )

        return BaseResponse(
            message="Products retrieved successfully",
            data={
                "products": product_list,
                "total": total,
                "skip": skip,
                "limit": limit,
            },
        )

    except Exception as e:
        logger.error(f"Error listing products: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@app.get("/products/{product_id}", response_model=BaseResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """Get specific product"""
    try:
        product = (
            db.query(Product)
            .filter(Product.id == product_id, Product.tenant_id == tenant_id)
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )

        return BaseResponse(
            message="Product retrieved successfully",
            data={
                "id": product.id,
                "codigo_produto": product.codigo_produto,
                "descricao": product.descricao,
                "ncm": product.ncm,
                "cest": product.cest,
                "unidade": product.unidade,
                "valor_unitario": product.valor_unitario,
                "categoria_fiscal": product.categoria_fiscal,
                "classificacao_ia": product.classificacao_ia,
                "confianca_classificacao": product.confianca_classificacao,
                "is_active": product.is_active,
                "created_at": product.created_at,
                "updated_at": product.updated_at,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@app.put("/products/{product_id}", response_model=BaseResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """Update product"""
    try:
        product = (
            db.query(Product)
            .filter(Product.id == product_id, Product.tenant_id == tenant_id)
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )

        # Update fields
        if product_data.codigo_produto is not None:
            product.codigo_produto = product_data.codigo_produto
        if product_data.descricao is not None:
            product.descricao = product_data.descricao
        if product_data.ncm is not None:
            product.ncm = product_data.ncm
        if product_data.cest is not None:
            product.cest = product_data.cest
        if product_data.unidade is not None:
            product.unidade = product_data.unidade
        if product_data.valor_unitario is not None:
            product.valor_unitario = product_data.valor_unitario
        if product_data.categoria_fiscal is not None:
            product.categoria_fiscal = product_data.categoria_fiscal
        if product_data.classificacao_ia is not None:
            product.classificacao_ia = product_data.classificacao_ia
        if product_data.confianca_classificacao is not None:
            product.confianca_classificacao = product_data.confianca_classificacao
        if product_data.is_active is not None:
            product.is_active = product_data.is_active

        product.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(product)

        logger.info(f"Product updated: {product.codigo_produto} for tenant {tenant_id}")

        return BaseResponse(
            message="Product updated successfully",
            data={
                "id": product.id,
                "codigo_produto": product.codigo_produto,
                "descricao": product.descricao,
                "updated_at": product.updated_at,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@app.delete("/products/{product_id}", response_model=BaseResponse)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """Delete product (soft delete)"""
    try:
        product = (
            db.query(Product)
            .filter(Product.id == product_id, Product.tenant_id == tenant_id)
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )

        # Soft delete
        product.is_active = False
        product.updated_at = datetime.utcnow()

        db.commit()

        logger.info(f"Product deleted: {product.codigo_produto} for tenant {tenant_id}")

        return BaseResponse(
            message="Product deleted successfully",
            data={"id": product.id, "codigo_produto": product.codigo_produto},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@app.get("/products/statistics/summary", response_model=BaseResponse)
async def get_product_statistics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """Get product statistics for tenant"""
    try:
        total_products = (
            db.query(Product).filter(Product.tenant_id == tenant_id).count()
        )
        active_products = (
            db.query(Product)
            .filter(Product.tenant_id == tenant_id, Product.is_active)
            .count()
        )
        classified_products = (
            db.query(Product)
            .filter(
                Product.tenant_id == tenant_id, Product.classificacao_ia.isnot(None)
            )
            .count()
        )

        return BaseResponse(
            message="Product statistics retrieved",
            data={
                "total_products": total_products,
                "active_products": active_products,
                "inactive_products": total_products - active_products,
                "classified_products": classified_products,
                "unclassified_products": total_products - classified_products,
                "classification_percentage": (
                    (classified_products / total_products * 100)
                    if total_products > 0
                    else 0
                ),
            },
        )

    except Exception as e:
        logger.error(f"Error getting product statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
