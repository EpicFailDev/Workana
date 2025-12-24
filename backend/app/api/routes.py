"""
Rotas da API para automação do Workana.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
from loguru import logger

from app.api.schemas import (
    CredentialsInput, CredentialsStatus, MessageResponse,
    SearchFilters, SavedFilter, Project, ProjectList,
    ProposalTemplate, ProposalTemplateCreate,
    ProposalSubmit, ProposalResult, ProposalHistory,
    DashboardStats, AutomationStatus, AutomationConfig
)
from app.automation.browser import WorkanaAutomation
from app.database import crud

router = APIRouter()

# Instância global da automação
automation = WorkanaAutomation()


# ==================== Credenciais ====================

@router.post("/credentials", response_model=MessageResponse)
async def save_credentials(credentials: CredentialsInput):
    """Salva as credenciais do Workana."""
    try:
        await crud.save_credentials(credentials.email, credentials.password)
        logger.info(f"Credenciais salvas para {credentials.email}")
        return MessageResponse(success=True, message="Credenciais salvas com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao salvar credenciais: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/credentials/status", response_model=CredentialsStatus)
async def get_credentials_status():
    """Verifica se as credenciais estão configuradas."""
    creds = await crud.get_credentials()
    if creds:
        # Ocultar parte do email
        email = creds["email"]
        hidden_email = email[:3] + "***" + email[email.index("@"):]
        return CredentialsStatus(configured=True, email=hidden_email)
    return CredentialsStatus(configured=False, email=None)


# ==================== Automação ====================

@router.get("/automation/status", response_model=AutomationStatus)
async def get_automation_status():
    """Retorna o status atual da automação."""
    return automation.get_status()


@router.post("/automation/login", response_model=MessageResponse)
async def login_workana():
    """Realiza login no Workana."""
    try:
        creds = await crud.get_credentials()
        if not creds:
            raise HTTPException(status_code=400, detail="Credenciais não configuradas")
        
        success = await automation.login(creds["email"], creds["password"])
        if success:
            return MessageResponse(success=True, message="Login realizado com sucesso!")
        else:
            raise HTTPException(status_code=401, detail="Falha no login. Verifique suas credenciais.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automation/logout", response_model=MessageResponse)
async def logout_workana():
    """Realiza logout do Workana."""
    await automation.logout()
    return MessageResponse(success=True, message="Logout realizado!")


@router.put("/automation/config", response_model=MessageResponse)
async def update_automation_config(config: AutomationConfig):
    """Atualiza configurações de automação."""
    await crud.save_automation_config(config.model_dump())
    return MessageResponse(success=True, message="Configurações atualizadas!")


# ==================== Busca de Projetos ====================

@router.post("/projects/search", response_model=ProjectList)
async def search_projects(filters: SearchFilters):
    """Busca projetos no Workana com os filtros especificados."""
    try:
        if not automation.is_logged_in:
            raise HTTPException(status_code=401, detail="Faça login primeiro")
        
        projects = await automation.search_projects(filters)
        return ProjectList(projects=projects, total=len(projects))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}", response_model=Project)
async def get_project_details(project_id: str):
    """Obtém detalhes de um projeto específico."""
    try:
        if not automation.is_logged_in:
            raise HTTPException(status_code=401, detail="Faça login primeiro")
        
        project = await automation.get_project_details(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter projeto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Filtros Salvos ====================

@router.get("/filters", response_model=List[SavedFilter])
async def list_saved_filters():
    """Lista todos os filtros salvos."""
    return await crud.get_saved_filters()


@router.post("/filters", response_model=SavedFilter)
async def create_filter(filter_data: SavedFilter):
    """Salva um novo filtro."""
    return await crud.create_filter(filter_data)


@router.delete("/filters/{filter_id}", response_model=MessageResponse)
async def delete_filter(filter_id: int):
    """Remove um filtro salvo."""
    await crud.delete_filter(filter_id)
    return MessageResponse(success=True, message="Filtro removido!")


# ==================== Templates de Proposta ====================

@router.get("/templates", response_model=List[ProposalTemplate])
async def list_templates():
    """Lista todos os templates de proposta."""
    return await crud.get_templates()


@router.post("/templates", response_model=ProposalTemplate)
async def create_template(template: ProposalTemplateCreate):
    """Cria um novo template de proposta."""
    return await crud.create_template(template)


@router.put("/templates/{template_id}", response_model=ProposalTemplate)
async def update_template(template_id: int, template: ProposalTemplateCreate):
    """Atualiza um template existente."""
    result = await crud.update_template(template_id, template)
    if not result:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    return result


@router.delete("/templates/{template_id}", response_model=MessageResponse)
async def delete_template(template_id: int):
    """Remove um template."""
    await crud.delete_template(template_id)
    return MessageResponse(success=True, message="Template removido!")


# ==================== Propostas ====================

@router.post("/proposals/send", response_model=ProposalResult)
async def send_proposal(proposal: ProposalSubmit):
    """Envia uma proposta para um projeto."""
    try:
        if not automation.is_logged_in:
            raise HTTPException(status_code=401, detail="Faça login primeiro")
        
        # Verificar limite diário
        stats = await crud.get_daily_stats()
        config = await crud.get_automation_config()
        if stats["proposals_today"] >= config.get("max_proposals_per_day", 10):
            raise HTTPException(
                status_code=429, 
                detail="Limite diário de propostas atingido"
            )
        
        # Obter template se especificado
        message = proposal.custom_message
        if proposal.template_id:
            template = await crud.get_template(proposal.template_id)
            if template:
                message = template.content
        
        # Enviar proposta
        result = await automation.send_proposal(
            project_id=proposal.project_id,
            message=message,
            budget=proposal.budget,
            deadline_days=proposal.deadline_days
        )
        
        # Salvar no histórico
        if result.success:
            await crud.save_proposal_history(proposal, result)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao enviar proposta: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proposals/history", response_model=List[ProposalHistory])
async def get_proposal_history(limit: int = 50):
    """Obtém o histórico de propostas enviadas."""
    return await crud.get_proposal_history(limit)


# ==================== Dashboard ====================

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Retorna estatísticas para o dashboard."""
    return await crud.get_dashboard_stats()
