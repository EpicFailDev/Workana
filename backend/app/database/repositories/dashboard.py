"""
Repository para métricas e estatísticas do Dashboard.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, and_

import app.database.crud as crud
from app.database.models import (
    DailyStatistics as DailyStatisticsModel,
    ProposalHistory as ProposalHistoryModel,
    Project as ProjectModel,
    ActivityLog as ActivityLogModel,
)
from app.api.schemas import DashboardStats


async def get_daily_stats(user_id: Any) -> Dict[str, int]:
    """Obtém estatísticas diárias do usuário."""
    async with crud.async_session() as session:
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


async def get_dashboard_stats(user_id: Any) -> DashboardStats:
    """Obtém estatísticas consolidadas do dashboard com filtragem por user_id."""
    async with crud.async_session() as session:
        now = datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        today_date = now.date()
        
        # 1. Obter estatísticas diárias de hoje
        stats_today_result = await session.execute(
            select(DailyStatisticsModel).where(
                and_(DailyStatisticsModel.date == today, DailyStatisticsModel.user_id == user_id)
            )
        )
        _stats_today = stats_today_result.scalar_one_or_none()
        
        # 2. Total de projetos na tabela projects do usuário
        total_projects_res = await session.execute(
            select(func.count(ProjectModel.id)).where(ProjectModel.user_id == user_id)
        )
        _total_projects = total_projects_res.scalar() or 0
        
        # 3. Propostas esta semana do usuário
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
        
        # 4. Propostas este mês do usuário
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
        
        # 5. Projetos favoritos / salvos do usuário
        favorites_res = await session.execute(
            select(func.count(ProjectModel.id))
            .where(and_(ProjectModel.is_favorite == True, ProjectModel.user_id == user_id))
        )
        _saved_projects = favorites_res.scalar() or 0
        
        # 6. Propostas aceitas
        accepted_res = await session.execute(
            select(func.count(ProposalHistoryModel.id))
            .where(and_(ProposalHistoryModel.status == "accepted", ProposalHistoryModel.user_id == user_id))
        )
        accepted = accepted_res.scalar() or 0
        
        # 7. Total de propostas enviadas
        total_proposals_res = await session.execute(
            select(func.count(ProposalHistoryModel.id)).where(ProposalHistoryModel.user_id == user_id)
        )
        total_proposals = total_proposals_res.scalar() or 0
        response_rate = (accepted / total_proposals * 100) if total_proposals > 0 else 0.0
        
        # 8. Propostas enviadas hoje
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

        # 9. Última atividade do usuário
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


async def _update_daily_stats(user_id: Any, action_type: str, status: str, increment: int = 1) -> None:
    """Atualiza estatísticas diárias internas de um usuário específico."""
    async with crud.async_session() as session:
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
    async with crud.async_session() as session:
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
    async with crud.async_session() as session:
        now = datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        today_result = await session.execute(
            select(DailyStatisticsModel).where(
                and_(DailyStatisticsModel.date == today, DailyStatisticsModel.user_id == user_id)
            )
        )
        today_stats = today_result.scalar_one_or_none()
        
        week_result = await session.execute(
            select(
                func.sum(DailyStatisticsModel.proposals_sent),
                func.sum(DailyStatisticsModel.projects_found),
                func.sum(DailyStatisticsModel.searches_count)
            ).where(and_(DailyStatisticsModel.date >= week_ago, DailyStatisticsModel.user_id == user_id))
        )
        week_stats = week_result.one()
        
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
