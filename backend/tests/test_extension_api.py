"""
Testes unitários para a API da Extensão e Envio Seguro de Propostas.
"""

import pytest
from unittest.mock import AsyncMock, patch


def test_extension_status_initial(client):
    """Verifica status da extensão quando nenhuma esteve conectada."""
    response = client.get("/api/automation/extension/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_connected" in data
    assert "pending_tasks" in data
    assert "completed_today" in data


def test_extension_heartbeat_and_status(client):
    """Verifica envio de heartbeat e atualização de status conectado."""
    hb_payload = {
        "version": "2.0.0",
        "active": True,
        "workana_logged_in": True,
        "bids_remaining": 15,
    }
    hb_res = client.post("/api/automation/extension/heartbeat", json=hb_payload)
    assert hb_res.status_code == 200
    assert hb_res.json()["success"] is True

    status_res = client.get("/api/automation/extension/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["is_connected"] is True
    assert status_data["version"] == "2.0.0"
    assert status_data["bids_remaining"] == 15


def test_extension_tasks_workflow(client):
    """Verifica criação de tarefa, consulta e relatório de conclusão da extensão."""
    # 1. Criar tarefa
    task_payload = {
        "project_id": "desenvolvimento-api-fastapi-123",
        "budget": 1200.0,
        "custom_message": "Olá, tenho vasta experiência em desenvolvimento FastAPI assíncrono.",
        "deadline_days": 10,
    }
    create_res = client.post("/api/automation/extension/tasks", json=task_payload)
    assert create_res.status_code == 200
    task_data = create_res.json()
    assert "task_id" in task_data
    task_id = task_data["task_id"]
    assert task_data["budget"] == 1200.0

    # 2. Consultar tarefas pendentes
    get_res = client.get("/api/automation/extension/tasks")
    assert get_res.status_code == 200
    tasks = get_res.json()["tasks"]
    assert any(t["task_id"] == task_id for t in tasks)

    # 3. Reportar conclusão
    with patch("app.automation.antiban.antiban.register_proposal_sent", new_callable=AsyncMock):
        with patch("app.database.crud.save_proposal_history", new_callable=AsyncMock):
            complete_payload = {
                "success": True,
                "message": "Proposta enviada com sucesso!",
                "project_id": "desenvolvimento-api-fastapi-123",
                "redirect_url": "https://www.workana.com/messages/index/123?added=999&bid=1",
                "duration_ms": 2100,
            }
            complete_res = client.post(
                f"/api/automation/extension/tasks/{task_id}/complete",
                json=complete_payload,
            )
            assert complete_res.status_code == 200
            assert complete_res.json()["success"] is True


def test_submit_proposal_extension_dispatch_mode(client):
    """Verifica o redirecionamento automático para a extensão quando dispatch_mode='extension'."""
    proposal_payload = {
        "project_id": "projeto-extensao-teste-456",
        "custom_message": "Proposta via extensão com segurança máxima.",
        "budget": 750.0,
        "deadline_days": 7,
        "dispatch_mode": "extension",
    }

    res = client.post(
        "/api/projects/projeto-extensao-teste-456/submit-proposal",
        json=proposal_payload,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "extensão" in data["message"].lower() or "extension" in data["message"].lower()
    assert data["project_id"] == "projeto-extensao-teste-456"
    assert data["proposal_id"] is not None


def test_generate_proposal_quick_endpoint(client):
    """Verifica a geração rápida de propostas da extensão com dados diretos e tom."""
    fake_ai_result = {
        "success": True,
        "proposal": "Olá, tudo bem?\n\nAnalisei seu projeto de aplicativo e posso entregar um MVP completo.",
        "suggested_price": "R$ 1.500,00",
        "suggested_deadline_days": 10,
        "justification": "Escopo condizente com complexidade média.",
        "template_id_used": "system:workana-consultivo",
    }

    with patch(
        "app.services.proposal_agent.proposal_agent_instance.generate_proposal",
        new_callable=AsyncMock,
    ) as mock_gen:
        mock_gen.return_value = fake_ai_result

        with patch("app.database.crud.save_ai_proposal", new_callable=AsyncMock) as mock_save:
            mock_save.return_value = 888
            with patch("app.database.crud.save_project_to_draft_batch", new_callable=AsyncMock):
                with patch(
                    "app.database.crud.get_project_proposal_versions", new_callable=AsyncMock
                ) as mock_ver:
                    mock_ver.return_value = [{"id": 888, "proposal": fake_ai_result["proposal"]}]

                    payload = {
                        "project_id": "job-slug-direto-777",
                        "title": "Desenvolver App Flutter com Pagamento",
                        "description": "Precisamos de um aplicativo mobile em Flutter com autenticação e gateway.",
                        "skills": ["Flutter", "Dart", "Firebase"],
                        "budget": "R$ 1.000 - 3.000",
                        "client_name": "Carlos",
                        "tone": "persuasivo",
                        "price_level": "standard",
                    }

                    res = client.post("/api/proposals/generate-quick", json=payload)
                    assert res.status_code == 200
                    data = res.json()
                    assert data["success"] is True
                    assert "Analisei seu projeto" in data["proposal"]
                    assert data["proposal_id"] == 888
                    assert mock_gen.called
                    call_kwargs = mock_gen.call_args.kwargs
                    assert call_kwargs.get("tone") == "persuasivo"
                    assert call_kwargs.get("price_level") == "standard"
                    assert (
                        mock_gen.call_args.args[1]["title"]
                        == "Desenvolver App Flutter com Pagamento"
                    )
