"""
API para Cadastro e Gestão de Empresas
=====================================
Endpoints para criar, listar, editar e excluir empresas/tenants
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr, validator
import uuid
from datetime import datetime

# Modelos Pydantic
class AtividadeEconomica(BaseModel):
    cnae: str
    descricao: str
    principal: bool = False

class DadosBasicos(BaseModel):
    razao_social: str
    nome_fantasia: Optional[str] = None
    cnpj: str
    inscricao_estadual: Optional[str] = None
    inscricao_municipal: Optional[str] = None

class Endereco(BaseModel):
    cep: str
    logradouro: str
    numero: str
    complemento: Optional[str] = None
    bairro: str
    cidade: str
    estado: str

class Contato(BaseModel):
    telefone: str
    email: EmailStr
    responsavel: str

class Configuracoes(BaseModel):
    regime_tributario: str
    porte_empresa: str
    contribuinte_icms: bool = False
    contribuinte_ipi: bool = False
    optante_simples: bool = False

class EmpresaSettings(BaseModel):
    dados_basicos: DadosBasicos
    endereco: Endereco
    contato: Contato
    atividades: List[AtividadeEconomica]
    configuracoes: Configuracoes

class EmpresaCreate(BaseModel):
    name: str
    cnpj: str
    email: EmailStr
    settings: EmpresaSettings
    
    @validator('cnpj')
    def validate_cnpj(cls, v):
        # Remover caracteres não numéricos
        cnpj_nums = ''.join(filter(str.isdigit, v))
        if len(cnpj_nums) != 14:
            raise ValueError('CNPJ deve ter 14 dígitos')
        return v

class EmpresaUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    settings: Optional[EmpresaSettings] = None
    status: Optional[str] = None

class EmpresaResponse(BaseModel):
    id: str
    name: str
    cnpj: str
    email: str
    status: str
    created_at: datetime
    updated_at: datetime
    settings: Optional[dict] = None
    total_produtos: int = 0
    ultimo_acesso: Optional[datetime] = None

# Router
router = APIRouter(prefix="/api/tenants", tags=["empresas"])

# Simulação de banco de dados em memória
empresas_db = {}

def get_current_tenant_id():
    """Simulação de obter tenant atual"""
    return "default"

@router.post("", response_model=EmpresaResponse)
async def criar_empresa(empresa: EmpresaCreate):
    """Criar nova empresa/tenant"""
    
    try:
        # Verificar se CNPJ já existe
        for existing_id, existing_empresa in empresas_db.items():
            if existing_empresa.get("cnpj") == empresa.cnpj:
                raise HTTPException(
                    status_code=400,
                    detail="CNPJ já cadastrado no sistema"
                )
        
        # Gerar ID único
        empresa_id = str(uuid.uuid4())
        
        # Criar registro da empresa
        now = datetime.now()
        nova_empresa = {
            "id": empresa_id,
            "name": empresa.name,
            "cnpj": empresa.cnpj,
            "email": empresa.email,
            "status": "ATIVA",
            "created_at": now,
            "updated_at": now,
            "settings": empresa.settings.dict(),
            "total_produtos": 0,
            "ultimo_acesso": now
        }
        
        # Salvar no "banco"
        empresas_db[empresa_id] = nova_empresa
        
        return EmpresaResponse(**nova_empresa)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar empresa: {str(e)}"
        )

@router.get("", response_model=List[EmpresaResponse])
async def listar_empresas(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
):
    """Listar todas as empresas"""
    
    try:
        empresas = list(empresas_db.values())
        
        # Filtrar por status se especificado
        if status:
            empresas = [emp for emp in empresas if emp.get("status") == status]
        
        # Aplicar paginação
        empresas = empresas[skip:skip + limit]
        
        return [EmpresaResponse(**emp) for emp in empresas]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao listar empresas: {str(e)}"
        )

@router.get("/{empresa_id}", response_model=EmpresaResponse)
async def obter_empresa(empresa_id: str):
    """Obter detalhes de uma empresa específica"""
    
    if empresa_id not in empresas_db:
        raise HTTPException(
            status_code=404,
            detail="Empresa não encontrada"
        )
    
    empresa = empresas_db[empresa_id]
    return EmpresaResponse(**empresa)

@router.put("/{empresa_id}", response_model=EmpresaResponse)
async def atualizar_empresa(empresa_id: str, empresa_update: EmpresaUpdate):
    """Atualizar dados de uma empresa"""
    
    if empresa_id not in empresas_db:
        raise HTTPException(
            status_code=404,
            detail="Empresa não encontrada"
        )
    
    try:
        empresa = empresas_db[empresa_id]
        
        # Atualizar campos fornecidos
        if empresa_update.name is not None:
            empresa["name"] = empresa_update.name
        
        if empresa_update.email is not None:
            empresa["email"] = empresa_update.email
        
        if empresa_update.settings is not None:
            empresa["settings"] = empresa_update.settings.dict()
        
        if empresa_update.status is not None:
            empresa["status"] = empresa_update.status
        
        empresa["updated_at"] = datetime.now()
        
        return EmpresaResponse(**empresa)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar empresa: {str(e)}"
        )

@router.patch("/{empresa_id}/status")
async def alterar_status_empresa(empresa_id: str, status_data: dict):
    """Alterar status de uma empresa"""
    
    if empresa_id not in empresas_db:
        raise HTTPException(
            status_code=404,
            detail="Empresa não encontrada"
        )
    
    novo_status = status_data.get("status")
    if novo_status not in ["ATIVA", "INATIVA", "SUSPENSA"]:
        raise HTTPException(
            status_code=400,
            detail="Status inválido. Use: ATIVA, INATIVA ou SUSPENSA"
        )
    
    try:
        empresa = empresas_db[empresa_id]
        empresa["status"] = novo_status
        empresa["updated_at"] = datetime.now()
        
        return {"message": f"Status alterado para {novo_status} com sucesso"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao alterar status: {str(e)}"
        )

@router.delete("/{empresa_id}")
async def excluir_empresa(empresa_id: str):
    """Excluir uma empresa"""
    
    if empresa_id not in empresas_db:
        raise HTTPException(
            status_code=404,
            detail="Empresa não encontrada"
        )
    
    try:
        # Verificar se empresa tem dados dependentes
        empresa = empresas_db[empresa_id]
        if empresa.get("total_produtos", 0) > 0:
            raise HTTPException(
                status_code=400,
                detail="Não é possível excluir empresa com produtos cadastrados"
            )
        
        # Remover empresa
        del empresas_db[empresa_id]
        
        return {"message": "Empresa excluída com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao excluir empresa: {str(e)}"
        )

@router.get("/{empresa_id}/estatisticas")
async def obter_estatisticas_empresa(empresa_id: str):
    """Obter estatísticas de uma empresa"""
    
    if empresa_id not in empresas_db:
        raise HTTPException(
            status_code=404,
            detail="Empresa não encontrada"
        )
    
    empresa = empresas_db[empresa_id]
    
    # Simular estatísticas
    estatisticas = {
        "total_produtos": empresa.get("total_produtos", 0),
        "produtos_classificados": int(empresa.get("total_produtos", 0) * 0.85),
        "produtos_pendentes": int(empresa.get("total_produtos", 0) * 0.15),
        "precisao_classificacao": 92.5,
        "total_importacoes": 12,
        "ultima_importacao": empresa.get("ultimo_acesso"),
        "periodo_ativo": {
            "dias": (datetime.now() - empresa["created_at"]).days,
            "desde": empresa["created_at"].strftime("%d/%m/%Y")
        }
    }
    
    return estatisticas

# Inicializar com dados de exemplo
def init_sample_data():
    """Inicializar com dados de exemplo se banco estiver vazio"""
    
    if not empresas_db:
        sample_empresas = [
            {
                "id": "sample-1",
                "name": "ABC Comércio de Produtos Ltda",
                "cnpj": "12.345.678/0001-90",
                "email": "contato@abcloja.com.br",
                "status": "ATIVA",
                "created_at": datetime(2025, 1, 15),
                "updated_at": datetime(2025, 8, 23),
                "total_produtos": 1250,
                "ultimo_acesso": datetime(2025, 8, 23),
                "settings": {
                    "dados_basicos": {
                        "razao_social": "ABC Comércio de Produtos Ltda",
                        "nome_fantasia": "ABC Loja",
                        "cnpj": "12.345.678/0001-90",
                        "inscricao_estadual": "123.456.789.012",
                        "inscricao_municipal": "123456"
                    },
                    "endereco": {
                        "cep": "01310-100",
                        "logradouro": "Av. Paulista",
                        "numero": "1000",
                        "bairro": "Bela Vista",
                        "cidade": "São Paulo",
                        "estado": "SP"
                    },
                    "contato": {
                        "telefone": "(11) 99999-9999",
                        "email": "contato@abcloja.com.br",
                        "responsavel": "João Silva"
                    },
                    "configuracoes": {
                        "regime_tributario": "SIMPLES_NACIONAL",
                        "porte_empresa": "ME",
                        "contribuinte_icms": True,
                        "contribuinte_ipi": False,
                        "optante_simples": True
                    }
                }
            }
        ]
        
        for empresa in sample_empresas:
            empresas_db[empresa["id"]] = empresa

# Inicializar dados de exemplo na importação
init_sample_data()
