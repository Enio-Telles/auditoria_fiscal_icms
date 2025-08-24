"""
AI Service
LLM integration service with Ollama, OpenAI, and Anthropic support
"""

# Standard Library Imports
import json
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

# Third-party Imports
import httpx
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text
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
logger = setup_logger("ai-service")


# Database Models
class AIInteraction(Base):
    __tablename__ = "ai_interactions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    interaction_id = Column(String, unique=True, nullable=False)
    provider = Column(String, nullable=False)  # ollama, openai, anthropic
    model = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text)
    tokens_used = Column(Integer)
    processing_time = Column(Float)
    cost = Column(Float)
    status = Column(String, default="completed")  # pending, completed, failed
    error_message = Column(Text)
    interaction_metadata = Column(
        JSON
    )  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    created_at = Column(DateTime, default=datetime.utcnow)


# Pydantic Models
class AIRequest(BaseModel):
    prompt: str
    provider: Optional[str] = "auto"  # auto, ollama, openai, anthropic
    model: Optional[str] = None
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    system_prompt: Optional[str] = None


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    provider: Optional[str] = "auto"
    model: Optional[str] = None
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7


class ClassificationAIRequest(BaseModel):
    product_description: str
    context: Optional[str] = None
    provider: Optional[str] = "auto"
    model: Optional[str] = None


class RAGRequest(BaseModel):
    query: str
    context_documents: Optional[List[str]] = None
    provider: Optional[str] = "auto"
    model: Optional[str] = None
    max_tokens: Optional[int] = 1500


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize on startup"""
    engine = db_config.initialize()
    Base.metadata.create_all(bind=engine)
    logger.info("AI service started")
    yield
    # Cleanup code (if needed) would go here


# FastAPI App
app = FastAPI(
    title="AI Service",
    description="LLM integration service with multiple provider support",
    version="1.0.0",
    lifespan=lifespan,
)

# AI Provider Configuration
AI_PROVIDERS = {
    "ollama": {
        "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        "models": ["llama3", "mistral", "codellama", "gemma"],
        "default_model": "llama3",
    },
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "models": ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
        "default_model": "gpt-3.5-turbo",
    },
    "anthropic": {
        "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "models": ["claude-3-sonnet", "claude-3-haiku", "claude-instant"],
        "default_model": "claude-3-haiku",
    },
}


@app.get("/health")
async def health_check():
    return BaseResponse(message="AI service is healthy")


@app.get("/providers", response_model=BaseResponse)
async def get_available_providers():
    """Get available AI providers and models"""
    providers_status = {}

    for provider_name, config in AI_PROVIDERS.items():
        try:
            if provider_name == "ollama":
                status = await check_ollama_status(config["base_url"])
            elif provider_name == "openai":
                status = {
                    "available": bool(config["api_key"]),
                    "models": config["models"],
                }
            elif provider_name == "anthropic":
                status = {
                    "available": bool(config["api_key"]),
                    "models": config["models"],
                }
            else:
                status = {"available": False, "models": []}

            providers_status[provider_name] = status

        except Exception as e:
            providers_status[provider_name] = {"available": False, "error": str(e)}

    return BaseResponse(message="AI providers status retrieved", data=providers_status)


@app.post("/generate", response_model=BaseResponse)
async def generate_text(
    request: AIRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """Generate text using specified AI provider"""
    try:
        start_time = datetime.utcnow()
        interaction_id = f"gen_{int(start_time.timestamp())}"

        # Determine provider and model
        provider, model = await select_provider_and_model(
            request.provider, request.model
        )

        # Create interaction record
        interaction = AIInteraction(
            tenant_id=tenant_id,
            interaction_id=interaction_id,
            provider=provider,
            model=model,
            prompt=request.prompt,
            status="pending",
        )

        db.add(interaction)
        db.commit()

        try:
            # Generate response
            response_data = await call_ai_provider(
                provider=provider,
                model=model,
                prompt=request.prompt,
                system_prompt=request.system_prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            # Update interaction
            interaction.response = response_data["text"]
            interaction.tokens_used = response_data.get("tokens_used", 0)
            interaction.processing_time = processing_time
            interaction.cost = response_data.get("cost", 0.0)
            interaction.status = "completed"
            interaction.metadata = response_data.get("metadata", {})

            db.commit()

            logger.info(
                f"Text generated for tenant {tenant_id} using {provider}/{model}"
            )

            return BaseResponse(
                message="Text generated successfully",
                data={
                    "interaction_id": interaction_id,
                    "text": response_data["text"],
                    "provider": provider,
                    "model": model,
                    "tokens_used": response_data.get("tokens_used", 0),
                    "processing_time": processing_time,
                },
            )

        except Exception as ai_error:
            # Update interaction with error
            interaction.status = "failed"
            interaction.error_message = str(ai_error)
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI generation failed: {str(ai_error)}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in text generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Text generation error",
        )


@app.post("/chat", response_model=BaseResponse)
async def chat_completion(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """Chat completion using specified AI provider"""
    try:
        start_time = datetime.utcnow()
        interaction_id = f"chat_{int(start_time.timestamp())}"

        # Determine provider and model
        provider, model = await select_provider_and_model(
            request.provider, request.model
        )

        # Format messages for logging
        messages_text = json.dumps(request.messages, ensure_ascii=False)

        # Create interaction record
        interaction = AIInteraction(
            tenant_id=tenant_id,
            interaction_id=interaction_id,
            provider=provider,
            model=model,
            prompt=messages_text,
            status="pending",
        )

        db.add(interaction)
        db.commit()

        try:
            # Generate chat response
            response_data = await call_chat_provider(
                provider=provider,
                model=model,
                messages=request.messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            # Update interaction
            interaction.response = response_data["text"]
            interaction.tokens_used = response_data.get("tokens_used", 0)
            interaction.processing_time = processing_time
            interaction.cost = response_data.get("cost", 0.0)
            interaction.status = "completed"
            interaction.metadata = response_data.get("metadata", {})

            db.commit()

            logger.info(
                f"Chat completion for tenant {tenant_id} using {provider}/{model}"
            )

            return BaseResponse(
                message="Chat completion successful",
                data={
                    "interaction_id": interaction_id,
                    "message": {"role": "assistant", "content": response_data["text"]},
                    "provider": provider,
                    "model": model,
                    "tokens_used": response_data.get("tokens_used", 0),
                    "processing_time": processing_time,
                },
            )

        except Exception as ai_error:
            # Update interaction with error
            interaction.status = "failed"
            interaction.error_message = str(ai_error)
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Chat completion failed: {str(ai_error)}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat completion error",
        )


@app.post("/classify", response_model=BaseResponse)
async def classify_product_ai(
    request: ClassificationAIRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """AI-powered product classification"""
    try:
        # Classification prompt template
        system_prompt = """
        Você é um especialista em classificação fiscal de produtos para auditoria de ICMS.

        Classifique o produto nas seguintes categorias:
        - PRODUTO_ALIMENTICIO
        - PRODUTO_ELETRONICO
        - PRODUTO_TEXTIL
        - PRODUTO_FARMACEUTICO
        - PRODUTO_COSMETICO
        - PRODUTO_INDUSTRIAL
        - PRODUTO_AUTOMOTIVO
        - PRODUTO_CONSTRUCAO
        - PRODUTO_OUTROS

        Responda apenas com a categoria, sem explicações adicionais.
        """

        user_prompt = f"""
        Produto para classificar: {request.product_description}

        {f"Contexto adicional: {request.context}" if request.context else ""}

        Classificação:
        """

        # Determine provider and model
        provider, model = await select_provider_and_model(
            request.provider, request.model
        )

        # Generate classification
        response_data = await call_ai_provider(
            provider=provider,
            model=model,
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=50,
            temperature=0.1,
        )

        classification = response_data["text"].strip().upper()

        # Validate classification
        valid_categories = [
            "PRODUTO_ALIMENTICIO",
            "PRODUTO_ELETRONICO",
            "PRODUTO_TEXTIL",
            "PRODUTO_FARMACEUTICO",
            "PRODUTO_COSMETICO",
            "PRODUTO_INDUSTRIAL",
            "PRODUTO_AUTOMOTIVO",
            "PRODUTO_CONSTRUCAO",
            "PRODUTO_OUTROS",
        ]

        if classification not in valid_categories:
            classification = "PRODUTO_OUTROS"

        logger.info(f"Product classified as {classification} for tenant {tenant_id}")

        return BaseResponse(
            message="Product classified successfully",
            data={
                "classification": classification,
                "confidence": 0.85,  # Mock confidence
                "provider": provider,
                "model": model,
                "processing_time": response_data.get("processing_time", 0),
            },
        )

    except Exception as e:
        logger.error(f"Error in product classification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Product classification error",
        )


@app.post("/rag", response_model=BaseResponse)
async def rag_query(
    request: RAGRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """RAG (Retrieval-Augmented Generation) query"""
    try:
        # Build context from documents
        context = ""
        if request.context_documents:
            context = "\n\n".join(request.context_documents)

        # RAG prompt template
        system_prompt = """
        Você é um assistente especializado em auditoria fiscal e ICMS.
        Use apenas as informações fornecidas no contexto para responder às perguntas.
        Se a informação não estiver disponível no contexto, diga que não possui essa informação.
        """

        user_prompt = f"""
        Contexto:
        {context}

        Pergunta: {request.query}

        Resposta baseada no contexto:
        """

        # Determine provider and model
        provider, model = await select_provider_and_model(
            request.provider, request.model
        )

        # Generate response
        response_data = await call_ai_provider(
            provider=provider,
            model=model,
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=request.max_tokens,
            temperature=0.3,
        )

        logger.info(f"RAG query processed for tenant {tenant_id}")

        return BaseResponse(
            message="RAG query processed successfully",
            data={
                "query": request.query,
                "response": response_data["text"],
                "provider": provider,
                "model": model,
                "tokens_used": response_data.get("tokens_used", 0),
                "processing_time": response_data.get("processing_time", 0),
            },
        )

    except Exception as e:
        logger.error(f"Error in RAG query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="RAG query error"
        )


@app.get("/interactions", response_model=BaseResponse)
async def get_ai_interactions(
    skip: int = 0,
    limit: int = 100,
    provider: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant),
):
    """Get AI interaction history for tenant"""
    try:
        query = db.query(AIInteraction).filter(AIInteraction.tenant_id == tenant_id)

        if provider:
            query = query.filter(AIInteraction.provider == provider)

        total = query.count()
        interactions = (
            query.order_by(AIInteraction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        interaction_list = []
        for interaction in interactions:
            interaction_list.append(
                {
                    "id": interaction.id,
                    "interaction_id": interaction.interaction_id,
                    "provider": interaction.provider,
                    "model": interaction.model,
                    "prompt": (
                        interaction.prompt[:200] + "..."
                        if len(interaction.prompt) > 200
                        else interaction.prompt
                    ),
                    "tokens_used": interaction.tokens_used,
                    "processing_time": interaction.processing_time,
                    "cost": interaction.cost,
                    "status": interaction.status,
                    "created_at": interaction.created_at,
                }
            )

        return BaseResponse(
            message="AI interactions retrieved",
            data={
                "interactions": interaction_list,
                "total": total,
                "skip": skip,
                "limit": limit,
            },
        )

    except Exception as e:
        logger.error(f"Error getting AI interactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


async def select_provider_and_model(
    provider_request: str, model_request: Optional[str]
) -> tuple:
    """Select best available provider and model"""

    if provider_request == "auto":
        # Auto-select based on availability
        for provider_name in ["ollama", "openai", "anthropic"]:
            config = AI_PROVIDERS[provider_name]
            if provider_name == "ollama":
                if await check_ollama_availability(config["base_url"]):
                    return provider_name, model_request or config["default_model"]
            elif config.get("api_key"):
                return provider_name, model_request or config["default_model"]

        # Fallback to mock
        return "mock", "mock-model"
    else:
        config = AI_PROVIDERS.get(provider_request, {})
        model = model_request or config.get("default_model", "default")
        return provider_request, model


async def call_ai_provider(
    provider: str,
    model: str,
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 1000,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """Call specific AI provider"""

    if provider == "ollama":
        return await call_ollama(model, prompt, system_prompt, max_tokens, temperature)
    elif provider == "openai":
        return await call_openai(model, prompt, system_prompt, max_tokens, temperature)
    elif provider == "anthropic":
        return await call_anthropic(
            model, prompt, system_prompt, max_tokens, temperature
        )
    else:
        # Mock response
        return {
            "text": f"Mock response for: {prompt[:100]}...",
            "tokens_used": len(prompt.split()) + 50,
            "cost": 0.0,
            "processing_time": 0.5,
        }


async def call_chat_provider(
    provider: str,
    model: str,
    messages: List[Dict[str, str]],
    max_tokens: int = 1000,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """Call chat completion provider"""

    # Convert messages to prompt for non-chat models
    prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

    return await call_ai_provider(
        provider, model, prompt, None, max_tokens, temperature
    )


async def check_ollama_status(base_url: str) -> Dict[str, Any]:
    """Check Ollama server status"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return {
                    "available": True,
                    "models": [model["name"] for model in models],
                }
            else:
                return {"available": False, "models": []}
    except Exception:
        return {"available": False, "models": []}


async def check_ollama_availability(base_url: str) -> bool:
    """Check if Ollama is available"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/tags", timeout=3.0)
            return response.status_code == 200
    except Exception:
        return False


async def call_ollama(
    model: str,
    prompt: str,
    system_prompt: Optional[str],
    max_tokens: int,
    temperature: float,
) -> Dict[str, Any]:
    """Call Ollama API"""
    try:
        base_url = AI_PROVIDERS["ollama"]["base_url"]

        payload = {
            "model": model,
            "prompt": prompt,
            "system": system_prompt,
            "options": {"num_predict": max_tokens, "temperature": temperature},
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{base_url}/api/generate", json=payload)

            if response.status_code == 200:
                result = response.json()
                return {
                    "text": result.get("response", ""),
                    "tokens_used": len(prompt.split())
                    + len(result.get("response", "").split()),
                    "cost": 0.0,  # Ollama is free
                    "processing_time": result.get("total_duration", 0)
                    / 1_000_000_000,  # Convert to seconds
                }
            else:
                raise Exception(f"Ollama API error: {response.status_code}")

    except Exception as e:
        logger.error(f"Ollama call failed: {str(e)}")
        raise Exception(f"Ollama error: {str(e)}")


async def call_openai(
    model: str,
    prompt: str,
    system_prompt: Optional[str],
    max_tokens: int,
    temperature: float,
) -> Dict[str, Any]:
    """Call OpenAI API (mock implementation)"""
    # Mock implementation - replace with actual OpenAI API call
    return {
        "text": f"Mock OpenAI response for: {prompt[:50]}...",
        "tokens_used": len(prompt.split()) + 100,
        "cost": 0.002,
        "processing_time": 1.2,
    }


async def call_anthropic(
    model: str,
    prompt: str,
    system_prompt: Optional[str],
    max_tokens: int,
    temperature: float,
) -> Dict[str, Any]:
    """Call Anthropic API (mock implementation)"""
    # Mock implementation - replace with actual Anthropic API call
    return {
        "text": f"Mock Anthropic response for: {prompt[:50]}...",
        "tokens_used": len(prompt.split()) + 120,
        "cost": 0.003,
        "processing_time": 1.5,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8006)
