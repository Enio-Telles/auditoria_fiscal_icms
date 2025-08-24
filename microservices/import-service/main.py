"""
Import Service
Handles data import and processing from Excel/CSV files
"""
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from contextlib import asynccontextmanager
import sys
import os
import pandas as pd
import json
import io
import uuid

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
logger = setup_logger("import-service")

# Database Models
class ImportJob(Base):
    __tablename__ = "import_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    job_id = Column(String, unique=True, nullable=False)
    filename = Column(String, nullable=False)
    file_size = Column(Integer)
    total_rows = Column(Integer)
    processed_rows = Column(Integer, default=0)
    successful_rows = Column(Integer, default=0)
    failed_rows = Column(Integer, default=0)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    error_log = Column(JSON)
    import_settings = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

class ImportError(Base):
    __tablename__ = "import_errors"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    error_type = Column(String, nullable=False)
    error_message = Column(Text, nullable=False)
    row_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Models
class ImportSettings(BaseModel):
    sheet_name: Optional[str] = None
    header_row: Optional[int] = 0
    skip_rows: Optional[int] = 0
    column_mapping: Optional[Dict[str, str]] = None
    validate_ncm: Optional[bool] = True
    auto_classify: Optional[bool] = False

class ImportJobResponse(BaseModel):
    id: int
    job_id: str
    filename: str
    total_rows: Optional[int]
    processed_rows: int
    successful_rows: int
    failed_rows: int
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize on startup"""
    engine = db_config.initialize()
    Base.metadata.create_all(bind=engine)
    logger.info("Import service started")
    yield
    # Cleanup code (if needed) would go here

# FastAPI App
app = FastAPI(
    title="Import Service",
    description="Data import and processing from Excel/CSV files",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return BaseResponse(message="Import service is healthy")

@app.post("/upload", response_model=BaseResponse)
async def upload_file(
    file: UploadFile = File(...),
    settings: str = Form("{}"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Upload and process data file"""
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only Excel (.xlsx, .xls) and CSV files are supported"
            )
        
        # Parse import settings
        try:
            import_settings = json.loads(settings)
        except json.JSONDecodeError:
            import_settings = {}
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Create import job record
        import_job = ImportJob(
            tenant_id=tenant_id,
            job_id=job_id,
            filename=file.filename,
            file_size=file_size,
            import_settings=import_settings,
            status="pending"
        )
        
        db.add(import_job)
        db.commit()
        db.refresh(import_job)
        
        # Process file
        try:
            # Read data based on file type
            if file.filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(content))
            else:
                sheet_name = import_settings.get('sheet_name', 0)
                df = pd.read_excel(io.BytesIO(content), sheet_name=sheet_name)
            
            # Apply settings
            header_row = import_settings.get('header_row', 0)
            skip_rows = import_settings.get('skip_rows', 0)
            
            if skip_rows > 0:
                df = df.iloc[skip_rows:]
            
            total_rows = len(df)
            
            # Update job with total rows
            import_job.total_rows = total_rows
            import_job.status = "processing"
            db.commit()
            
            # Process data
            results = await process_import_data(df, import_job, import_settings, tenant_id, db)
            
            # Update job status
            import_job.processed_rows = results["processed"]
            import_job.successful_rows = results["successful"]
            import_job.failed_rows = results["failed"]
            import_job.status = "completed" if results["failed"] == 0 else "completed_with_errors"
            import_job.completed_at = datetime.utcnow()
            import_job.error_log = results.get("error_summary", {})
            
            db.commit()
            
            logger.info(f"Import job {job_id} completed: {results['successful']} successful, {results['failed']} failed")
            
            return BaseResponse(
                message="File imported successfully",
                data={
                    "job_id": job_id,
                    "filename": file.filename,
                    "total_rows": total_rows,
                    "processed_rows": results["processed"],
                    "successful_rows": results["successful"],
                    "failed_rows": results["failed"],
                    "status": import_job.status
                }
            )
            
        except Exception as processing_error:
            # Update job status to failed
            import_job.status = "failed"
            import_job.error_log = {"error": str(processing_error)}
            db.commit()
            
            logger.error(f"Import job {job_id} failed: {str(processing_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File processing failed: {str(processing_error)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload error"
        )

@app.get("/jobs", response_model=BaseResponse)
async def list_import_jobs(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """List import jobs for tenant"""
    try:
        query = db.query(ImportJob).filter(ImportJob.tenant_id == tenant_id)
        
        if status_filter:
            query = query.filter(ImportJob.status == status_filter)
        
        total = query.count()
        jobs = query.order_by(ImportJob.created_at.desc()).offset(skip).limit(limit).all()
        
        job_list = []
        for job in jobs:
            job_list.append({
                "id": job.id,
                "job_id": job.job_id,
                "filename": job.filename,
                "file_size": job.file_size,
                "total_rows": job.total_rows,
                "processed_rows": job.processed_rows,
                "successful_rows": job.successful_rows,
                "failed_rows": job.failed_rows,
                "status": job.status,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
                "completed_at": job.completed_at
            })
        
        return BaseResponse(
            message="Import jobs retrieved successfully",
            data={
                "jobs": job_list,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
        
    except Exception as e:
        logger.error(f"Error listing import jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/jobs/{job_id}", response_model=BaseResponse)
async def get_import_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Get specific import job details"""
    try:
        job = db.query(ImportJob).filter(
            ImportJob.job_id == job_id,
            ImportJob.tenant_id == tenant_id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import job not found"
            )
        
        return BaseResponse(
            message="Import job details retrieved",
            data={
                "id": job.id,
                "job_id": job.job_id,
                "filename": job.filename,
                "file_size": job.file_size,
                "total_rows": job.total_rows,
                "processed_rows": job.processed_rows,
                "successful_rows": job.successful_rows,
                "failed_rows": job.failed_rows,
                "status": job.status,
                "import_settings": job.import_settings,
                "error_log": job.error_log,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
                "completed_at": job.completed_at
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting import job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/jobs/{job_id}/errors", response_model=BaseResponse)
async def get_import_errors(
    job_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Get import errors for specific job"""
    try:
        # Verify job belongs to tenant
        job = db.query(ImportJob).filter(
            ImportJob.job_id == job_id,
            ImportJob.tenant_id == tenant_id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import job not found"
            )
        
        query = db.query(ImportError).filter(ImportError.job_id == job_id)
        total = query.count()
        errors = query.order_by(ImportError.row_number).offset(skip).limit(limit).all()
        
        error_list = []
        for error in errors:
            error_list.append({
                "id": error.id,
                "row_number": error.row_number,
                "error_type": error.error_type,
                "error_message": error.error_message,
                "row_data": error.row_data,
                "created_at": error.created_at
            })
        
        return BaseResponse(
            message="Import errors retrieved",
            data={
                "errors": error_list,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting import errors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/statistics", response_model=BaseResponse)
async def get_import_statistics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Get import statistics for tenant"""
    try:
        total_jobs = db.query(ImportJob).filter(ImportJob.tenant_id == tenant_id).count()
        
        completed_jobs = db.query(ImportJob).filter(
            ImportJob.tenant_id == tenant_id,
            ImportJob.status.in_(["completed", "completed_with_errors"])
        ).count()
        
        failed_jobs = db.query(ImportJob).filter(
            ImportJob.tenant_id == tenant_id,
            ImportJob.status == "failed"
        ).count()
        
        # Total rows processed
        total_rows_query = db.query(ImportJob.processed_rows).filter(
            ImportJob.tenant_id == tenant_id
        ).all()
        
        total_rows_processed = sum([r[0] for r in total_rows_query if r[0]])
        
        return BaseResponse(
            message="Import statistics retrieved",
            data={
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "pending_jobs": total_jobs - completed_jobs - failed_jobs,
                "success_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
                "total_rows_processed": total_rows_processed
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting import statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

async def process_import_data(
    df: pd.DataFrame, 
    import_job: ImportJob, 
    settings: Dict[str, Any], 
    tenant_id: str, 
    db: Session
) -> Dict[str, Any]:
    """Process imported data and create products"""
    
    processed = 0
    successful = 0
    failed = 0
    errors = []
    
    # Column mapping
    column_mapping = settings.get('column_mapping', {})
    
    # Expected columns with defaults
    expected_columns = {
        'codigo_produto': ['codigo', 'codigo_produto', 'product_code'],
        'descricao': ['descricao', 'description', 'produto'],
        'ncm': ['ncm', 'codigo_ncm'],
        'cest': ['cest', 'codigo_cest'],
        'unidade': ['unidade', 'unit', 'un'],
        'valor_unitario': ['valor', 'preco', 'price', 'valor_unitario']
    }
    
    # Map columns
    mapped_columns = {}
    for expected_col, possible_names in expected_columns.items():
        mapped_col = column_mapping.get(expected_col)
        if mapped_col and mapped_col in df.columns:
            mapped_columns[expected_col] = mapped_col
        else:
            # Try to find column automatically
            for possible_name in possible_names:
                matching_cols = [col for col in df.columns if possible_name.lower() in col.lower()]
                if matching_cols:
                    mapped_columns[expected_col] = matching_cols[0]
                    break
    
    for index, row in df.iterrows():
        try:
            processed += 1
            
            # Extract product data
            product_data = {}
            
            # Required fields
            if 'codigo_produto' in mapped_columns:
                product_data['codigo_produto'] = str(row[mapped_columns['codigo_produto']])
            else:
                raise ValueError("Código do produto não encontrado")
            
            if 'descricao' in mapped_columns:
                product_data['descricao'] = str(row[mapped_columns['descricao']])
            else:
                raise ValueError("Descrição não encontrada")
            
            # Optional fields
            for field in ['ncm', 'cest', 'unidade']:
                if field in mapped_columns and pd.notna(row[mapped_columns[field]]):
                    product_data[field] = str(row[mapped_columns[field]])
            
            # Numeric fields
            if 'valor_unitario' in mapped_columns and pd.notna(row[mapped_columns['valor_unitario']]):
                try:
                    product_data['valor_unitario'] = float(row[mapped_columns['valor_unitario']])
                except (ValueError, TypeError):
                    pass
            
            # Validate data
            if not product_data.get('codigo_produto') or not product_data.get('descricao'):
                raise ValueError("Código e descrição são obrigatórios")
            
            # Create product via product service (mock implementation)
            success = await create_product_via_service(product_data, tenant_id)
            
            if success:
                successful += 1
            else:
                failed += 1
                error_record = ImportError(
                    job_id=import_job.job_id,
                    row_number=index + 1,
                    error_type="creation_failed",
                    error_message="Falha ao criar produto",
                    row_data=product_data
                )
                db.add(error_record)
                
        except Exception as e:
            failed += 1
            error_record = ImportError(
                job_id=import_job.job_id,
                row_number=index + 1,
                error_type="validation_error",
                error_message=str(e),
                row_data=row.to_dict()
            )
            db.add(error_record)
            errors.append({
                "row": index + 1,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "processed": processed,
        "successful": successful,
        "failed": failed,
        "error_summary": {
            "total_errors": len(errors),
            "sample_errors": errors[:10]  # First 10 errors as sample
        }
    }

async def create_product_via_service(product_data: Dict[str, Any], tenant_id: str) -> bool:
    """Create product via product service (mock implementation)"""
    try:
        # Mock implementation - in real scenario, make HTTP call to product service
        logger.info(f"Creating product: {product_data['codigo_produto']} for tenant {tenant_id}")
        return True
    except Exception as e:
        logger.error(f"Error creating product via service: {str(e)}")
        return False

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
