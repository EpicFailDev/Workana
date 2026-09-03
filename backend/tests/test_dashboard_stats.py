import pytest
from unittest.mock import MagicMock
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
async def test_get_dashboard_stats_correct_mapping(monkeypatch):
    # 1. Crie um user_id único de teste
    user_id = uuid4()
    now = datetime.now(timezone.utc)
    
    # Sequence of 9 queries in get_dashboard_stats:
    # 1. stats_today (DailyStatisticsModel) -> None
    # 2. total_projects (ProjectModel count) -> 1
    # 3. proposals_week (ProposalHistory count week) -> 2
    # 4. proposals_month (ProposalHistory count month) -> 3
    # 5. saved_projects (ProjectModel favorites count) -> 1
    # 6. accepted (ProposalHistory count accepted) -> 1
    # 7. total_proposals (ProposalHistory count total) -> 3
    # 8. proposals_today (ProposalHistory count today) -> 2
    # 9. last_activity (ActivityLog created_at) -> now
    
    mock_responses = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=None), scalar=MagicMock(return_value=None)), # 1. stats_today
        MagicMock(scalar=MagicMock(return_value=1)), # 2. total_projects
        MagicMock(scalar=MagicMock(return_value=2)), # 3. proposals_week
        MagicMock(scalar=MagicMock(return_value=3)), # 4. proposals_month
        MagicMock(scalar=MagicMock(return_value=1)), # 5. saved_projects
        MagicMock(scalar=MagicMock(return_value=1)), # 6. accepted
        MagicMock(scalar=MagicMock(return_value=3)), # 7. total_proposals
        MagicMock(scalar=MagicMock(return_value=2)), # 8. proposals_today
        MagicMock(scalar_one_or_none=MagicMock(return_value=now)), # 9. last_activity
    ]
    query_call = [0]

    class FakeSession:
        async def execute(self, stmt):
            idx = query_call[0]
            query_call[0] += 1
            if idx < len(mock_responses):
                return mock_responses[idx]
            return MagicMock(scalar=MagicMock(return_value=0), scalar_one_or_none=MagicMock(return_value=None))

    class FakeSessionCtx:
        async def __aenter__(self):
            return FakeSession()
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr("app.database.crud.async_session", FakeSessionCtx)

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
