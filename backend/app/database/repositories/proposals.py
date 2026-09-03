"""
Repository para gerenciamento de histórico e status de propostas de usuários.
"""
from typing import Optional, List, Dict, Any
import re
from datetime import datetime, timezone
from sqlalchemy import select, and_, or_, delete, func

import app.database.crud as crud
from app.database.models import (
    ProposalHistory as ProposalHistoryModel,
    ProposalBatchItem as ProposalBatchItemModel,
    Project as ProjectModel,
    ProjectCatalog as ProjectCatalogModel,
)
from app.api.schemas import ProposalSubmit, ProposalResult, ProposalHistory


async def save_proposal_history(user_id: Any, proposal: ProposalSubmit, result: ProposalResult) -> None:
    """Salva uma tentativa de envio de proposta no histórico."""
    async with crud.async_session() as session:
        project_title = getattr(proposal, "project_title", None)
        project_url = getattr(proposal, "project_url", None)
        
        if not project_title or not project_url:
            # Buscar no catálogo
            cat_res = await session.execute(
                select(ProjectCatalogModel).where(ProjectCatalogModel.workana_id == proposal.project_id)
            )
            cat = cat_res.scalar_one_or_none()
            if cat:
                project_title = project_title or cat.title
                project_url = project_url or cat.url
            else:
                proj_result = await session.execute(
                    select(ProjectModel).where(and_(ProjectModel.user_id == user_id, ProjectModel.workana_id == proposal.project_id))
                )
                db_project = proj_result.scalar_one_or_none()
                if db_project:
                    project_title = project_title or db_project.title
                    project_url = project_url or db_project.url
                else:
                    project_title = project_title or f"Projeto {proposal.project_id}"
                    project_url = project_url or f"https://www.workana.com/job/{proposal.project_id}"

        now = datetime.now(timezone.utc)
        
        # Verificar se já existia registro gerado para este projeto e atualizar
        existing_res = await session.execute(
            select(ProposalHistoryModel).where(
                and_(ProposalHistoryModel.user_id == user_id, ProposalHistoryModel.project_id == proposal.project_id)
            ).order_by(ProposalHistoryModel.sent_at.desc())
        )
        existing = existing_res.scalar_one_or_none()
        
        if existing:
            existing.project_title = project_title
            existing.project_url = project_url
            existing.budget = proposal.budget
            existing.deadline_days = proposal.deadline_days
            existing.message = proposal.custom_message or getattr(proposal, "message", None) or existing.message
            existing.status = "sent" if result.success else "failed"
            existing.sent_at = now
            if proposal.template_id:
                existing.template_id = proposal.template_id if isinstance(proposal.template_id, int) else None
        else:
            history = ProposalHistoryModel(
                user_id=user_id,
                project_id=proposal.project_id,
                project_title=project_title,
                project_url=project_url,
                budget=proposal.budget,
                deadline_days=proposal.deadline_days,
                message=proposal.custom_message or getattr(proposal, "message", None),
                status="sent" if result.success else "failed",
                template_id=proposal.template_id if isinstance(proposal.template_id, int) else None,
                sent_at=now,
            )
            session.add(history)
            
        await session.commit()


async def get_project_proposal_versions(user_id: Any, project_id: str) -> List[Dict[str, Any]]:
    """Obtém todas as versões de proposta geradas ou salvas para um projeto específico."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProposalHistoryModel)
            .where(
                and_(ProposalHistoryModel.user_id == user_id, ProposalHistoryModel.project_id == project_id)
            )
            .order_by(ProposalHistoryModel.sent_at.desc())
        )
        histories = result.scalars().all()
        versions = []
        for h in histories:
            versions.append({
                "id": h.id,
                "project_id": h.project_id,
                "project_title": h.project_title,
                "project_url": h.project_url,
                "proposal": h.message,
                "budget": h.budget,
                "deadline_days": h.deadline_days,
                "status": h.status,
                "sent_at": h.sent_at.isoformat() if h.sent_at else None,
                "template_id": h.template_id,
                "template_slug": h.template_slug,
                "template_version": h.template_version,
                "template_type": h.template_type,
                "source": "history",
            })
        return versions


async def get_latest_project_proposal(user_id: Any, project_id: str) -> Optional[Dict[str, Any]]:
    """Obtém a proposta mais recente e a lista de versões para um projeto específico."""
    versions = await get_project_proposal_versions(user_id, project_id)
    if versions:
        latest = versions[0]
        return {
            "has_proposal": True,
            **latest,
            "versions": versions,
            "total_versions": len(versions),
        }

    # 2. Buscar nos itens de lote de proposta (se houver gerado lá)
    async with crud.async_session() as session:
        item_res = await session.execute(
            select(ProposalBatchItemModel)
            .where(
                and_(ProposalBatchItemModel.user_id == user_id, ProposalBatchItemModel.workana_id == project_id)
            )
            .order_by(ProposalBatchItemModel.updated_at.desc())
            .limit(1)
        )
        item = item_res.scalar_one_or_none()
        if item and item.generated_message:
            item_data = {
                "id": item.id,
                "batch_id": item.batch_id,
                "project_id": item.workana_id,
                "project_title": item.project_title,
                "project_url": item.project_url,
                "proposal": item.generated_message,
                "budget": item.budget,
                "deadline_days": item.deadline_days,
                "status": item.status,
                "sent_at": item.sent_at.isoformat() if item.sent_at else None,
                "suggested_price": item.suggested_price,
                "source": "batch_item",
            }
            return {
                "has_proposal": True,
                **item_data,
                "versions": [item_data],
                "total_versions": 1,
            }

    return None


async def save_ai_proposal(
    user_id: Any,
    project_id: str,
    project_title: str,
    project_url: str,
    proposal_text: str,
    suggested_price: str,
    template_id: Optional[Any] = None,
    budget: Optional[float] = None,
    deadline_days: int = 7,
    status: str = "generated",
    proposal_id: Optional[int] = None,
    force_new_version: bool = False,
) -> int:
    """Salva ou atualiza uma proposta no histórico do usuário com suporte a versionamento."""
    async with crud.async_session() as session:
        if budget is None:
            price_clean = str(suggested_price).replace('.', '').replace(',', '.')
            price_match = re.search(r'[\d.]+', price_clean)
            budget = float(price_match.group()) if price_match else 0.0

        numeric_template_id = template_id if isinstance(template_id, int) else None
        template_slug = None
        template_type = None
        if isinstance(template_id, str):
            if template_id.startswith("personal:"):
                try:
                    numeric_template_id = int(template_id.split(":")[1])
                    template_type = "personal"
                except Exception:
                    pass
            elif template_id.startswith("system:"):
                template_slug = template_id.split(":")[1]
                template_type = "system"
            else:
                try:
                    numeric_template_id = int(template_id)
                    template_type = "personal"
                except Exception:
                    template_slug = template_id

        now = datetime.now(timezone.utc)

        # Se proposal_id for especificado, atualiza especificamente esse registro
        if proposal_id and not force_new_version:
            res = await session.execute(
                select(ProposalHistoryModel).where(
                    and_(ProposalHistoryModel.id == proposal_id, ProposalHistoryModel.user_id == user_id)
                )
            )
            existing = res.scalar_one_or_none()
            if existing:
                existing.project_title = project_title or existing.project_title
                existing.project_url = project_url or existing.project_url
                existing.message = proposal_text
                existing.budget = budget
                existing.deadline_days = deadline_days
                if existing.status != "sent":
                    existing.status = status
                if numeric_template_id is not None:
                    existing.template_id = numeric_template_id
                if template_slug is not None:
                    existing.template_slug = template_slug
                if template_type is not None:
                    existing.template_type = template_type
                existing.sent_at = now
                await session.commit()
                return existing.id

        # Se não forçar nova versão e não especificou proposal_id, atualiza rascunho mais recente não enviado
        if not force_new_version:
            existing_res = await session.execute(
                select(ProposalHistoryModel).where(
                    and_(
                        ProposalHistoryModel.user_id == user_id,
                        ProposalHistoryModel.project_id == project_id,
                        ProposalHistoryModel.status.in_(["generated", "draft", "ready"])
                    )
                ).order_by(ProposalHistoryModel.sent_at.desc())
            )
            existing = existing_res.scalar_one_or_none()
            if existing:
                existing.project_title = project_title or existing.project_title
                existing.project_url = project_url or existing.project_url
                existing.message = proposal_text
                existing.budget = budget
                existing.deadline_days = deadline_days
                existing.status = status
                if numeric_template_id is not None:
                    existing.template_id = numeric_template_id
                if template_slug is not None:
                    existing.template_slug = template_slug
                if template_type is not None:
                    existing.template_type = template_type
                existing.sent_at = now
                await session.commit()
                return existing.id

        # Cria uma nova versão
        history = ProposalHistoryModel(
            user_id=user_id,
            project_id=project_id,
            project_title=project_title,
            project_url=project_url,
            budget=budget,
            deadline_days=deadline_days,
            message=proposal_text,
            status=status,
            template_id=numeric_template_id,
            template_slug=template_slug,
            template_type=template_type,
            sent_at=now,
        )
        session.add(history)
        await session.commit()
        await session.refresh(history)
        return history.id


async def delete_project_proposal_version(user_id: Any, project_id: str, proposal_id: int) -> bool:
    """Remove uma versão específica de proposta de um projeto."""
    async with crud.async_session() as session:
        result = await session.execute(
            delete(ProposalHistoryModel).where(
                and_(
                    ProposalHistoryModel.id == proposal_id,
                    ProposalHistoryModel.project_id == project_id,
                    ProposalHistoryModel.user_id == user_id
                )
            )
        )
        await session.commit()
        return result.rowcount > 0


async def get_proposal_history(user_id: Any, limit: int = 50) -> List[ProposalHistory]:
    """Obtém o histórico de propostas do usuário."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProposalHistoryModel)
            .where(ProposalHistoryModel.user_id == user_id)
            .order_by(ProposalHistoryModel.sent_at.desc())
            .limit(limit)
        )
        history = result.scalars().all()
        
        return [
            ProposalHistory(
                id=h.id,
                project_id=h.project_id,
                project_title=h.project_title,
                project_url=h.project_url,
                budget=h.budget,
                deadline_days=h.deadline_days,
                status=h.status,
                sent_at=h.sent_at,
                template_id=h.template_id
            )
            for h in history
        ]


async def get_all_unified_proposals(
    user_id: Any,
    status: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """Lista todas as propostas salvas, geradas e enviadas do usuário com filtro e busca."""
    async with crud.async_session() as session:
        query = select(ProposalHistoryModel).where(ProposalHistoryModel.user_id == user_id)
        
        if status:
            if status == "draft" or status == "generated":
                query = query.where(ProposalHistoryModel.status.in_(["generated", "draft", "ready"]))
            elif status == "sent":
                query = query.where(ProposalHistoryModel.status == "sent")
            elif status == "failed":
                query = query.where(ProposalHistoryModel.status == "failed")
            else:
                query = query.where(ProposalHistoryModel.status == status)

        if q:
            pattern = f"%{q}%"
            query = query.where(
                or_(
                    ProposalHistoryModel.project_title.ilike(pattern),
                    ProposalHistoryModel.project_id.ilike(pattern),
                    ProposalHistoryModel.message.ilike(pattern),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_res = await session.execute(count_query)
        total = total_res.scalar() or 0

        query = query.order_by(ProposalHistoryModel.sent_at.desc()).limit(limit).offset(offset)
        result = await session.execute(query)
        rows = result.scalars().all()

        items = []
        for r in rows:
            items.append({
                "id": r.id,
                "project_id": r.project_id,
                "project_title": r.project_title,
                "project_url": r.project_url,
                "message": r.message,
                "budget": r.budget,
                "deadline_days": r.deadline_days,
                "status": r.status,
                "sent_at": r.sent_at.isoformat() if r.sent_at else None,
                "template_id": r.template_id,
                "template_slug": r.template_slug,
                "template_type": r.template_type,
            })

        return {
            "proposals": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }


async def update_proposal_status(user_id: Any, proposal_id: int, status: str) -> bool:
    """Atualiza o status de uma proposta do usuário."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProposalHistoryModel)
            .where(and_(ProposalHistoryModel.id == proposal_id, ProposalHistoryModel.user_id == user_id))
        )
        proposal = result.scalar_one_or_none()
        
        if proposal:
            proposal.status = status
            await session.commit()
            return True
        return False


async def delete_proposal_history(user_id: Any, proposal_id: int) -> bool:
    """Remove uma proposta do histórico do usuário."""
    async with crud.async_session() as session:
        result = await session.execute(
            delete(ProposalHistoryModel).where(
                and_(ProposalHistoryModel.id == proposal_id, ProposalHistoryModel.user_id == user_id)
            )
        )
        await session.commit()
        return result.rowcount > 0

