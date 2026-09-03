"""
Repository para clientes bloqueados (blacklist).
"""

from typing import Optional, List, Dict, Any
from sqlalchemy import select, delete, and_

import app.database.crud as crud
from app.database.models import BlacklistedClient as BlacklistedClientModel


async def add_blacklisted_client(
    user_id: Any, client_name: str, reason: Optional[str] = None
) -> None:
    """Adiciona um cliente à lista negra de um usuário específico."""
    async with crud.async_session() as session:
        client = BlacklistedClientModel(user_id=user_id, client_name=client_name, reason=reason)
        session.add(client)
        await session.commit()


async def get_blacklisted_clients(user_id: Any) -> List[Dict[str, Any]]:
    """Lista clientes na lista negra de um usuário específico."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(BlacklistedClientModel)
            .where(BlacklistedClientModel.user_id == user_id)
            .order_by(BlacklistedClientModel.created_at.desc())
        )
        clients = result.scalars().all()

        return [
            {
                "id": c.id,
                "client_name": c.client_name,
                "reason": c.reason,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in clients
        ]


async def remove_blacklisted_client(user_id: Any, client_id: int) -> None:
    """Remove um cliente da lista negra de um usuário específico."""
    async with crud.async_session() as session:
        await session.execute(
            delete(BlacklistedClientModel).where(
                and_(
                    BlacklistedClientModel.id == client_id,
                    BlacklistedClientModel.user_id == user_id,
                )
            )
        )
        await session.commit()


async def is_client_blacklisted(user_id: Any, client_name: str) -> bool:
    """Verifica se um cliente está na lista negra de um usuário específico."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(BlacklistedClientModel).where(
                and_(
                    BlacklistedClientModel.client_name.ilike(f"%{client_name}%"),
                    BlacklistedClientModel.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none() is not None
