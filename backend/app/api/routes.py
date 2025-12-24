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
from app.automation.antiban import antiban
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
            # Tentar obter erro específico
            status = automation.get_status()
            error_msg = status.last_error if status.last_error else "Falha no login. Verifique suas credenciais."
            raise HTTPException(status_code=401, detail=error_msg)
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


# ==================== Login Social (Google/Facebook/Apple) ====================

@router.get("/automation/session-status")
async def get_session_status():
    """Verifica se existe uma sessão salva."""
    return {
        "has_session": automation.has_saved_session(),
        "is_logged_in": automation.is_logged_in
    }


@router.post("/automation/login-with-session")
async def login_with_saved_session():
    """Tenta fazer login usando sessão salva anteriormente."""
    try:
        success = await automation.login_with_session()
        if success:
            await crud.log_activity(
                action_type="login",
                description="Login realizado via sessão salva"
            )
            return {"success": True, "message": "Login realizado via sessão salva!"}
        else:
            return {"success": False, "message": "Sessão expirada. Faça login novamente."}
    except Exception as e:
        logger.error(f"Erro no login com sessão: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automation/start-manual-login")
async def start_manual_login():
    """
    Inicia login manual (para Google/Facebook/Apple).
    Abre navegador visível para o usuário fazer login.
    """
    try:
        result = await automation.start_manual_login()
        if result["success"]:
            await crud.log_activity(
                action_type="login_manual_start",
                description="Iniciado processo de login manual"
            )
        return result
    except Exception as e:
        logger.error(f"Erro ao iniciar login manual: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automation/confirm-manual-login")
async def confirm_manual_login():
    """Confirma que o login manual foi concluído e salva a sessão."""
    try:
        result = await automation.confirm_manual_login()
        if result["success"]:
            await crud.log_activity(
                action_type="login",
                description="Login manual confirmado e sessão salva"
            )
        return result
    except Exception as e:
        logger.error(f"Erro ao confirmar login: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automation/cancel-manual-login")
async def cancel_manual_login():
    """Cancela o processo de login manual."""
    return await automation.cancel_manual_login()


@router.delete("/automation/clear-session")
async def clear_session():
    """Remove sessão salva."""
    await automation.clear_session()
    return {"success": True, "message": "Sessão removida!"}


# ==================== Busca de Projetos ====================

@router.post("/projects/search", response_model=ProjectList)
async def search_projects(filters: SearchFilters):
    """Busca projetos no Workana com os filtros especificados."""
    try:
        # Busca sempre anônima (Fast Search) conforme solicitado pelo usuário
        projects = await automation.search_projects(filters, anonymous=True)
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
        # Busca anônima de detalhes (conforme solicitado pelo usuário, para não exigir login na "busca/filtro")
        project = await automation.get_project_details(project_id, anonymous=True)
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
            # Tenta auto-login se houver sessão (solicitação do usuário: "login quando necessario")
            if automation.has_saved_session():
                logger.info("Login necessário para proposta. Tentando restaurar sessão...")
                if not await automation.login_with_session():
                     raise HTTPException(status_code=401, detail="Sessão expirada. Faça login novamente.")
            else:
                raise HTTPException(status_code=401, detail="Faça login primeiro para enviar propostas")
        
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


# ==================== Projetos Salvos ====================

@router.get("/saved-projects")
async def list_saved_projects(
    limit: int = 50,
    offset: int = 0,
    favorites_only: bool = False,
    not_applied_only: bool = False,
    category: str = None
):
    """Lista projetos salvos no banco de dados."""
    projects = await crud.get_projects(
        limit=limit,
        offset=offset,
        only_favorites=favorites_only,
        only_not_applied=not_applied_only,
        category=category
    )
    return {"projects": projects, "total": len(projects)}


@router.get("/saved-projects/{project_id}")
async def get_saved_project(project_id: int):
    """Obtém detalhes de um projeto salvo."""
    project = await crud.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return project


@router.post("/saved-projects")
async def save_project(project_data: dict):
    """Salva um projeto encontrado no banco de dados."""
    try:
        project_id = await crud.save_project(project_data)
        await crud.log_activity(
            action_type="project_saved",
            description=f"Projeto salvo: {project_data.get('title', 'Sem título')}"
        )
        return {"success": True, "project_id": project_id, "message": "Projeto salvo!"}
    except Exception as e:
        logger.error(f"Erro ao salvar projeto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/saved-projects/{project_id}/favorite")
async def toggle_favorite(project_id: int):
    """Alterna o status de favorito de um projeto."""
    is_favorite = await crud.toggle_project_favorite(project_id)
    return {"success": True, "is_favorite": is_favorite}


@router.post("/saved-projects/{project_id}/applied")
async def mark_as_applied(project_id: int):
    """Marca um projeto como aplicado."""
    await crud.mark_project_applied(project_id)
    return {"success": True, "message": "Projeto marcado como aplicado!"}


@router.post("/saved-projects/{project_id}/ignore")
async def ignore_project(project_id: int):
    """Ignora um projeto (não aparece mais nas listagens)."""
    await crud.ignore_project(project_id)
    return {"success": True, "message": "Projeto ignorado!"}


@router.put("/saved-projects/{project_id}/notes")
async def update_notes(project_id: int, notes_data: dict):
    """Atualiza as notas de um projeto."""
    notes = notes_data.get("notes", "")
    await crud.update_project_notes(project_id, notes)
    return {"success": True, "message": "Notas atualizadas!"}


# ==================== Logs de Atividade ====================

@router.get("/logs")
async def list_activity_logs(
    limit: int = 100,
    action_type: str = None,
    status: str = None
):
    """Lista logs de atividade do sistema."""
    logs = await crud.get_activity_logs(
        limit=limit,
        action_type=action_type,
        status=status
    )
    return {"logs": logs, "total": len(logs)}


@router.post("/logs")
async def create_log(log_data: dict):
    """Cria uma entrada de log manualmente."""
    await crud.log_activity(
        action_type=log_data.get("action_type", "manual"),
        description=log_data.get("description", "Ação manual"),
        details=log_data.get("details"),
        project_id=log_data.get("project_id"),
        status=log_data.get("status", "success")
    )
    return {"success": True, "message": "Log criado!"}


# ==================== Estatísticas ====================

@router.get("/statistics")
async def get_statistics(days: int = 30):
    """Obtém estatísticas dos últimos N dias."""
    stats = await crud.get_statistics(days)
    return {"statistics": stats, "days": days}


@router.get("/statistics/summary")
async def get_statistics_summary():
    """Obtém resumo das estatísticas (hoje, semana, mês)."""
    return await crud.get_statistics_summary()


# ==================== Clientes Bloqueados ====================

@router.get("/blacklist")
async def list_blacklisted_clients():
    """Lista clientes na lista negra."""
    clients = await crud.get_blacklisted_clients()
    return {"clients": clients, "total": len(clients)}


@router.post("/blacklist")
async def add_to_blacklist(client_data: dict):
    """Adiciona um cliente à lista negra."""
    client_name = client_data.get("client_name")
    reason = client_data.get("reason")
    
    if not client_name:
        raise HTTPException(status_code=400, detail="Nome do cliente é obrigatório")
    
    await crud.add_blacklisted_client(client_name, reason)
    await crud.log_activity(
        action_type="blacklist_add",
        description=f"Cliente adicionado à lista negra: {client_name}"
    )
    return {"success": True, "message": f"Cliente '{client_name}' adicionado à lista negra!"}


@router.delete("/blacklist/{client_id}")
async def remove_from_blacklist(client_id: int):
    """Remove um cliente da lista negra."""
    await crud.remove_blacklisted_client(client_id)
    return {"success": True, "message": "Cliente removido da lista negra!"}


@router.get("/blacklist/check/{client_name}")
async def check_blacklist(client_name: str):
    """Verifica se um cliente está na lista negra."""
    is_blacklisted = await crud.is_client_blacklisted(client_name)
    return {"client_name": client_name, "is_blacklisted": is_blacklisted}


# ==================== Sistema Anti-Ban ====================

@router.get("/antiban/status")
async def get_antiban_status():
    """Retorna status atual do sistema anti-ban."""
    return antiban.get_status()


@router.get("/antiban/config")
async def get_antiban_config():
    """Retorna configuração atual do sistema anti-ban."""
    return antiban.get_config_dict()


@router.put("/antiban/config")
async def update_antiban_config(config: dict):
    """Atualiza configuração do sistema anti-ban."""
    antiban.update_config(config)
    await crud.log_activity(
        action_type="antiban_config",
        description="Configuração anti-ban atualizada",
        details=config
    )
    return {"success": True, "message": "Configuração anti-ban atualizada!", "config": antiban.get_config_dict()}


@router.get("/antiban/can-send-proposal")
async def can_send_proposal():
    """Verifica se pode enviar uma proposta agora."""
    can_send, message = antiban.can_send_proposal()
    return {
        "can_send": can_send,
        "message": message,
        "proposals_today": antiban.stats.proposals_sent_today,
        "max_today": antiban.config.max_proposals_per_day,
        "proposals_this_hour": antiban.stats.proposals_sent_this_hour,
        "max_per_hour": antiban.config.max_proposals_per_hour
    }


@router.get("/antiban/can-search")
async def can_search():
    """Verifica se pode fazer uma busca agora."""
    can_do, message = antiban.can_search()
    return {
        "can_search": can_do,
        "message": message,
        "searches_this_hour": antiban.stats.searches_this_hour,
        "max_per_hour": antiban.config.max_searches_per_hour
    }


@router.post("/antiban/reset-consecutive")
async def reset_consecutive_proposals():
    """Reseta contador de propostas consecutivas (após pausa)."""
    antiban.reset_consecutive_proposals()
    return {"success": True, "message": "Contador de propostas consecutivas resetado!"}


@router.get("/antiban/working-hours")
async def get_working_hours():
    """Retorna informações sobre horário de operação."""
    return {
        "is_within_working_hours": antiban.is_within_working_hours(),
        "working_hours_start": antiban.config.working_hours_start,
        "working_hours_end": antiban.config.working_hours_end,
        "respect_working_hours": antiban.config.respect_working_hours
    }
