import pytest
from datetime import datetime, timezone, timedelta
from app.automation.antiban import AntibanSystem, AntibanConfig

@pytest.mark.asyncio
async def test_antiban_working_hours():
    # 1. Configurar horário de trabalho fictício
    config = AntibanConfig(
        working_hours_start=9,
        working_hours_end=17,
        respect_working_hours=True
    )
    system = AntibanSystem(config=config)

    # 2. Testar dentro do horário (se simularmos)
    system.config.working_hours_start = 0
    system.config.working_hours_end = 24
    assert system.is_within_working_hours() is True

    # 3. Testar se desrespeitar horário estiver ativado
    system.config.respect_working_hours = False
    system.config.working_hours_start = 9
    system.config.working_hours_end = 17
    assert system.is_within_working_hours() is True


@pytest.mark.asyncio
async def test_antiban_search_limits():
    config = AntibanConfig(
        max_searches_per_hour=2,
        respect_working_hours=False
    )
    system = AntibanSystem(config=config)
    
    # Inicialmente pode buscar
    can_search, msg = await system.can_search()
    assert can_search is True
    assert msg == "OK"
    
    # Registrar duas buscas
    await system.register_search()
    await system.register_search()
    
    # Terceira busca deve falhar
    can_search, msg = await system.can_search()
    assert can_search is False
    assert "Limite" in msg


@pytest.mark.asyncio
async def test_antiban_proposal_limits():
    config = AntibanConfig(
        max_proposals_per_day=3,
        max_proposals_per_hour=2,
        min_pause_between_proposals_minutes=5,
        respect_working_hours=False
    )
    system = AntibanSystem(config=config)
    
    # Primeira proposta: OK
    can_prop, msg = await system.can_send_proposal()
    assert can_prop is True
    
    await system.register_proposal_sent()
    
    # Segunda proposta imediata deve falhar por conta do delay mínimo
    can_prop, msg = await system.can_send_proposal()
    assert can_prop is False
    assert "Aguarde" in msg
