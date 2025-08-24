"""
Common models and schemas for microservices
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime

class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class UserInfo(BaseModel):
    """User information model"""
    user_id: str
    username: str
    email: str
    tenant_id: str
    permissions: Optional[Dict[str, Any]] = None

class TenantInfo(BaseModel):
    """Tenant information model"""
    tenant_id: str
    tenant_name: str
    settings: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
