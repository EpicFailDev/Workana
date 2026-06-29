import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from app.main import app
from app.automation.browser import WorkanaAutomation

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
