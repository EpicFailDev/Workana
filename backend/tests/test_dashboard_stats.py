import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from app.database.models import (
    async_session,
    ProposalHistory as ProposalHistoryModel,
    Project as ProjectModel,
    ActivityLog as ActivityLogModel
)
from app.database.crud import get_dashboard_stats


@pytest.mark.asyncio
async def test_get_dashboard_stats_correct_mapping():
    # 1. Crie um user_id único de teste
    user_id = uuid4()
    
    async with async_session() as session:
        # 2. Insira dados de propostas de teste (algumas de hoje, algumas mais antigas, algumas aceitas)
        now = datetime.now(timezone.utc)
        
        # Proposta enviada hoje, status = accepted
        p1 = ProposalHistoryModel(
            user_id=user_id,
            project_id="p1",
            project_title="Proj 1",
            budget=100.0,
            deadline_days=5,
            message="Msg 1",
            status="accepted",
            sent_at=now
        )
        # Proposta enviada hoje, status = sent
        p2 = ProposalHistoryModel(
            user_id=user_id,
            project_id="p2",
            project_title="Proj 2",
            budget=200.0,
            deadline_days=10,
            message="Msg 2",
            status="sent",
            sent_at=now
        )
        # Proposta enviada 10 dias atrás (dentro do mês, fora da semana), status = sent
        p3 = ProposalHistoryModel(
            user_id=user_id,
            project_id="p3",
            project_title="Proj 3",
            budget=150.0,
            deadline_days=3,
            message="Msg 3",
            status="sent",
            sent_at=now - timedelta(days=10)
        )
        
        # Log de atividade do usuário
        log = ActivityLogModel(
            user_id=user_id,
            action_type="test",
            action_description="Test activity",
            created_at=now
        )
        
        # Projeto do usuário
        proj = ProjectModel(
            user_id=user_id,
            workana_id="workana_test_p1",
            title="Some scraped project",
            description="Scraped desc",
            budget_min=100.0,
            budget_max=200.0,
            url="http://example.com",
            is_favorite=True
        )
        
        session.add_all([p1, p2, p3, log, proj])
        await session.commit()

    # 3. Obtenha as estatísticas do dashboard
    stats = await get_dashboard_stats(user_id)
    
    # 4. Assegure que as contagens estão corretas de acordo com a semântica correta das propriedades
    # Total de propostas enviadas pelo usuário = 3 (p1, p2, p3). O bug anterior retornaria 1 (total_projects).
    assert stats.total_proposals_sent == 3
    
    # Propostas enviadas hoje = 2 (p1, p2). O bug anterior retornaria searches_today (0).
    assert stats.proposals_today == 2
    
    # Propostas nesta semana = 2 (p1, p2). p3 foi há 10 dias.
    assert stats.proposals_this_week == 2
    
    # Propostas neste mês = 3 (p1, p2, p3).
    assert stats.proposals_this_month == 3
    
    # Propostas aceitas = 1 (p1). O bug anterior retornaria saved_projects (1).
    assert stats.accepted_proposals == 1
    
    # Propostas pendentes = 2 (p2, p3).
    assert stats.pending_proposals == 2
    
    # Taxa de resposta = (1 / 3) * 100 = 33.3%
    assert stats.response_rate == pytest.approx(33.3, 0.1)
    
    assert stats.last_activity is not None
