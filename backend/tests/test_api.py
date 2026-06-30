
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.api.schemas import Project

client = TestClient(app)

# Mock da automação para não abrir navegador
@pytest.fixture(autouse=True)
def mock_automation():
    with patch("app.api.routers.projects.automation") as mock:
        # Configurar retorno do search_projects
        mock.search_projects = AsyncMock(return_value=[
            Project(
                id="123",
                title="Projeto Teste",
                description="Descrição",
                budget="R$ 1000",
                skills=["Python"],
                url="http://workana.com/job/123",
                proposals_count=5,
                posted_at="1h"
            )
        ])
        # Configurar retorno do get_project_details
        mock.get_project_details = AsyncMock(return_value=Project(
            id="123", 
            title="Detalhe Teste", 
            description="Desc", 
            url="url",
            skills=[]
        ))
        yield mock

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Workana Automation API"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200

def test_automation_status():
    response = client.get("/api/automation/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_running" in data

def test_search_projects(mock_automation):
    response = client.post("/api/projects/search", json={"keywords": "python"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["projects"][0]["title"] == "Projeto Teste"
    
def test_get_project_details(mock_automation):
    response = client.get("/api/projects/123")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Detalhe Teste"

@patch("app.api.routers.dashboard.crud.get_dashboard_stats")
def test_dashboard_stats(mock_stats):
    from app.api.schemas import DashboardStats
    mock_stats.return_value = DashboardStats(
        total_proposals_sent=10,
        proposals_today=2,
        proposals_this_week=5,
        proposals_this_month=8,
        accepted_proposals=1,
        pending_proposals=9,
        response_rate=10.0,
        last_activity="2026-06-30T12:00:00"
    )
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    assert "total_proposals_sent" in response.json()
