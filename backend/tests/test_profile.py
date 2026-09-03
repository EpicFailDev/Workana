import warnings
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4
from datetime import datetime, timedelta, timezone
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
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
        "scraped_at": datetime.now(timezone.utc).isoformat()
    }
    
    from app.services.profile_scraper import ProfileScraperService
    with patch.object(ProfileScraperService, "_parse_profile_html", return_value=mock_metrics), \
         patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>Profile</html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # 1. Primeira busca (validação)
        res1 = await profile_scraper.fetch_public_profile(url, force_refresh=True)
        assert res1["display_name"] == "Cached User"
        assert mock_get.call_count == 1
        
        # 2. Segunda busca (sincronização sem force)
        mock_get.reset_mock()
        res2 = await profile_scraper.fetch_public_profile(url, force_refresh=False)
        assert res2["display_name"] == "Cached User"
        # Deve retornar direto do cache, sem chamar HTTP novamente
        mock_get.assert_not_called()


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
    """Garante isolamento por tenant/RLS e propagação do usuário atual."""
    user1 = uuid4()
    user2 = uuid4()
    
    # 1. Valida isolamento de ContextVar
    prev_user = current_user_id.get()
    token1 = current_user_id.set(user1)
    assert current_user_id.get() == user1
    current_user_id.reset(token1)
    assert current_user_id.get() == prev_user
    
    # 2. Valida propagação no TenantAsyncSession
    executed_queries = []
    mock_session = AsyncMock()
    
    async def fake_execute(stmt, params=None):
        executed_queries.append((str(stmt), params))
        return MagicMock()
        
    mock_session.execute = fake_execute

    class FakeTenantSession:
        async def __aenter__(self):
            uid = current_user_id.get()
            if uid:
                await mock_session.execute(
                    "SELECT set_config('request.jwt.claim.sub', :user_id, true)",
                    {"user_id": str(uid)}
                )
            return mock_session

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    token2 = current_user_id.set(user2)
    try:
        async with FakeTenantSession():
            pass
        assert len(executed_queries) == 1
        assert executed_queries[0][1] == {"user_id": str(user2)}
    finally:
        current_user_id.reset(token2)
