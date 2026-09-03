import pytest
from app.services.realtime_pusher import WorkanaRealtimePusher


def test_normalize_pusher_project():
    raw_payload = {
        "id": "12345",
        "slug": "dev-em-flutterflow-ia",
        "title": "Desenvolvedor FlutterFlow com IA",
        "description": "Precisamos de um dev para criar app corporativo.",
        "budget": "R$ 3.000",
        "skills": "flutter, api, n8n",
        "proposals_count": 2,
        "is_hourly": False
    }
    normalized = WorkanaRealtimePusher._normalize_pusher_project(raw_payload)
    assert normalized is not None
    assert normalized["workana_id"] == "dev-em-flutterflow-ia"
    assert normalized["title"] == "Desenvolvedor FlutterFlow com IA"
    assert normalized["skills"] == ["flutter", "api", "n8n"]
    assert normalized["contract_type"] == "fixed"
    assert normalized["is_active"] is True


def test_normalize_pusher_project_hourly():
    raw_payload = {
        "slug": "hourly-dev-project",
        "title": "Projeto por hora",
        "budget": "R$ 50 / hora",
        "is_hourly": True
    }
    normalized = WorkanaRealtimePusher._normalize_pusher_project(raw_payload)
    assert normalized is not None
    assert normalized["contract_type"] == "hourly"
