from fastapi import APIRouter, HTTPException, Depends, Query
from loguru import logger
from typing import List, Optional, Any

from app.api.schemas import (
    SearchFilters, SavedFilter, Project, ProjectList, ProposalGenerationResult,
    ProposalSubmit, ProposalResult, ProposalGenerateRequest,
    CatalogProjectList, SortOption,
)
from app.auth import get_current_user
from app.database import crud

router = APIRouter()
from app.automation.browser import (
    SearchUnavailableError,
    automation_instance as automation,
)

# ==================== Busca de Projetos ====================

@router.get("/projects", response_model=CatalogProjectList)
async def list_catalog(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=24, ge=1, le=100),
    q: Optional[str] = None,
    category: Optional[str] = None,
    min_budget: Optional[float] = None,
    max_budget: Optional[float] = None,
    payment_verified: bool = False,
    sort: SortOption = SortOption.NEWEST,
    favorites_only: bool = False,
    hidden_only: bool = False,
    user: dict = Depends(get_current_user)
):
    """Busca paginada no catálogo de projetos (banco de dados, sem scraping)."""
    result = await crud.search_catalog(
        user_id=user["user_id"],
        page=page,
        limit=limit,
        q=q,
        category=category,
        min_budget=min_budget,
        max_budget=max_budget,
        payment_verified=payment_verified if payment_verified else None,
        sort=sort,
        favorites_only=favorites_only,
        hidden_only=hidden_only,
    )
    return result


@router.post("/projects/search", response_model=ProjectList)
async def search_projects(filters: SearchFilters, user: dict = Depends(get_current_user)):
    """Busca projetos no Workana com os filtros especificados."""
    try:
        projects = await automation.search_projects(filters, user_id=user["user_id"])
        
        # Calcular o match_score do backend para cada projeto
        from app.services.scorer import ProjectScorer
        for proj in projects:
            proj.match_score = ProjectScorer.calculate_score(proj, filters)
        
        # Logar atividade de busca e quantidade encontrada
        await crud.log_activity(
            user_id=user["user_id"],
            action_type="search",
            description=f"Busca realizada: {filters.keywords or 'Sem palavras-chave'}",
            details={"filters": filters.model_dump(), "count": len(projects)}
        )
        
        # Se encontrou projetos, registrar também essa estatística
        if projects:
            await crud.log_activity(
                user_id=user["user_id"],
                action_type="project_found",
                description=f"Encontrados {len(projects)} projetos na busca",
                details={"count": len(projects)}
            )
            
        return ProjectList(projects=projects, total=len(projects))
    except SearchUnavailableError as e:
        status_code = 429 if e.restricted else 502
        raise HTTPException(status_code=status_code, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        raise HTTPException(status_code=500, detail=str(e))
 
 
@router.get("/projects/{project_id}", response_model=Project)
async def get_project_details(project_id: str, user: dict = Depends(get_current_user)):
    """Obtém detalhes de um projeto específico (live search)."""
    try:
        project = await automation.get_project_details(project_id, user_id=user["user_id"])
        if not project:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter projeto: {e}")
        raise HTTPException(status_code=500, detail=str(e))
 
 
@router.post("/projects/{project_id}/generate-proposal", response_model=ProposalGenerationResult)
async def generate_proposal(
    project_id: str,
    payload: Optional[ProposalGenerateRequest] = None,
    template_id: Optional[Any] = None,
    user: dict = Depends(get_current_user)
):
    """Gera uma proposta personalizada usando IA."""
    from app.services.proposal_agent import proposal_agent_instance
    
    try:
        # Primeiro busca os detalhes do projeto para alimentar a IA
        project = await automation.get_project_details(project_id, user_id=user["user_id"])
        if not project:
            raise HTTPException(status_code=404, detail="Projeto não encontrado para gerar proposta")
        
        # Converte para dict para facilitar o uso na AI
        project_dict = {
            "title": project.title,
            "description": project.description,
            "skills": project.skills,
            "budget": project.budget
        }
        
        # Obter o template_id de query param ou JSON body payload
        actual_template_id = template_id
        if payload and payload.template_id:
            actual_template_id = payload.template_id
            
        # Chama a IA
        result = await proposal_agent_instance.generate_proposal(
            user["user_id"], project_dict, template_id=actual_template_id
        )
        
        if not result.get("success") and result.get("error_code") == 404:
            raise HTTPException(status_code=404, detail=result.get("error"))
        
        # Salvar proposta gerada no histórico
        if result.get("success"):
            try:
                await crud.save_ai_proposal(
                    user_id=user["user_id"],
                    project_id=project_id,
                    project_title=project.title,
                    project_url=project.url,
                    proposal_text=result.get("proposal", ""),
                    suggested_price=result.get("suggested_price", "R$ 0"),
                    template_id=result.get("template_id_used")
                )
                logger.info(f"Proposta salva no histórico para o usuário {user['user_id']}, projeto: {project_id}")
            except Exception as e:
                logger.warning(f"Erro ao salvar proposta no histórico: {e}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar proposta: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Projetos Salvos ====================

@router.get("/saved-projects")
async def list_saved_projects(
    limit: int = 50,
    offset: int = 0,
    favorites_only: bool = False,
    not_applied_only: bool = False,
    category: str = None,
    user: dict = Depends(get_current_user)
):
    """Lista projetos salvos no banco de dados do usuário."""
    projects = await crud.get_projects(
        user_id=user["user_id"],
        limit=limit,
        offset=offset,
        only_favorites=favorites_only,
        only_not_applied=not_applied_only,
        category=category
    )
    return {"projects": projects, "total": len(projects)}


@router.get("/saved-projects/{project_id}")
async def get_saved_project(project_id: int, user: dict = Depends(get_current_user)):
    """Obtém detalhes de um projeto salvo do usuário."""
    project = await crud.get_project(user["user_id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return project


@router.post("/saved-projects")
async def save_project(project_data: dict, user: dict = Depends(get_current_user)):
    """Salva um projeto encontrado no banco de dados do usuário."""
    try:
        project_id = await crud.save_project(user["user_id"], project_data)
        await crud.log_activity(
            user_id=user["user_id"],
            action_type="project_saved",
            description=f"Projeto salvo: {project_data.get('title', 'Sem título')}"
        )
        return {"success": True, "project_id": project_id, "message": "Projeto salvo!"}
    except Exception as e:
        logger.error(f"Erro ao salvar projeto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/saved-projects/{project_id}/favorite")
async def toggle_favorite(project_id: int, user: dict = Depends(get_current_user)):
    """Alterna o status de favorito de um projeto do usuário."""
    is_favorite = await crud.toggle_project_favorite(user["user_id"], project_id)
    return {"success": True, "is_favorite": is_favorite}


@router.post("/saved-projects/{project_id}/applied")
async def mark_as_applied(project_id: int, user: dict = Depends(get_current_user)):
    """Marca um projeto como aplicado."""
    await crud.mark_project_applied(user["user_id"], project_id)
    return {"success": True, "message": "Projeto marcado como aplicado!"}


@router.post("/saved-projects/{project_id}/ignore")
async def ignore_project(project_id: int, user: dict = Depends(get_current_user)):
    """Ignora um projeto (não aparece mais nas listagens)."""
    await crud.ignore_project(user["user_id"], project_id)
    return {"success": True, "message": "Projeto ignorado!"}


@router.put("/saved-projects/{project_id}/notes")
async def update_notes(project_id: int, notes_data: dict, user: dict = Depends(get_current_user)):
    """Atualiza as notas de um projeto do usuário."""
    notes = notes_data.get("notes", "")
    await crud.update_project_notes(user["user_id"], project_id, notes)
    return {"success": True, "message": "Notas atualizadas!"}


# ==================== Filtros Salvos ====================

@router.get("/filters", response_model=List[SavedFilter])
async def list_saved_filters(user: dict = Depends(get_current_user)):
    """Lista todos os filtros salvos do usuário."""
    return await crud.get_saved_filters(user["user_id"])


@router.post("/filters", response_model=SavedFilter)
async def create_filter(filter_data: SavedFilter, user: dict = Depends(get_current_user)):
    """Salva um novo filtro para o usuário."""
    return await crud.create_filter(user["user_id"], filter_data)


@router.delete("/filters/{filter_id}")
async def delete_filter(filter_id: int, user: dict = Depends(get_current_user)):
    """Remove um filtro salvo do usuário."""
    await crud.delete_filter(user["user_id"], filter_id)
    return {"success": True, "message": "Filtro removido!"}


# ==================== Envio de Propostas ====================

@router.post("/projects/{project_id}/submit-proposal", response_model=ProposalResult)
async def submit_proposal(project_id: str, proposal: ProposalSubmit, user: dict = Depends(get_current_user)):
    """Envia uma proposta de fato para o projeto no Workana."""
    try:
        if proposal.project_id != project_id:
            proposal.project_id = project_id
            
        result = await automation.submit_proposal(user["user_id"], proposal)
        return result
    except Exception as e:
        logger.error(f"Erro ao enviar proposta para {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
