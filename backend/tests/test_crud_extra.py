import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.database.models import async_session
from app.database import crud

@pytest.mark.asyncio
async def test_crud_save_and_retrieve_project_extra_fields():
    user_id = uuid4()
    
    # Mock de projeto contendo os novos campos de mercado
    project_data = {
        "workana_id": "test_extra_fields_proj",
        "title": "Projeto com Campos Extra",
        "description": "Uma descrição detalhada",
        "url": "https://workana.com/job/test-extra",
        "category": "TI",
        "skills": ["Python", "Flask"],
        "client_name": "Empresa Teste",
        "client_country": "Portugal",
        "client_rating": 4.8,
        "proposals_count": 7,
        "payment_verified": True,
        "posted_at": "há 3 dias"
    }
    
    # 1. Salvar no banco
    proj_id = await crud.save_project(user_id, project_data)
    assert proj_id is not None
    
    # 2. Buscar individualmente
    retrieved = await crud.get_project(user_id, proj_id)
    assert retrieved is not None
    assert retrieved["client_country"] == "Portugal"
    assert retrieved["payment_verified"] is True
    assert retrieved["posted_at"] == "há 3 dias"
    
    # 3. Buscar na listagem
    project_list = await crud.get_projects(user_id, limit=10)
    assert len(project_list) > 0
    match = next(p for p in project_list if p["id"] == proj_id)
    assert match is not None
    assert match["client_country"] == "Portugal"
    assert match["payment_verified"] is True
    assert match["posted_at"] == "há 3 dias"
