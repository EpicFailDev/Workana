import asyncio
import os
import tempfile
from pathlib import Path

import pytest
from uuid import UUID

# Configure o banco antes de importar a aplicação/settings. A suíte nunca deve
# ler ou alterar o workana.db real do desenvolvedor.
TEST_DB_PATH = Path(tempfile.gettempdir()) / f"workana-accelerator-tests-{os.getpid()}.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}"

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from app.main import app
from app.auth import get_current_user
from app.automation.browser import WorkanaAutomation
from app.database.models import engine, init_db

TEST_USER = {
    "user_id": UUID("00000000-0000-0000-0000-000000000001"),
    "email": "test@example.com",
}


@pytest.fixture(scope="session", autouse=True)
def isolated_database():
    asyncio.run(init_db())
    yield
    asyncio.run(engine.dispose())
    TEST_DB_PATH.unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def authenticated_user():
    """Isola testes de API da rede/JWKS sem desativar auth em produção."""
    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    yield TEST_USER
    app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture
def client():
    """Fixture for FastAPI TestClient."""
    return TestClient(app)

@pytest.fixture
def mock_automation():
    """Fixture to mock the automation class."""
    mock = AsyncMock(spec=WorkanaAutomation)
    # Configure default behaviors
    mock.search_projects.return_value = []
    return mock

@pytest.fixture
def override_dependency(mock_automation):
    """Override the automation dependency in the app."""
    # Note: Dependent on how dependency injection is handled. 
    # If using a global instance, we might need to patch it.
    from app.api.routers.projects import automation
    
    # We will patch the instance used in the router
    original_automation = automation
    
    # Patching logic would go here if we were using dependency injection cleanly.
    # Since we imported an instance, we might need to mock where it's imported.
    pass
