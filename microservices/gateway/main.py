"""
API Gateway for microservices architecture
Handles routing, authentication, and load balancing
"""

# Standard Library Imports
import os
import sys
from typing import Any, Dict, List, Optional

# Third-party Imports
import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add the microservices directory to Python path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
microservices_dir = os.path.dirname(current_dir)
sys.path.insert(0, microservices_dir)

# Local Application Imports
from shared.auth import get_current_user  # noqa: E402
from shared.logging_config import setup_logger  # noqa: E402
from shared.models import BaseResponse  # noqa: E402

# Initialize logger
logger = setup_logger("api-gateway")


# =================== MODELOS ===================
class EmpresaCreate(BaseModel):
    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str] = None
    atividade_principal: Optional[str] = None
    regime_tributario: Optional[str] = "Simples Nacional"


class EmpresaResponse(BaseModel):
    id: int
    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str]
    database_name: str
    ativa: bool


# Mock data for empresas
mock_empresas = [
    {
        "id": 1,
        "cnpj": "12345678000190",
        "razao_social": "Empresa Demo Ltda",
        "nome_fantasia": "Demo Corp",
        "database_name": "empresa_12345678000190",
        "ativa": True,
    },
    {
        "id": 2,
        "cnpj": "98765432000110",
        "razao_social": "Tech Solutions SA",
        "nome_fantasia": "TechSol",
        "database_name": "empresa_98765432000110",
        "ativa": True,
    },
]

# Service URLs
SERVICES = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://localhost:8001"),
    "tenant": os.getenv("TENANT_SERVICE_URL", "http://localhost:8002"),
    "product": os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8003"),
    "classification": os.getenv("CLASSIFICATION_SERVICE_URL", "http://localhost:8004"),
    "import": os.getenv("IMPORT_SERVICE_URL", "http://localhost:8005"),
    "ai": os.getenv("AI_SERVICE_URL", "http://localhost:8006"),
}

app = FastAPI(
    title="Auditoria Fiscal ICMS - API Gateway",
    description="API Gateway for microservices architecture",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return BaseResponse(
        message="API Gateway is running", data={"services": list(SERVICES.keys())}
    )


@app.get("/health")
async def health_check():
    """Health check for all services"""
    service_status = {}

    async with httpx.AsyncClient() as client:
        for service_name, service_url in SERVICES.items():
            try:
                response = await client.get(f"{service_url}/health", timeout=5.0)
                service_status[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": service_url,
                }
            except Exception as e:
                service_status[service_name] = {
                    "status": "unreachable",
                    "error": str(e),
                    "url": service_url,
                }

    return BaseResponse(message="Service health check completed", data=service_status)


# =================== ENDPOINTS DE EMPRESAS ===================


@app.get("/empresas", response_model=List[EmpresaResponse])
async def listar_empresas():
    """Lista empresas"""
    try:
        logger.info("Listando empresas via Gateway")
        return mock_empresas
    except Exception as e:
        logger.error(f"Erro ao listar empresas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/empresas", response_model=EmpresaResponse)
async def criar_empresa(empresa: EmpresaCreate):
    """Cria nova empresa (versão simplificada com dados mock)"""
    try:
        logger.info(
            f"Criando empresa via Gateway: {empresa.cnpj} - {empresa.razao_social}"
        )

        # Verificar se empresa já existe
        for emp in mock_empresas:
            if emp["cnpj"] == empresa.cnpj:
                raise HTTPException(status_code=400, detail="Empresa já cadastrada")

        # Criar nova empresa (mock)
        novo_id = max([emp["id"] for emp in mock_empresas]) + 1
        cnpj_clean = "".join(filter(str.isdigit, empresa.cnpj))
        database_name = f"empresa_{cnpj_clean}"

        nova_empresa = {
            "id": novo_id,
            "cnpj": empresa.cnpj,
            "razao_social": empresa.razao_social,
            "nome_fantasia": empresa.nome_fantasia or empresa.razao_social,
            "database_name": database_name,
            "ativa": True,
        }

        # Adicionar aos dados mock
        mock_empresas.append(nova_empresa)

        logger.info(f"Empresa criada com sucesso via Gateway: ID {novo_id}")
        return nova_empresa

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar empresa via Gateway: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar empresa: {str(e)}")


# Auth routes (no authentication required)
@app.post("/auth/login")
async def login(request: Request):
    """Forward login request to auth service"""
    return await forward_request("auth", "/login", request)


@app.post("/auth/register")
async def register(request: Request):
    """Forward register request to auth service"""
    return await forward_request("auth", "/register", request)


# Protected routes
@app.api_route("/tenant/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def tenant_proxy(
    path: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Forward requests to tenant service"""
    return await forward_request("tenant", f"/{path}", request, current_user)


@app.api_route("/product/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def product_proxy(
    path: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Forward requests to product service"""
    return await forward_request("product", f"/{path}", request, current_user)


@app.api_route("/classification/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def classification_proxy(
    path: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Forward requests to classification service"""
    return await forward_request("classification", f"/{path}", request, current_user)


@app.api_route("/import/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def import_proxy(
    path: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Forward requests to import service"""
    return await forward_request("import", f"/{path}", request, current_user)


@app.api_route("/ai/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def ai_proxy(
    path: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Forward requests to AI service"""
    return await forward_request("ai", f"/{path}", request, current_user)


async def forward_request(
    service_name: str, path: str, request: Request, current_user: Dict[str, Any] = None
):
    """Forward request to appropriate microservice"""
    service_url = SERVICES.get(service_name)
    if not service_url:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

    # Prepare headers
    headers = dict(request.headers)
    if current_user:
        headers["X-User-ID"] = current_user.get("sub", "")
        headers["X-Tenant-ID"] = current_user.get("tenant_id", "")

    # Get request body
    body = await request.body()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=f"{service_url}{path}",
                headers=headers,
                content=body,
                params=request.query_params,
                timeout=30.0,
            )

            logger.info(
                f"Forwarded {request.method} {path} to {service_name} - Status: {response.status_code}"
            )

            return JSONResponse(
                status_code=response.status_code,
                content=response.json(),
                headers=dict(response.headers),
            )

    except httpx.TimeoutException:
        logger.error(f"Timeout forwarding request to {service_name}")
        raise HTTPException(status_code=504, detail=f"Service {service_name} timeout")
    except Exception as e:
        logger.error(f"Error forwarding request to {service_name}: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Service {service_name} error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
