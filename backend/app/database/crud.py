"""
Operações CRUD para o banco de dados.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from loguru import logger
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

async def save_credentials(user_id: Any, email: str, password: str):
    """Salva as credenciais criptografadas de um usuário específico."""
    async with async_session() as session:
        # Remover credenciais antigas do usuário
        await session.execute(delete(Credentials).where(Credentials.user_id == user_id))
        
        # Inserir novas credenciais
        encrypted_password = _encrypt(password)
        creds = Credentials(user_id=user_id, email=email, encrypted_password=encrypted_password)
        session.add(creds)
        await session.commit()


async def get_credentials(user_id: Any) -> Optional[Dict[str, str]]:
    """Obtém as credenciais descriptografadas de um usuário específico."""
    async with async_session() as session:
        result = await session.execute(
            select(Credentials).where(Credentials.user_id == user_id).limit(1)
        )
        creds = result.scalar_one_or_none()
        
        if creds:
            try:
                password = _decrypt(creds.encrypted_password)
                return {"email": creds.email, "password": password}
            except Exception:
                return None
        return None


# ==================== Filtros Salvos ====================

async def get_saved_filters(user_id: Any) -> List[SavedFilter]:
    """Lista todos os filtros salvos de um usuário específico."""
    async with async_session() as session:
        result = await session.execute(
            select(SavedFilterModel)
            .where(SavedFilterModel.user_id == user_id)
            .order_by(SavedFilterModel.created_at.desc())
        )
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


async def create_filter(user_id: Any, filter_data: SavedFilter) -> SavedFilter:
    """Cria um novo filtro para um usuário específico."""
    async with async_session() as session:
        db_filter = SavedFilterModel(
            user_id=user_id,
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


async def delete_filter(user_id: Any, filter_id: int):
    """Remove um filtro de um usuário específico."""
    async with async_session() as session:
        await session.execute(
            delete(SavedFilterModel)
            .where(and_(SavedFilterModel.id == filter_id, SavedFilterModel.user_id == user_id))
        )
        await session.commit()


# ==================== Templates ====================

async def get_templates(user_id: Any) -> List[ProposalTemplate]:
    """Lista todos os templates de um usuário específico."""
    async with async_session() as session:
        result = await session.execute(
            select(ProposalTemplateModel)
            .where(ProposalTemplateModel.user_id == user_id)
            .order_by(ProposalTemplateModel.is_default.desc(), ProposalTemplateModel.name)
        )
        templates = result.scalars().all()
        
        return [
            ProposalTemplate(
                id=t.id,
                name=t.name,
                content=t.content,
                default_budget=t.default_budget,
                default_deadline_days=t.default_deadline_days,
                is_default=t.is_default
            )
            for t in templates
        ]


async def get_template(user_id: Any, template_id: int) -> Optional[ProposalTemplate]:
    """Obtém um template específico de um usuário."""
    async with async_session() as session:
        result = await session.execute(
            select(ProposalTemplateModel)
            .where(and_(ProposalTemplateModel.id == template_id, ProposalTemplateModel.user_id == user_id))
        )
        t = result.scalar_one_or_none()
        
        if t:
            return ProposalTemplate(
                id=t.id,
                name=t.name,
                content=t.content,
                default_budget=t.default_budget,
                default_deadline_days=t.default_deadline_days,
                is_default=t.is_default
            )
        return None


async def create_template(user_id: Any, template: ProposalTemplateCreate) -> ProposalTemplate:
    """Cria um novo template para o usuário."""
    async with async_session() as session:
        # Se for default, desmarcar outros do mesmo usuário
        if template.is_default:
            await session.execute(
                update(ProposalTemplateModel)
                .where(ProposalTemplateModel.user_id == user_id)
                .values(is_default=False)
            )
            
        db_template = ProposalTemplateModel(
            user_id=user_id,
            name=template.name,
            content=template.content,
            default_budget=template.default_budget,
            default_deadline_days=template.default_deadline_days,
            is_default=template.is_default or False
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
            is_default=db_template.is_default
        )


async def update_template(user_id: Any, template_id: int, template: ProposalTemplateCreate) -> Optional[ProposalTemplate]:
    """Atualiza um template de um usuário específico."""
    async with async_session() as session:
        if template.is_default:
            await session.execute(
                update(ProposalTemplateModel)
                .where(ProposalTemplateModel.user_id == user_id)
                .values(is_default=False)
            )
            
        result = await session.execute(
            select(ProposalTemplateModel)
            .where(and_(ProposalTemplateModel.id == template_id, ProposalTemplateModel.user_id == user_id))
        )
        db_template = result.scalar_one_or_none()
        
        if db_template:
            db_template.name = template.name
            db_template.content = template.content
            db_template.default_budget = template.default_budget
            db_template.default_deadline_days = template.default_deadline_days
            db_template.is_default = template.is_default or False
            db_template.updated_at = datetime.now(timezone.utc)
            
            await session.commit()
            await session.refresh(db_template)
            
            return ProposalTemplate(
                id=db_template.id,
                name=db_template.name,
                content=db_template.content,
                default_budget=db_template.default_budget,
                default_deadline_days=db_template.default_deadline_days,
                is_default=db_template.is_default
            )
        return None


async def delete_template(user_id: Any, template_id: int):
    """Remove um template de um usuário."""
    async with async_session() as session:
        await session.execute(
            delete(ProposalTemplateModel)
            .where(and_(ProposalTemplateModel.id == template_id, ProposalTemplateModel.user_id == user_id))
        )
        await session.commit()


# ==================== Histórico de Propostas ====================

async def save_proposal_history(user_id: Any, proposal: ProposalSubmit, result: ProposalResult):
    """Salva uma tentativa de envio de proposta no histórico."""
    async with async_session() as session:
        history = ProposalHistoryModel(
            user_id=user_id,
            project_id=proposal.project_id,
            project_title=proposal.project_title,
            project_url=proposal.project_url,
            budget=proposal.budget,
            deadline_days=proposal.deadline_days,
            message=proposal.message,
            status="sent" if result.success else "failed"
        )
        session.add(history)
        await session.commit()


async def save_ai_proposal(
    user_id: Any,
    project_id: str,
    project_title: str,
    project_url: str,
    proposal_text: str,
    suggested_price: str
) -> int:
    """Salva uma proposta gerada por IA no histórico do usuário."""
    import re
    async with async_session() as session:
        # Extrair valor numérico do preço (ex: "R$ 1.500" -> 1500.0)
        price_clean = suggested_price.replace('.', '').replace(',', '.')
        price_match = re.search(r'[\d.]+', price_clean)
        budget = float(price_match.group()) if price_match else 0.0
        
        history = ProposalHistoryModel(
            user_id=user_id,
            project_id=project_id,
            project_title=project_title,
            project_url=project_url,
            budget=budget,
            deadline_days=7,  # Padrão
            message=proposal_text,
            status="generated"
        )
        session.add(history)
        await session.commit()
        await session.refresh(history)
        return history.id


async def get_proposal_history(user_id: Any, limit: int = 50) -> List[ProposalHistory]:
    """Obtém o histórico de propostas do usuário."""
    async with async_session() as session:
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
                sent_at=h.sent_at
            )
            for h in history
        ]


async def update_proposal_status(user_id: Any, proposal_id: int, status: str) -> bool:
    """Atualiza o status de uma proposta do usuário."""
    async with async_session() as session:
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


async def get_daily_stats(user_id: Any) -> Dict[str, int]:
    """Obtém estatísticas diárias do usuário."""
    async with async_session() as session:
        today = datetime.now(timezone.utc).date()
        result = await session.execute(
            select(func.count(ProposalHistoryModel.id))
            .where(
                and_(
                    func.date(ProposalHistoryModel.sent_at) == today,
                    ProposalHistoryModel.user_id == user_id
                )
            )
        )
        proposals_today = result.scalar() or 0
        
        return {"proposals_today": proposals_today}


# ==================== Dashboard ====================

async def get_dashboard_stats(user_id: Any) -> DashboardStats:
    """Obtém estatísticas do dashboard com filtragem por user_id."""
    async with async_session() as session:
        now = datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Obter estatísticas diárias de hoje
        stats_today_result = await session.execute(
            select(DailyStatisticsModel).where(
                and_(DailyStatisticsModel.date == today, DailyStatisticsModel.user_id == user_id)
            )
        )
        stats_today = stats_today_result.scalar_one_or_none()
        
        # Encontrados (Total) -> Total de projetos na tabela projects do usuário
        total_projects_res = await session.execute(
            select(func.count(ProjectModel.id)).where(ProjectModel.user_id == user_id)
        )
        total_projects = total_projects_res.scalar() or 0
        
        # Buscas Hoje -> searches_count de hoje
        searches_today = stats_today.searches_count if stats_today else 0
        
        # Propostas este mês/semana do usuário
        week_result = await session.execute(
            select(func.count(ProposalHistoryModel.id))
            .where(
                and_(
                    ProposalHistoryModel.sent_at >= week_ago,
                    ProposalHistoryModel.user_id == user_id
                )
            )
        )
        proposals_week = week_result.scalar() or 0
        
        month_result = await session.execute(
            select(func.count(ProposalHistoryModel.id))
            .where(
                and_(
                    ProposalHistoryModel.sent_at >= month_ago,
                    ProposalHistoryModel.user_id == user_id
                )
            )
        )
        proposals_month = month_result.scalar() or 0
        
        # Projetos favoritos / salvos do usuário
        favorites_res = await session.execute(
            select(func.count(ProjectModel.id))
            .where(and_(ProjectModel.is_favorite == True, ProjectModel.user_id == user_id))
        )
        saved_projects = favorites_res.scalar() or 0
        
        # Taxa de resposta (response_rate)
        accepted_res = await session.execute(
            select(func.count(ProposalHistoryModel.id))
            .where(and_(ProposalHistoryModel.status == "accepted", ProposalHistoryModel.user_id == user_id))
        )
        accepted = accepted_res.scalar() or 0
        
        total_proposals_res = await session.execute(
            select(func.count(ProposalHistoryModel.id)).where(ProposalHistoryModel.user_id == user_id)
        )
        total_proposals = total_proposals_res.scalar() or 0
        response_rate = (accepted / total_proposals * 100) if total_proposals > 0 else 0.0
        
        # Propostas enviadas hoje
        today_date = datetime.now(timezone.utc).date()
        proposals_today_res = await session.execute(
            select(func.count(ProposalHistoryModel.id))
            .where(
                and_(
                    func.date(ProposalHistoryModel.sent_at) == today_date,
                    ProposalHistoryModel.user_id == user_id
                )
            )
        )
        proposals_today = proposals_today_res.scalar() or 0

        # Última atividade do usuário
        last_activity_result = await session.execute(
            select(ActivityLogModel.created_at)
            .where(ActivityLogModel.user_id == user_id)
            .order_by(ActivityLogModel.created_at.desc())
            .limit(1)
        )
        last_activity = last_activity_result.scalar_one_or_none()
        
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

async def get_automation_config(user_id: Any) -> Dict[str, Any]:
    """Obtém configurações de automação. Se não existirem, inicializa-as para o usuário."""
    async with async_session() as session:
        result = await session.execute(
            select(AutomationConfigModel).where(AutomationConfigModel.user_id == user_id).limit(1)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            config = AutomationConfigModel(
                user_id=user_id,
                headless=True,
                delay_between_actions_ms=2000,
                max_proposals_per_day=10,
                auto_apply=False,
                preferred_template_id=None,
                gemini_api_key=None,
                user_full_name=None
            )
            session.add(config)
            await session.commit()
            await session.refresh(config)
        
        gemini_key = None
        if config.gemini_api_key:
            try:
                gemini_key = _decrypt(config.gemini_api_key)
            except Exception:
                logger.error("Erro ao descriptografar chave Gemini. A chave será resetada.")
                gemini_key = None

        return {
            "headless": config.headless,
            "delay_between_actions_ms": config.delay_between_actions_ms,
            "max_proposals_per_day": config.max_proposals_per_day,
            "auto_apply": config.auto_apply,
            "preferred_template_id": config.preferred_template_id,
            "gemini_api_key": gemini_key,
            "user_full_name": config.user_full_name
        }


async def save_automation_config(user_id: Any, config: Dict[str, Any]):
    """Salva ou cria configurações de automação de um usuário."""
    async with async_session() as session:
        result = await session.execute(
            select(AutomationConfigModel).where(AutomationConfigModel.user_id == user_id).limit(1)
        )
        db_config = result.scalar_one_or_none()
        
        gemini_api_key = config.get("gemini_api_key")
        encrypted_gemini = _encrypt(gemini_api_key) if gemini_api_key else None
        
        if db_config:
            db_config.headless = config.get("headless", True)
            db_config.delay_between_actions_ms = config.get("delay_between_actions_ms", 2000)
            db_config.max_proposals_per_day = config.get("max_proposals_per_day", 10)
            db_config.auto_apply = config.get("auto_apply", False)
            if "preferred_template_id" in config:
                db_config.preferred_template_id = config.get("preferred_template_id")
            if gemini_api_key is not None:
                db_config.gemini_api_key = encrypted_gemini
            if "user_full_name" in config:
                db_config.user_full_name = config.get("user_full_name")
            db_config.updated_at = datetime.now(timezone.utc)
        else:
            db_config = AutomationConfigModel(
                user_id=user_id,
                headless=config.get("headless", True),
                delay_between_actions_ms=config.get("delay_between_actions_ms", 2000),
                max_proposals_per_day=config.get("max_proposals_per_day", 10),
                auto_apply=config.get("auto_apply", False),
                preferred_template_id=config.get("preferred_template_id"),
                gemini_api_key=encrypted_gemini,
                user_full_name=config.get("user_full_name")
            )
            session.add(db_config)
            
        await session.commit()


# ==================== Projetos ====================

async def save_project(user_id: Any, project_data: Dict[str, Any]) -> int:
    """Salva ou atualiza um projeto encontrado para um usuário específico."""
    async with async_session() as session:
        # Verificar se já existe para este usuário
        result = await session.execute(
            select(ProjectModel).where(
                and_(ProjectModel.workana_id == project_data.get("workana_id"), ProjectModel.user_id == user_id)
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Atualizar projeto existente
            for key, value in project_data.items():
                if hasattr(existing, key) and key != "id" and key != "user_id":
                    setattr(existing, key, value)
            existing.updated_at = datetime.now(timezone.utc)
            await session.commit()
            return existing.id
        else:
            # Criar novo projeto
            project_data["user_id"] = user_id
            project = ProjectModel(**project_data)
            session.add(project)
            await session.commit()
            await session.refresh(project)
            return project.id


async def get_projects(
    user_id: Any,
    limit: int = 50,
    offset: int = 0,
    only_favorites: bool = False,
    only_not_applied: bool = False,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista projetos salvos de um usuário com filtros."""
    async with async_session() as session:
        query = select(ProjectModel).where(ProjectModel.user_id == user_id)
        
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


async def get_project(user_id: Any, project_id: int) -> Optional[Dict[str, Any]]:
    """Obtém um projeto específico de um usuário."""
    async with async_session() as session:
        result = await session.execute(
            select(ProjectModel).where(and_(ProjectModel.id == project_id, ProjectModel.user_id == user_id))
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


async def toggle_project_favorite(user_id: Any, project_id: int) -> bool:
    """Alterna o status de favorito de um projeto de um usuário específico."""
    async with async_session() as session:
        result = await session.execute(
            select(ProjectModel).where(and_(ProjectModel.id == project_id, ProjectModel.user_id == user_id))
        )
        project = result.scalar_one_or_none()
        
        if project:
            project.is_favorite = not project.is_favorite
            await session.commit()
            return project.is_favorite
        return False


async def mark_project_applied(user_id: Any, project_id: int):
    """Marca um projeto de um usuário como aplicado."""
    async with async_session() as session:
        result = await session.execute(
            select(ProjectModel).where(and_(ProjectModel.id == project_id, ProjectModel.user_id == user_id))
        )
        project = result.scalar_one_or_none()
        
        if project:
            project.is_applied = True
            project.updated_at = datetime.now(timezone.utc)
            await session.commit()


async def ignore_project(user_id: Any, project_id: int):
    """Ignora um projeto de um usuário específico."""
    async with async_session() as session:
        result = await session.execute(
            select(ProjectModel).where(and_(ProjectModel.id == project_id, ProjectModel.user_id == user_id))
        )
        project = result.scalar_one_or_none()
        
        if project:
            project.is_ignored = True
            await session.commit()


async def update_project_notes(user_id: Any, project_id: int, notes: str):
    """Atualiza notas de um projeto do usuário."""
    async with async_session() as session:
        result = await session.execute(
            select(ProjectModel).where(and_(ProjectModel.id == project_id, ProjectModel.user_id == user_id))
        )
        project = result.scalar_one_or_none()
        
        if project:
            project.notes = notes
            project.updated_at = datetime.now(timezone.utc)
            await session.commit()


# ==================== Log de Atividades ====================

async def log_activity(
    user_id: Any,
    action_type: str,
    description: str,
    details: Optional[Dict[str, Any]] = None,
    project_id: Optional[int] = None,
    status: str = "success",
    error_message: Optional[str] = None,
    duration_ms: Optional[int] = None
):
    """Registra uma atividade no log vinculada ao user_id."""
    async with async_session() as session:
        log = ActivityLogModel(
            user_id=user_id,
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
        increment = 1
        if details and "count" in details:
            try:
                increment = int(details["count"])
            except:
                pass
        await _update_daily_stats(user_id, action_type, status, increment=increment)
        
async def get_activity_logs(
    user_id: Any,
    limit: int = 100,
    action_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Obtém logs de atividade de um usuário específico."""
    async with async_session() as session:
        query = select(ActivityLogModel).where(ActivityLogModel.user_id == user_id)
        
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

async def _update_daily_stats(user_id: Any, action_type: str, status: str, increment: int = 1):
    """Atualiza estatísticas diárias internas de um usuário específico."""
    async with async_session() as session:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        result = await session.execute(
            select(DailyStatisticsModel).where(
                and_(DailyStatisticsModel.date == today, DailyStatisticsModel.user_id == user_id)
            )
        )
        stats = result.scalar_one_or_none()
        
        if not stats:
            stats = DailyStatisticsModel(user_id=user_id, date=today)
            session.add(stats)
        
        # Atualizar contadores baseado no tipo de ação
        if action_type == "login":
            stats.logins_count = (stats.logins_count or 0) + increment
        elif action_type == "search":
            stats.searches_count = (stats.searches_count or 0) + increment
        elif action_type == "apply":
            stats.proposals_sent = (stats.proposals_sent or 0) + increment
        elif action_type == "project_found":
            stats.projects_found = (stats.projects_found or 0) + increment
        elif action_type == "project_view":
            stats.projects_viewed = (stats.projects_viewed or 0) + increment
        
        if status == "error":
            stats.errors_count = (stats.errors_count or 0) + increment
        
        stats.updated_at = datetime.now(timezone.utc)
        await session.commit()


async def get_statistics(user_id: Any, days: int = 30) -> List[Dict[str, Any]]:
    """Obtém estatísticas dos últimos N dias de um usuário específico."""
    async with async_session() as session:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        result = await session.execute(
            select(DailyStatisticsModel)
            .where(and_(DailyStatisticsModel.date >= start_date, DailyStatisticsModel.user_id == user_id))
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


async def get_statistics_summary(user_id: Any) -> Dict[str, Any]:
    """Obtém resumo das estatísticas de um usuário específico."""
    async with async_session() as session:
        now = datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Hoje
        today_result = await session.execute(
            select(DailyStatisticsModel).where(
                and_(DailyStatisticsModel.date == today, DailyStatisticsModel.user_id == user_id)
            )
        )
        today_stats = today_result.scalar_one_or_none()
        
        # Semana
        week_result = await session.execute(
            select(
                func.sum(DailyStatisticsModel.proposals_sent),
                func.sum(DailyStatisticsModel.projects_found),
                func.sum(DailyStatisticsModel.searches_count)
            ).where(and_(DailyStatisticsModel.date >= week_ago, DailyStatisticsModel.user_id == user_id))
        )
        week_stats = week_result.one()
        
        # Mês
        month_result = await session.execute(
            select(
                func.sum(DailyStatisticsModel.proposals_sent),
                func.sum(DailyStatisticsModel.projects_found)
            ).where(and_(DailyStatisticsModel.date >= month_ago, DailyStatisticsModel.user_id == user_id))
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

async def add_blacklisted_client(user_id: Any, client_name: str, reason: Optional[str] = None):
    """Adiciona um cliente à lista negra de um usuário específico."""
    async with async_session() as session:
        client = BlacklistedClientModel(
            user_id=user_id,
            client_name=client_name,
            reason=reason
        )
        session.add(client)
        await session.commit()


async def get_blacklisted_clients(user_id: Any) -> List[Dict[str, Any]]:
    """Lista clientes na lista negra de um usuário específico."""
    async with async_session() as session:
        result = await session.execute(
            select(BlacklistedClientModel)
            .where(BlacklistedClientModel.user_id == user_id)
            .order_by(BlacklistedClientModel.created_at.desc())
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


async def remove_blacklisted_client(user_id: Any, client_id: int):
    """Remove um cliente da lista negra de um usuário específico."""
    async with async_session() as session:
        await session.execute(
            delete(BlacklistedClientModel)
            .where(and_(BlacklistedClientModel.id == client_id, BlacklistedClientModel.user_id == user_id))
        )
        await session.commit()


async def is_client_blacklisted(user_id: Any, client_name: str) -> bool:
    """Verifica se um cliente está na lista negra de um usuário específico."""
    async with async_session() as session:
        result = await session.execute(
            select(BlacklistedClientModel).where(
                and_(
                    BlacklistedClientModel.client_name.ilike(f"%{client_name}%"),
                    BlacklistedClientModel.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none() is not None
