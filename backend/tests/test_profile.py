import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.services.profile_scraper import (
    is_professional_title,
    clean_normalize_skills,
    validate_metrics_semantics,
    profile_scraper
)
from app.database.models import async_session, ProfileConfig, ProfileMetrics, current_user_id

# ==================== Testes de Helpers do Scraper ====================

def test_is_professional_title():
    # Títulos profissionais conhecidos devem retornar True
    assert is_professional_title("Full Stack Developer") is True
    assert is_professional_title("Desenvolvedor Python Pleno") is True
    assert is_professional_title("UI/UX Designer") is True
    
    # Nomes legítimos devem retornar False
    assert is_professional_title("João Silva") is False
    assert is_professional_title("Maria F.") is False
    assert is_professional_title(None) is False


def test_clean_normalize_skills():
    raw_skills = [
        "Python",
        "Design & Multimedia",  # Blacklisted (categoria global)
        "Entrar",              # Blacklisted (navegação)
        "   JavaScript   ",     # Espaços extras
        "Python",              # Duplicata
        "Java",
        "React"
    ]
    cleaned = clean_normalize_skills(raw_skills)
    assert "Python" in cleaned
    assert "JavaScript" in cleaned
    assert "Java" in cleaned
    assert "React" in cleaned
    assert "Design & Multimedia" not in cleaned
    assert "Entrar" not in cleaned
    assert len(cleaned) == 4  # Sem duplicatas ou itens banidos


def test_validate_metrics_semantics():
    valid_metrics = {
        "display_name": "João S.",
        "username": "joao-s",
        "country": "Brasil",
        "skills": ["Python", "Docker"],
        "projects_completed": 0  # 0 projetos é legítimo
    }
    
    # Perfil legítimo
    assert validate_metrics_semantics(valid_metrics, "https://www.workana.com/freelancer/joao-s") is True
    
    # URL final inválida
    assert validate_metrics_semantics(valid_metrics, "https://www.workana.com/login") is False
    
    # Nome inválido (cargo profissional)
    bad_name_metrics = valid_metrics.copy()
    bad_name_metrics["display_name"] = "Full Stack Developer"
    assert validate_metrics_semantics(bad_name_metrics, "https://www.workana.com/freelancer/joao-s") is False
    
    # Pouca evidência (falta country, skills, member_since, etc)
    insufficient_metrics = {
        "display_name": "João S.",
        "username": "joao-s"
    }
    assert validate_metrics_semantics(insufficient_metrics, "https://www.workana.com/freelancer/joao-s") is False


# ==================== Testes de Cache e Única Execução ====================

@pytest.mark.asyncio
async def test_validation_then_sync_uses_cache():
    """Validação seguida de salvamento/sincronização não deve chamar Playwright/HTTP duas vezes."""
    profile_scraper.clear_cache()
    url = "https://www.workana.com/freelancer/cached-user"
    
    mock_metrics = {
        "success": True,
        "profile_url": url,
        "username": "cached-user",
        "display_name": "Cached User",
        "country": "Brasil",
        "skills": ["Python"],
        "projects_completed": 3,
        "scraped_at": datetime.utcnow().isoformat()
    }
    
    # Simula que a primeira execução preenche o cache
    with patch("app.services.profile_scraper.ProfileScraperService._fetch_with_playwright", new_callable=AsyncMock) as mock_pw:
        mock_pw.return_value = mock_metrics
        
        # 1. Primeira busca (validação)
        res1 = await profile_scraper.fetch_public_profile(url, force_refresh=True)
        assert res1["display_name"] == "Cached User"
        assert mock_pw.call_count == 1
        
        # 2. Segunda busca (sincronização sem force)
        mock_pw.reset_mock()
        res2 = await profile_scraper.fetch_public_profile(url, force_refresh=False)
        assert res2["display_name"] == "Cached User"
        # Deve retornar direto do cache, sem chamar Playwright novamente
        mock_pw.assert_not_called()


# ==================== Testes de Endpoints API ====================

def test_api_healthcheck():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_profile_validate_endpoint():
    client = TestClient(app)
    mock_metrics = {
        "success": True,
        "display_name": "João S.",
        "username": "joao-s",
        "country": "Brasil",
        "skills": ["Python"],
        "projects_completed": 0
    }
    
    with patch("app.api.routers.profile.profile_scraper.fetch_public_profile", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_metrics
        response = client.post("/api/profile/validate?url=https://www.workana.com/freelancer/joao-s")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["display_name"] == "João S."
        assert data["username"] == "joao-s"
        assert "metrics" in data


# ==================== Testes de RLS (Row Level Security) ====================

@pytest.mark.asyncio
async def test_rls_profile_tables():
    """Garante isolamento por tenant/RLS caso banco real esteja ativo."""
    import os
    db_url = os.getenv("DATABASE_URL", "")
    if "dummy_user" in db_url or not db_url:
        pytest.skip("Ignorado: Banco de dados de teste PostgreSQL real não disponível.")
        
    from sqlalchemy import select
    
    user1 = uuid4()
    user2 = uuid4()
    
    # 1. Inserir dados como User 1
    token1 = current_user_id.set(user1)
    try:
        async with async_session() as session:
            # Limpeza preventiva
            await session.execute(ProfileConfig.__table__.delete().where(ProfileConfig.user_id == user1))
            await session.execute(ProfileMetrics.__table__.delete().where(ProfileMetrics.user_id == user1))
            
            config1 = ProfileConfig(
                user_id=user1,
                profile_url="https://www.workana.com/freelancer/user-one",
                auto_sync_enabled=True
            )
            metric1 = ProfileMetrics(
                user_id=user1,
                profile_url="https://www.workana.com/freelancer/user-one",
                username="user-one",
                display_name="User One",
                projects_completed=5
            )
            session.add(config1)
            session.add(metric1)
            await session.commit()
    finally:
        current_user_id.reset(token1)
        
    # 2. Tentar ler dados do User 1 através do contexto do User 2
    token2 = current_user_id.set(user2)
    try:
        async with async_session() as session:
            # Busca ProfileConfig do User 1 usando a sessão com contexto do User 2
            res_config = await session.execute(
                select(ProfileConfig).where(ProfileConfig.user_id == user1)
            )
            config_read = res_config.scalar_one_or_none()
            assert config_read is None  # RLS deve filtrar e não retornar nada
            
            # Busca ProfileMetrics do User 1 usando a sessão com contexto do User 2
            res_metric = await session.execute(
                select(ProfileMetrics).where(ProfileMetrics.user_id == user1)
            )
            metric_read = res_metric.scalar_one_or_none()
            assert metric_read is None  # RLS deve filtrar e não retornar nada
    finally:
        current_user_id.reset(token2)
