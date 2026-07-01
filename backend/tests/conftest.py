import asyncio
import os
from uuid import UUID
import pytest

# Configure test environment and variables before loading application settings.
os.environ["TESTING"] = "true"
os.environ["DEBUG"] = "true"

# Define dummy variables to pass Pydantic validation if not set
if "DATABASE_URL" not in os.environ or "sqlite" in os.environ.get("DATABASE_URL", "").lower():
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://dummy_user:dummy_pass@localhost:5432/dummy_db"

if "SUPABASE_URL" not in os.environ:
    os.environ["SUPABASE_URL"] = "https://cztwxtsuewwacjcgajjz.supabase.co"

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from app.main import app
from app.auth import get_current_user
from app.automation.browser import WorkanaAutomation
from app.database.models import engine

TEST_USER = {
    "user_id": UUID("00000000-0000-0000-0000-000000000001"),
    "email": "test@example.com",
}


@pytest.fixture(scope="session", autouse=True)
def cleanup_database():
    yield
    try:
        asyncio.run(engine.dispose())
    except Exception:
        pass


@pytest.fixture(autouse=True)
def check_db_test_safety(request):
    """Garante que testes de banco de dados não rodem contra produção e sejam pulados se não houver DB de testes."""
    db_test_files = {"test_crud_extra", "test_dashboard_stats"}
    module_name = request.module.__name__.split(".")[-1]
    
    if module_name in db_test_files:
        db_url = os.getenv("DATABASE_URL", "")
        # Ignora se for a URL dummy de teste
        if "dummy_user" in db_url:
            pytest.skip("Teste de banco ignorado: DATABASE_URL é dummy (sem banco PostgreSQL local configurado).")
        # Proteção rígida contra testes destrutivos contra o projeto hospedado
        if "cztwxtsuewwacjcgajjz" in db_url:
            pytest.skip("Bloqueio de segurança: Não é permitido rodar testes contra o banco hospedado em produção.")


@pytest.fixture(autouse=True)
def mock_db_session(monkeypatch, request):
    """Mocka a sessão do banco de dados para testes unitários/API quando DATABASE_URL é dummy."""
    db_test_files = {"test_crud_extra", "test_dashboard_stats"}
    module_name = request.module.__name__.split(".")[-1]
    
    if module_name not in db_test_files:
        db_url = os.getenv("DATABASE_URL", "")
        if "dummy_user" in db_url:
            from unittest.mock import MagicMock, AsyncMock
            
            mock_session = AsyncMock()
            mock_session.execute.return_value = MagicMock()
            mock_session.commit.return_value = None
            
            class MockSessionContext:
                def __init__(self, *args, **kwargs):
                    pass
                async def __aenter__(self):
                    return mock_session
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
                    
            monkeypatch.setattr("app.database.models.async_session", MockSessionContext)
            monkeypatch.setattr("app.database.crud.async_session", MockSessionContext)


@pytest.fixture(autouse=True)
def authenticated_user():
    """Isola testes de API da rede/JWKS sem desativar auth em produção."""
    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    yield TEST_USER
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def client():
    """Fixture para FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture
def mock_automation():
    """Fixture para mockar a classe de automação do Workana."""
    mock = AsyncMock(spec=WorkanaAutomation)
    mock.search_projects.return_value = []
    return mock
