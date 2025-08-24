"""
Endpoints de Importação de Dados
Conecta com bancos de empresas e importa produtos para classificação
"""

import uuid
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import logging

from ...database.connection import get_db_session
from ...database.models import (
    Usuario,
    Empresa,
    ProdutoEmpresa as MercadoriaAClassificar,
)
from ...integrations.stock_analysis.stock_adapter import StockIntegrationManager
from ..schemas import DataImportRequest, DataImportResponse, MessageResponse
from .auth import get_current_user
from ..middleware.error_handler import BusinessLogicError

logger = logging.getLogger(__name__)
router = APIRouter()

# Cache de jobs de importação (em produção, usar Redis)
import_jobs_cache: Dict[str, Dict[str, Any]] = {}


async def execute_data_import(
    job_id: str,
    empresa_id: int,
    database_config: dict,
    table_name: str = "produto",
    limit: Optional[int] = None,
    filters: Optional[dict] = None,
):
    """
    Executa importação de dados em background
    """
    try:
        logger.info(f"🔄 Iniciando importação {job_id} para empresa {empresa_id}")

        # Atualizar status do job
        import_jobs_cache[job_id]["status"] = "running"
        import_jobs_cache[job_id][
            "message"
        ] = "Conectando ao banco de dados da empresa..."

        # Inicializar adaptador de estoque
        integration_manager = StockIntegrationManager(database_config)

        # Construir query de importação
        base_query = f"""
        SELECT
            produto_id,
            descricao_produto,
            codigo_barra,
            codigo_produto,
            ncm,
            cest,
            CASE
                WHEN descricao_produto IS NOT NULL AND TRIM(descricao_produto) != ''
                THEN ROW_NUMBER() OVER (PARTITION BY TRIM(UPPER(descricao_produto)) ORDER BY produto_id)
                ELSE produto_id
            END as id_agregados
        FROM {table_name}
        WHERE descricao_produto IS NOT NULL
        AND TRIM(descricao_produto) != ''
        """

        # Aplicar filtros adicionais
        if filters:
            for field, value in filters.items():
                if isinstance(value, str):
                    base_query += f" AND {field} ILIKE '%{value}%'"
                else:
                    base_query += f" AND {field} = {value}"

        # Aplicar limite
        if limit:
            base_query += f" LIMIT {limit}"

        logger.info(f"📊 Executando query: {base_query}")

        # Atualizar status
        import_jobs_cache[job_id][
            "message"
        ] = "Executando consulta no banco da empresa..."

        # Executar query através do adaptador
        records = await integration_manager.execute_query(base_query)

        if not records:
            import_jobs_cache[job_id]["status"] = "completed"
            import_jobs_cache[job_id][
                "message"
            ] = "Nenhum registro encontrado para importar"
            import_jobs_cache[job_id]["total_records"] = 0
            return

        # Atualizar status com total encontrado
        total_records = len(records)
        import_jobs_cache[job_id]["total_records"] = total_records
        import_jobs_cache[job_id][
            "message"
        ] = f"Importando {total_records} registros..."

        logger.info(
            f"📦 Importando {total_records} registros para empresa {empresa_id}"
        )

        # Conectar ao banco local
        from ...database.connection import db_manager

        # Processar registros em lotes
        batch_size = 100
        processed = 0

        with db_manager.session_scope() as db:
            # Limpar dados existentes da empresa (se necessário)
            db.query(MercadoriaAClassificar).filter(
                MercadoriaAClassificar.empresa_id == empresa_id
            ).delete()

            for i in range(0, total_records, batch_size):
                batch = records[i : i + batch_size]

                for record in batch:
                    # Criar objeto MercadoriaAClassificar
                    mercadoria = MercadoriaAClassificar(
                        empresa_id=empresa_id,
                        produto_id_origem=record.get("produto_id"),
                        descricao_original=record.get("descricao_produto"),
                        codigo_barra=record.get("codigo_barra"),
                        codigo_produto=record.get("codigo_produto"),
                        ncm_informado=record.get("ncm"),
                        cest_informado=record.get("cest"),
                        id_agregados=record.get(
                            "id_agregados", record.get("produto_id")
                        ),
                        status="PENDENTE",
                    )

                    db.add(mercadoria)
                    processed += 1

                # Commit do lote
                db.commit()

                # Atualizar progresso
                progress = (processed / total_records) * 100
                import_jobs_cache[job_id]["processed"] = processed
                import_jobs_cache[job_id]["progress"] = progress
                import_jobs_cache[job_id][
                    "message"
                ] = f"Processado {processed}/{total_records} registros ({progress:.1f}%)"

                # Pequena pausa para não sobrecarregar
                await asyncio.sleep(0.1)

        # Finalizar importação
        import_jobs_cache[job_id]["status"] = "completed"
        import_jobs_cache[job_id]["processed"] = processed
        import_jobs_cache[job_id]["progress"] = 100.0
        import_jobs_cache[job_id][
            "message"
        ] = f"Importação concluída com sucesso! {processed} registros importados."

        logger.info(f"✅ Importação {job_id} concluída: {processed} registros")

    except Exception as e:
        # Tratar erro
        error_message = f"Erro na importação: {str(e)}"
        logger.error(f"❌ {error_message}")

        import_jobs_cache[job_id]["status"] = "error"
        import_jobs_cache[job_id]["message"] = error_message
        import_jobs_cache[job_id]["error"] = str(e)


@router.post(
    "/import", response_model=DataImportResponse, summary="Importar dados da empresa"
)
async def import_company_data(
    import_request: DataImportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Inicia importação de dados do banco da empresa

    Conecta ao banco de dados da empresa e importa produtos para classificação
    """
    logger.info(
        f"📥 Solicitação de importação para empresa {import_request.empresa_id} - Por: {current_user.email}"
    )

    # Verificar acesso à empresa
    from ...database.models import UsuarioEmpresaAcesso

    access = (
        db.query(UsuarioEmpresaAcesso)
        .filter(
            UsuarioEmpresaAcesso.usuario_id == current_user.id,
            UsuarioEmpresaAcesso.empresa_id == import_request.empresa_id,
            UsuarioEmpresaAcesso.nivel_acesso.in_(["admin", "editor"]),
        )
        .first()
    )

    if not access:
        logger.warning(
            f"❌ Usuário {current_user.email} sem acesso à empresa {import_request.empresa_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado à empresa ou permissão insuficiente",
        )

    # Verificar se empresa existe e está ativa
    empresa = (
        db.query(Empresa)
        .filter(Empresa.id == import_request.empresa_id, Empresa.ativo)
        .first()
    )

    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada ou inativa",
        )

    # Validar configuração do banco
    db_config = import_request.database_config
    required_fields = ["host", "port", "database", "username", "password"]

    for field in required_fields:
        if not getattr(db_config, field):
            raise BusinessLogicError(
                f"Campo obrigatório não informado: {field}", {"missing_field": field}
            )

    # Gerar ID único para o job
    job_id = str(uuid.uuid4())

    # Inicializar cache do job
    import_jobs_cache[job_id] = {
        "job_id": job_id,
        "empresa_id": import_request.empresa_id,
        "status": "initiated",
        "message": "Importação iniciada...",
        "total_records": None,
        "processed": 0,
        "progress": 0.0,
        "started_at": "2025-08-19T12:00:00Z",
        "user_email": current_user.email,
    }

    # Converter configuração para dict
    db_config_dict = {
        "database_type": db_config.database_type.value,
        "host": db_config.host,
        "port": db_config.port,
        "database": db_config.database,
        "username": db_config.username,
        "password": db_config.password,
        "schema": db_config.schema,
    }

    # Adicionar task em background
    background_tasks.add_task(
        execute_data_import,
        job_id=job_id,
        empresa_id=import_request.empresa_id,
        database_config=db_config_dict,
        table_name=import_request.table_name,
        limit=import_request.limit,
        filters=import_request.filters,
    )

    logger.info(f"🚀 Job de importação {job_id} iniciado para empresa {empresa.nome}")

    return DataImportResponse(
        job_id=job_id,
        empresa_id=import_request.empresa_id,
        status="initiated",
        message="Importação iniciada com sucesso. Use o job_id para acompanhar o progresso.",
    )


@router.get("/import/status/{job_id}", summary="Status da importação")
async def get_import_status(
    job_id: str, current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna o status de um job de importação
    """
    logger.info(f"📊 Consultando status do job {job_id} - Por: {current_user.email}")

    # Verificar se job existe
    if job_id not in import_jobs_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job de importação não encontrado",
        )

    job_info = import_jobs_cache[job_id]

    # Verificar se usuário tem acesso ao job (mesma empresa)
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
                detail="Acesso negado ao job de importação",
            )

    return job_info


@router.delete(
    "/import/{job_id}", response_model=MessageResponse, summary="Cancelar importação"
)
async def cancel_import(job_id: str, current_user: Usuario = Depends(get_current_user)):
    """
    Cancela um job de importação em andamento
    """
    logger.info(f"🚫 Cancelando job {job_id} - Por: {current_user.email}")

    if job_id not in import_jobs_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job de importação não encontrado",
        )

    job_info = import_jobs_cache[job_id]

    # Verificar acesso
    from ...database.models import UsuarioEmpresaAcesso
    from ...database.connection import db_manager

    with db_manager.session_scope() as db:
        access = (
            db.query(UsuarioEmpresaAcesso)
            .filter(
                UsuarioEmpresaAcesso.usuario_id == current_user.id,
                UsuarioEmpresaAcesso.empresa_id == job_info["empresa_id"],
                UsuarioEmpresaAcesso.nivel_acesso.in_(["admin", "editor"]),
            )
            .first()
        )

        if not access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão insuficiente para cancelar importação",
            )

    # Marcar como cancelado
    if job_info["status"] in ["initiated", "running"]:
        import_jobs_cache[job_id]["status"] = "cancelled"
        import_jobs_cache[job_id]["message"] = "Importação cancelada pelo usuário"

        logger.info(f"✅ Job {job_id} cancelado com sucesso")

        return MessageResponse(
            message="Importação cancelada com sucesso",
            success=True,
            data={"job_id": job_id},
        )
    else:
        raise BusinessLogicError(
            f"Job não pode ser cancelado. Status atual: {job_info['status']}"
        )
