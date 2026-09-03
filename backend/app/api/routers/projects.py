"""
Router principal para descoberta, catálogo e interações com projetos.
Propostas e lotes foram modularizados em `app.api.routers.proposals`.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from loguru import logger
from typing import List, Optional

from app.api.schemas import (
    SearchFilters,
    SavedFilter,
    Project,
    ProjectList,
    CatalogProjectList,
    SortOption,
    BulkStateRequest,
    BulkStateResult,
    ProjectStateRequest,
    ProjectNotesUpdate,
    AnalyzeRequest,
    AnalysisResult,
    BidsHistoryResponse,
    BidsHistoryPoint,
)
from app.auth import get_current_user
from app.database import crud
from app.services.scorer import ProjectScorer
from app.automation.browser import (
    SearchUnavailableError,
    automation_instance as automation,
)
from app.api.routers import proposals

router = APIRouter()

# Incluir rotas de propostas e lotes (batches) mantendo total compatibilidade de URLs
router.include_router(proposals.router)


# ==================== Catálogo de Projetos ====================


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
    user: dict = Depends(get_current_user),
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


# ==================== Estado e Interações do Catálogo ====================


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


# ==================== Análise Heurística & IA ====================


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

    projects_list = await crud.get_catalog_projects_by_ids(user["user_id"], ids)
    profile = await _build_analysis_profile(
        user["user_id"],
        payload.filters.model_dump() if payload.filters else None,
    )

    results = []
    for project in projects_list:
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


# ==================== Scraping em Tempo Real ====================


@router.post("/projects/search", response_model=ProjectList)
async def search_projects(filters: SearchFilters, user: dict = Depends(get_current_user)):
    """Busca projetos no Workana com os filtros especificados (live scraping)."""
    try:
        projects_found = await automation.search_projects(filters, user_id=user["user_id"])

        for proj in projects_found:
            proj.match_score = ProjectScorer.calculate_score(proj, filters)

        await crud.log_activity(
            user_id=user["user_id"],
            action_type="search",
            description=f"Busca realizada: {filters.keywords or 'Sem palavras-chave'}",
            details={"filters": filters.model_dump(), "count": len(projects_found)},
        )

        if projects_found:
            await crud.log_activity(
                user_id=user["user_id"],
                action_type="project_found",
                description=f"Encontrados {len(projects_found)} projetos na busca",
                details={"count": len(projects_found)},
            )

        return ProjectList(projects=projects_found, total=len(projects_found))
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


# ==================== Projetos Salvos (Legado) ====================


@router.get("/saved-projects")
async def list_saved_projects(
    limit: int = 50,
    offset: int = 0,
    favorites_only: bool = False,
    not_applied_only: bool = False,
    category: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """Lista projetos salvos no banco de dados do usuário."""
    saved = await crud.get_projects(
        user_id=user["user_id"],
        limit=limit,
        offset=offset,
        only_favorites=favorites_only,
        only_not_applied=not_applied_only,
        category=category,
    )
    return {"projects": saved, "total": len(saved)}


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
            description=f"Projeto salvo: {project_data.get('title', 'Sem título')}",
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
