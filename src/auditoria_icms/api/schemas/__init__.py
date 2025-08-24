"""
Schemas Pydantic para validação da API
Definições de entrada e saída para todos os endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# =============================================================================
# SCHEMAS DE AUTENTICAÇÃO
# =============================================================================


class UserLogin(BaseModel):
    """Schema para login de usuário"""

    email: str = Field(..., description="Email do usuário")
    password: str = Field(..., description="Senha do usuário")


class TokenResponse(BaseModel):
    """Schema para resposta de autenticação"""

    access_token: str = Field(..., description="Token JWT de acesso")
    token_type: str = Field(default="bearer", description="Tipo do token")
    expires_in: int = Field(..., description="Tempo de expiração em segundos")
    user_info: Dict[str, Any] = Field(..., description="Informações do usuário")


# =============================================================================
# SCHEMAS DE USUÁRIOS
# =============================================================================


class UserCreate(BaseModel):
    """Schema para criação de usuário"""

    nome: str = Field(..., min_length=2, max_length=255, description="Nome completo")
    email: str = Field(..., description="Email único")
    cargo: Optional[str] = Field(None, max_length=100, description="Cargo/função")
    identificacao: Optional[str] = Field(
        None, max_length=50, description="Identificação interna"
    )
    password: str = Field(..., min_length=8, description="Senha (mínimo 8 caracteres)")

    @validator("email")
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Email deve conter @")
        return v.lower()


class UserResponse(BaseModel):
    """Schema para resposta de usuário"""

    id: int
    nome: str
    email: str
    cargo: Optional[str]
    identificacao: Optional[str]
    ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema para atualização de usuário"""

    nome: Optional[str] = Field(None, min_length=2, max_length=255)
    cargo: Optional[str] = Field(None, max_length=100)
    identificacao: Optional[str] = Field(None, max_length=50)
    ativo: Optional[bool] = None


# =============================================================================
# SCHEMAS DE EMPRESAS
# =============================================================================


class CompanyCreate(BaseModel):
    """Schema para criação de empresa"""

    nome: str = Field(..., min_length=2, max_length=255, description="Razão social")
    cnpj: str = Field(
        ..., min_length=14, max_length=14, description="CNPJ (apenas números)"
    )
    uf: str = Field(..., min_length=2, max_length=2, description="UF (sigla do estado)")
    atividades: List[str] = Field(
        ..., min_items=1, description="Lista de atividades da empresa"
    )
    endereco: Optional[str] = Field(None, description="Endereço completo")
    telefone: Optional[str] = Field(None, description="Telefone de contato")
    email_contato: Optional[str] = Field(None, description="Email de contato")

    @validator("cnpj")
    def validate_cnpj(cls, v):
        # Remove caracteres não numéricos
        cnpj_numbers = "".join(filter(str.isdigit, v))
        if len(cnpj_numbers) != 14:
            raise ValueError("CNPJ deve ter 14 dígitos")
        return cnpj_numbers

    @validator("uf")
    def validate_uf(cls, v):
        return v.upper()


class CompanyResponse(BaseModel):
    """Schema para resposta de empresa"""

    id: int
    nome: str
    cnpj: str
    uf: str
    atividades: List[str]
    endereco: Optional[str]
    telefone: Optional[str]
    email_contato: Optional[str]
    ativo: bool
    criado_em: datetime

    class Config:
        from_attributes = True


# =============================================================================
# SCHEMAS DE IMPORTAÇÃO DE DADOS
# =============================================================================


class DatabaseConnectionType(str, Enum):
    """Tipos de banco de dados suportados"""

    postgresql = "postgresql"
    sql_server = "sql_server"
    oracle = "oracle"


class DatabaseConnection(BaseModel):
    """Schema para configuração de conexão com banco da empresa"""

    database_type: DatabaseConnectionType
    host: str = Field(..., description="Host do banco de dados")
    port: int = Field(..., gt=0, le=65535, description="Porta do banco")
    database: str = Field(..., description="Nome do banco de dados")
    username: str = Field(..., description="Usuário do banco")
    password: str = Field(..., description="Senha do banco")
    schema: Optional[str] = Field("dbo", description="Schema do banco (padrão: dbo)")


class DataImportRequest(BaseModel):
    """Schema para requisição de importação de dados"""

    empresa_id: int = Field(..., description="ID da empresa")
    database_config: DatabaseConnection = Field(
        ..., description="Configuração do banco"
    )
    table_name: str = Field(default="produto", description="Nome da tabela a importar")
    limit: Optional[int] = Field(
        None, gt=0, description="Limite de registros (opcional)"
    )
    filters: Optional[Dict[str, Any]] = Field(
        None, description="Filtros SQL adicionais"
    )


class DataImportResponse(BaseModel):
    """Schema para resposta de importação"""

    job_id: str = Field(..., description="ID do job de importação")
    empresa_id: int
    status: str = Field(default="initiated", description="Status da importação")
    total_records: Optional[int] = Field(
        None, description="Total de registros a importar"
    )
    message: str = Field(..., description="Mensagem de status")


# =============================================================================
# SCHEMAS DE CLASSIFICAÇÃO
# =============================================================================


class ClassificationStatus(str, Enum):
    """Status de classificação"""

    pending = "PENDENTE"
    processing = "PROCESSANDO"
    completed = "CONCLUIDA"
    review_needed = "REVISAO_MANUAL"
    error = "ERRO"


class BatchClassificationRequest(BaseModel):
    """Schema para requisição de classificação em lote"""

    empresa_id: int = Field(..., description="ID da empresa")
    limit: Optional[int] = Field(
        None, gt=0, description="Limite de produtos a classificar"
    )
    status_filter: Optional[List[ClassificationStatus]] = Field(
        None, description="Filtrar por status específicos"
    )
    produto_ids: Optional[List[int]] = Field(
        None, description="IDs específicos para classificar"
    )
    force_reclassify: bool = Field(
        default=False, description="Forçar reclassificação de produtos já processados"
    )


class BatchClassificationResponse(BaseModel):
    """Schema para resposta de classificação em lote"""

    job_id: str = Field(..., description="ID do job de classificação")
    empresa_id: int
    total_products: int = Field(..., description="Total de produtos no lote")
    status: str = Field(default="initiated", description="Status do job")
    estimated_time: Optional[int] = Field(
        None, description="Tempo estimado em segundos"
    )


class ClassificationJobStatus(BaseModel):
    """Schema para status de job de classificação"""

    job_id: str
    status: str
    total: int = Field(..., description="Total de itens")
    processed: int = Field(..., description="Itens processados")
    successful: int = Field(..., description="Classificações bem-sucedidas")
    failed: int = Field(..., description="Classificações falharam")
    progress_percentage: float = Field(..., description="Porcentagem de progresso")
    estimated_remaining: Optional[int] = Field(
        None, description="Tempo restante estimado (segundos)"
    )
    current_item: Optional[str] = Field(
        None, description="Item sendo processado atualmente"
    )


# =============================================================================
# SCHEMAS DE RESULTADOS
# =============================================================================


class ProductClassificationResult(BaseModel):
    """Schema para resultado de classificação de produto"""

    mercadoria_id: int
    produto_id: str
    descricao_original: str
    descricao_enriquecida: Optional[str]
    ncm_informado: Optional[str]
    cest_informado: Optional[str]
    ncm_determinado: Optional[str]
    cest_determinado: Optional[str]
    confianca_ncm: Optional[float]
    confianca_cest: Optional[float]
    status: ClassificationStatus
    justificativa_ncm: Optional[str]
    contexto_ncm: Optional[Dict[str, Any]]
    justificativa_cest: Optional[str]
    contexto_cest: Optional[Dict[str, Any]]
    processado_em: Optional[datetime]

    class Config:
        from_attributes = True


class ClassificationDetailResponse(BaseModel):
    """Schema para detalhes de classificação com trilha de auditoria"""

    classification: ProductClassificationResult
    audit_trail: List[Dict[str, Any]] = Field(
        ..., description="Trilha de auditoria com decisões dos agentes"
    )
    rag_contexts: List[Dict[str, Any]] = Field(
        ..., description="Contextos RAG utilizados"
    )
    similar_products: Optional[List[ProductClassificationResult]] = Field(
        None, description="Produtos similares identificados"
    )


class ResultsListRequest(BaseModel):
    """Schema para requisição de lista de resultados"""

    empresa_id: int
    page: int = Field(default=1, ge=1, description="Página (iniciando em 1)")
    page_size: int = Field(default=50, ge=1, le=500, description="Itens por página")
    status_filter: Optional[List[ClassificationStatus]] = None
    ncm_filter: Optional[str] = Field(None, description="Filtro por NCM")
    search_term: Optional[str] = Field(None, description="Termo de busca na descrição")


class ResultsListResponse(BaseModel):
    """Schema para resposta de lista de resultados"""

    items: List[ProductClassificationResult]
    total: int = Field(..., description="Total de registros")
    page: int = Field(..., description="Página atual")
    page_size: int = Field(..., description="Itens por página")
    total_pages: int = Field(..., description="Total de páginas")


# =============================================================================
# SCHEMAS DE GOLDEN SET
# =============================================================================


class GoldenSetCreate(BaseModel):
    """Schema para criação de entrada no Golden Set"""

    descricao_produto: str = Field(
        ..., min_length=5, description="Descrição do produto"
    )
    descricao_enriquecida: Optional[str] = Field(
        None, description="Descrição enriquecida"
    )
    gtin: Optional[str] = Field(None, description="GTIN/código de barras")
    ncm_correto: str = Field(
        ..., min_length=8, max_length=10, description="NCM correto"
    )
    cest_correto: Optional[str] = Field(
        None, min_length=7, max_length=7, description="CEST correto"
    )
    fonte_empresa_id: Optional[int] = Field(None, description="ID da empresa fonte")
    observacoes: Optional[str] = Field(None, description="Observações adicionais")


class GoldenSetResponse(BaseModel):
    """Schema para resposta de Golden Set"""

    id: int
    descricao_produto: str
    descricao_enriquecida: Optional[str]
    gtin: Optional[str]
    ncm_correto: str
    cest_correto: Optional[str]
    fonte_usuario: Optional[str]
    fonte_empresa_id: Optional[int]
    data_confirmacao: datetime
    observacoes: Optional[str]

    class Config:
        from_attributes = True


# =============================================================================
# SCHEMAS DE AGENTES
# =============================================================================


class AgentType(str, Enum):
    """Tipos de agentes disponíveis"""

    enrichment = "enrichment"
    ncm_classification = "ncm_classification"
    cest_classification = "cest_classification"
    aggregation = "aggregation"
    reconciliation = "reconciliation"


class AgentExecutionRequest(BaseModel):
    """Schema para execução individual de agente"""

    agent_type: AgentType
    empresa_id: int
    produto_ids: Optional[List[int]] = Field(
        None, description="IDs específicos para processar"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Parâmetros específicos do agente"
    )


class AgentExecutionResponse(BaseModel):
    """Schema para resposta de execução de agente"""

    job_id: str
    agent_type: AgentType
    status: str
    started_at: datetime
    parameters: Optional[Dict[str, Any]]


# =============================================================================
# SCHEMAS GENÉRICOS
# =============================================================================


class MessageResponse(BaseModel):
    """Schema para respostas simples com mensagem"""

    message: str
    success: bool = True
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Schema para respostas de erro"""

    error: bool = True
    message: str
    details: Optional[Dict[str, Any]] = None
    status_code: Optional[int] = None


class HealthCheckResponse(BaseModel):
    """Schema para resposta de health check"""

    status: str
    timestamp: datetime
    services: Dict[str, str]
    version: str = "16.0"
