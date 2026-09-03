"""
Repository para métricas e configurações do perfil do usuário no Workana.
"""

from typing import Optional, List, Any
from datetime import datetime, timezone
from sqlalchemy import select, and_

import app.database.crud as crud
from app.database.models import (
    ProfileMetrics as ProfileMetricsModel,
    ProfileConfig as ProfileConfigModel,
)


async def get_profile_config(user_id: Any) -> Optional[ProfileConfigModel]:
    """Obtém a configuração do perfil do usuário."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProfileConfigModel).where(ProfileConfigModel.user_id == user_id).limit(1)
        )
        return result.scalar_one_or_none()


async def get_or_create_profile_config(user_id: Any) -> ProfileConfigModel:
    """Obtém ou cria a configuração padrão de perfil do usuário."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProfileConfigModel).where(ProfileConfigModel.user_id == user_id).limit(1)
        )
        config = result.scalar_one_or_none()
        if not config:
            config = ProfileConfigModel(
                user_id=user_id,
                profile_url=None,
                auto_sync_enabled=True,
                sync_interval_hours=6,
            )
            session.add(config)
            await session.commit()
            await session.refresh(config)
        return config


async def get_latest_profile_metrics(
    user_id: Any, profile_url: Optional[str] = None
) -> Optional[ProfileMetricsModel]:
    """Obtém as métricas mais recentes do perfil do usuário."""
    async with crud.async_session() as session:
        query = select(ProfileMetricsModel).where(ProfileMetricsModel.user_id == user_id)
        if profile_url:
            query = query.where(ProfileMetricsModel.profile_url == profile_url)
        query = query.order_by(ProfileMetricsModel.scraped_at.desc()).limit(1)

        result = await session.execute(query)
        return result.scalar_one_or_none()


async def get_profile_history(user_id: Any, limit: int = 30) -> List[ProfileMetricsModel]:
    """Obtém histórico de capturas de perfil do usuário."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(ProfileMetricsModel)
            .where(ProfileMetricsModel.user_id == user_id)
            .order_by(ProfileMetricsModel.scraped_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
