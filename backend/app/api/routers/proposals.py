"""
Router especializado para propostas e lotes (batches) de envio.
Seguindo o Princípio da Responsabilidade Única (SRP).
"""

import asyncio
from typing import List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from loguru import logger
from sqlalchemy import select, and_

from app.auth import get_current_user
from app.database import crud
from app.database.models import ProposalBatchItem
from app.automation.browser import automation_instance as automation
from app.services.proposal_agent import proposal_agent_instance
from app.services.batch_processor import ProposalBatchProcessor
from app.api.schemas import (
    ProposalSubmit,
    ProposalResult,
    ProposalGenerationResult,
    ProposalGenerateRequest,
    ProposalSaveRequest,
    BatchItemUpdateRequest,
    ProposalBatchCreate,
    ProposalBatchResponse,
    ProposalBatchItemResponse,
    ProposalBatchListResponse,
)

router = APIRouter()


# ==================== Histórico Unificado de Propostas ====================


@router.get("/projects/all-proposals")
async def get_all_proposals(
    status: Optional[str] = Query(
        None, description="Filtrar por status: draft, sent, failed, etc."
    ),
    q: Optional[str] = Query(None, description="Termo de busca por título ou texto"),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
):
    """Retorna todas as propostas geradas, salvas e enviadas pelo usuário."""
    return await crud.get_all_unified_proposals(
        user_id=user["user_id"],
        status=status,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.delete("/proposals/{proposal_id}")
async def delete_proposal(
    proposal_id: int,
    user: dict = Depends(get_current_user),
):
    """Remove uma proposta do histórico ou rascunhos."""
    deleted = await crud.delete_proposal_history(user["user_id"], proposal_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Proposta não encontrada.")
    return {"success": True, "message": "Proposta removida com sucesso."}


# ==================== Proposta Individual por Projeto ====================


@router.get("/projects/{project_id}/proposal")
async def get_project_proposal(project_id: str, user: dict = Depends(get_current_user)):
    """Obtém a proposta existente (gerada, rascunho ou enviada) e o histórico de versões para o projeto."""
    proposal = await crud.get_latest_project_proposal(user["user_id"], project_id)
    if not proposal:
        return {"has_proposal": False, "proposal": None, "versions": [], "total_versions": 0}
    return {
        "has_proposal": True,
        **proposal,
    }


@router.get("/projects/{project_id}/versions")
async def get_project_versions(project_id: str, user: dict = Depends(get_current_user)):
    """Lista todas as versões de propostas salvas ou geradas para o projeto."""
    versions = await crud.get_project_proposal_versions(user["user_id"], project_id)
    return {"project_id": project_id, "versions": versions, "total": len(versions)}


@router.delete("/projects/{project_id}/proposals/{proposal_id}")
async def delete_project_proposal(
    project_id: str,
    proposal_id: int,
    user: dict = Depends(get_current_user),
):
    """Remove uma versão específica de proposta deste projeto."""
    deleted = await crud.delete_project_proposal_version(user["user_id"], project_id, proposal_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Versão de proposta não encontrada.")
    versions = await crud.get_project_proposal_versions(user["user_id"], project_id)
    return {
        "success": True,
        "message": "Versão da proposta removida com sucesso.",
        "versions": versions,
    }


@router.post("/projects/{project_id}/save-proposal")
async def save_project_proposal(
    project_id: str,
    payload: ProposalSaveRequest,
    user: dict = Depends(get_current_user),
):
    """Salva ou atualiza a proposta editada nos rascunhos e no lote de envio."""
    try:
        project = await automation.get_project_details(project_id, user_id=user["user_id"])
        project_title = project.title if project else f"Projeto {project_id}"
        project_url = project.url if project else f"https://www.workana.com/job/{project_id}"

        history_id = await crud.save_ai_proposal(
            user_id=user["user_id"],
            project_id=project_id,
            project_title=project_title,
            project_url=project_url,
            proposal_text=payload.proposal_text,
            suggested_price=f"R$ {payload.budget}" if payload.budget else "R$ 0",
            template_id=payload.template_id,
            budget=payload.budget,
            deadline_days=payload.deadline_days or 7,
            status="generated",
            proposal_id=payload.proposal_id,
            force_new_version=payload.force_new_version,
        )

        batch_result = None
        if payload.add_to_batch:
            batch_result = await crud.save_project_to_draft_batch(
                user_id=user["user_id"],
                project_id=project_id,
                proposal_text=payload.proposal_text,
                budget=payload.budget,
                deadline_days=payload.deadline_days or 7,
                template_ref=str(payload.template_id) if payload.template_id else None,
            )

        versions = await crud.get_project_proposal_versions(user["user_id"], project_id)

        return {
            "success": True,
            "message": "Proposta salva nos rascunhos e lotes com sucesso!",
            "proposal_id": history_id,
            "batch_info": batch_result,
            "versions": versions,
        }
    except Exception as e:
        logger.error(f"Erro ao salvar proposta para {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/generate-proposal", response_model=ProposalGenerationResult)
async def generate_proposal(
    project_id: str,
    payload: Optional[ProposalGenerateRequest] = None,
    template_id: Optional[Any] = None,
    user: dict = Depends(get_current_user),
):
    """Gera uma proposta personalizada usando IA ou recupera proposta salva se já gerada."""
    try:
        force_regenerate = payload.force_regenerate if payload else False
        actual_template_id = template_id
        if payload and payload.template_id:
            actual_template_id = payload.template_id

        if not force_regenerate:
            existing = await crud.get_latest_project_proposal(user["user_id"], project_id)
            if existing and existing.get("proposal"):
                versions = await crud.get_project_proposal_versions(user["user_id"], project_id)
                return ProposalGenerationResult(
                    success=True,
                    proposal=existing.get("proposal"),
                    suggested_price=f"R$ {existing.get('budget', 0):.2f}"
                    if existing.get("budget")
                    else None,
                    suggested_deadline_days=existing.get("deadline_days", 7),
                    justification="Proposta carregada do histórico salvo.",
                    template_id_used=existing.get("template_id") or existing.get("template_slug"),
                    proposal_id=existing.get("id"),
                    versions=versions,
                )

        project = await automation.get_project_details(project_id, user_id=user["user_id"])
        if not project:
            raise HTTPException(
                status_code=404, detail="Projeto não encontrado para gerar proposta"
            )

        project_dict = {
            "title": project.title,
            "description": project.description,
            "skills": project.skills,
            "budget": project.budget,
            "client_name": project.client_name,
            "deadline": project.deadline,
        }

        price_level = payload.price_level if payload and payload.price_level else "standard"
        result = await proposal_agent_instance.generate_proposal(
            user["user_id"], project_dict, template_id=actual_template_id, price_level=price_level
        )

        if not result.get("success") and result.get("error_code") == 404:
            raise HTTPException(status_code=404, detail=result.get("error"))

        proposal_id_created = None
        if result.get("success"):
            try:
                save_new = payload.save_as_new_version if payload else True
                proposal_id_created = await crud.save_ai_proposal(
                    user_id=user["user_id"],
                    project_id=project_id,
                    project_title=project.title,
                    project_url=project.url,
                    proposal_text=result.get("proposal", ""),
                    suggested_price=result.get("suggested_price", "R$ 0"),
                    template_id=result.get("template_id_used"),
                    deadline_days=result.get("suggested_deadline_days") or 7,
                    status="generated",
                    force_new_version=save_new,
                )

                await crud.save_project_to_draft_batch(
                    user_id=user["user_id"],
                    project_id=project_id,
                    proposal_text=result.get("proposal", ""),
                    deadline_days=result.get("suggested_deadline_days") or 7,
                    template_ref=str(result.get("template_id_used"))
                    if result.get("template_id_used")
                    else None,
                )
                logger.info(
                    f"Proposta salva no histórico e lotes para o usuário {user['user_id']}, projeto: {project_id}"
                )
            except Exception as e:
                logger.warning(f"Erro ao salvar proposta no histórico: {e}")

        versions = await crud.get_project_proposal_versions(user["user_id"], project_id)
        result["proposal_id"] = proposal_id_created
        result["versions"] = versions
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar proposta: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/submit-proposal", response_model=ProposalResult)
async def submit_proposal(
    project_id: str, proposal: ProposalSubmit, user: dict = Depends(get_current_user)
):
    """Envia uma proposta de fato para o projeto no Workana."""
    try:
        if proposal.project_id != project_id:
            proposal.project_id = project_id

        result = await automation.submit_proposal(user["user_id"], proposal)
        return result
    except Exception as e:
        logger.error(f"Erro ao enviar proposta para {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Lotes de Propostas (Batches) ====================


@router.get("/projects/batches", response_model=ProposalBatchListResponse)
async def list_batches(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
):
    """Lista o histórico de lotes de proposta do usuário."""
    batches = await crud.get_proposal_batches(user["user_id"], limit=limit, offset=offset)
    total = await crud.count_proposal_batches(user["user_id"])
    return ProposalBatchListResponse(batches=batches, total=total)


@router.post("/projects/batch", response_model=ProposalBatchResponse)
async def create_batch_singular(
    payload: ProposalBatchCreate,
    user: dict = Depends(get_current_user),
):
    """Cria um novo lote de propostas para disparo em background ou fila."""
    if not payload.project_ids and not payload.filters and not payload.custom_proposals:
        raise HTTPException(
            status_code=422, detail="Informe project_ids, filters ou custom_proposals."
        )

    custom_proposals_dicts = (
        [p.model_dump() for p in payload.custom_proposals] if payload.custom_proposals else None
    )
    filters_dict = payload.filters.model_dump() if payload.filters else None

    result = await crud.create_proposal_batch(
        user_id=user["user_id"],
        project_ids=payload.project_ids,
        filters=filters_dict,
        exclude_ids=payload.exclude_ids,
        template_ref=payload.template_ref,
        custom_proposals=custom_proposals_dicts,
        daily_limit=payload.daily_limit,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400, detail=result.get("error", "Erro ao criar lote de propostas.")
        )

    batch = await crud.get_proposal_batch(user["user_id"], result["batch_id"])
    if batch:
        asyncio.create_task(ProposalBatchProcessor.process_one())
        return batch

    return result


@router.post("/projects/batches")
async def create_batch(
    payload: ProposalBatchCreate,
    user: dict = Depends(get_current_user),
):
    """Cria um novo lote de propostas (alias plural)."""
    if not payload.project_ids and not payload.filters and not payload.custom_proposals:
        raise HTTPException(
            status_code=422, detail="Informe project_ids, filters ou custom_proposals."
        )

    custom_proposals_dicts = (
        [p.model_dump() for p in payload.custom_proposals] if payload.custom_proposals else None
    )
    filters_dict = payload.filters.model_dump() if payload.filters else None

    result = await crud.create_proposal_batch(
        user_id=user["user_id"],
        project_ids=payload.project_ids,
        filters=filters_dict,
        exclude_ids=payload.exclude_ids,
        template_ref=payload.template_ref,
        custom_proposals=custom_proposals_dicts,
        daily_limit=payload.daily_limit,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400, detail=result.get("error", "Erro ao criar lote de propostas.")
        )

    asyncio.create_task(ProposalBatchProcessor.process_one())
    return result


@router.get("/projects/batches/{batch_id}", response_model=ProposalBatchResponse)
async def get_batch_detail(
    batch_id: int,
    user: dict = Depends(get_current_user),
):
    """Retorna detalhes e itens individuais de um lote de proposta."""
    batch = await crud.get_proposal_batch(user["user_id"], batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Lote de propostas não encontrado.")
    return batch


@router.get("/projects/batches/{batch_id}/items", response_model=List[ProposalBatchItemResponse])
async def get_batch_items(
    batch_id: int,
    user: dict = Depends(get_current_user),
):
    """Lista os itens individuais de um lote de propostas."""
    batch = await crud.get_proposal_batch(user["user_id"], batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Lote de propostas não encontrado.")
    return batch.get("items", [])


@router.post("/projects/batches/{batch_id}/start")
async def start_batch(
    batch_id: int,
    user: dict = Depends(get_current_user),
):
    """Inicia o processamento de um lote de propostas."""
    batch = await crud.get_proposal_batch(user["user_id"], batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Lote de propostas não encontrado.")

    if batch["status"] not in ["queued", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível iniciar um lote com status '{batch['status']}'.",
        )

    processed = await ProposalBatchProcessor.process_one()
    return {
        "success": True,
        "batch_id": batch_id,
        "status": batch["status"],
        "processed": processed,
        "message": "Processamento do lote iniciado.",
    }


@router.post("/projects/batches/{batch_id}/cancel")
async def cancel_batch(
    batch_id: int,
    user: dict = Depends(get_current_user),
):
    """Cancela um lote de propostas em andamento."""
    success = await crud.cancel_proposal_batch(user["user_id"], batch_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lote não encontrado ou não pertence a você.")
    return {"success": True, "message": "Lote de propostas cancelado com sucesso."}


@router.post("/projects/batches/{batch_id}/retry")
async def retry_batch(
    batch_id: int,
    user: dict = Depends(get_current_user),
):
    """Reinicia itens que falharam ou foram cancelados em um lote."""
    success = await crud.retry_failed_batch_items(user["user_id"], batch_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lote não encontrado ou não pertence a você.")

    asyncio.create_task(ProposalBatchProcessor.process_one())
    return {"success": True, "message": "Itens do lote reiniciados para reenvio."}


@router.post("/projects/batches/process-now")
async def trigger_batch_processing(
    user: dict = Depends(get_current_user),
):
    """Aciona manualmente o processamento de um item da fila de lotes."""
    processed = await ProposalBatchProcessor.process_one()
    return {"success": True, "processed": processed}


@router.put("/projects/batches/items/{item_id}")
async def update_batch_item(
    item_id: int,
    payload: BatchItemUpdateRequest,
    user: dict = Depends(get_current_user),
):
    """Atualiza a mensagem, valor ou prazo de um item de lote de propostas."""
    updated = await crud.update_proposal_batch_item(
        user_id=user["user_id"],
        item_id=item_id,
        data=payload.model_dump(exclude_unset=True),
    )
    if not updated:
        raise HTTPException(
            status_code=404, detail="Item do lote não encontrado ou não pertence a você."
        )
    return {"success": True, "item": updated}


@router.delete("/projects/batches/items/{item_id}")
async def delete_batch_item(
    item_id: int,
    user: dict = Depends(get_current_user),
):
    """Exclui um item específico de um lote de propostas."""
    deleted = await crud.delete_proposal_batch_item(user["user_id"], item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item do lote não encontrado.")
    return {"success": True, "message": "Item removido com sucesso."}


@router.post("/projects/batches/items/{item_id}/send-now")
async def send_batch_item_now(
    item_id: int,
    user: dict = Depends(get_current_user),
):
    """Dispara imediatamente o envio de uma proposta individual do lote/rascunhos."""
    async with crud.async_session() as session:
        res = await session.execute(
            select(ProposalBatchItem).where(
                and_(ProposalBatchItem.id == item_id, ProposalBatchItem.user_id == user["user_id"])
            )
        )
        item = res.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Item não encontrado.")

        if not item.generated_message:
            raise HTTPException(
                status_code=400,
                detail="Este item não possui mensagem de proposta gerada para envio.",
            )

        proposal = ProposalSubmit(
            project_id=item.workana_id,
            custom_message=item.generated_message,
            budget=item.budget or 100.0,
            deadline_days=item.deadline_days or 7,
        )

    result = await automation.submit_proposal(user["user_id"], proposal)
    if result.success:
        await crud.update_batch_item_status(item_id, status="sent")
    else:
        await crud.update_batch_item_status(item_id, status="failed", error=result.message)

    return result
