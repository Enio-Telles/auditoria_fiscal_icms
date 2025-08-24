"""
Authentication Service
Handles user authentication, registration, and JWT token management
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime, timedelta
from typing import Optional
from contextlib import asynccontextmanager
import sys
import os

# Add the microservices directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
microservices_dir = os.path.dirname(current_dir)
sys.path.insert(0, microservices_dir)

from shared.database import Base, get_db, db_config
from shared.auth import AuthManager, get_current_user
from shared.models import BaseResponse, ErrorResponse, UserInfo
from shared.logging_config import setup_logger
from pydantic import BaseModel, EmailStr

# Initialize logger
logger = setup_logger("auth-service")

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    tenant_id = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    tenant_id: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize on startup"""
    engine = db_config.initialize()
    Base.metadata.create_all(bind=engine)
    logger.info("Authentication service started")
    yield
    # Cleanup code (if needed) would go here

# FastAPI App
app = FastAPI(
    title="Authentication Service",
    description="User authentication and JWT token management",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return BaseResponse(message="Authentication service is healthy")

@app.post("/register", response_model=BaseResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == user_data.username) | (User.email == user_data.email)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )
        
        # Create new user
        hashed_password = AuthManager.get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            tenant_id=user_data.tenant_id
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"New user registered: {user_data.username}")
        
        return BaseResponse(
            message="User registered successfully",
            data={
                "user_id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "tenant_id": new_user.tenant_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/login", response_model=BaseResponse)
async def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token"""
    try:
        # Find user
        user = db.query(User).filter(User.username == user_data.username).first()
        
        if not user or not AuthManager.verify_password(user_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        # Create access token
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "tenant_id": user.tenant_id
        }
        
        access_token = AuthManager.create_access_token(data=token_data)
        
        logger.info(f"User logged in: {user.username}")
        
        return BaseResponse(
            message="Login successful",
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 1800,
                "user_info": {
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "tenant_id": user.tenant_id
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/me", response_model=BaseResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user information"""
    try:
        user = db.query(User).filter(User.id == int(current_user["sub"])).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return BaseResponse(
            message="User information retrieved",
            data={
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "tenant_id": user.tenant_id,
                "is_active": user.is_active,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/validate-token", response_model=BaseResponse)
async def validate_token(current_user: dict = Depends(get_current_user)):
    """Validate JWT token"""
    return BaseResponse(
        message="Token is valid",
        data=current_user
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
