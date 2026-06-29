from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.api.schemas import (
    AutomationStatus, AutomationConfig,
    ProposalTemplate, ProposalTemplateCreate
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
    """Lista todos os templates de proposta do usuário."""
    return await crud.get_templates(user["user_id"])


@router.post("/templates", response_model=ProposalTemplate)
async def create_template(template: ProposalTemplateCreate, user: dict = Depends(get_current_user)):
    """Cria um novo template de proposta do usuário."""
    return await crud.create_template(user["user_id"], template)


@router.put("/templates/{template_id}", response_model=ProposalTemplate)
async def update_template(template_id: int, template: ProposalTemplateCreate, user: dict = Depends(get_current_user)):
    """Atualiza um template existente do usuário."""
    result = await crud.update_template(user["user_id"], template_id, template)
    if not result:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    return result


@router.delete("/templates/{template_id}")
async def delete_template(template_id: int, user: dict = Depends(get_current_user)):
    """Remove um template do usuário."""
    await crud.delete_template(user["user_id"], template_id)
    return {"success": True, "message": "Template removido!"}


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

