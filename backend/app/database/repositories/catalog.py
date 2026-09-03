"""
Repository para gerenciamento de projetos do catálogo e projetos legados.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, and_, or_, cast, Float, String, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

import app.database.crud as crud
from app.database.models import (
    Project as ProjectModel,
    ProjectCatalog as ProjectCatalogModel,
    UserProjectState as UserProjectStateModel,
    ProjectBidsHistory as ProjectBidsHistoryModel,
)


# ==================== Projetos (Legado / Pessoais) ====================


async def save_project(user_id: Any, project_data: Dict[str, Any]) -> int:
    """Salva ou atualiza um projeto encontrado para um usuário específico."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProjectModel).where(
                and_(
                    ProjectModel.workana_id == project_data.get("workana_id"),
                    ProjectModel.user_id == user_id,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            for key, value in project_data.items():
                if hasattr(existing, key) and key not in ("id", "user_id"):
                    setattr(existing, key, value)
            existing.updated_at = datetime.now(timezone.utc)
            await session.commit()
            return existing.id
        else:
            project_data["user_id"] = user_id
            project = ProjectModel(**project_data)
            session.add(project)
            await session.commit()
            await session.refresh(project)
            return project.id


async def get_projects(
    user_id: Any,
    limit: int = 50,
    offset: int = 0,
    only_favorites: bool = False,
    only_not_applied: bool = False,
    category: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista projetos salvos de um usuário com filtros."""
    async with crud.async_session() as session:
        query = select(ProjectModel).where(ProjectModel.user_id == user_id)

        if only_favorites:
            query = query.where(ProjectModel.is_favorite == True)
        if only_not_applied:
            query = query.where(ProjectModel.is_applied == False)
        if category:
            query = query.where(ProjectModel.category == category)

        query = query.where(ProjectModel.is_ignored == False)
        query = query.order_by(ProjectModel.found_at.desc())
        query = query.offset(offset).limit(limit)

        result = await session.execute(query)
        projects = result.scalars().all()

        return [
            {
                "id": p.id,
                "workana_id": p.workana_id,
                "title": p.title,
                "description": p.description,
                "url": p.url,
                "category": p.category,
                "budget_min": p.budget_min,
                "budget_max": p.budget_max,
                "budget_type": p.budget_type,
                "deadline": p.deadline,
                "skills": p.skills,
                "client_name": p.client_name,
                "client_country": p.client_country,
                "client_rating": p.client_rating,
                "proposals_count": p.proposals_count,
                "payment_verified": p.payment_verified,
                "posted_at": p.posted_at,
                "is_favorite": p.is_favorite,
                "is_applied": p.is_applied,
                "notes": p.notes,
                "found_at": p.found_at.isoformat() if p.found_at else None,
            }
            for p in projects
        ]


async def get_project(user_id: Any, project_id: int) -> Optional[Dict[str, Any]]:
    """Obtém um projeto específico de um usuário."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProjectModel).where(
                and_(ProjectModel.id == project_id, ProjectModel.user_id == user_id)
            )
        )
        p = result.scalar_one_or_none()

        if p:
            return {
                "id": p.id,
                "workana_id": p.workana_id,
                "title": p.title,
                "description": p.description,
                "url": p.url,
                "category": p.category,
                "subcategory": p.subcategory,
                "budget_min": p.budget_min,
                "budget_max": p.budget_max,
                "budget_type": p.budget_type,
                "deadline": p.deadline,
                "skills": p.skills,
                "client_name": p.client_name,
                "client_country": p.client_country,
                "client_rating": p.client_rating,
                "client_projects_posted": p.client_projects_posted,
                "proposals_count": p.proposals_count,
                "payment_verified": p.payment_verified,
                "posted_at": p.posted_at,
                "is_favorite": p.is_favorite,
                "is_applied": p.is_applied,
                "is_ignored": p.is_ignored,
                "notes": p.notes,
                "found_at": p.found_at.isoformat() if p.found_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
        return None


async def get_project_by_workana_id(user_id: Any, workana_id: str) -> Optional[Dict[str, Any]]:
    """Obtém um projeto pelo seu workana_id buscando no catálogo global e nos projetos salvos."""
    clean_id = (
        str(workana_id)
        .replace("https://www.workana.com/job/", "")
        .replace("https://www.workana.com/messages/bid/", "")
        .strip("/")
    )
    async with crud.async_session() as session:
        # 1. Buscar no catálogo global
        result_cat = await session.execute(
            select(ProjectCatalogModel)
            .where(
                or_(
                    ProjectCatalogModel.workana_id == str(workana_id),
                    ProjectCatalogModel.workana_id == clean_id,
                )
            )
            .limit(1)
        )
        cat_p = result_cat.scalar_one_or_none()
        if cat_p:
            return {
                "id": cat_p.workana_id,
                "workana_id": cat_p.workana_id,
                "title": cat_p.title,
                "description": cat_p.description,
                "url": cat_p.url or f"https://www.workana.com/job/{cat_p.workana_id}",
                "category": cat_p.category,
                "subcategory": cat_p.subcategory,
                "budget_min": cat_p.budget_min,
                "budget_max": cat_p.budget_max,
                "budget_type": cat_p.budget_type,
                "deadline": cat_p.deadline,
                "skills": cat_p.skills,
                "client_name": cat_p.client_name,
                "client_country": cat_p.client_country,
                "client_rating": cat_p.client_rating,
                "proposals_count": cat_p.proposals_count,
                "payment_verified": cat_p.payment_verified,
            }

        # 2. Fallback para tabela de projetos
        result_proj = await session.execute(
            select(ProjectModel)
            .where(
                or_(ProjectModel.workana_id == str(workana_id), ProjectModel.workana_id == clean_id)
            )
            .limit(1)
        )
        p = result_proj.scalar_one_or_none()
        if p:
            return {
                "id": p.id,
                "workana_id": p.workana_id,
                "title": p.title,
                "description": p.description,
                "url": p.url or f"https://www.workana.com/job/{p.workana_id}",
                "category": p.category,
                "subcategory": p.subcategory,
                "budget_min": p.budget_min,
                "budget_max": p.budget_max,
                "budget_type": p.budget_type,
                "deadline": p.deadline,
                "skills": p.skills,
                "client_name": p.client_name,
                "client_country": p.client_country,
                "client_rating": p.client_rating,
                "proposals_count": p.proposals_count,
                "payment_verified": p.payment_verified,
            }

        return None


async def toggle_project_favorite(user_id: Any, project_id: int) -> bool:
    """Alterna o status de favorito de um projeto de um usuário específico."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProjectModel).where(
                and_(ProjectModel.id == project_id, ProjectModel.user_id == user_id)
            )
        )
        project = result.scalar_one_or_none()

        if project:
            project.is_favorite = not project.is_favorite
            await session.commit()
            return project.is_favorite
        return False


async def mark_project_applied(user_id: Any, project_id: int) -> None:
    """Marca um projeto de um usuário como aplicado."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProjectModel).where(
                and_(ProjectModel.id == project_id, ProjectModel.user_id == user_id)
            )
        )
        project = result.scalar_one_or_none()
        if project:
            project.is_applied = True
            project.updated_at = datetime.now(timezone.utc)
            await session.commit()


async def ignore_project(user_id: Any, project_id: int) -> None:
    """Ignora um projeto de um usuário específico."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProjectModel).where(
                and_(ProjectModel.id == project_id, ProjectModel.user_id == user_id)
            )
        )
        project = result.scalar_one_or_none()
        if project:
            project.is_ignored = True
            await session.commit()


async def update_project_notes(user_id: Any, project_id: int, notes: str) -> None:
    """Atualiza notas de um projeto do usuário."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProjectModel).where(
                and_(ProjectModel.id == project_id, ProjectModel.user_id == user_id)
            )
        )
        project = result.scalar_one_or_none()
        if project:
            project.notes = notes
            project.updated_at = datetime.now(timezone.utc)
            await session.commit()


# ==================== Catálogo de Projetos ====================


def _serialize_catalog_row(
    cat: ProjectCatalogModel, state: Optional[UserProjectStateModel]
) -> Dict[str, Any]:
    return {
        "workana_id": cat.workana_id,
        "title": cat.title,
        "description": cat.description,
        "url": cat.url,
        "category": cat.category,
        "subcategory": cat.subcategory,
        "budget_min": cat.budget_min,
        "budget_max": cat.budget_max,
        "budget_type": cat.budget_type,
        "deadline": cat.deadline,
        "skills": cat.skills,
        "details": cat.details or {},
        "client_name": cat.client_name,
        "client_country": cat.client_country,
        "client_rating": cat.client_rating,
        "client_projects_posted": cat.client_projects_posted,
        "client_projects_paid": cat.client_projects_paid,
        "client_member_since": cat.client_member_since,
        "client_plan": cat.client_plan,
        "proposals_count": cat.proposals_count,
        "payment_verified": cat.payment_verified,
        "posted_at": cat.posted_at,
        "published_at": cat.published_at,
        "last_client_activity": cat.last_client_activity,
        "is_urgent": cat.is_urgent,
        "is_featured": cat.is_featured,
        "estimated_published_at": cat.estimated_published_at.isoformat()
        if cat.estimated_published_at
        else None,
        "proposals_delta": cat.proposals_delta,
        "contract_type": cat.contract_type,
        "status": cat.status,
        "first_seen_at": cat.first_seen_at.isoformat() if cat.first_seen_at else None,
        "last_seen_at": cat.last_seen_at.isoformat() if cat.last_seen_at else None,
        "is_favorite": state.is_favorite if state else False,
        "is_hidden": state.is_hidden if state else False,
        "notes": state.notes if state else None,
        "analysis": state.analysis if state else None,
        "analyzed_at": state.analyzed_at.isoformat() if state and state.analyzed_at else None,
    }


CATEGORY_ALIASES: Dict[str, List[str]] = {
    # TI & Programação
    "ti-programacao": [
        "ti-programacao",
        "ti e programação",
        "ti & programação",
        "it & programming",
        "it-programming",
        "it y programación",
        "programação",
        "ti",
        "it",
    ],
    "it-programming": [
        "ti-programacao",
        "ti e programação",
        "ti & programação",
        "it & programming",
        "it-programming",
        "it y programação",
        "programação",
        "ti",
        "it",
    ],
    "ti e programação": [
        "ti-programacao",
        "ti e programação",
        "ti & programação",
        "it & programming",
        "it-programming",
        "it y programação",
        "programação",
        "ti",
        "it",
    ],
    "ti & programação": [
        "ti-programacao",
        "ti e programação",
        "ti & programação",
        "it & programming",
        "it-programming",
        "it y programação",
        "programação",
        "ti",
        "it",
    ],
    # Design & Multimídia
    "design-multimidia": [
        "design-multimidia",
        "design-multimedia",
        "design e multimídia",
        "design & multimídia",
        "design & multimedia",
        "design e multimedia",
        "design y multimedia",
        "design",
        "multimídia",
        "multimedia",
    ],
    "design-multimedia": [
        "design-multimidia",
        "design-multimedia",
        "design e multimídia",
        "design & multimídia",
        "design & multimedia",
        "design e multimedia",
        "design y multimedia",
        "design",
        "multimídia",
        "multimedia",
    ],
    "design e multimídia": [
        "design-multimidia",
        "design-multimedia",
        "design e multimídia",
        "design & multimídia",
        "design & multimedia",
        "design e multimedia",
        "design y multimedia",
        "design",
        "multimídia",
        "multimedia",
    ],
    "design e multimedia": [
        "design-multimidia",
        "design-multimedia",
        "design e multimídia",
        "design & multimídia",
        "design & multimedia",
        "design e multimedia",
        "design y multimedia",
        "design",
        "multimídia",
        "multimedia",
    ],
    # Tradução e Conteúdos / Escrita
    "traducao-conteudos": [
        "traducao-conteudos",
        "writing-translation",
        "tradução e conteúdos",
        "tradução & conteúdos",
        "tradução e conteudos",
        "escrita e tradução",
        "escrita & tradução",
        "writing & translation",
        "redacción y traducción",
        "tradução",
        "redação",
        "conteúdos",
    ],
    "writing-translation": [
        "traducao-conteudos",
        "writing-translation",
        "tradução e conteúdos",
        "tradução & conteúdos",
        "tradução e conteudos",
        "escrita e tradução",
        "escrita & tradução",
        "writing & translation",
        "redacción y traducción",
        "tradução",
        "redação",
        "conteúdos",
    ],
    "tradução e conteúdos": [
        "traducao-conteudos",
        "writing-translation",
        "tradução e conteúdos",
        "tradução & conteúdos",
        "tradução e conteudos",
        "escrita e tradução",
        "escrita & tradução",
        "writing & translation",
        "redacción y traducción",
        "tradução",
        "redação",
        "conteúdos",
    ],
    # Vendas e Marketing
    "marketing-vendas": [
        "marketing-vendas",
        "marketing-sales",
        "vendas e marketing",
        "vendas & marketing",
        "marketing e vendas",
        "sales & marketing",
        "marketing y ventas",
        "marketing",
        "vendas",
    ],
    "marketing-sales": [
        "marketing-vendas",
        "marketing-sales",
        "vendas e marketing",
        "vendas & marketing",
        "marketing e vendas",
        "sales & marketing",
        "marketing y ventas",
        "marketing",
        "vendas",
    ],
    "marketing e vendas": [
        "marketing-vendas",
        "marketing-sales",
        "vendas e marketing",
        "vendas & marketing",
        "marketing e vendas",
        "sales & marketing",
        "marketing y ventas",
        "marketing",
        "vendas",
    ],
    "vendas e marketing": [
        "marketing-vendas",
        "marketing-sales",
        "vendas e marketing",
        "vendas & marketing",
        "marketing e vendas",
        "sales & marketing",
        "marketing y ventas",
        "marketing",
        "vendas",
    ],
    # Suporte Administrativo
    "suporte-administrativo": [
        "suporte-administrativo",
        "admin-support",
        "suporte administrativo",
        "administrativo e suporte",
        "administrativo & suporte",
        "admin support",
        "soporte administrativo",
        "suporte",
        "administrativo",
    ],
    "admin-support": [
        "suporte-administrativo",
        "admin-support",
        "suporte administrativo",
        "administrativo e suporte",
        "administrativo & suporte",
        "admin support",
        "soporte administrativo",
        "suporte",
        "administrativo",
    ],
    "suporte administrativo": [
        "suporte-administrativo",
        "admin-support",
        "suporte administrativo",
        "administrativo e suporte",
        "administrativo & suporte",
        "admin support",
        "soporte administrativo",
        "suporte",
        "administrativo",
    ],
    # Finanças e Jurídico
    "financas-administracao": [
        "financas-administracao",
        "finance-legal",
        "finanças e administração",
        "finanças & jurídico",
        "jurídico",
        "finance & legal",
        "finanzas y administración",
        "legal",
        "finanças",
    ],
    "finance-legal": [
        "financas-administracao",
        "finance-legal",
        "finanças e administração",
        "finanças & jurídico",
        "jurídico",
        "finance & legal",
        "finanzas y administración",
        "legal",
        "finanças",
    ],
    "finanças e administração": [
        "financas-administracao",
        "finance-legal",
        "finanças e administração",
        "finanças & jurídico",
        "jurídico",
        "finance & legal",
        "finanzas y administration",
        "legal",
        "finanças",
    ],
    "jurídico": [
        "financas-administracao",
        "finance-legal",
        "finanças e administração",
        "finanças & jurídico",
        "jurídico",
        "finance & legal",
        "finanzas y administración",
        "legal",
        "finanças",
    ],
    # Engenharia e Manufatura
    "engenharia-manufatura": [
        "engenharia-manufatura",
        "engineering",
        "engenharia e manufatura",
        "engenharia & arquitetura",
        "engineering & manufacturing",
        "ingeniería y manufactura",
        "engenharia",
        "arquitetura",
    ],
    "engineering": [
        "engenharia-manufatura",
        "engineering",
        "engenharia e manufatura",
        "engenharia & arquitetura",
        "engineering & manufacturing",
        "ingeniería y manufactura",
        "engenharia",
        "arquitetura",
    ],
    "engenharia e manufatura": [
        "engenharia-manufatura",
        "engineering",
        "engenharia e manufatura",
        "engenharia & arquitetura",
        "engineering & manufacturing",
        "ingeniería y manufactura",
        "engenharia",
        "arquitetura",
    ],
}


async def count_active_catalog_projects(category: Optional[str] = None) -> int:
    """Retorna a contagem total de projetos ativos no catálogo."""
    async with crud.async_session() as session:
        query = select(func.count(ProjectCatalogModel.workana_id)).where(
            ProjectCatalogModel.status == "active"
        )
        if category:
            category_norm = category.strip().lower()
            aliases = CATEGORY_ALIASES.get(category_norm, [category_norm])
            query = query.where(
                or_(*[ProjectCatalogModel.category.ilike(f"%{alias}%") for alias in aliases])
            )
        result = await session.execute(query)
        return result.scalar() or 0


async def search_catalog(
    user_id: Any,
    page: int = 1,
    limit: int = 24,
    q: Optional[str] = None,
    category: Optional[str] = None,
    min_budget: Optional[float] = None,
    max_budget: Optional[float] = None,
    payment_verified: Optional[bool] = None,
    sort: Any = "created_at_desc",
    favorites_only: bool = False,
    hidden_only: bool = False,
) -> Dict[str, Any]:
    """Busca paginada no catálogo, incorporando estado do usuário."""
    async with crud.async_session() as session:
        query = select(ProjectCatalogModel, UserProjectStateModel).where(
            ProjectCatalogModel.status == "active"
        )

        if q:
            pattern = f"%{q}%"
            query = query.where(
                or_(
                    ProjectCatalogModel.title.ilike(pattern),
                    ProjectCatalogModel.description.ilike(pattern),
                    ProjectCatalogModel.skills.cast(String).ilike(pattern),
                )
            )

        if category:
            category_norm = category.strip().lower()
            aliases = CATEGORY_ALIASES.get(category_norm, [category_norm])
            query = query.where(
                or_(*[ProjectCatalogModel.category.ilike(f"%{alias}%") for alias in aliases])
            )

        if min_budget is not None:
            query = query.where(
                or_(
                    ProjectCatalogModel.budget_min >= min_budget,
                    ProjectCatalogModel.budget_max >= min_budget,
                )
            )
        if max_budget is not None:
            query = query.where(
                or_(
                    ProjectCatalogModel.budget_max <= max_budget,
                    ProjectCatalogModel.budget_min <= max_budget,
                )
            )
        if payment_verified:
            query = query.where(ProjectCatalogModel.payment_verified == True)

        query = query.outerjoin(
            UserProjectStateModel,
            and_(
                UserProjectStateModel.workana_id == ProjectCatalogModel.workana_id,
                UserProjectStateModel.user_id == user_id,
            ),
        )

        if favorites_only:
            query = query.where(UserProjectStateModel.is_favorite == True)

        if hidden_only:
            query = query.where(UserProjectStateModel.is_hidden == True)
        else:
            query = query.where(
                or_(
                    UserProjectStateModel.is_hidden == False,
                    UserProjectStateModel.is_hidden == None,
                )
            )

        sort_value = getattr(sort, "value", sort)
        sort_map = {
            "newest": ProjectCatalogModel.estimated_published_at.desc().nullslast(),
            "created_at_desc": ProjectCatalogModel.estimated_published_at.desc().nullslast(),
            "oldest": ProjectCatalogModel.estimated_published_at.asc().nullsfirst(),
            "created_at_asc": ProjectCatalogModel.estimated_published_at.asc().nullsfirst(),
            "budget_desc": ProjectCatalogModel.budget_max.desc().nullslast(),
            "budget_asc": ProjectCatalogModel.budget_min.asc().nullsfirst(),
            "bids_asc": ProjectCatalogModel.proposals_count.asc().nullsfirst(),
            "bids_desc": ProjectCatalogModel.proposals_count.desc().nullslast(),
            "ranking": func.coalesce(
                cast(UserProjectStateModel.analysis["score"], Float),
                -1.0,
            ).desc(),
        }
        order_clause = sort_map.get(sort_value, ProjectCatalogModel.last_seen_at.desc())
        query = query.order_by(order_clause)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await session.execute(query)
        rows = result.unique().all()

        projects = [_serialize_catalog_row(cat, state) for cat, state in rows]
        return {"projects": projects, "total": total, "page": page, "limit": limit}


async def get_catalog_projects_by_ids(user_id: Any, workana_ids: List[str]) -> List[Dict[str, Any]]:
    """Obtém projetos do catálogo preservando a ordem de entrada."""
    ordered_ids = list(dict.fromkeys([item for item in workana_ids if item]))
    if not ordered_ids:
        return []

    async with crud.async_session() as session:
        result = await session.execute(
            select(ProjectCatalogModel, UserProjectStateModel)
            .outerjoin(
                UserProjectStateModel,
                and_(
                    UserProjectStateModel.workana_id == ProjectCatalogModel.workana_id,
                    UserProjectStateModel.user_id == user_id,
                ),
            )
            .where(
                and_(
                    ProjectCatalogModel.status == "active",
                    ProjectCatalogModel.workana_id.in_(ordered_ids),
                )
            )
        )
        rows = result.unique().all()

    by_id = {cat.workana_id: _serialize_catalog_row(cat, state) for cat, state in rows}
    return [by_id[item] for item in ordered_ids if item in by_id]


async def save_project_analysis(user_id: Any, analyses: List[Dict[str, Any]]) -> int:
    """Persiste análise estruturada no overlay do usuário."""
    if not analyses:
        return 0

    now = datetime.now(timezone.utc)
    rows = []
    for item in analyses:
        workana_id = item.get("workana_id")
        if not workana_id:
            continue
        rows.append(
            {
                "user_id": user_id,
                "workana_id": workana_id,
                "analysis": item,
                "analyzed_at": now,
                "created_at": now,
                "updated_at": now,
            }
        )

    if not rows:
        return 0

    statement = pg_insert(UserProjectStateModel).values(rows)
    excluded = statement.excluded
    statement = statement.on_conflict_do_update(
        index_elements=[
            UserProjectStateModel.user_id,
            UserProjectStateModel.workana_id,
        ],
        set_={
            "analysis": excluded.analysis,
            "analyzed_at": excluded.analyzed_at,
            "updated_at": excluded.updated_at,
        },
    )
    async with crud.async_session() as session:
        await session.execute(statement)
        await session.commit()
    return len(rows)


async def resolve_target_workana_ids(
    user_id: Any,
    project_ids: Optional[List[str]] = None,
    filters: Optional[Dict[str, Any]] = None,
    exclude_ids: Optional[List[str]] = None,
    cap: int = 2000,
) -> List[str]:
    """Resolve seleção explícita ou filtrada, mantendo o mesmo builder da busca."""
    cap = max(1, min(cap, 2000))
    excluded = set(exclude_ids or [])

    if project_ids:
        ordered_ids = list(dict.fromkeys(project_ids))[:cap]
        async with crud.async_session() as session:
            result = await session.execute(
                select(ProjectCatalogModel.workana_id).where(
                    and_(
                        ProjectCatalogModel.status == "active",
                        ProjectCatalogModel.workana_id.in_(ordered_ids),
                    )
                )
            )
            existing = set(result.scalars().all())
        return [item for item in ordered_ids if item in existing and item not in excluded]

    filter_values = dict(filters or {})
    result = await crud.search_catalog(
        user_id=user_id,
        page=1,
        limit=cap,
        q=filter_values.get("q"),
        category=filter_values.get("category"),
        min_budget=filter_values.get("min_budget"),
        max_budget=filter_values.get("max_budget"),
        payment_verified=filter_values.get("payment_verified"),
        favorites_only=filter_values.get("favorites_only", False),
        hidden_only=filter_values.get("hidden_only", False),
    )
    return [
        project["workana_id"]
        for project in result["projects"]
        if project["workana_id"] not in excluded
    ][:cap]


async def apply_bulk_state(user_id: Any, workana_ids: List[str], action: str) -> int:
    """Upsert vetorizado do overlay sem sobrescrever o outro flag."""
    if not workana_ids:
        return 0

    action_map = {
        "favorite": ("is_favorite", True),
        "unfavorite": ("is_favorite", False),
        "hide": ("is_hidden", True),
        "restore": ("is_hidden", False),
    }
    if action not in action_map:
        raise ValueError(f"Ação de estado inválida: {action}")

    field, value = action_map[action]
    now = datetime.now(timezone.utc)
    rows = [
        {
            "user_id": user_id,
            "workana_id": workana_id,
            field: value,
            "created_at": now,
            "updated_at": now,
        }
        for workana_id in dict.fromkeys(workana_ids)
    ]
    statement = pg_insert(UserProjectStateModel).values(rows)
    statement = statement.on_conflict_do_update(
        index_elements=[
            UserProjectStateModel.user_id,
            UserProjectStateModel.workana_id,
        ],
        set_={field: value, "updated_at": now},
    )
    async with crud.async_session() as session:
        await session.execute(statement)
        await session.commit()
    return len(rows)


async def catalog_project_exists(workana_id: str) -> bool:
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProjectCatalogModel.workana_id).where(
                ProjectCatalogModel.workana_id == workana_id
            )
        )
        return result.scalar_one_or_none() is not None


async def get_bids_history(workana_id: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Retorna a evolução de contagem de propostas de um projeto do catálogo."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(
                ProjectBidsHistoryModel.proposals_count,
                ProjectBidsHistoryModel.captured_at,
            )
            .where(ProjectBidsHistoryModel.workana_id == workana_id)
            .order_by(ProjectBidsHistoryModel.captured_at.desc())
            .limit(limit)
        )
    return [
        {
            "proposals_count": count,
            "captured_at": captured_at.isoformat() if captured_at else None,
        }
        for count, captured_at in result.all()
    ]


async def get_catalog_brief(workana_id: str) -> Optional[Dict[str, Any]]:
    """Retorna título e contagem atual de um projeto do catálogo."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(
                ProjectCatalogModel.title,
                ProjectCatalogModel.proposals_count,
            ).where(ProjectCatalogModel.workana_id == workana_id)
        )
        row = result.first()
    if row is None:
        return None
    return {"title": row.title, "proposals_count": row.proposals_count}


async def export_catalog_rows(
    limit: int = 5000,
    include_inactive: bool = False,
) -> List[Dict[str, Any]]:
    """Retorna as linhas do catálogo para exportação CSV."""
    async with crud.async_session() as session:
        query = select(ProjectCatalogModel)
        if not include_inactive:
            query = query.where(ProjectCatalogModel.status == "active")
        query = query.order_by(
            ProjectCatalogModel.estimated_published_at.desc().nulls_last(),
            ProjectCatalogModel.last_seen_at.desc(),
        ).limit(limit)
        rows = (await session.execute(query)).scalars().all()

    def _iso(value) -> Optional[str]:
        return value.isoformat() if value else None

    return [
        {
            "workana_id": c.workana_id,
            "title": c.title,
            "url": c.url,
            "category": c.category,
            "subcategory": c.subcategory,
            "budget_min": c.budget_min,
            "budget_max": c.budget_max,
            "budget_type": c.budget_type,
            "deadline": c.deadline,
            "skills": ", ".join(c.skills) if isinstance(c.skills, list) else c.skills,
            "proposals_count": c.proposals_count,
            "proposals_delta": c.proposals_delta,
            "contract_type": c.contract_type,
            "estimated_published_at": _iso(c.estimated_published_at),
            "posted_at": c.posted_at,
            "published_at": c.published_at,
            "last_client_activity": c.last_client_activity,
            "is_urgent": c.is_urgent,
            "is_featured": c.is_featured,
            "status": c.status,
            "client_name": c.client_name,
            "client_country": c.client_country,
            "client_rating": c.client_rating,
            "client_projects_posted": c.client_projects_posted,
            "client_projects_paid": c.client_projects_paid,
            "client_member_since": c.client_member_since,
            "client_plan": c.client_plan,
            "payment_verified": c.payment_verified,
            "first_seen_at": _iso(c.first_seen_at),
            "last_seen_at": _iso(c.last_seen_at),
        }
        for c in rows
    ]


async def set_catalog_project_notes(user_id: Any, workana_id: str, notes: str) -> None:
    """Cria ou atualiza apenas as notas do overlay do usuário."""
    now = datetime.now(timezone.utc)
    statement = pg_insert(UserProjectStateModel).values(
        user_id=user_id,
        workana_id=workana_id,
        notes=notes,
        created_at=now,
        updated_at=now,
    )
    statement = statement.on_conflict_do_update(
        index_elements=[
            UserProjectStateModel.user_id,
            UserProjectStateModel.workana_id,
        ],
        set_={"notes": notes, "updated_at": now},
    )
    async with crud.async_session() as session:
        await session.execute(statement)
        await session.commit()


async def upsert_catalog_row(project_data: dict) -> None:
    """Upsert um projeto no catálogo (usado pelo scraper/worker)."""
    workana_id = str(project_data.get("workana_id") or "").strip()
    if not workana_id:
        return

    async with crud.async_session() as session:
        now = datetime.now(timezone.utc)
        values = {
            key: project_data.get(key)
            for key in (
                "workana_id",
                "title",
                "description",
                "url",
                "category",
                "subcategory",
                "budget_min",
                "budget_max",
                "budget_type",
                "deadline",
                "skills",
                "details",
                "client_name",
                "client_country",
                "client_rating",
                "client_projects_posted",
                "client_projects_paid",
                "client_member_since",
                "client_plan",
                "proposals_count",
                "payment_verified",
                "posted_at",
                "published_at",
                "last_client_activity",
                "is_urgent",
                "is_featured",
                "estimated_published_at",
            )
        }
        values["contract_type"] = project_data.get("contract_type") or "project_fixed"
        values.update(
            status="active",
            first_seen_at=project_data.get("first_seen_at") or now,
            last_seen_at=now,
            updated_at=now,
            proposals_delta=0,
        )
        statement = pg_insert(ProjectCatalogModel).values(**values)
        excluded = statement.excluded
        update_fields = {
            column: getattr(excluded, column)
            for column in values
            if column
            not in {
                "workana_id",
                "first_seen_at",
                "last_seen_at",
                "updated_at",
                "status",
                "previous_proposals_count",
                "proposals_delta",
            }
        }
        update_fields.update(
            last_seen_at=now,
            updated_at=now,
            status="active",
            closed_at=None,
            previous_proposals_count=ProjectCatalogModel.proposals_count,
            proposals_delta=(excluded.proposals_count - ProjectCatalogModel.proposals_count),
        )
        result = await session.execute(
            statement.on_conflict_do_update(
                index_elements=[ProjectCatalogModel.workana_id],
                set_=update_fields,
            ).returning(
                ProjectCatalogModel.workana_id,
                ProjectCatalogModel.proposals_count,
                ProjectCatalogModel.previous_proposals_count,
                ProjectCatalogModel.proposals_delta,
            )
        )
        row = result.first()
        await session.commit()

        if (
            row is not None
            and row.proposals_count is not None
            and (row.previous_proposals_count is None or row.proposals_delta != 0)
        ):
            await session.execute(
                pg_insert(ProjectBidsHistoryModel).values(
                    workana_id=row.workana_id,
                    proposals_count=row.proposals_count,
                    captured_at=now,
                )
            )
            await session.commit()


async def upsert_catalog_rows_batch(projects_data: List[dict]) -> int:
    """Upsert em lote de projetos no catálogo em uma única sessão."""
    if not projects_data:
        return 0

    valid_rows = []
    now = datetime.now(timezone.utc)

    for project_data in projects_data:
        workana_id = str(project_data.get("workana_id") or "").strip()
        if not workana_id:
            continue
        values = {
            key: project_data.get(key)
            for key in (
                "workana_id",
                "title",
                "description",
                "url",
                "category",
                "subcategory",
                "budget_min",
                "budget_max",
                "budget_type",
                "deadline",
                "skills",
                "details",
                "client_name",
                "client_country",
                "client_rating",
                "client_projects_posted",
                "client_projects_paid",
                "client_member_since",
                "client_plan",
                "proposals_count",
                "payment_verified",
                "posted_at",
                "published_at",
                "last_client_activity",
                "is_urgent",
                "is_featured",
                "estimated_published_at",
            )
        }
        values["contract_type"] = project_data.get("contract_type") or "project_fixed"
        values.update(
            status="active",
            first_seen_at=project_data.get("first_seen_at") or now,
            last_seen_at=now,
            updated_at=now,
            proposals_delta=0,
        )
        valid_rows.append(values)

    if not valid_rows:
        return 0

    upserted_count = 0
    async with crud.async_session() as session:
        for values in valid_rows:
            statement = pg_insert(ProjectCatalogModel).values(**values)
            excluded = statement.excluded
            update_fields = {
                column: getattr(excluded, column)
                for column in values
                if column
                not in {
                    "workana_id",
                    "first_seen_at",
                    "last_seen_at",
                    "updated_at",
                    "status",
                    "previous_proposals_count",
                    "proposals_delta",
                }
            }
            update_fields.update(
                last_seen_at=now,
                updated_at=now,
                status="active",
                closed_at=None,
                previous_proposals_count=ProjectCatalogModel.proposals_count,
                proposals_delta=(excluded.proposals_count - ProjectCatalogModel.proposals_count),
            )
            result = await session.execute(
                statement.on_conflict_do_update(
                    index_elements=[ProjectCatalogModel.workana_id],
                    set_=update_fields,
                ).returning(
                    ProjectCatalogModel.workana_id,
                    ProjectCatalogModel.proposals_count,
                    ProjectCatalogModel.previous_proposals_count,
                    ProjectCatalogModel.proposals_delta,
                )
            )
            row = result.first()
            upserted_count += 1

            if (
                row is not None
                and row.proposals_count is not None
                and (row.previous_proposals_count is None or row.proposals_delta != 0)
            ):
                await session.execute(
                    pg_insert(ProjectBidsHistoryModel).values(
                        workana_id=row.workana_id,
                        proposals_count=row.proposals_count,
                        captured_at=now,
                    )
                )

        await session.commit()

    return upserted_count


async def mark_gone_catalog_projects(
    seen_ids: List[str],
    cycle_started_at: Optional[datetime] = None,
    category: Optional[str] = None,
    is_full_catalog_cycle: bool = True,
    close_after_minutes: int = 45,
) -> Dict[str, int]:
    """Avança active->gone e gone->closed com proteção contra buscas parciais ou incompletas."""
    if not seen_ids:
        return {"gone": 0, "closed": 0}

    # Se não foi um ciclo completo do catálogo e nenhuma categoria foi especificada (ex: busca por palavra-chave),
    # não marcamos nada como 'gone' para não invalidar projetos que não faziam parte do escopo da busca.
    if not is_full_catalog_cycle and not category:
        return {"gone": 0, "closed": 0}

    async with crud.async_session() as session:
        now = datetime.now(timezone.utc)
        cycle_started_at = cycle_started_at or now

        # Verificar quantidade de projetos ativos no escopo para evitar falso positivo
        count_query = select(func.count(ProjectCatalogModel.workana_id)).where(
            ProjectCatalogModel.status == "active"
        )
        if category:
            count_query = count_query.where(ProjectCatalogModel.category.ilike(f"%{category}%"))

        active_count_res = await session.execute(count_query)
        active_count = active_count_res.scalar() or 0

        # Trava de segurança: se a quantidade vista for drasticamente menor que o total ativo (ex: < 20%),
        # indica que o scraper foi interrompido antes do fim ou retornou poucas páginas.
        if active_count >= 30 and len(seen_ids) < int(active_count * 0.25):
            from loguru import logger

            logger.warning(
                f"🛡️ Proteção de Catálogo ativada: {len(seen_ids)} projetos vistos vs {active_count} ativos. "
                "Abortando marcação de 'gone' para proteger o catálogo."
            )
            return {"gone": 0, "closed": 0}

        # Filtro de fechamento
        closed_where = [
            ProjectCatalogModel.status == "gone",
            ProjectCatalogModel.last_seen_at <= now - timedelta(minutes=close_after_minutes),
            ProjectCatalogModel.workana_id.notin_(seen_ids),
        ]
        if category:
            closed_where.append(ProjectCatalogModel.category.ilike(f"%{category}%"))

        closed_result = await session.execute(
            update(ProjectCatalogModel)
            .where(and_(*closed_where))
            .values(status="closed", closed_at=now, updated_at=now)
        )

        # Filtro de transição active -> gone
        gone_where = [
            ProjectCatalogModel.status == "active",
            ProjectCatalogModel.workana_id.notin_(seen_ids),
            ProjectCatalogModel.last_seen_at < cycle_started_at,
        ]
        if category:
            gone_where.append(ProjectCatalogModel.category.ilike(f"%{category}%"))

        gone_result = await session.execute(
            update(ProjectCatalogModel)
            .where(and_(*gone_where))
            .values(status="gone", updated_at=now)
        )
        await session.commit()
        return {"gone": gone_result.rowcount or 0, "closed": closed_result.rowcount or 0}


async def restore_gone_catalog_projects(category: Optional[str] = None) -> int:
    """Restaura projetos marcados incorretamente como 'gone' de volta para 'active'."""
    async with crud.async_session() as session:
        now = datetime.now(timezone.utc)
        query = update(ProjectCatalogModel).where(ProjectCatalogModel.status == "gone")
        if category:
            query = query.where(ProjectCatalogModel.category.ilike(f"%{category}%"))
        result = await session.execute(
            query.values(status="active", last_seen_at=now, updated_at=now)
        )
        await session.commit()
        return result.rowcount or 0
