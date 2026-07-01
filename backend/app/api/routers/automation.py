from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.api.schemas import (
    AutomationStatus, AutomationConfig,
    ProposalTemplate, ProposalTemplateCreate,
    BlueprintTestRequest
)
from app.auth import get_current_user
from app.automation.browser import WorkanaAutomation
from app.automation.antiban import antiban
from app.database import crud

router = APIRouter()
from app.automation.browser import automation_instance as automation

# ==================== Automação ====================

@router.get("/automation/status", response_model=AutomationStatus)
async def get_automation_status(user: dict = Depends(get_current_user)):
    """Retorna o status atual da automação."""
    return automation.get_status()


@router.get("/automation/config", response_model=AutomationConfig)
async def get_automation_config(user: dict = Depends(get_current_user)):
    """Retorna as configurações de automação do usuário."""
    return await crud.get_automation_config(user["user_id"])


@router.put("/automation/config")
async def update_automation_config(config: AutomationConfig, user: dict = Depends(get_current_user)):
    """Atualiza configurações de automação do usuário."""
    await crud.save_automation_config(user["user_id"], config.model_dump())
    return {"success": True, "message": "Configurações atualizadas!"}


@router.get("/automation/credentials", response_model=dict)
async def get_credentials_status(user: dict = Depends(get_current_user)):
    """Retorna se as credenciais do usuário estão configuradas."""
    creds = await crud.get_credentials(user["user_id"])
    if creds:
        email = creds.get("email", "")
        # Mascarar email
        if "@" in email:
            parts = email.split("@")
            masked = parts[0][:3] + "***" + "@" + parts[1]
        else:
            masked = "***"
        return {"configured": True, "email": masked}
    return {"configured": False, "email": None}


@router.post("/automation/credentials")
async def update_credentials(creds: dict, user: dict = Depends(get_current_user)):
    """Atualiza as credenciais do Workana do usuário."""
    email = creds.get("email")
    password = creds.get("password")
    if not email or not password:
        return {"success": False, "message": "Email e senha são obrigatórios"}
    await crud.save_credentials(user["user_id"], email, password)
    return {"success": True, "message": "Credenciais salvas com sucesso!"}


# ==================== Templates de Proposta ====================

@router.get("/templates", response_model=List[ProposalTemplate])
async def list_templates(user: dict = Depends(get_current_user)):
    """Lista todos os templates de proposta do usuário, combinados com o template global ativo."""
    personal_templates = await crud.get_templates(user["user_id"])
    
    # Adicionar metadados nos templates pessoais
    for t in personal_templates:
        t.template_ref = f"personal:{t.id}"
        t.is_system = False
        t.can_edit = True
        t.can_delete = True
        t.version = t.schema_version
        
    has_personal_default = any(t.is_default for t in personal_templates)
    
    # Buscar o template de sistema ativo
    sys_template = await crud.get_active_system_template("workana-consultivo")
    if sys_template:
        # Converter o blueprint JSON em objetos TemplateBlock
        from app.api.schemas import TemplateBlock
        blueprint_blocks = []
        for b in sys_template.blueprint:
            blueprint_blocks.append(TemplateBlock(
                id=b.get("id"),
                type=b.get("type"),
                mode=b.get("mode"),
                enabled=b.get("enabled", True),
                content=b.get("content"),
                config=b.get("config")
            ))
            
        sys_t = ProposalTemplate(
            id=None,
            name=sys_template.name,
            content=sys_template.content,
            blueprint=blueprint_blocks,
            schema_version=1,
            default_budget=None,
            default_deadline_days=None,
            is_default=not has_personal_default,
            created_at=sys_template.created_at,
            updated_at=sys_template.updated_at,
            template_ref=f"system:{sys_template.slug}",
            is_system=True,
            can_edit=False,
            can_delete=False,
            version=sys_template.version
        )
        if sys_t.is_default:
            return [sys_t] + personal_templates
        else:
            return personal_templates + [sys_t]
            
    return personal_templates


@router.post("/templates/duplicate/{slug}", response_model=ProposalTemplate)
async def duplicate_system_template(slug: str, user: dict = Depends(get_current_user)):
    """Duplica um template de sistema ativo, criando um template pessoal editável."""
    sys_template = await crud.get_active_system_template(slug)
    if not sys_template:
        raise HTTPException(status_code=404, detail="Template de sistema não encontrado")
    
    from app.api.schemas import ProposalTemplateCreate, TemplateBlock
    
    blueprint_blocks = []
    for b in sys_template.blueprint:
        blueprint_blocks.append(TemplateBlock(
            id=b.get("id"),
            type=b.get("type"),
            mode=b.get("mode"),
            enabled=b.get("enabled", True),
            content=b.get("content"),
            config=b.get("config")
        ))
        
    template_create = ProposalTemplateCreate(
        name=f"{sys_template.name} (Cópia)",
        blueprint=blueprint_blocks,
        schema_version=1,
        default_budget=None,
        default_deadline_days=None,
        is_default=False
    )
    
    # Cria o template pessoal a partir do blueprint do sistema
    created_personal = await crud.create_template(user["user_id"], template_create)
    
    # Preencher metadados para resposta do endpoint
    created_personal.template_ref = f"personal:{created_personal.id}"
    created_personal.is_system = False
    created_personal.can_edit = True
    created_personal.can_delete = True
    created_personal.version = created_personal.schema_version
    
    return created_personal


@router.post("/templates", response_model=ProposalTemplate)
async def create_template(template: ProposalTemplateCreate, user: dict = Depends(get_current_user)):
    """Cria um novo template de proposta do usuário."""
    res = await crud.create_template(user["user_id"], template)
    res.template_ref = f"personal:{res.id}"
    res.is_system = False
    res.can_edit = True
    res.can_delete = True
    res.version = res.schema_version
    return res


@router.put("/templates/{template_id}", response_model=ProposalTemplate)
async def update_template(template_id: int, template: ProposalTemplateCreate, user: dict = Depends(get_current_user)):
    """Atualiza um template existente do usuário."""
    result = await crud.update_template(user["user_id"], template_id, template)
    if not result:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    result.template_ref = f"personal:{result.id}"
    result.is_system = False
    result.can_edit = True
    result.can_delete = True
    result.version = result.schema_version
    return result


@router.delete("/templates/{template_id}")
async def delete_template(template_id: int, user: dict = Depends(get_current_user)):
    """Remove um template do usuário."""
    deleted = await crud.delete_template(user["user_id"], template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    return {"success": True, "message": "Template removido!"}


@router.post("/templates/test-blueprint")
async def test_blueprint(payload: BlueprintTestRequest, user: dict = Depends(get_current_user)):
    """
    Testa a compilação de um blueprint e opcionalmente gera a proposta com IA
    usando dados fictícios sem precisar salvar no banco primeiro.
    """
    from app.services.prompt_builder import ProposalPromptBuilder
    from app.services.proposal_agent import proposal_agent_instance
    
    # 1. Obter dados do projeto fictício (ou usar dados padrão de teste)
    project_data = payload.project
    if not project_data:
        project_data = {
            "title": "Desenvolvimento de Aplicativo Delivery",
            "description": "Preciso de um desenvolvedor para criar um aplicativo de delivery completo com painel administrativo e app para motoboys em React Native.",
            "skills": ["React Native", "Node.js", "PostgreSQL", "Firebase"],
            "budget": "R$ 5.000 - 10.000",
            "client_name": "Cliente de Exemplo"
        }
    
    # 2. Compilar o blueprint para a representação em prompt
    blueprint_dicts = [b.dict() for b in payload.blueprint]
    user_name = "Desenvolvedor"
    
    try:
        config = await crud.get_automation_config(user["user_id"])
        if config.get("user_full_name"):
            user_name = config.get("user_full_name")
    except Exception:
        pass
        
    compiled_prompt = ProposalPromptBuilder.build_with_blueprint(
        project=project_data,
        user_name=user_name,
        blueprint=blueprint_dicts
    )
    
    response_data = {
        "success": True,
        "compiled_prompt": compiled_prompt,
        "ai_result": None
    }
    
    # 3. Executar o teste com IA se solicitado
    if payload.run_ai:
        gen_res = await proposal_agent_instance.generate_proposal(
            user_id=user["user_id"],
            project_details=project_data,
            blueprint=blueprint_dicts
        )
        response_data["ai_result"] = gen_res
        
    return response_data


# ==================== Sistema Anti-Ban ====================

@router.get("/antiban/status")
async def get_antiban_status(user: dict = Depends(get_current_user)):
    """Retorna status atual do sistema anti-ban."""
    return await antiban.get_status(user["user_id"])


@router.get("/antiban/config")
async def get_antiban_config(user: dict = Depends(get_current_user)):
    """Retorna configuração atual do sistema anti-ban."""
    return antiban.get_config_dict()


@router.put("/antiban/config")
async def update_antiban_config(config: dict, user: dict = Depends(get_current_user)):
    """Atualiza configuração do sistema anti-ban."""
    antiban.update_config(config)
    await crud.log_activity(
        user_id=user["user_id"],
        action_type="antiban_config",
        description="Configuração anti-ban atualizada",
        details=config
    )
    return {"success": True, "message": "Configuração anti-ban atualizada!", "config": antiban.get_config_dict()}


@router.get("/antiban/can-search")
async def can_search(user: dict = Depends(get_current_user)):
    """Verifica se pode fazer uma busca agora."""
    can_do, message = await antiban.can_search(user["user_id"])
    status = await antiban.get_status(user["user_id"])
    return {
        "can_search": can_do,
        "message": message,
        "searches_this_hour": status["searches_this_hour"],
        "max_per_hour": antiban.config.max_searches_per_hour
    }


# ==================== Catálogo do Sistema ====================

@router.post("/automation/catalog/refresh")
async def refresh_catalog(user: dict = Depends(get_current_user)):
    """Aciona manualmente uma coleta do catálogo (lock-aware, retorna 409 se já em execução)."""
    from app.services.scheduler import scheduler_instance

    # executa um ciclo síncrono (sem job); o lock previne concorrência.
    try:
        result = await scheduler_instance.execute_catalog_upsert()
        return result
    except RuntimeError as e:
        if "already running" in str(e).lower() or "lock" in str(e).lower():
            from fastapi import HTTPException
            raise HTTPException(status_code=409, detail="Uma coleta do catálogo já está em execução.")
        raise

