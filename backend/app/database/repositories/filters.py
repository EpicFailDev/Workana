"""
Repository para gerenciamento de filtros salvos de projetos.
"""
from typing import List, Dict, Any, Tuple
import json
from sqlalchemy import select, delete, and_

import app.database.crud as crud
from app.database.models import SavedFilter as SavedFilterModel
from app.api.schemas import SavedFilter


async def get_saved_filters(user_id: Any) -> List[SavedFilter]:
    """Lista todos os filtros salvos de um usuário específico."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(SavedFilterModel)
            .where(SavedFilterModel.user_id == user_id)
            .order_by(SavedFilterModel.created_at.desc())
        )
        filters = result.scalars().all()
        
        return [
            SavedFilter(
                id=f.id,
                name=f.name,
                filters=f.filters_json,
                created_at=f.created_at
            )
            for f in filters
        ]


async def create_filter(user_id: Any, filter_data: SavedFilter) -> SavedFilter:
    """Cria um novo filtro para um usuário específico."""
    async with crud.async_session() as session:
        db_filter = SavedFilterModel(
            user_id=user_id,
            name=filter_data.name,
            filters_json=filter_data.filters.model_dump() if hasattr(filter_data.filters, "model_dump") else filter_data.filters
        )
        session.add(db_filter)
        await session.commit()
        await session.refresh(db_filter)
        
        return SavedFilter(
            id=db_filter.id,
            name=db_filter.name,
            filters=filter_data.filters,
            created_at=db_filter.created_at
        )


async def delete_filter(user_id: Any, filter_id: int) -> None:
    """Remove um filtro de um usuário específico."""
    async with crud.async_session() as session:
        await session.execute(
            delete(SavedFilterModel)
            .where(and_(SavedFilterModel.id == filter_id, SavedFilterModel.user_id == user_id))
        )
        await session.commit()


async def get_distinct_saved_filter_queries() -> List[dict]:
    """Retorna pares únicos (keywords, category) agregados de todos os filtros salvos."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(SavedFilterModel.user_id, SavedFilterModel.filters_json)
        )

        queries_by_key: Dict[Tuple[str, str], dict] = {}
        for user_id, raw in result.all():
            try:
                data = json.loads(raw) if isinstance(raw, str) else raw
            except (TypeError, json.JSONDecodeError):
                continue
            if not isinstance(data, dict):
                continue
            key = (
                str(data.get("keywords") or "").strip().lower(),
                str(data.get("category") or "").strip().lower(),
            )
            if not any(key):
                continue
            entry = queries_by_key.setdefault(
                key,
                {**data, "_metric_user_ids": []},
            )
            if str(user_id) not in entry["_metric_user_ids"]:
                entry["_metric_user_ids"].append(str(user_id))

        return list(queries_by_key.values())
