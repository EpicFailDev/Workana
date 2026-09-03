"""
Repository para gerenciamento de lotes de proposta (Proposal Batches e Batch Items).
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy import select, func, and_, update

import app.database.crud as crud
from app.database.models import (
    ProposalBatch as ProposalBatchModel,
    ProposalBatchItem as ProposalBatchItemModel,
    ProjectCatalog as ProjectCatalogModel,
)


async def create_proposal_batch(
    user_id: Any,
    project_ids: Optional[List[str]] = None,
    filters: Optional[dict] = None,
    exclude_ids: Optional[List[str]] = None,
    template_ref: Optional[str] = None,
    custom_proposals: Optional[List[dict]] = None,
    daily_limit: Optional[int] = None,
) -> dict:
    """Cria um novo lote de propostas com itens individuais."""
    async with crud.async_session() as session:
        custom_map = {}
        if custom_proposals:
            for item in custom_proposals:
                wid = item.get("workana_id")
                if wid:
                    custom_map[wid] = item

        if custom_map and not project_ids and not filters:
            resolved_ids = list(custom_map.keys())
        else:
            resolved_ids = await crud.resolve_target_workana_ids(
                user_id=user_id,
                project_ids=project_ids or (list(custom_map.keys()) if custom_map else None),
                filters=filters,
                exclude_ids=exclude_ids or [],
                cap=500,
            )

        if not resolved_ids:
            return {"success": False, "error": "Nenhum projeto selecionado para o lote."}

        catalog_result = await session.execute(
            select(
                ProjectCatalogModel.workana_id,
                ProjectCatalogModel.title,
                ProjectCatalogModel.url,
                ProjectCatalogModel.budget_min,
                ProjectCatalogModel.budget_max,
            ).where(ProjectCatalogModel.workana_id.in_(resolved_ids))
        )
        catalog_dict = {
            row.workana_id: {
                "title": row.title,
                "url": row.url,
                "budget_min": row.budget_min,
                "budget_max": row.budget_max,
            }
            for row in catalog_result.all()
        }

        if not template_ref:
            config = await crud.get_automation_config(user_id)
            pref_tid = config.get("preferred_template_id")
            if pref_tid:
                template_ref = f"personal:{pref_tid}"
            else:
                template_ref = "system:workana-consultivo"

        now = datetime.now(timezone.utc)
        batch = ProposalBatchModel(
            user_id=user_id,
            template_ref=template_ref,
            summary={"source": "manual_selection" if project_ids else "filtered_catalog"},
            status="queued",
            total=len(resolved_ids),
            sent_count=0,
            failed_count=0,
            skipped_count=0,
            daily_limit=daily_limit,
            created_at=now,
            updated_at=now,
        )
        session.add(batch)
        await session.flush()

        batch_items = []
        for wid in resolved_ids:
            cat_data = catalog_dict.get(wid, {})
            custom_data = custom_map.get(wid)

            if custom_data and custom_data.get("proposal_text"):
                item_status = "ready"
                gen_msg = custom_data.get("proposal_text")
                budget_val = custom_data.get("budget")
                deadline_val = custom_data.get("deadline_days") or 7
            else:
                item_status = "queued"
                gen_msg = None
                budget_val = cat_data.get("budget_min") or cat_data.get("budget_max")
                deadline_val = 7

            item = ProposalBatchItemModel(
                batch_id=batch.id,
                user_id=user_id,
                workana_id=wid,
                project_title=cat_data.get("title", f"Projeto {wid}"),
                project_url=cat_data.get("url", f"https://www.workana.com/job/{wid}"),
                status=item_status,
                generated_message=gen_msg,
                budget=budget_val,
                deadline_days=deadline_val,
                attempts=0,
                created_at=now,
                updated_at=now,
            )
            session.add(item)
            batch_items.append(item)

        await session.commit()
        await session.refresh(batch)

        return {
            "success": True,
            "batch_id": batch.id,
            "total": batch.total,
            "status": batch.status,
            "template_ref": batch.template_ref,
        }


async def get_proposal_batches(user_id: Any, limit: int = 20, offset: int = 0) -> List[dict]:
    """Lista lotes de proposta do usuário."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProposalBatchModel)
            .where(ProposalBatchModel.user_id == user_id)
            .order_by(ProposalBatchModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        batches = result.scalars().all()

        return [
            {
                "id": b.id,
                "user_id": str(b.user_id),
                "template_ref": b.template_ref,
                "summary": b.summary,
                "status": b.status,
                "total": b.total,
                "sent_count": b.sent_count,
                "failed_count": b.failed_count,
                "skipped_count": b.skipped_count,
                "daily_limit": b.daily_limit,
                "error": b.error,
                "created_at": b.created_at,
                "started_at": b.started_at,
                "finished_at": b.finished_at,
            }
            for b in batches
        ]


async def count_proposal_batches(user_id: Any) -> int:
    """Retorna contagem total de lotes do usuário."""
    async with crud.async_session() as session:
        res = await session.execute(
            select(func.count(ProposalBatchModel.id)).where(ProposalBatchModel.user_id == user_id)
        )
        return res.scalar() or 0


async def get_proposal_batch(user_id: Any, batch_id: int) -> Optional[dict]:
    """Retorna detalhes completos de um lote com seus itens."""
    async with crud.async_session() as session:
        batch_res = await session.execute(
            select(ProposalBatchModel).where(
                and_(ProposalBatchModel.id == batch_id, ProposalBatchModel.user_id == user_id)
            )
        )
        batch = batch_res.scalar_one_or_none()
        if not batch:
            return None

        items_res = await session.execute(
            select(ProposalBatchItemModel)
            .where(
                and_(
                    ProposalBatchItemModel.batch_id == batch_id,
                    ProposalBatchItemModel.user_id == user_id,
                )
            )
            .order_by(ProposalBatchItemModel.id.asc())
        )
        items = items_res.scalars().all()

        return {
            "id": batch.id,
            "user_id": str(batch.user_id),
            "template_ref": batch.template_ref,
            "summary": batch.summary,
            "status": batch.status,
            "total": batch.total,
            "sent_count": batch.sent_count,
            "failed_count": batch.failed_count,
            "skipped_count": batch.skipped_count,
            "daily_limit": batch.daily_limit,
            "error": batch.error,
            "created_at": batch.created_at,
            "started_at": batch.started_at,
            "finished_at": batch.finished_at,
            "items": [
                {
                    "id": item.id,
                    "batch_id": item.batch_id,
                    "workana_id": item.workana_id,
                    "project_title": item.project_title,
                    "project_url": item.project_url,
                    "status": item.status,
                    "generated_message": item.generated_message,
                    "suggested_price": item.suggested_price,
                    "budget": item.budget,
                    "deadline_days": item.deadline_days,
                    "error": item.error,
                    "attempts": item.attempts,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                    "sent_at": item.sent_at,
                }
                for item in items
            ],
        }


async def cancel_proposal_batch(user_id: Any, batch_id: int) -> bool:
    """Cancela um lote e todos os itens ainda não processados."""
    async with crud.async_session() as session:
        now = datetime.now(timezone.utc)
        batch_res = await session.execute(
            select(ProposalBatchModel).where(
                and_(ProposalBatchModel.id == batch_id, ProposalBatchModel.user_id == user_id)
            )
        )
        batch = batch_res.scalar_one_or_none()
        if not batch:
            return False

        batch.status = "cancelled"
        batch.finished_at = now
        batch.updated_at = now

        await session.execute(
            update(ProposalBatchItemModel)
            .where(
                and_(
                    ProposalBatchItemModel.batch_id == batch_id,
                    ProposalBatchItemModel.user_id == user_id,
                    ProposalBatchItemModel.status.in_(["queued", "generating", "ready"]),
                )
            )
            .values(status="cancelled", updated_at=now)
        )

        await session.commit()
        return True


async def retry_failed_batch_items(user_id: Any, batch_id: int) -> bool:
    """Reinicia itens que falharam ou foram cancelados em um lote."""
    async with crud.async_session() as session:
        now = datetime.now(timezone.utc)
        batch_res = await session.execute(
            select(ProposalBatchModel).where(
                and_(ProposalBatchModel.id == batch_id, ProposalBatchModel.user_id == user_id)
            )
        )
        batch = batch_res.scalar_one_or_none()
        if not batch:
            return False

        batch.status = "queued"
        batch.error = None
        batch.finished_at = None
        batch.updated_at = now

        await session.execute(
            update(ProposalBatchItemModel)
            .where(
                and_(
                    ProposalBatchItemModel.batch_id == batch_id,
                    ProposalBatchItemModel.user_id == user_id,
                    ProposalBatchItemModel.status.in_(["failed", "skipped", "cancelled"]),
                )
            )
            .values(
                status=func.case(
                    (ProposalBatchItemModel.generated_message.isnot(None), "ready"),
                    else_="queued",
                ),
                error=None,
                updated_at=now,
            )
        )

        await session.commit()
        return True


async def recalculate_batch_progress(batch_id: int) -> dict:
    """Recalcula contadores e status geral do lote."""
    async with crud.async_session() as session:
        now = datetime.now(timezone.utc)
        items_res = await session.execute(
            select(
                ProposalBatchItemModel.status,
                func.count(ProposalBatchItemModel.id),
            )
            .where(ProposalBatchItemModel.batch_id == batch_id)
            .group_by(ProposalBatchItemModel.status)
        )
        counts = {status: count for status, count in items_res.all()}

        sent = counts.get("sent", 0)
        failed = counts.get("failed", 0)
        skipped = counts.get("skipped", 0)
        cancelled = counts.get("cancelled", 0)
        pending = (
            counts.get("queued", 0)
            + counts.get("generating", 0)
            + counts.get("ready", 0)
            + counts.get("sending", 0)
        )
        total = sum(counts.values())

        batch_res = await session.execute(
            select(ProposalBatchModel).where(ProposalBatchModel.id == batch_id)
        )
        batch = batch_res.scalar_one_or_none()
        if not batch:
            return {"batch_id": batch_id, "status": "not_found"}

        batch.sent_count = sent
        batch.failed_count = failed
        batch.skipped_count = skipped + cancelled
        batch.total = total
        batch.updated_at = now

        if pending == 0:
            if batch.status != "cancelled":
                if sent > 0 or (failed == 0 and skipped == 0):
                    batch.status = "completed"
                else:
                    batch.status = "failed"
            batch.finished_at = batch.finished_at or now
        else:
            if batch.status == "queued":
                batch.status = "running"
                batch.started_at = batch.started_at or now

        await session.commit()
        return {
            "batch_id": batch_id,
            "status": batch.status,
            "sent_count": sent,
            "failed_count": failed,
            "skipped_count": batch.skipped_count,
            "total": total,
            "pending": pending,
        }


async def get_next_batch_item_for_processing() -> Optional[Tuple[dict, dict]]:
    """Busca o próximo item pendente em qualquer lote ativo para processamento no worker."""
    async with crud.async_session() as session:
        batch_res = await session.execute(
            select(ProposalBatchModel)
            .where(ProposalBatchModel.status.in_(["queued", "running"]))
            .order_by(ProposalBatchModel.created_at.asc())
            .limit(1)
        )
        batch = batch_res.scalar_one_or_none()
        if not batch:
            return None

        now = datetime.now(timezone.utc)
        if batch.status == "queued":
            batch.status = "running"
            batch.started_at = batch.started_at or now
            batch.updated_at = now
            await session.commit()

        item_res = await session.execute(
            select(ProposalBatchItemModel)
            .where(
                and_(
                    ProposalBatchItemModel.batch_id == batch.id,
                    ProposalBatchItemModel.status.in_(["queued", "ready"]),
                )
            )
            .order_by(ProposalBatchItemModel.id.asc())
            .limit(1)
        )
        item = item_res.scalar_one_or_none()
        if not item:
            await recalculate_batch_progress(batch.id)
            return None

        batch_dict = {
            "id": batch.id,
            "user_id": str(batch.user_id),
            "template_ref": batch.template_ref,
            "daily_limit": batch.daily_limit,
            "status": batch.status,
        }
        item_dict = {
            "id": item.id,
            "batch_id": item.batch_id,
            "user_id": str(item.user_id),
            "workana_id": item.workana_id,
            "project_title": item.project_title,
            "project_url": item.project_url,
            "status": item.status,
            "generated_message": item.generated_message,
            "suggested_price": item.suggested_price,
            "budget": item.budget,
            "deadline_days": item.deadline_days,
            "attempts": item.attempts,
        }
        return batch_dict, item_dict


async def update_batch_item_status(
    item_id: int,
    status: str,
    error: Optional[str] = None,
    generated_message: Optional[str] = None,
    budget: Optional[float] = None,
    deadline_days: Optional[int] = None,
    suggested_price: Optional[str] = None,
    increment_attempts: bool = False,
) -> None:
    """Atualiza o status e dados de um item de lote."""
    async with crud.async_session() as session:
        now = datetime.now(timezone.utc)
        values: dict = {"status": status, "updated_at": now}
        if error is not None:
            values["error"] = error
        if generated_message is not None:
            values["generated_message"] = generated_message
        if budget is not None:
            values["budget"] = budget
        if deadline_days is not None:
            values["deadline_days"] = deadline_days
        if suggested_price is not None:
            values["suggested_price"] = suggested_price
        if status == "sent":
            values["sent_at"] = now
            values["error"] = None
        if increment_attempts:
            values["attempts"] = ProposalBatchItemModel.attempts + 1

        await session.execute(
            update(ProposalBatchItemModel)
            .where(ProposalBatchItemModel.id == item_id)
            .values(**values)
        )
        await session.commit()


async def update_proposal_batch_item(
    user_id: Any,
    item_id: int,
    data: dict,
) -> Optional[dict]:
    """Permite ao usuário editar o texto da proposta, valor ou prazo de um item do lote."""
    async with crud.async_session() as session:
        now = datetime.now(timezone.utc)
        item_res = await session.execute(
            select(ProposalBatchItemModel).where(
                and_(
                    ProposalBatchItemModel.id == item_id, ProposalBatchItemModel.user_id == user_id
                )
            )
        )
        item = item_res.scalar_one_or_none()
        if not item:
            return None

        if "generated_message" in data and data["generated_message"] is not None:
            item.generated_message = data["generated_message"]
            if item.status == "queued":
                item.status = "ready"
        if "budget" in data and data["budget"] is not None:
            item.budget = data["budget"]
        if "deadline_days" in data and data["deadline_days"] is not None:
            item.deadline_days = data["deadline_days"]
        if "status" in data and data["status"] is not None:
            item.status = data["status"]

        item.updated_at = now
        await session.commit()
        await session.refresh(item)

        return {
            "id": item.id,
            "batch_id": item.batch_id,
            "workana_id": item.workana_id,
            "project_title": item.project_title,
            "project_url": item.project_url,
            "status": item.status,
            "generated_message": item.generated_message,
            "budget": item.budget,
            "deadline_days": item.deadline_days,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        }


async def delete_proposal_batch_item(user_id: Any, item_id: int) -> bool:
    """Exclui um item do lote e recalcula o progresso do lote."""
    async with crud.async_session() as session:
        item_res = await session.execute(
            select(ProposalBatchItemModel).where(
                and_(
                    ProposalBatchItemModel.id == item_id, ProposalBatchItemModel.user_id == user_id
                )
            )
        )
        item = item_res.scalar_one_or_none()
        if not item:
            return False

        batch_id = item.batch_id
        await session.delete(item)
        await session.commit()

        await recalculate_batch_progress(batch_id)
        return True


async def save_project_to_draft_batch(
    user_id: Any,
    project_id: str,
    proposal_text: str,
    budget: Optional[float] = None,
    deadline_days: int = 7,
    template_ref: Optional[str] = None,
) -> dict:
    """Adiciona ou atualiza uma proposta nos lotes em fila / rascunho do usuário."""
    async with crud.async_session() as session:
        now = datetime.now(timezone.utc)

        # Buscar lote recente aberto ('queued' ou 'running')
        batch_res = await session.execute(
            select(ProposalBatchModel)
            .where(
                and_(
                    ProposalBatchModel.user_id == user_id,
                    ProposalBatchModel.status.in_(["queued", "running"]),
                )
            )
            .order_by(ProposalBatchModel.created_at.desc())
            .limit(1)
        )
        batch = batch_res.scalar_one_or_none()

        # Se não houver lote aberto, cria um lote 'queued' para rascunhos
        if not batch:
            batch = ProposalBatchModel(
                user_id=user_id,
                template_ref=template_ref or "system:workana-consultivo",
                summary={"source": "ai_draft_queue"},
                status="queued",
                total=0,
                sent_count=0,
                failed_count=0,
                skipped_count=0,
                created_at=now,
                updated_at=now,
            )
            session.add(batch)
            await session.flush()

        # Buscar detalhes do projeto no catálogo
        cat_res = await session.execute(
            select(ProjectCatalogModel).where(ProjectCatalogModel.workana_id == project_id)
        )
        cat = cat_res.scalar_one_or_none()
        project_title = cat.title if cat else f"Projeto {project_id}"
        project_url = cat.url if cat else f"https://www.workana.com/job/{project_id}"
        if budget is None and cat:
            budget = cat.budget_min or cat.budget_max

        # Verificar se já existe o item neste lote
        item_res = await session.execute(
            select(ProposalBatchItemModel).where(
                and_(
                    ProposalBatchItemModel.batch_id == batch.id,
                    ProposalBatchItemModel.workana_id == project_id,
                )
            )
        )
        item = item_res.scalar_one_or_none()

        if item:
            item.generated_message = proposal_text
            item.budget = budget
            item.deadline_days = deadline_days
            item.status = "ready"
            item.updated_at = now
        else:
            item = ProposalBatchItemModel(
                batch_id=batch.id,
                user_id=user_id,
                workana_id=project_id,
                project_title=project_title,
                project_url=project_url,
                status="ready",
                generated_message=proposal_text,
                budget=budget,
                deadline_days=deadline_days,
                attempts=0,
                created_at=now,
                updated_at=now,
            )
            session.add(item)

        await session.commit()
        await recalculate_batch_progress(batch.id)

        return {
            "success": True,
            "batch_id": batch.id,
            "item_id": item.id,
            "workana_id": project_id,
            "status": "ready",
            "message": "Proposta salva com sucesso no lote de rascunhos!",
        }
