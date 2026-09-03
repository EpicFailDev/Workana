from fastapi import APIRouter, HTTPException, Depends, Query
from loguru import logger
from typing import List, Optional, Any

from app.api.schemas import (
    SearchFilters, SavedFilter, Project, ProjectList, ProposalGenerationResult,
    ProposalSubmit, ProposalResult, ProposalGenerateRequest, ProposalSaveRequest,
    BatchItemUpdateRequest,
    CatalogProjectList, SortOption, BulkStateRequest, BulkStateResult,
    ProjectStateRequest, ProjectNotesUpdate, AnalyzeRequest, AnalysisResult,
    BulkGenerateRequest, BulkGenerateResponse, ProposalBatchCreate,
    ProposalBatchResponse, ProposalBatchItemResponse, ProposalBatchListResponse,
    BidsHistoryResponse, BidsHistoryPoint,
)
from app.auth import get_current_user
from app.database import crud
from app.services.scorer import ProjectScorer

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


@router.get("/projects/batches", response_model=ProposalBatchListResponse)
async def list_batches(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
):
    """Lista o histórico de lotes de proposta do usuário."""
    batches = await crud.get_proposal_batches(user["user_id"], limit=limit, offset=offset)
    total = await crud.count_proposal_batches(user["user_id"])
    return ProposalBatchListResponse(batches=batches, total=total)


@router.get("/projects/all-proposals")
async def get_all_proposals(
    status: Optional[str] = Query(None, description="Filtrar por status: draft, sent, failed, etc."),
    q: Optional[str] = Query(None, description="Termo de busca por título ou texto"),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
):
    """Retorna todas as propostas geradas, salvas e enviadas pelo usuário."""
    return await crud.get_all_unified_proposals(
        user_id=user["user_id"],
        status=status,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.post("/projects/bulk-state", response_model=BulkStateResult)
async def bulk_project_state(
    payload: BulkStateRequest,
    user: dict = Depends(get_current_user),
):
    """Aplica favorito/oculto a IDs explícitos ou a todos os resultados filtrados."""
    if not payload.project_ids and payload.filters is None:
        raise HTTPException(status_code=422, detail="Informe project_ids ou filters.")

    ids = await crud.resolve_target_workana_ids(
        user_id=user["user_id"],
        project_ids=payload.project_ids,
        filters=payload.filters.model_dump() if payload.filters else None,
        exclude_ids=payload.exclude_ids,
        cap=2000,
    )
    updated = await crud.apply_bulk_state(user["user_id"], ids, payload.action)
    return BulkStateResult(updated=updated, total=len(ids))


@router.post("/projects/{workana_id}/state")
async def set_project_state(
    workana_id: str,
    payload: ProjectStateRequest,
    user: dict = Depends(get_current_user),
):
    """Atualiza estado ou notas de um único projeto do catálogo."""
    if payload.action is None and payload.notes is None:
        raise HTTPException(status_code=422, detail="Informe action ou notes.")
    if not await crud.catalog_project_exists(workana_id):
        raise HTTPException(status_code=404, detail="Projeto não encontrado no catálogo.")

    updated = 0
    if payload.action:
        updated = await crud.apply_bulk_state(user["user_id"], [workana_id], payload.action)
    if payload.notes is not None:
        await crud.set_catalog_project_notes(user["user_id"], workana_id, payload.notes)
        updated = 1
    return {"success": True, "updated": updated}


@router.put("/projects/{workana_id}/notes")
async def update_catalog_notes(
    workana_id: str,
    payload: ProjectNotesUpdate,
    user: dict = Depends(get_current_user),
):
    """Atualiza notas no overlay do usuário."""
    if not await crud.catalog_project_exists(workana_id):
        raise HTTPException(status_code=404, detail="Projeto não encontrado no catálogo.")
    await crud.set_catalog_project_notes(user["user_id"], workana_id, payload.notes)
    return {"success": True, "message": "Notas atualizadas!"}


@router.get("/projects/{workana_id}/bids-history", response_model=BidsHistoryResponse)
async def get_project_bids_history(
    workana_id: str,
    limit: int = Query(default=30, ge=1, le=200),
    user: dict = Depends(get_current_user),
):
    """Evolução de propostas de um projeto do catálogo (gráfico de concorrência)."""
    brief = await crud.get_catalog_brief(workana_id)
    if brief is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado no catálogo.")
    points = await crud.get_bids_history(workana_id, limit=limit)
    return BidsHistoryResponse(
        workana_id=workana_id,
        title=brief["title"],
        current_count=brief["proposals_count"],
        points=[BidsHistoryPoint(**p) for p in points],
    )


async def _build_analysis_profile(user_id, filters: Optional[dict] = None) -> dict:
    config = await crud.get_automation_config(user_id)
    saved_filters = await crud.get_saved_filters(user_id)
    profile: dict = {
        "keywords": None,
        "skills": [],
        "category": None,
        "min_budget": None,
        "max_budget": None,
        "payment_verified": None,
        "automation_config": {
            "auto_apply": config.get("auto_apply"),
            "max_proposals_per_day": config.get("max_proposals_per_day"),
        },
    }

    if saved_filters:
        latest = saved_filters[0].filters.model_dump()
        for key in ("keywords", "category", "min_budget", "max_budget", "payment_verified"):
            if latest.get(key) is not None:
                profile[key] = latest.get(key)
        profile["skills"] = latest.get("skills") or []

    if filters:
        if filters.get("q") and not profile.get("keywords"):
            profile["keywords"] = filters.get("q")
        for key in ("keywords", "category", "min_budget", "max_budget", "payment_verified"):
            if filters.get(key) is not None:
                profile[key] = filters.get(key)
        if filters.get("skills") is not None:
            profile["skills"] = filters.get("skills") or []

    return profile


@router.post("/projects/analyze", response_model=List[AnalysisResult])
async def analyze_projects(
    payload: AnalyzeRequest,
    user: dict = Depends(get_current_user),
):
    """Analisa projetos do catálogo, persiste o resultado e devolve a lista ranqueada."""
    if not payload.project_ids and payload.filters is None:
        raise HTTPException(status_code=422, detail="Informe project_ids ou filters.")

    ids = await crud.resolve_target_workana_ids(
        user_id=user["user_id"],
        project_ids=payload.project_ids,
        filters=payload.filters.model_dump() if payload.filters else None,
        exclude_ids=payload.exclude_ids,
        cap=2000,
    )
    if not ids:
        return []

    projects = await crud.get_catalog_projects_by_ids(user["user_id"], ids)
    profile = await _build_analysis_profile(
        user["user_id"],
        payload.filters.model_dump() if payload.filters else None,
    )

    results = []
    for project in projects:
        analysis = ProjectScorer.analyze_project(project, profile)
        results.append(
            {
                "workana_id": project["workana_id"],
                "score": analysis["score"],
                "recommendation": analysis["recommendation"],
                "dimensions": analysis["dimensions"],
                "justification": analysis["justification"],
            }
        )

    results.sort(key=lambda item: (-item["score"], item["recommendation"]))
    await crud.save_project_analysis(user["user_id"], results)
    return results


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
 
 
@router.get("/projects/{project_id}/proposal")
async def get_project_proposal(project_id: str, user: dict = Depends(get_current_user)):
    """Obtém a proposta existente (gerada, rascunho ou enviada) e o histórico de versões para o projeto."""
    proposal = await crud.get_latest_project_proposal(user["user_id"], project_id)
    if not proposal:
        return {"has_proposal": False, "proposal": None, "versions": [], "total_versions": 0}
    return {
        "has_proposal": True,
        **proposal,
    }


@router.get("/projects/{project_id}/versions")
async def get_project_versions(project_id: str, user: dict = Depends(get_current_user)):
    """Lista todas as versões de propostas salvas ou geradas para o projeto."""
    versions = await crud.get_project_proposal_versions(user["user_id"], project_id)
    return {"project_id": project_id, "versions": versions, "total": len(versions)}


@router.delete("/projects/{project_id}/proposals/{proposal_id}")
async def delete_project_proposal(
    project_id: str,
    proposal_id: int,
    user: dict = Depends(get_current_user),
):
    """Remove uma versão específica de proposta deste projeto."""
    deleted = await crud.delete_project_proposal_version(user["user_id"], project_id, proposal_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Versão de proposta não encontrada.")
    versions = await crud.get_project_proposal_versions(user["user_id"], project_id)
    return {"success": True, "message": "Versão da proposta removida com sucesso.", "versions": versions}


@router.post("/projects/{project_id}/save-proposal")
async def save_project_proposal(
    project_id: str,
    payload: ProposalSaveRequest,
    user: dict = Depends(get_current_user),
):
    """Salva ou atualiza a proposta editada nos rascunhos e no lote de envio."""
    try:
        # Obter dados do projeto
        project = await automation.get_project_details(project_id, user_id=user["user_id"])
        project_title = project.title if project else f"Projeto {project_id}"
        project_url = project.url if project else f"https://www.workana.com/job/{project_id}"

        # 1. Salvar ou atualizar no histórico do usuário
        history_id = await crud.save_ai_proposal(
            user_id=user["user_id"],
            project_id=project_id,
            project_title=project_title,
            project_url=project_url,
            proposal_text=payload.proposal_text,
            suggested_price=f"R$ {payload.budget}" if payload.budget else "R$ 0",
            template_id=payload.template_id,
            budget=payload.budget,
            deadline_days=payload.deadline_days or 7,
            status="generated",
            proposal_id=payload.proposal_id,
            force_new_version=payload.force_new_version,
        )

        # 2. Se solicitado, sincroniza também no lote de rascunhos (Batches)
        batch_result = None
        if payload.add_to_batch:
            batch_result = await crud.save_project_to_draft_batch(
                user_id=user["user_id"],
                project_id=project_id,
                proposal_text=payload.proposal_text,
                budget=payload.budget,
                deadline_days=payload.deadline_days or 7,
                template_ref=str(payload.template_id) if payload.template_id else None,
            )

        versions = await crud.get_project_proposal_versions(user["user_id"], project_id)

        return {
            "success": True,
            "message": "Proposta salva nos rascunhos e lotes com sucesso!",
            "proposal_id": history_id,
            "batch_info": batch_result,
            "versions": versions,
        }
    except Exception as e:
        logger.error(f"Erro ao salvar proposta para {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/generate-proposal", response_model=ProposalGenerationResult)
async def generate_proposal(
    project_id: str,
    payload: Optional[ProposalGenerateRequest] = None,
    template_id: Optional[Any] = None,
    user: dict = Depends(get_current_user)
):
    """Gera uma proposta personalizada usando IA ou recupera proposta salva se já gerada."""
    from app.services.proposal_agent import proposal_agent_instance
    
    try:
        force_regenerate = payload.force_regenerate if payload else False
        actual_template_id = template_id
        if payload and payload.template_id:
            actual_template_id = payload.template_id

        # Se não forçar nova geração, verifica se já existe uma proposta gerada para economizar tokens
        if not force_regenerate:
            existing = await crud.get_latest_project_proposal(user["user_id"], project_id)
            if existing and existing.get("proposal"):
                versions = await crud.get_project_proposal_versions(user["user_id"], project_id)
                return ProposalGenerationResult(
                    success=True,
                    proposal=existing.get("proposal"),
                    suggested_price=f"R$ {existing.get('budget', 0):.2f}" if existing.get('budget') else None,
                    suggested_deadline_days=existing.get("deadline_days", 7),
                    justification="Proposta carregada do histórico salvo.",
                    template_id_used=existing.get("template_id") or existing.get("template_slug"),
                    proposal_id=existing.get("id"),
                    versions=versions,
                )

        # Primeiro busca os detalhes do projeto para alimentar a IA
        project = await automation.get_project_details(project_id, user_id=user["user_id"])
        if not project:
            raise HTTPException(status_code=404, detail="Projeto não encontrado para gerar proposta")
        
        # Converte para dict para alimentar a IA
        project_dict = {
            "title": project.title,
            "description": project.description,
            "skills": project.skills,
            "budget": project.budget,
            "client_name": project.client_name,
            "deadline": project.deadline
        }
            
        # Chama a IA com o nível de preço selecionado
        price_level = payload.price_level if payload and payload.price_level else "standard"
        result = await proposal_agent_instance.generate_proposal(
            user["user_id"], project_dict, template_id=actual_template_id, price_level=price_level
        )
        
        if not result.get("success") and result.get("error_code") == 404:
            raise HTTPException(status_code=404, detail=result.get("error"))
        
        proposal_id_created = None
        # Salvar proposta gerada no histórico e no lote de rascunhos
        if result.get("success"):
            try:
                save_new = payload.save_as_new_version if payload else True
                proposal_id_created = await crud.save_ai_proposal(
                    user_id=user["user_id"],
                    project_id=project_id,
                    project_title=project.title,
                    project_url=project.url,
                    proposal_text=result.get("proposal", ""),
                    suggested_price=result.get("suggested_price", "R$ 0"),
                    template_id=result.get("template_id_used"),
                    deadline_days=result.get("suggested_deadline_days") or 7,
                    status="generated",
                    force_new_version=save_new,
                )

                # Salvar também no lote ativo de rascunhos
                await crud.save_project_to_draft_batch(
                    user_id=user["user_id"],
                    project_id=project_id,
                    proposal_text=result.get("proposal", ""),
                    deadline_days=result.get("suggested_deadline_days") or 7,
                    template_ref=str(result.get("template_id_used")) if result.get("template_id_used") else None,
                )
                logger.info(f"Proposta salva no histórico e lotes para o usuário {user['user_id']}, projeto: {project_id}")
            except Exception as e:
                logger.warning(f"Erro ao salvar proposta no histórico: {e}")
        
        versions = await crud.get_project_proposal_versions(user["user_id"], project_id)
        result["proposal_id"] = proposal_id_created
        result["versions"] = versions
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


# ==================== Geração e Disparo em Lote (Bulk & Batches) ====================

@router.post("/projects/batch", response_model=ProposalBatchResponse)
async def create_batch_singular(
    payload: ProposalBatchCreate,
    user: dict = Depends(get_current_user),
):
    """Cria um novo lote de propostas para disparo em background ou fila."""
    import asyncio
    from app.services.batch_processor import ProposalBatchProcessor

    if not payload.project_ids and not payload.filters and not payload.custom_proposals:
        raise HTTPException(status_code=422, detail="Informe project_ids, filters ou custom_proposals.")

    custom_proposals_dicts = [p.model_dump() for p in payload.custom_proposals] if payload.custom_proposals else None
    filters_dict = payload.filters.model_dump() if payload.filters else None

    result = await crud.create_proposal_batch(
        user_id=user["user_id"],
        project_ids=payload.project_ids,
        filters=filters_dict,
        exclude_ids=payload.exclude_ids,
        template_ref=payload.template_ref,
        custom_proposals=custom_proposals_dicts,
        daily_limit=payload.daily_limit,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Erro ao criar lote de propostas."))

    batch = await crud.get_proposal_batch(user["user_id"], result["batch_id"])
    if batch:
        # Aciona o worker para iniciar o processamento imediatamente
        asyncio.create_task(ProposalBatchProcessor.process_one())
        return batch

    return result


@router.get("/projects/batches/{batch_id}/items", response_model=List[ProposalBatchItemResponse])
async def get_batch_items(
    batch_id: int,
    user: dict = Depends(get_current_user),
):
    """Lista os itens individuais de um lote de propostas."""
    batch = await crud.get_proposal_batch(user["user_id"], batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Lote de propostas não encontrado.")
    return batch.get("items", [])


@router.post("/projects/batches/{batch_id}/start")
async def start_batch(
    batch_id: int,
    user: dict = Depends(get_current_user),
):
    """Inicia o processamento de um lote de propostas."""
    from app.services.batch_processor import ProposalBatchProcessor

    batch = await crud.get_proposal_batch(user["user_id"], batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Lote de propostas não encontrado.")

    if batch["status"] not in ["queued", "failed"]:
        raise HTTPException(status_code=400, detail=f"Não é possível iniciar um lote com status '{batch['status']}'.")

    # Dispara o processamento
    processed = await ProposalBatchProcessor.process_one()

    return {
        "success": True,
        "batch_id": batch_id,
        "status": batch["status"],
        "processed": processed,
        "message": "Processamento do lote iniciado."
    }


@router.post("/projects/batches")
async def create_batch(
    payload: ProposalBatchCreate,
    user: dict = Depends(get_current_user),
):
    """Cria um novo lote de propostas para disparo em background ou fila."""
    import asyncio
    from app.services.batch_processor import ProposalBatchProcessor

    if not payload.project_ids and not payload.filters and not payload.custom_proposals:
        raise HTTPException(status_code=422, detail="Informe project_ids, filters ou custom_proposals.")

    custom_proposals_dicts = [p.model_dump() for p in payload.custom_proposals] if payload.custom_proposals else None
    filters_dict = payload.filters.model_dump() if payload.filters else None

    result = await crud.create_proposal_batch(
        user_id=user["user_id"],
        project_ids=payload.project_ids,
        filters=filters_dict,
        exclude_ids=payload.exclude_ids,
        template_ref=payload.template_ref,
        custom_proposals=custom_proposals_dicts,
        daily_limit=payload.daily_limit,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Erro ao criar lote de propostas."))

    # Aciona o worker para iniciar o processamento imediatamente
    asyncio.create_task(ProposalBatchProcessor.process_one())

    return result


@router.get("/projects/batches/{batch_id}", response_model=ProposalBatchResponse)
async def get_batch_detail(
    batch_id: int,
    user: dict = Depends(get_current_user),
):
    """Retorna detalhes e itens individuais de um lote de proposta."""
    batch = await crud.get_proposal_batch(user["user_id"], batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Lote de propostas não encontrado.")
    return batch


@router.post("/projects/batches/{batch_id}/cancel")
async def cancel_batch(
    batch_id: int,
    user: dict = Depends(get_current_user),
):
    """Cancela um lote de propostas em andamento."""
    success = await crud.cancel_proposal_batch(user["user_id"], batch_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lote não encontrado ou não pertence a você.")
    return {"success": True, "message": "Lote de propostas cancelado com sucesso."}


@router.post("/projects/batches/{batch_id}/retry")
async def retry_batch(
    batch_id: int,
    user: dict = Depends(get_current_user),
):
    """Reinicia itens que falharam ou foram cancelados em um lote."""
    import asyncio
    from app.services.batch_processor import ProposalBatchProcessor

    success = await crud.retry_failed_batch_items(user["user_id"], batch_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lote não encontrado ou não pertence a você.")

    asyncio.create_task(ProposalBatchProcessor.process_one())
    return {"success": True, "message": "Itens do lote reiniciados para reenvio."}


@router.post("/projects/batches/process-now")
async def trigger_batch_processing(
    user: dict = Depends(get_current_user),
):
    """Aciona manualmente o processamento de um item da fila de lotes."""
    from app.services.batch_processor import ProposalBatchProcessor
    processed = await ProposalBatchProcessor.process_one()
    return {"success": True, "processed": processed}


@router.put("/projects/batches/items/{item_id}")
async def update_batch_item(
    item_id: int,
    payload: BatchItemUpdateRequest,
    user: dict = Depends(get_current_user),
):
    """Atualiza a mensagem, valor ou prazo de um item de lote de propostas."""
    updated = await crud.update_proposal_batch_item(
        user_id=user["user_id"],
        item_id=item_id,
        data=payload.model_dump(exclude_unset=True),
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Item do lote não encontrado ou não pertence a você.")
    return {"success": True, "item": updated}


@router.delete("/projects/batches/items/{item_id}")
async def delete_batch_item(
    item_id: int,
    user: dict = Depends(get_current_user),
):
    """Exclui um item específico de um lote de propostas."""
    deleted = await crud.delete_proposal_batch_item(user["user_id"], item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item do lote não encontrado.")
    return {"success": True, "message": "Item removido com sucesso."}


@router.post("/projects/batches/items/{item_id}/send-now")
async def send_batch_item_now(
    item_id: int,
    user: dict = Depends(get_current_user),
):
    """Dispara imediatamente o envio de uma proposta individual do lote/rascunhos."""
    from app.database.models import ProposalBatchItem
    from sqlalchemy import select, and_

    async with crud.async_session() as session:
        res = await session.execute(
            select(ProposalBatchItem).where(
                and_(ProposalBatchItem.id == item_id, ProposalBatchItem.user_id == user["user_id"])
            )
        )
        item = res.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Item não encontrado.")

        if not item.generated_message:
            raise HTTPException(status_code=400, detail="Este item não possui mensagem de proposta gerada para envio.")

        proposal = ProposalSubmit(
            project_id=item.workana_id,
            custom_message=item.generated_message,
            budget=item.budget or 100.0,
            deadline_days=item.deadline_days or 7,
        )

    # Envia a proposta
    result = await automation.submit_proposal(user["user_id"], proposal)

    # Atualiza o status do item
    if result.success:
        await crud.update_batch_item_status(item_id, status="sent")
    else:
        await crud.update_batch_item_status(item_id, status="failed", error=result.message)

    return result


@router.delete("/proposals/{proposal_id}")
async def delete_proposal(
    proposal_id: int,
    user: dict = Depends(get_current_user),
):
    """Remove uma proposta do histórico ou rascunhos."""
    deleted = await crud.delete_proposal_history(user["user_id"], proposal_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Proposta não encontrada.")
    return {"success": True, "message": "Proposta removida com sucesso."}


