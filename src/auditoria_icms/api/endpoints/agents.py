"""
Endpoints para Execução Individual de Agentes
Permite executar agentes específicos isoladamente
"""

import uuid
import asyncio
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from ...database.connection import get_db_session
from ...database.models import Usuario, ProdutoEmpresa as MercadoriaAClassificar
from ...agents.enrichment_agent import EnrichmentAgent
from ...agents.ncm_agent import NCMAgent
from ...agents.cest_agent import CESTAgent
from ...agents.reconciliation_agent import ReconciliationAgent
from ..schemas import AgentExecutionRequest, AgentExecutionResponse
from .auth import get_current_user
from ..middleware.error_handler import BusinessLogicError

logger = logging.getLogger(__name__)
router = APIRouter()

# Cache de jobs de agentes
agent_jobs_cache: Dict[str, Dict[str, Any]] = {}


async def execute_agent_task(
    job_id: str,
    agent_type: str,
    empresa_id: int,
    produto_ids: Optional[List[int]] = None,
    parameters: Optional[Dict[str, Any]] = None,
):
    """
    Executa um agente específico em background
    """
    try:
        logger.info(f"🤖 Iniciando execução do agente {agent_type} - Job {job_id}")

        # Atualizar status
        agent_jobs_cache[job_id]["status"] = "running"
        agent_jobs_cache[job_id]["message"] = f"Executando agente {agent_type}..."

        # Conectar ao banco
        from ...database.connection import db_manager

        with db_manager.session_scope() as db:
            # Buscar produtos
            query = db.query(MercadoriaAClassificar).filter(
                MercadoriaAClassificar.empresa_id == empresa_id
            )

            if produto_ids:
                query = query.filter(MercadoriaAClassificar.id.in_(produto_ids))

            produtos = query.all()

            if not produtos:
                agent_jobs_cache[job_id]["status"] = "completed"
                agent_jobs_cache[job_id]["message"] = "Nenhum produto encontrado"
                agent_jobs_cache[job_id]["results"] = []
                return

            total_produtos = len(produtos)
            agent_jobs_cache[job_id]["total"] = total_produtos

            # Inicializar agente específico
            agent = None
            if agent_type == "enrichment":
                agent = EnrichmentAgent()
            elif agent_type == "ncm_classification":
                agent = NCMAgent()
            elif agent_type == "cest_classification":
                agent = CESTAgent()
            elif agent_type == "reconciliation":
                agent = ReconciliationAgent()
            else:
                raise ValueError(f"Tipo de agente não suportado: {agent_type}")

            logger.info(f"🔧 Processando {total_produtos} produtos com {agent_type}")

            # Processar produtos
            results = []
            processed = 0

            for produto in produtos:
                try:
                    # Preparar dados do produto
                    _product_data = {
                        "mercadoria_id": produto.id,
                        "produto_id": produto.produto_id_origem,
                        "descricao_original": produto.descricao_original,
                        "codigo_barra": produto.codigo_barra,
                        "codigo_produto": produto.codigo_produto,
                        "ncm_informado": produto.ncm_informado,
                        "cest_informado": produto.cest_informado,
                        "empresa_id": empresa_id,
                    }

                    # Executar agente
                    if agent_type == "enrichment":
                        result = await agent.enrich_description(
                            produto.descricao_original, context=parameters or {}
                        )

                        # Atualizar descrição enriquecida no banco
                        if result["success"]:
                            produto.descricao_enriquecida = result.get(
                                "enriched_description"
                            )
                            db.commit()

                    elif agent_type == "ncm_classification":
                        result = await agent.classify_ncm(
                            description=produto.descricao_original,
                            existing_ncm=produto.ncm_informado,
                            context=parameters or {},
                        )

                    elif agent_type == "cest_classification":
                        # Para CEST, precisa do NCM
                        ncm_to_use = produto.ncm_informado
                        if not ncm_to_use:
                            # Se não tem NCM, tentar classificar primeiro
                            ncm_agent = NCMAgent()
                            ncm_result = await ncm_agent.classify_ncm(
                                description=produto.descricao_original
                            )
                            ncm_to_use = (
                                ncm_result.get("ncm_code")
                                if ncm_result["success"]
                                else None
                            )

                        result = await agent.classify_cest(
                            description=produto.descricao_original,
                            ncm_code=ncm_to_use,
                            existing_cest=produto.cest_informado,
                            context=parameters or {},
                        )

                    elif agent_type == "reconciliation":
                        result = await agent.reconcile_classification(
                            ncm_code=produto.ncm_informado,
                            cest_code=produto.cest_informado,
                            description=produto.descricao_original,
                            context=parameters or {},
                        )

                    # Adicionar resultado
                    results.append(
                        {
                            "produto_id": produto.id,
                            "success": result["success"],
                            "result": result,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

                    processed += 1

                    # Atualizar progresso
                    progress = (processed / total_produtos) * 100
                    agent_jobs_cache[job_id]["processed"] = processed
                    agent_jobs_cache[job_id]["progress"] = progress
                    agent_jobs_cache[job_id][
                        "message"
                    ] = f"Processado {processed}/{total_produtos} ({progress:.1f}%)"

                    logger.info(
                        f"✅ Produto {produto.id} processado pelo agente {agent_type}"
                    )

                except Exception as item_error:
                    logger.error(
                        f"❌ Erro ao processar produto {produto.id}: {item_error}"
                    )

                    results.append(
                        {
                            "produto_id": produto.id,
                            "success": False,
                            "error": str(item_error),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

                    processed += 1

                # Pequena pausa
                await asyncio.sleep(0.1)

        # Finalizar job
        agent_jobs_cache[job_id]["status"] = "completed"
        agent_jobs_cache[job_id]["progress"] = 100.0
        agent_jobs_cache[job_id]["results"] = results
        agent_jobs_cache[job_id][
            "message"
        ] = f"Agente {agent_type} executado com sucesso!"

        successful = sum(1 for r in results if r["success"])
        logger.info(
            f"🎉 Agente {agent_type} concluído: {successful}/{total_produtos} sucessos"
        )

    except Exception as e:
        error_message = f"Erro na execução do agente {agent_type}: {str(e)}"
        logger.error(f"❌ {error_message}")

        agent_jobs_cache[job_id]["status"] = "error"
        agent_jobs_cache[job_id]["message"] = error_message
        agent_jobs_cache[job_id]["error"] = str(e)


@router.post(
    "/execute",
    response_model=AgentExecutionResponse,
    summary="Executar agente específico",
)
async def execute_agent(
    agent_request: AgentExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Executa um agente específico sobre produtos de uma empresa

    Permite testar e executar agentes individuais para debug ou casos específicos
    """
    logger.info(
        f"🤖 Solicitação de execução do agente {agent_request.agent_type} - Empresa: {agent_request.empresa_id}"
    )

    # Verificar acesso à empresa
    from ...database.models import UsuarioEmpresaAcesso

    access = (
        db.query(UsuarioEmpresaAcesso)
        .filter(
            UsuarioEmpresaAcesso.usuario_id == current_user.id,
            UsuarioEmpresaAcesso.empresa_id == agent_request.empresa_id,
        )
        .first()
    )

    if not access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado à empresa"
        )

    # Verificar se há produtos para processar
    query = db.query(MercadoriaAClassificar).filter(
        MercadoriaAClassificar.empresa_id == agent_request.empresa_id
    )

    if agent_request.produto_ids:
        query = query.filter(MercadoriaAClassificar.id.in_(agent_request.produto_ids))

    product_count = query.count()

    if product_count == 0:
        raise BusinessLogicError("Nenhum produto encontrado para processar")

    # Gerar ID único para o job
    job_id = str(uuid.uuid4())

    # Inicializar cache do job
    agent_jobs_cache[job_id] = {
        "job_id": job_id,
        "agent_type": agent_request.agent_type.value,
        "empresa_id": agent_request.empresa_id,
        "status": "initiated",
        "total": product_count,
        "processed": 0,
        "progress": 0.0,
        "message": f"Executando agente {agent_request.agent_type.value}...",
        "started_at": datetime.utcnow().isoformat(),
        "user_email": current_user.email,
        "parameters": agent_request.parameters,
    }

    # Adicionar task em background
    background_tasks.add_task(
        execute_agent_task,
        job_id=job_id,
        agent_type=agent_request.agent_type.value,
        empresa_id=agent_request.empresa_id,
        produto_ids=agent_request.produto_ids,
        parameters=agent_request.parameters,
    )

    logger.info(f"🚀 Job de agente {job_id} iniciado para {product_count} produtos")

    return AgentExecutionResponse(
        job_id=job_id,
        agent_type=agent_request.agent_type,
        status="initiated",
        started_at=datetime.utcnow(),
        parameters=agent_request.parameters,
    )


@router.get("/status/{job_id}", summary="Status da execução do agente")
async def get_agent_status(
    job_id: str, current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna o status de execução de um agente
    """
    logger.info(f"📊 Consultando status do agente {job_id}")

    if job_id not in agent_jobs_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job de agente não encontrado"
        )

    job_info = agent_jobs_cache[job_id]

    # Verificar acesso
    from ...database.models import UsuarioEmpresaAcesso
    from ...database.connection import db_manager

    with db_manager.session_scope() as db:
        access = (
            db.query(UsuarioEmpresaAcesso)
            .filter(
                UsuarioEmpresaAcesso.usuario_id == current_user.id,
                UsuarioEmpresaAcesso.empresa_id == job_info["empresa_id"],
            )
            .first()
        )

        if not access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado ao job do agente",
            )

    return job_info


@router.post("/aggregate", summary="Executar agregação de produtos")
async def execute_aggregation(
    empresa_id: int,
    background_tasks: BackgroundTasks,
    similarity_threshold: float = 0.95,
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Executa agregação de produtos similares para uma empresa

    Identifica produtos iguais/similares com descrições diferentes
    """
    logger.info(f"🔗 Executando agregação para empresa {empresa_id}")

    # Verificar acesso
    from ...database.models import UsuarioEmpresaAcesso

    access = (
        db.query(UsuarioEmpresaAcesso)
        .filter(
            UsuarioEmpresaAcesso.usuario_id == current_user.id,
            UsuarioEmpresaAcesso.empresa_id == empresa_id,
            UsuarioEmpresaAcesso.nivel_acesso.in_(["admin", "editor"]),
        )
        .first()
    )

    if not access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão insuficiente para executar agregação",
        )

    # Usar AgentExecutionRequest para agregação
    aggregation_request = AgentExecutionRequest(
        agent_type="aggregation",
        empresa_id=empresa_id,
        parameters={"similarity_threshold": similarity_threshold},
    )

    # Executar usando o endpoint padrão
    return await execute_agent(aggregation_request, background_tasks, db, current_user)


@router.get("/results/{job_id}", summary="Resultados da execução do agente")
async def get_agent_results(
    job_id: str, current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna os resultados detalhados da execução de um agente
    """
    logger.info(f"📋 Buscando resultados do agente {job_id}")

    if job_id not in agent_jobs_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job de agente não encontrado"
        )

    job_info = agent_jobs_cache[job_id]

    # Verificar acesso
    from ...database.models import UsuarioEmpresaAcesso
    from ...database.connection import db_manager

    with db_manager.session_scope() as db:
        access = (
            db.query(UsuarioEmpresaAcesso)
            .filter(
                UsuarioEmpresaAcesso.usuario_id == current_user.id,
                UsuarioEmpresaAcesso.empresa_id == job_info["empresa_id"],
            )
            .first()
        )

        if not access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado aos resultados do agente",
            )

    if job_info["status"] != "completed":
        return {
            "job_id": job_id,
            "status": job_info["status"],
            "message": "Job ainda não foi concluído",
            "results": None,
        }

    return {
        "job_id": job_id,
        "agent_type": job_info["agent_type"],
        "status": job_info["status"],
        "total": job_info["total"],
        "processed": job_info["processed"],
        "results": job_info.get("results", []),
        "started_at": job_info["started_at"],
        "completed_at": datetime.utcnow().isoformat(),
    }
