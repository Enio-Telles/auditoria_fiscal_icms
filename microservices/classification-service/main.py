"""
Classification Service
AI-powered product classification using multiple LLM providers
"""
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import sys
import os
import httpx
import json

# Add the microservices directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
microservices_dir = os.path.dirname(current_dir)
sys.path.insert(0, microservices_dir)

from shared.database import Base, get_db, db_config
from shared.auth import get_current_user, get_current_tenant
from shared.models import BaseResponse, ErrorResponse
from shared.logging_config import setup_logger
from pydantic import BaseModel

# Initialize logger
logger = setup_logger("classification-service")

# Database Models
class ClassificationHistory(Base):
    __tablename__ = "classification_history"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    product_id = Column(Integer, nullable=False)
    descricao_produto = Column(Text, nullable=False)
    estrategia_usada = Column(String, nullable=False)
    classificacao_resultado = Column(String)
    confianca = Column(Float)
    tempo_processamento = Column(Float)
    detalhes_classificacao = Column(JSON)
    status = Column(String, default="completed")
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Models
class ClassificationRequest(BaseModel):
    product_id: int
    descricao: str
    estrategia: Optional[str] = "auto"  # auto, openai, ollama, anthropic, ensemble

class ClassificationBatchRequest(BaseModel):
    products: List[Dict[str, Any]]
    estrategia: Optional[str] = "auto"

class ClassificationResponse(BaseModel):
    product_id: int
    classificacao: str
    confianca: float
    estrategia_usada: str
    tempo_processamento: float
    detalhes: Optional[Dict[str, Any]] = None

# Classification strategies
CLASSIFICATION_STRATEGIES = {
    "openai": "OpenAI GPT-4",
    "ollama": "Ollama Local Models",
    "anthropic": "Anthropic Claude",
    "ensemble": "Ensemble of Multiple Models",
    "auto": "Automatic Best Strategy Selection"
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    engine = db_config.initialize()
    Base.metadata.create_all(bind=engine)
    logger.info("Classification service started")
    yield
    # Cleanup code (if needed) would go here
    logger.info("Classification service shutting down")

# FastAPI App
app = FastAPI(
    title="Classification Service",
    description="AI-powered product classification with multiple LLM providers",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return BaseResponse(message="Classification service is healthy")

@app.get("/strategies", response_model=BaseResponse)
async def get_available_strategies():
    """Get available classification strategies"""
    return BaseResponse(
        message="Available classification strategies",
        data=CLASSIFICATION_STRATEGIES
    )

@app.post("/classify", response_model=BaseResponse)
async def classify_product(
    request: ClassificationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Classify a single product"""
    try:
        start_time = datetime.utcnow()
        
        # Get product details from product service
        product_info = await get_product_details(request.product_id, tenant_id)
        if not product_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Perform classification
        classification_result = await perform_classification(
            request.descricao,
            request.estrategia,
            tenant_id
        )
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Save classification history
        history_record = ClassificationHistory(
            tenant_id=tenant_id,
            product_id=request.product_id,
            descricao_produto=request.descricao,
            estrategia_usada=classification_result["strategy"],
            classificacao_resultado=classification_result["classification"],
            confianca=classification_result["confidence"],
            tempo_processamento=processing_time,
            detalhes_classificacao=classification_result.get("details", {}),
            status="completed"
        )
        
        db.add(history_record)
        db.commit()
        
        # Update product with classification
        await update_product_classification(
            request.product_id,
            classification_result["classification"],
            classification_result["confidence"],
            tenant_id
        )
        
        logger.info(f"Product {request.product_id} classified as {classification_result['classification']} for tenant {tenant_id}")
        
        return BaseResponse(
            message="Product classified successfully",
            data={
                "product_id": request.product_id,
                "classificacao": classification_result["classification"],
                "confianca": classification_result["confidence"],
                "estrategia_usada": classification_result["strategy"],
                "tempo_processamento": processing_time,
                "detalhes": classification_result.get("details", {})
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error classifying product: {str(e)}")
        # Save error in history
        history_record = ClassificationHistory(
            tenant_id=tenant_id,
            product_id=request.product_id,
            descricao_produto=request.descricao,
            estrategia_usada=request.estrategia,
            status="error",
            detalhes_classificacao={"error": str(e)}
        )
        db.add(history_record)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Classification error"
        )

@app.post("/classify/batch", response_model=BaseResponse)
async def classify_products_batch(
    request: ClassificationBatchRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Classify multiple products in batch"""
    try:
        results = []
        
        for product_data in request.products:
            try:
                start_time = datetime.utcnow()
                
                # Perform classification
                classification_result = await perform_classification(
                    product_data["descricao"],
                    request.estrategia,
                    tenant_id
                )
                
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Save classification history
                history_record = ClassificationHistory(
                    tenant_id=tenant_id,
                    product_id=product_data["product_id"],
                    descricao_produto=product_data["descricao"],
                    estrategia_usada=classification_result["strategy"],
                    classificacao_resultado=classification_result["classification"],
                    confianca=classification_result["confidence"],
                    tempo_processamento=processing_time,
                    detalhes_classificacao=classification_result.get("details", {}),
                    status="completed"
                )
                
                db.add(history_record)
                
                # Update product
                await update_product_classification(
                    product_data["product_id"],
                    classification_result["classification"],
                    classification_result["confidence"],
                    tenant_id
                )
                
                results.append({
                    "product_id": product_data["product_id"],
                    "classificacao": classification_result["classification"],
                    "confianca": classification_result["confidence"],
                    "estrategia_usada": classification_result["strategy"],
                    "status": "success"
                })
                
            except Exception as e:
                logger.error(f"Error classifying product {product_data['product_id']}: {str(e)}")
                results.append({
                    "product_id": product_data["product_id"],
                    "status": "error",
                    "error": str(e)
                })
        
        db.commit()
        
        successful = len([r for r in results if r.get("status") == "success"])
        failed = len(results) - successful
        
        return BaseResponse(
            message=f"Batch classification completed: {successful} successful, {failed} failed",
            data={
                "results": results,
                "summary": {
                    "total": len(results),
                    "successful": successful,
                    "failed": failed
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error in batch classification: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch classification error"
        )

@app.get("/history", response_model=BaseResponse)
async def get_classification_history(
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Get classification history for tenant"""
    try:
        query = db.query(ClassificationHistory).filter(
            ClassificationHistory.tenant_id == tenant_id
        )
        
        if product_id:
            query = query.filter(ClassificationHistory.product_id == product_id)
        
        total = query.count()
        history = query.order_by(ClassificationHistory.created_at.desc()).offset(skip).limit(limit).all()
        
        history_list = []
        for record in history:
            history_list.append({
                "id": record.id,
                "product_id": record.product_id,
                "descricao_produto": record.descricao_produto,
                "estrategia_usada": record.estrategia_usada,
                "classificacao_resultado": record.classificacao_resultado,
                "confianca": record.confianca,
                "tempo_processamento": record.tempo_processamento,
                "status": record.status,
                "created_at": record.created_at
            })
        
        return BaseResponse(
            message="Classification history retrieved",
            data={
                "history": history_list,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting classification history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/statistics", response_model=BaseResponse)
async def get_classification_statistics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Get classification statistics for tenant"""
    try:
        total_classifications = db.query(ClassificationHistory).filter(
            ClassificationHistory.tenant_id == tenant_id
        ).count()
        
        successful_classifications = db.query(ClassificationHistory).filter(
            ClassificationHistory.tenant_id == tenant_id,
            ClassificationHistory.status == "completed"
        ).count()
        
        # Strategy usage statistics
        strategy_stats = {}
        strategies = db.query(ClassificationHistory.estrategia_usada).filter(
            ClassificationHistory.tenant_id == tenant_id
        ).distinct().all()
        
        for strategy in strategies:
            count = db.query(ClassificationHistory).filter(
                ClassificationHistory.tenant_id == tenant_id,
                ClassificationHistory.estrategia_usada == strategy[0]
            ).count()
            strategy_stats[strategy[0]] = count
        
        # Average confidence
        avg_confidence = db.query(ClassificationHistory.confianca).filter(
            ClassificationHistory.tenant_id == tenant_id,
            ClassificationHistory.status == "completed"
        ).all()
        
        average_confidence = sum([c[0] for c in avg_confidence if c[0]]) / len(avg_confidence) if avg_confidence else 0
        
        return BaseResponse(
            message="Classification statistics retrieved",
            data={
                "total_classifications": total_classifications,
                "successful_classifications": successful_classifications,
                "failed_classifications": total_classifications - successful_classifications,
                "success_rate": (successful_classifications / total_classifications * 100) if total_classifications > 0 else 0,
                "average_confidence": round(average_confidence, 2),
                "strategy_usage": strategy_stats
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting classification statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

async def perform_classification(descricao: str, estrategia: str, tenant_id: str) -> Dict[str, Any]:
    """Perform product classification using specified strategy"""
    
    # Mock classification logic - replace with actual AI implementation
    classificacoes_mock = [
        "PRODUTO_ALIMENTICIO",
        "PRODUTO_ELETRONICO",
        "PRODUTO_TEXTIL",
        "PRODUTO_FARMACEUTICO",
        "PRODUTO_COSMETICO",
        "PRODUTO_INDUSTRIAL",
        "PRODUTO_AUTOMOTIVO",
        "PRODUTO_CONSTRUCAO"
    ]
    
    # Simple mock classification based on keywords
    descricao_lower = descricao.lower()
    
    if any(word in descricao_lower for word in ['alimento', 'comida', 'bebida', 'leite', 'carne']):
        classificacao = "PRODUTO_ALIMENTICIO"
        confianca = 0.95
    elif any(word in descricao_lower for word in ['eletronico', 'computador', 'celular', 'tv']):
        classificacao = "PRODUTO_ELETRONICO"
        confianca = 0.90
    elif any(word in descricao_lower for word in ['roupa', 'camisa', 'calca', 'tecido']):
        classificacao = "PRODUTO_TEXTIL"
        confianca = 0.85
    elif any(word in descricao_lower for word in ['remedio', 'medicamento', 'farmacia']):
        classificacao = "PRODUTO_FARMACEUTICO"
        confianca = 0.93
    else:
        classificacao = "PRODUTO_INDUSTRIAL"
        confianca = 0.70
    
    return {
        "classification": classificacao,
        "confidence": confianca,
        "strategy": estrategia if estrategia != "auto" else "mock_ai",
        "details": {
            "keywords_found": [word for word in ['alimento', 'eletronico', 'roupa', 'remedio'] if word in descricao_lower],
            "description_length": len(descricao),
            "model_version": "mock_v1.0"
        }
    }

async def get_product_details(product_id: int, tenant_id: str) -> Optional[Dict[str, Any]]:
    """Get product details from product service"""
    try:
        # Mock product service call - replace with actual HTTP call
        return {
            "id": product_id,
            "tenant_id": tenant_id,
            "exists": True
        }
    except Exception as e:
        logger.error(f"Error getting product details: {str(e)}")
        return None

async def update_product_classification(product_id: int, classificacao: str, confianca: float, tenant_id: str):
    """Update product with classification results"""
    try:
        # Mock product service update - replace with actual HTTP call
        logger.info(f"Product {product_id} classification updated: {classificacao} (confidence: {confianca})")
        return True
    except Exception as e:
        logger.error(f"Error updating product classification: {str(e)}")
        return False

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
