import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.prompt_builder import ProposalPromptBuilder
from app.services.proposal_agent import proposal_agent_instance
from app.database import crud
from app.api.schemas import TemplateBlock, ProposalTemplateCreate, BlueprintTestRequest

def test_compile_blueprint_to_content():
    # Test compiling a blueprint containing literal and instruction blocks
    blueprint = [
        {"id": "1", "type": "abertura", "mode": "literal", "enabled": True, "content": "Olá! Seja bem-vindo."},
        {"id": "2", "type": "tom_de_voz", "mode": "instruction", "enabled": True, "content": "Adote um tom profissional."},
        {"id": "3", "type": "cta", "mode": "literal", "enabled": False, "content": "Desativado"},
    ]
    compiled = ProposalPromptBuilder.compile_blueprint_to_content(blueprint)
    
    assert "=== ABERTURA (Texto Exato) ===" in compiled
    assert "Olá! Seja bem-vindo." in compiled
    assert "=== TOM DE VOZ (Instrução) ===" in compiled
    assert "Adote um tom profissional." in compiled
    assert "CTA" not in compiled  # Disabled blocks must be ignored

def test_build_prompt_with_blueprint():
    project = {
        "title": "React Frontend",
        "description": "Criar telas SPA",
        "skills": ["React"],
        "budget": "R$ 1000",
        "client_name": "John Doe"
    }
    blueprint = [
        {"id": "1", "type": "abertura", "mode": "literal", "enabled": True, "content": "Texto Literal de abertura"},
        {"id": "2", "type": "solucao", "mode": "instruction", "enabled": True, "content": "Instrução de solução"}
    ]
    prompt = ProposalPromptBuilder.build_with_blueprint(project, "Alice", blueprint)
    
    assert "React Frontend" in prompt
    assert "Alice" in prompt
    assert "PEÇA 1: ABERTURA (MODO LITERAL" in prompt
    assert "Texto Literal de abertura" in prompt
    assert "PEÇA 2: SOLUCAO (MODO INSTRUÇÃO" in prompt
    assert "Instrução de solução" in prompt

@pytest.mark.asyncio
@patch("app.database.crud.async_session")
async def test_create_template_compiles_blueprint(mock_session_ctx):
    # Mock session
    mock_session = AsyncMock()
    mock_session_ctx.return_value.__aenter__.return_value = mock_session
    
    template_in = ProposalTemplateCreate(
        name="Test Blueprint Template",
        blueprint=[
            TemplateBlock(id="b1", type="abertura", mode="literal", enabled=True, content="Olá!")
        ],
        is_default=True
    )
    
    # Mock config lookup
    mock_config = MagicMock()
    mock_config.preferred_template_id = None
    
    mock_execute_result = MagicMock()
    mock_execute_result.scalars.return_value.all.return_value = []
    mock_execute_result.scalar_one_or_none.return_value = mock_config
    
    mock_session.execute = AsyncMock(return_value=mock_execute_result)
    
    user_id = "00000000-0000-0000-0000-000000000001"
    res = await crud.create_template(user_id, template_in)
    
    assert res.name == "Test Blueprint Template"
    assert "=== ABERTURA (Texto Exato) ===" in res.content
    assert res.blueprint[0].id == "b1"
    assert res.is_default is True

@pytest.mark.asyncio
@patch("app.services.gemini_factory.GeminiFactory")
@patch("app.database.crud.get_automation_config")
@patch("app.database.crud.get_template")
async def test_generate_proposal_with_blueprint(mock_get_template, mock_get_config, mock_gemini_factory):
    # Mock API call
    mock_gemini_factory.create.return_value.generate_content.return_value.text = '{"proposal": "Minha proposta", "suggested_price": "R$ 900", "justification": "justificativa"}'
    
    mock_get_config.return_value = {
        "gemini_api_key": "dummy_key",
        "user_full_name": "Bob"
    }
    
    mock_template = MagicMock()
    mock_template.blueprint = [
        {"id": "1", "type": "abertura", "mode": "literal", "enabled": True, "content": "Olá!"}
    ]
    mock_get_template.return_value = mock_template
    
    project = {"title": "App", "description": "Desc", "skills": [], "budget": "R$ 1000"}
    res = await proposal_agent_instance.generate_proposal("user123", project, template_id=42)
    
    assert res["success"] is True
    assert res["proposal"] == "Minha proposta"
    assert res["suggested_price"] == "R$ 900"

def test_api_test_blueprint_endpoint(client):
    payload = {
        "blueprint": [
            {"id": "b1", "type": "abertura", "mode": "literal", "enabled": True, "content": "Texto abertura"}
        ],
        "project": {
            "title": "API Test Project",
            "description": "Desc",
            "skills": ["FastAPI"],
            "budget": "R$ 1000"
        },
        "run_ai": False
    }
    
    response = client.post("/api/templates/test-blueprint", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Texto abertura" in data["compiled_prompt"]
    assert "API Test Project" in data["compiled_prompt"]


from pydantic import ValidationError

def test_pydantic_blueprint_validation():
    # 1. Test duplicate IDs
    with pytest.raises(ValidationError) as excinfo:
        ProposalTemplateCreate(
            name="Test",
            blueprint=[
                TemplateBlock(id="b1", type="abertura", mode="literal", content="Olá"),
                TemplateBlock(id="b1", type="solucao", mode="instruction", content="Como vai")
            ]
        )
    assert "IDs de bloco duplicados" in str(excinfo.value)

    # 2. Test empty content on active block
    with pytest.raises(ValidationError) as excinfo:
        ProposalTemplateCreate(
            name="Test",
            blueprint=[
                TemplateBlock(id="b1", type="abertura", mode="literal", content="  ")
            ]
        )
    assert "não pode ter conteúdo vazio" in str(excinfo.value)

    # 3. Test no active blocks
    with pytest.raises(ValidationError) as excinfo:
        ProposalTemplateCreate(
            name="Test",
            blueprint=[
                TemplateBlock(id="b1", type="abertura", mode="literal", enabled=False, content="Olá")
            ]
        )
    assert "pelo menos uma peça ativa" in str(excinfo.value)


def test_variable_substitution():
    project = {
        "title": "Desenvolvimento SPA React",
        "description": "SPA",
        "skills": ["React"],
        "budget": "R$ 5000",
        "client_name": "Antônio Silva",
        "deadline_days": 15
    }
    
    # Test case insensitivity and multiple variables
    literal_text = "Olá {nome_cliente}, farei o {titulo_projeto} por {valor} em {prazo}. Assinado: {nome_usuario}."
    resolved = ProposalPromptBuilder.resolve_variables(literal_text, project, "Guilherme")
    
    assert "Antônio Silva" in resolved
    assert "Desenvolvimento SPA React" in resolved
    assert "R$ 5000" in resolved
    assert "15 dias" in resolved
    assert "Guilherme" in resolved
    
    # Test custom variables like {data_atual} and {anos_experiencia}
    literal_text_2 = "Tenho {anos_experiencia} anos de experiência. Hoje é {data_atual}."
    resolved_2 = ProposalPromptBuilder.resolve_variables(literal_text_2, project, "Guilherme")
    assert "vários" in resolved_2
    import datetime
    assert datetime.datetime.now().strftime("%d/%m/%Y") in resolved_2


@pytest.mark.asyncio
@patch("app.services.gemini_factory.GeminiFactory")
@patch("app.database.crud.get_automation_config")
@patch("app.database.crud.get_template")
async def test_generate_proposal_template_not_found(mock_get_template, mock_get_config, mock_gemini_factory):
    mock_get_template.return_value = None
    mock_get_config.return_value = {"gemini_api_key": "dummy_key", "user_full_name": "Bob"}
    
    project = {"title": "App", "description": "Desc", "skills": [], "budget": "R$ 1000"}
    res = await proposal_agent_instance.generate_proposal("user123", project, template_id=999)
    
    assert res["success"] is False
    assert res["error_code"] == 404
    assert "não encontrado ou acesso negado" in res["error"]


@pytest.mark.asyncio
@patch("app.services.gemini_factory.GeminiFactory")
@patch("app.database.crud.get_automation_config")
@patch("app.database.crud.get_template")
async def test_generate_proposal_returns_template_id_used(mock_get_template, mock_get_config, mock_gemini_factory):
    mock_gemini_factory.create.return_value.generate_content.return_value.text = '{"proposal": "Minha proposta", "suggested_price": "R$ 900", "justification": "justificativa"}'
    mock_get_config.return_value = {"gemini_api_key": "dummy_key", "user_full_name": "Bob"}
    
    mock_template = MagicMock()
    mock_template.id = 42
    mock_template.blueprint = [{"id": "1", "type": "abertura", "mode": "literal", "enabled": True, "content": "Olá!"}]
    mock_get_template.return_value = mock_template
    
    project = {"title": "App", "description": "Desc", "skills": [], "budget": "R$ 1000"}
    res = await proposal_agent_instance.generate_proposal("user123", project, template_id=42)
    
    assert res["success"] is True
    assert res["template_id_used"] == 42


@patch("app.api.routers.automation.crud.get_active_system_template")
@patch("app.api.routers.automation.crud.get_templates")
def test_api_list_templates_includes_system(mock_get_templates, mock_get_active_system_template, client):
    # Mock return list of personal templates
    personal_mock = MagicMock()
    personal_mock.id = 1
    personal_mock.name = "My Template"
    personal_mock.content = "Texto do meu template"
    personal_mock.blueprint = [{"id": "1", "type": "abertura", "mode": "literal", "enabled": True, "content": "Olá"}]
    personal_mock.is_default = False
    personal_mock.created_at = None
    personal_mock.updated_at = None
    personal_mock.schema_version = 1
    personal_mock.default_budget = None
    personal_mock.default_deadline_days = None
    
    mock_get_templates.return_value = [personal_mock]

    # Mock active system template
    sys_mock = MagicMock()
    sys_mock.slug = "workana-consultivo"
    sys_mock.name = "Proposta Consultiva de Alta Conversão"
    sys_mock.content = "Texto do template oficial"
    sys_mock.blueprint = [{"id": "b1", "type": "abertura", "mode": "literal", "enabled": True, "content": "Olá"}]
    sys_mock.version = 1
    sys_mock.created_at = None
    sys_mock.updated_at = None
    mock_get_active_system_template.return_value = sys_mock
    
    response = client.get("/api/templates")
    assert response.status_code == 200
    data = response.json()
    
    # Assert personal is in output
    assert any(t["name"] == "My Template" for t in data)
    # Assert system is in output
    assert any(t["name"] == "Proposta Consultiva de Alta Conversão" for t in data)


@patch("app.api.routers.automation.crud.create_template")
@patch("app.api.routers.automation.crud.get_active_system_template")
def test_api_duplicate_system_template(mock_get_active_system_template, mock_create_template, client):
    # Mock active system template
    sys_mock = MagicMock()
    sys_mock.slug = "workana-consultivo"
    sys_mock.name = "Proposta Consultiva de Alta Conversão"
    sys_mock.blueprint = [{"id": "b1", "type": "abertura", "mode": "literal", "enabled": True, "content": "Olá"}]
    sys_mock.version = 1
    sys_mock.created_at = None
    sys_mock.updated_at = None
    mock_get_active_system_template.return_value = sys_mock

    # Mock create_template return
    dup_mock = MagicMock()
    dup_mock.id = 99
    dup_mock.name = "Proposta Consultiva de Alta Conversão (Cópia)"
    dup_mock.content = "Texto da cópia do template"
    dup_mock.blueprint = [{"id": "1", "type": "abertura", "mode": "literal", "enabled": True, "content": "Olá"}]
    dup_mock.is_default = False
    dup_mock.schema_version = 1
    dup_mock.default_budget = None
    dup_mock.default_deadline_days = None
    
    mock_create_template.return_value = dup_mock
    
    response = client.post("/api/templates/duplicate/workana-consultivo")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 99
    assert data["name"] == "Proposta Consultiva de Alta Conversão (Cópia)"
