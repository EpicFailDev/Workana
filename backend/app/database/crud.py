"""
Operações CRUD para o banco de dados.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, func, delete, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.fernet import Fernet
import base64
import hashlib

from app.database.models import (
    async_session, Credentials, SavedFilter as SavedFilterModel,
    ProposalTemplate as ProposalTemplateModel, ProposalHistory as ProposalHistoryModel,
    AutomationConfig as AutomationConfigModel, Project as ProjectModel,
    ActivityLog as ActivityLogModel, DailyStatistics as DailyStatisticsModel,
    BlacklistedClient as BlacklistedClientModel
)
from app.api.schemas import (
    SavedFilter, ProposalTemplate, ProposalTemplateCreate,
    ProposalSubmit, ProposalResult, ProposalHistory, DashboardStats
)
from app.config import settings


def _get_fernet():
    """Retorna instância do Fernet para criptografia."""
    key = settings.encryption_key.encode()
    # Criar chave de 32 bytes a partir da configuração
    key = hashlib.sha256(key).digest()
    key = base64.urlsafe_b64encode(key)
    return Fernet(key)


def _encrypt(text: str) -> str:
    """Criptografa um texto."""
    fernet = _get_fernet()
    return fernet.encrypt(text.encode()).decode()


def _decrypt(encrypted_text: str) -> str:
    """Descriptografa um texto."""
    fernet = _get_fernet()
    return fernet.decrypt(encrypted_text.encode()).decode()


# ==================== Credenciais ====================

async def save_credentials(email: str, password: str):
    """Salva as credenciais criptografadas."""
    async with async_session() as session:
        # Remover credenciais antigas
        await session.execute(delete(Credentials))
        
        # Inserir novas credenciais
        encrypted_password = _encrypt(password)
        creds = Credentials(email=email, encrypted_password=encrypted_password)
        session.add(creds)
        await session.commit()


async def get_credentials() -> Optional[Dict[str, str]]:
    """Obtém as credenciais descriptografadas."""
    async with async_session() as session:
        result = await session.execute(select(Credentials).limit(1))
        creds = result.scalar_one_or_none()
        
        if creds:
            try:
                password = _decrypt(creds.encrypted_password)
                return {"email": creds.email, "password": password}
            except Exception:
                return None
        return None


# ==================== Filtros Salvos ====================

async def get_saved_filters() -> List[SavedFilter]:
    """Lista todos os filtros salvos."""
    async with async_session() as session:
        result = await session.execute(select(SavedFilterModel).order_by(SavedFilterModel.created_at.desc()))
        filters = result.scalars().all()
        
        return [
            SavedFilter(
                id=f.id,
                name=f.name,
                filters=f.filters_json,
                created_at=f.created_at
            )
            for f in filters
        ]


async def create_filter(filter_data: SavedFilter) -> SavedFilter:
    """Cria um novo filtro."""
    async with async_session() as session:
        db_filter = SavedFilterModel(
            name=filter_data.name,
            filters_json=filter_data.filters.model_dump()
        )
        session.add(db_filter)
        await session.commit()
        await session.refresh(db_filter)
        
        return SavedFilter(
            id=db_filter.id,
            name=db_filter.name,
            filters=filter_data.filters,
            created_at=db_filter.created_at
        )


async def delete_filter(filter_id: int):
    """Remove um filtro."""
    async with async_session() as session:
        await session.execute(delete(SavedFilterModel).where(SavedFilterModel.id == filter_id))
        await session.commit()


# ==================== Templates ====================

async def get_templates() -> List[ProposalTemplate]:
    """Lista todos os templates."""
    async with async_session() as session:
        result = await session.execute(
            select(ProposalTemplateModel).order_by(ProposalTemplateModel.is_default.desc(), ProposalTemplateModel.name)
        )
        templates = result.scalars().all()
        
        return [
            ProposalTemplate(
                id=t.id,
                name=t.name,
                content=t.content,
                default_budget=t.default_budget,
                default_deadline_days=t.default_deadline_days,
                is_default=t.is_default,
                created_at=t.created_at,
                updated_at=t.updated_at
            )
            for t in templates
        ]


async def get_template(template_id: int) -> Optional[ProposalTemplate]:
    """Obtém um template específico."""
    async with async_session() as session:
        result = await session.execute(
            select(ProposalTemplateModel).where(ProposalTemplateModel.id == template_id)
        )
        t = result.scalar_one_or_none()
        
        if t:
            return ProposalTemplate(
                id=t.id,
                name=t.name,
                content=t.content,
                default_budget=t.default_budget,
                default_deadline_days=t.default_deadline_days,
                is_default=t.is_default,
                created_at=t.created_at,
                updated_at=t.updated_at
            )
        return None


async def create_template(template: ProposalTemplateCreate) -> ProposalTemplate:
    """Cria um novo template."""
    async with async_session() as session:
        # Se é default, remover default dos outros
        if template.is_default:
            await session.execute(
                ProposalTemplateModel.__table__.update().values(is_default=False)
            )
        
        db_template = ProposalTemplateModel(
            name=template.name,
            content=template.content,
            default_budget=template.default_budget,
            default_deadline_days=template.default_deadline_days,
            is_default=template.is_default
        )
        session.add(db_template)
        await session.commit()
        await session.refresh(db_template)
        
        return ProposalTemplate(
            id=db_template.id,
            name=db_template.name,
            content=db_template.content,
            default_budget=db_template.default_budget,
            default_deadline_days=db_template.default_deadline_days,
            is_default=db_template.is_default,
            created_at=db_template.created_at,
            updated_at=db_template.updated_at
        )


async def update_template(template_id: int, template: ProposalTemplateCreate) -> Optional[ProposalTemplate]:
    """Atualiza um template existente."""
    async with async_session() as session:
        result = await session.execute(
            select(ProposalTemplateModel).where(ProposalTemplateModel.id == template_id)
        )
        db_template = result.scalar_one_or_none()
        
        if not db_template:
            return None
        
        # Se é default, remover default dos outros
        if template.is_default:
            await session.execute(
                ProposalTemplateModel.__table__.update().values(is_default=False)
            )
        
        db_template.name = template.name
        db_template.content = template.content
        db_template.default_budget = template.default_budget
        db_template.default_deadline_days = template.default_deadline_days
        db_template.is_default = template.is_default
        db_template.updated_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(db_template)
        
        return ProposalTemplate(
            id=db_template.id,
            name=db_template.name,
            content=db_template.content,
            default_budget=db_template.default_budget,
            default_deadline_days=db_template.default_deadline_days,
            is_default=db_template.is_default,
            created_at=db_template.created_at,
            updated_at=db_template.updated_at
        )


async def delete_template(template_id: int):
    """Remove um template."""
    async with async_session() as session:
        await session.execute(delete(ProposalTemplateModel).where(ProposalTemplateModel.id == template_id))
        await session.commit()


# ==================== Histórico de Propostas ====================

async def save_proposal_history(proposal: ProposalSubmit, result: ProposalResult):
    """Salva uma proposta no histórico."""
    async with async_session() as session:
        history = ProposalHistoryModel(
            project_id=proposal.project_id,
            project_title=f"Projeto {proposal.project_id}",  # Será atualizado com título real
            budget=proposal.budget,
            deadline_days=proposal.deadline_days,
            message=proposal.custom_message,
            status="sent" if result.success else "failed"
        )
        session.add(history)
        await session.commit()


async def get_proposal_history(limit: int = 50) -> List[ProposalHistory]:
    """Obtém o histórico de propostas."""
    async with async_session() as session:
        result = await session.execute(
            select(ProposalHistoryModel)
            .order_by(ProposalHistoryModel.sent_at.desc())
            .limit(limit)
        )
        history = result.scalars().all()
        
        return [
            ProposalHistory(
                id=h.id,
                project_id=h.project_id,
                project_title=h.project_title,
                budget=h.budget,
                deadline_days=h.deadline_days,
                status=h.status,
                sent_at=h.sent_at,
                message_preview=h.message[:100] if h.message else None
            )
            for h in history
        ]


async def get_daily_stats() -> Dict[str, int]:
    """Obtém estatísticas diárias."""
    async with async_session() as session:
        today = datetime.utcnow().date()
        result = await session.execute(
            select(func.count(ProposalHistoryModel.id))
            .where(func.date(ProposalHistoryModel.sent_at) == today)
        )
        proposals_today = result.scalar() or 0
        
        return {"proposals_today": proposals_today}


# ==================== Dashboard ====================

async def get_dashboard_stats() -> DashboardStats:
    """Obtém estatísticas do dashboard."""
    async with async_session() as session:
        now = datetime.utcnow()
        today = now.date()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Total de propostas
        total = await session.execute(select(func.count(ProposalHistoryModel.id)))
        total_proposals = total.scalar() or 0
        
        # Propostas hoje
        today_result = await session.execute(
            select(func.count(ProposalHistoryModel.id))
            .where(func.date(ProposalHistoryModel.sent_at) == today)
        )
        proposals_today = today_result.scalar() or 0
        
        # Propostas esta semana
        week_result = await session.execute(
            select(func.count(ProposalHistoryModel.id))
            .where(ProposalHistoryModel.sent_at >= week_ago)
        )
        proposals_week = week_result.scalar() or 0
        
        # Propostas este mês
        month_result = await session.execute(
            select(func.count(ProposalHistoryModel.id))
            .where(ProposalHistoryModel.sent_at >= month_ago)
        )
        proposals_month = month_result.scalar() or 0
        
        # Aceitas
        accepted_result = await session.execute(
            select(func.count(ProposalHistoryModel.id))
            .where(ProposalHistoryModel.status == "accepted")
        )
        accepted = accepted_result.scalar() or 0
        
        # Última atividade
        last_activity_result = await session.execute(
            select(ProposalHistoryModel.sent_at)
            .order_by(ProposalHistoryModel.sent_at.desc())
            .limit(1)
        )
        last_activity = last_activity_result.scalar_one_or_none()
        
        # Taxa de resposta
        response_rate = (accepted / total_proposals * 100) if total_proposals > 0 else 0.0
        
        return DashboardStats(
            total_proposals_sent=total_proposals,
            proposals_today=proposals_today,
            proposals_this_week=proposals_week,
            proposals_this_month=proposals_month,
            response_rate=round(response_rate, 1),
            accepted_proposals=accepted,
            pending_proposals=total_proposals - accepted,
            last_activity=last_activity
        )


# ==================== Configuração de Automação ====================

async def get_automation_config() -> Dict[str, Any]:
    """Obtém configurações de automação."""
    async with async_session() as session:
        result = await session.execute(select(AutomationConfigModel).limit(1))
        config = result.scalar_one_or_none()
        
        if config:
            return {
                "headless": config.headless,
                "delay_between_actions_ms": config.delay_between_actions_ms,
                "max_proposals_per_day": config.max_proposals_per_day,
                "auto_apply": config.auto_apply,
                "preferred_template_id": config.preferred_template_id
            }
        
        # Configurações padrão
        return {
            "headless": True,
            "delay_between_actions_ms": 2000,
            "max_proposals_per_day": 10,
            "auto_apply": False,
            "preferred_template_id": None
        }


async def save_automation_config(config: Dict[str, Any]):
    """Salva configurações de automação."""
    async with async_session() as session:
        result = await session.execute(select(AutomationConfigModel).limit(1))
        db_config = result.scalar_one_or_none()
        
        if db_config:
            db_config.headless = config.get("headless", True)
            db_config.delay_between_actions_ms = config.get("delay_between_actions_ms", 2000)
            db_config.max_proposals_per_day = config.get("max_proposals_per_day", 10)
            db_config.auto_apply = config.get("auto_apply", False)
            db_config.preferred_template_id = config.get("preferred_template_id")
        else:
            db_config = AutomationConfigModel(
                headless=config.get("headless", True),
                delay_between_actions_ms=config.get("delay_between_actions_ms", 2000),
                max_proposals_per_day=config.get("max_proposals_per_day", 10),
                auto_apply=config.get("auto_apply", False),
                preferred_template_id=config.get("preferred_template_id")
            )
            session.add(db_config)
        
        await session.commit()


# ==================== Projetos ====================

async def save_project(project_data: Dict[str, Any]) -> int:
    """Salva ou atualiza um projeto encontrado."""
    async with async_session() as session:
        # Verificar se já existe
        result = await session.execute(
            select(ProjectModel).where(ProjectModel.workana_id == project_data.get("workana_id"))
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Atualizar projeto existente
            for key, value in project_data.items():
                if hasattr(existing, key) and key != "id":
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            await session.commit()
            return existing.id
        else:
            # Criar novo projeto
            project = ProjectModel(**project_data)
            session.add(project)
            await session.commit()
            await session.refresh(project)
            return project.id


async def get_projects(
    limit: int = 50,
    offset: int = 0,
    only_favorites: bool = False,
    only_not_applied: bool = False,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista projetos salvos com filtros."""
    async with async_session() as session:
        query = select(ProjectModel)
        
        if only_favorites:
            query = query.where(ProjectModel.is_favorite == True)
        if only_not_applied:
            query = query.where(ProjectModel.is_applied == False)
        if category:
            query = query.where(ProjectModel.category == category)
        
        query = query.where(ProjectModel.is_ignored == False)
        query = query.order_by(ProjectModel.found_at.desc())
        query = query.offset(offset).limit(limit)
        
        result = await session.execute(query)
        projects = result.scalars().all()
        
        return [
            {
                "id": p.id,
                "workana_id": p.workana_id,
                "title": p.title,
                "description": p.description,
                "url": p.url,
                "category": p.category,
                "budget_min": p.budget_min,
                "budget_max": p.budget_max,
                "budget_type": p.budget_type,
                "deadline": p.deadline,
                "skills": p.skills,
                "client_name": p.client_name,
                "client_country": p.client_country,
                "client_rating": p.client_rating,
                "proposals_count": p.proposals_count,
                "is_favorite": p.is_favorite,
                "is_applied": p.is_applied,
                "notes": p.notes,
                "found_at": p.found_at.isoformat() if p.found_at else None
            }
            for p in projects
        ]


async def get_project(project_id: int) -> Optional[Dict[str, Any]]:
    """Obtém um projeto específico."""
    async with async_session() as session:
        result = await session.execute(
            select(ProjectModel).where(ProjectModel.id == project_id)
        )
        p = result.scalar_one_or_none()
        
        if p:
            return {
                "id": p.id,
                "workana_id": p.workana_id,
                "title": p.title,
                "description": p.description,
                "url": p.url,
                "category": p.category,
                "subcategory": p.subcategory,
                "budget_min": p.budget_min,
                "budget_max": p.budget_max,
                "budget_type": p.budget_type,
                "deadline": p.deadline,
                "skills": p.skills,
                "client_name": p.client_name,
                "client_country": p.client_country,
                "client_rating": p.client_rating,
                "client_projects_posted": p.client_projects_posted,
                "proposals_count": p.proposals_count,
                "is_favorite": p.is_favorite,
                "is_applied": p.is_applied,
                "is_ignored": p.is_ignored,
                "notes": p.notes,
                "found_at": p.found_at.isoformat() if p.found_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None
            }
        return None


async def toggle_project_favorite(project_id: int) -> bool:
    """Alterna o status de favorito de um projeto."""
    async with async_session() as session:
        result = await session.execute(
            select(ProjectModel).where(ProjectModel.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if project:
            project.is_favorite = not project.is_favorite
            await session.commit()
            return project.is_favorite
        return False


async def mark_project_applied(project_id: int):
    """Marca um projeto como aplicado."""
    async with async_session() as session:
        result = await session.execute(
            select(ProjectModel).where(ProjectModel.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if project:
            project.is_applied = True
            project.updated_at = datetime.utcnow()
            await session.commit()


async def ignore_project(project_id: int):
    """Ignora um projeto."""
    async with async_session() as session:
        result = await session.execute(
            select(ProjectModel).where(ProjectModel.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if project:
            project.is_ignored = True
            await session.commit()


async def update_project_notes(project_id: int, notes: str):
    """Atualiza notas de um projeto."""
    async with async_session() as session:
        result = await session.execute(
            select(ProjectModel).where(ProjectModel.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if project:
            project.notes = notes
            project.updated_at = datetime.utcnow()
            await session.commit()


# ==================== Log de Atividades ====================

async def log_activity(
    action_type: str,
    description: str,
    details: Optional[Dict[str, Any]] = None,
    project_id: Optional[int] = None,
    status: str = "success",
    error_message: Optional[str] = None,
    duration_ms: Optional[int] = None
):
    """Registra uma atividade no log."""
    async with async_session() as session:
        log = ActivityLogModel(
            action_type=action_type,
            action_description=description,
            details=details,
            project_id=project_id,
            status=status,
            error_message=error_message,
            duration_ms=duration_ms
        )
        session.add(log)
        await session.commit()
        
        # Atualizar estatísticas diárias
        await _update_daily_stats(action_type, status)


async def get_activity_logs(
    limit: int = 100,
    action_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Obtém logs de atividade."""
    async with async_session() as session:
        query = select(ActivityLogModel)
        
        if action_type:
            query = query.where(ActivityLogModel.action_type == action_type)
        if status:
            query = query.where(ActivityLogModel.status == status)
        
        query = query.order_by(ActivityLogModel.created_at.desc()).limit(limit)
        
        result = await session.execute(query)
        logs = result.scalars().all()
        
        return [
            {
                "id": log.id,
                "action_type": log.action_type,
                "description": log.action_description,
                "details": log.details,
                "project_id": log.project_id,
                "status": log.status,
                "error_message": log.error_message,
                "duration_ms": log.duration_ms,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]


# ==================== Estatísticas Diárias ====================

async def _update_daily_stats(action_type: str, status: str):
    """Atualiza estatísticas diárias internas."""
    async with async_session() as session:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        result = await session.execute(
            select(DailyStatisticsModel).where(DailyStatisticsModel.date == today)
        )
        stats = result.scalar_one_or_none()
        
        if not stats:
            stats = DailyStatisticsModel(date=today)
            session.add(stats)
        
        # Atualizar contadores baseado no tipo de ação
        if action_type == "login":
            stats.logins_count += 1
        elif action_type == "search":
            stats.searches_count += 1
        elif action_type == "apply":
            stats.proposals_sent += 1
        elif action_type == "project_found":
            stats.projects_found += 1
        elif action_type == "project_view":
            stats.projects_viewed += 1
        
        if status == "error":
            stats.errors_count += 1
        
        stats.updated_at = datetime.utcnow()
        await session.commit()


async def get_statistics(days: int = 30) -> List[Dict[str, Any]]:
    """Obtém estatísticas dos últimos N dias."""
    async with async_session() as session:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        result = await session.execute(
            select(DailyStatisticsModel)
            .where(DailyStatisticsModel.date >= start_date)
            .order_by(DailyStatisticsModel.date.desc())
        )
        stats = result.scalars().all()
        
        return [
            {
                "date": s.date.strftime("%Y-%m-%d"),
                "projects_found": s.projects_found,
                "projects_viewed": s.projects_viewed,
                "proposals_sent": s.proposals_sent,
                "proposals_accepted": s.proposals_accepted,
                "proposals_rejected": s.proposals_rejected,
                "logins_count": s.logins_count,
                "searches_count": s.searches_count,
                "errors_count": s.errors_count
            }
            for s in stats
        ]


async def get_statistics_summary() -> Dict[str, Any]:
    """Obtém resumo das estatísticas."""
    async with async_session() as session:
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Hoje
        today_result = await session.execute(
            select(DailyStatisticsModel).where(DailyStatisticsModel.date == today)
        )
        today_stats = today_result.scalar_one_or_none()
        
        # Semana
        week_result = await session.execute(
            select(
                func.sum(DailyStatisticsModel.proposals_sent),
                func.sum(DailyStatisticsModel.projects_found),
                func.sum(DailyStatisticsModel.searches_count)
            ).where(DailyStatisticsModel.date >= week_ago)
        )
        week_stats = week_result.one()
        
        # Mês
        month_result = await session.execute(
            select(
                func.sum(DailyStatisticsModel.proposals_sent),
                func.sum(DailyStatisticsModel.projects_found)
            ).where(DailyStatisticsModel.date >= month_ago)
        )
        month_stats = month_result.one()
        
        return {
            "today": {
                "proposals_sent": today_stats.proposals_sent if today_stats else 0,
                "projects_found": today_stats.projects_found if today_stats else 0,
                "searches": today_stats.searches_count if today_stats else 0,
                "errors": today_stats.errors_count if today_stats else 0
            },
            "week": {
                "proposals_sent": week_stats[0] or 0,
                "projects_found": week_stats[1] or 0,
                "searches": week_stats[2] or 0
            },
            "month": {
                "proposals_sent": month_stats[0] or 0,
                "projects_found": month_stats[1] or 0
            }
        }


# ==================== Clientes Bloqueados ====================

async def add_blacklisted_client(client_name: str, reason: Optional[str] = None):
    """Adiciona um cliente à lista negra."""
    async with async_session() as session:
        client = BlacklistedClientModel(
            client_name=client_name,
            reason=reason
        )
        session.add(client)
        await session.commit()


async def get_blacklisted_clients() -> List[Dict[str, Any]]:
    """Lista clientes na lista negra."""
    async with async_session() as session:
        result = await session.execute(
            select(BlacklistedClientModel).order_by(BlacklistedClientModel.created_at.desc())
        )
        clients = result.scalars().all()
        
        return [
            {
                "id": c.id,
                "client_name": c.client_name,
                "reason": c.reason,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in clients
        ]


async def remove_blacklisted_client(client_id: int):
    """Remove um cliente da lista negra."""
    async with async_session() as session:
        await session.execute(
            delete(BlacklistedClientModel).where(BlacklistedClientModel.id == client_id)
        )
        await session.commit()


async def is_client_blacklisted(client_name: str) -> bool:
    """Verifica se um cliente está na lista negra."""
    async with async_session() as session:
        result = await session.execute(
            select(BlacklistedClientModel).where(
                BlacklistedClientModel.client_name.ilike(f"%{client_name}%")
            )
        )
        return result.scalar_one_or_none() is not None
