import pytest
from unittest.mock import patch, AsyncMock
from app.api.schemas import Project

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@patch("app.api.routers.projects.automation")
def test_search_projects(mock_automation, client):
    """Test searching for projects."""
    # Mock data
    mock_projects = [
        Project(
            id="123",
            title="Test Project",
            description="Description",
            budget="100",
            skills=["Python"],
            url="http://test.com",
            proposals_count=5,
            posted_at="1 hour ago"
        )
    ]
    
    # Setup mock
    mock_automation.search_projects = AsyncMock(return_value=mock_projects)
    
    # Execute request
    payload = {
        "keywords": "python",
        "page": 1
    }
    response = client.post("/api/projects/search", json=payload)
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["projects"][0]["title"] == "Test Project"

@patch("app.database.crud.get_projects")
def test_list_saved_projects(mock_get_projects, client):
    """Test listing saved projects."""
    mock_get_projects.return_value = []
    
    response = client.get("/api/saved-projects")
    assert response.status_code == 200
    assert response.json()["total"] == 0
