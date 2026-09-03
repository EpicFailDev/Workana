"""
Repository para configurações e logs de automação.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from loguru import logger
from sqlalchemy import select, and_

import app.database.crud as crud
from app.database.models import (
    AutomationConfig as AutomationConfigModel,
    ActivityLog as ActivityLogModel,
    DailyStatistics as DailyStatisticsModel,
)
from app.database.repositories.credentials import encrypt_text, decrypt_text


async def get_automation_config(user_id: Any) -> Dict[str, Any]:
    """Obtém configurações de automação. Se não existirem, inicializa-as para o usuário."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(AutomationConfigModel).where(AutomationConfigModel.user_id == user_id).limit(1)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            config = AutomationConfigModel(
                user_id=user_id,
                headless=True,
                delay_between_actions_ms=2000,
                max_proposals_per_day=10,
                auto_apply=False,
                preferred_template_id=None,
                gemini_api_key=None,
                user_full_name=None,
                telegram_enabled=False,
                telegram_bot_token=None,
                telegram_chat_id=None,
                webhook_enabled=False,
                webhook_url=None,
                email_enabled=False,
                email_to=None
            )
            session.add(config)
            await session.commit()
            await session.refresh(config)
        
        gemini_key = None
        if config.gemini_api_key:
            try:
                gemini_key = decrypt_text(config.gemini_api_key)
            except Exception:
                logger.error("Erro ao descriptografar chave Gemini. A chave será resetada.")
                gemini_key = None

        telegram_token = None
        if config.telegram_bot_token:
            try:
                telegram_token = decrypt_text(config.telegram_bot_token)
            except Exception:
                logger.error("Erro ao descriptografar token Telegram. O token será resetado.")
                telegram_token = None

        return {
            "headless": config.headless,
            "delay_between_actions_ms": config.delay_between_actions_ms,
            "max_proposals_per_day": config.max_proposals_per_day,
            "auto_apply": config.auto_apply,
            "preferred_template_id": config.preferred_template_id,
            "gemini_api_key": gemini_key,
            "user_full_name": config.user_full_name,
            "telegram_enabled": config.telegram_enabled,
            "telegram_bot_token": telegram_token,
            "telegram_chat_id": config.telegram_chat_id,
            "webhook_enabled": config.webhook_enabled,
            "webhook_url": config.webhook_url,
            "email_enabled": config.email_enabled,
            "email_to": config.email_to
        }


async def save_automation_config(user_id: Any, config: Dict[str, Any]) -> None:
    """Salva ou cria configurações de automação de um usuário."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(AutomationConfigModel).where(AutomationConfigModel.user_id == user_id).limit(1)
        )
        db_config = result.scalar_one_or_none()
        
        gemini_api_key = config.get("gemini_api_key")
        encrypted_gemini = encrypt_text(gemini_api_key) if gemini_api_key else None

        telegram_bot_token = config.get("telegram_bot_token")
        encrypted_telegram = encrypt_text(telegram_bot_token) if telegram_bot_token else None
        
        if db_config:
            db_config.headless = config.get("headless", True)
            db_config.delay_between_actions_ms = config.get("delay_between_actions_ms", 2000)
            db_config.max_proposals_per_day = config.get("max_proposals_per_day", 10)
            db_config.auto_apply = config.get("auto_apply", False)
            if "preferred_template_id" in config:
                db_config.preferred_template_id = config.get("preferred_template_id")
            if gemini_api_key is not None:
                db_config.gemini_api_key = encrypted_gemini
            if "user_full_name" in config:
                db_config.user_full_name = config.get("user_full_name")
            
            db_config.telegram_enabled = config.get("telegram_enabled", False)
            if telegram_bot_token is not None:
                db_config.telegram_bot_token = encrypted_telegram
            if "telegram_chat_id" in config:
                db_config.telegram_chat_id = config.get("telegram_chat_id")
            db_config.webhook_enabled = config.get("webhook_enabled", False)
            if "webhook_url" in config:
                db_config.webhook_url = config.get("webhook_url")
            db_config.email_enabled = config.get("email_enabled", False)
            if "email_to" in config:
                db_config.email_to = config.get("email_to")
                
            db_config.updated_at = datetime.now(timezone.utc)
        else:
            db_config = AutomationConfigModel(
                user_id=user_id,
                headless=config.get("headless", True),
                delay_between_actions_ms=config.get("delay_between_actions_ms", 2000),
                max_proposals_per_day=config.get("max_proposals_per_day", 10),
                auto_apply=config.get("auto_apply", False),
                preferred_template_id=config.get("preferred_template_id"),
                gemini_api_key=encrypted_gemini,
                user_full_name=config.get("user_full_name"),
                telegram_enabled=config.get("telegram_enabled", False),
                telegram_bot_token=encrypted_telegram,
                telegram_chat_id=config.get("telegram_chat_id"),
                webhook_enabled=config.get("webhook_enabled", False),
                webhook_url=config.get("webhook_url"),
                email_enabled=config.get("email_enabled", False),
                email_to=config.get("email_to")
            )
            session.add(db_config)
            
        await session.commit()


async def log_activity(
    user_id: Any,
    action_type: str,
    description: str,
    details: Optional[Dict[str, Any]] = None,
    project_id: Optional[int] = None,
    status: str = "success",
    error_message: Optional[str] = None,
    duration_ms: Optional[int] = None
) -> None:
    """Registra uma atividade no log vinculada ao user_id."""
    async with crud.async_session() as session:
        log = ActivityLogModel(
            user_id=user_id,
            action_type=action_type,
            action_description=description,
            details=details,
            project_id=project_id,
            status=status,
            error_message=error_message,
            duration_ms=duration_ms
        )
        session.add(log)
        await session.commit()
        
        increment = 1
        if details and "count" in details:
            try:
                increment = int(details["count"])
            except Exception:
                pass
        await crud._update_daily_stats(user_id, action_type, status, increment=increment)


async def get_activity_logs(
    user_id: Any,
    limit: int = 100,
    action_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Obtém logs de atividade de um usuário específico."""
    async with crud.async_session() as session:
        query = select(ActivityLogModel).where(ActivityLogModel.user_id == user_id)
        
        if action_type:
            query = query.where(ActivityLogModel.action_type == action_type)
        if status:
            query = query.where(ActivityLogModel.status == status)
        
        query = query.order_by(ActivityLogModel.created_at.desc()).limit(limit)
        
        result = await session.execute(query)
        logs = result.scalars().all()
        
        return [
            {
                "id": log.id,
                "action_type": log.action_type,
                "description": log.action_description,
                "details": log.details,
                "project_id": log.project_id,
                "status": log.status,
                "error_message": log.error_message,
                "duration_ms": log.duration_ms,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]


async def update_scraping_stats(
    user_id: Any,
    success: bool,
    blocked: bool,
    duration_ms: int,
) -> None:
    """Registra métricas do scraper sem depender do log de atividade."""
    async with crud.async_session() as session:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await session.execute(
            select(DailyStatisticsModel).where(
                and_(DailyStatisticsModel.date == today, DailyStatisticsModel.user_id == user_id)
            )
        )
        stats = result.scalar_one_or_none()
        if not stats:
            stats = DailyStatisticsModel(user_id=user_id, date=today)
            session.add(stats)

        if success:
            stats.scraping_success_count = (stats.scraping_success_count or 0) + 1
        else:
            stats.scraping_failure_count = (stats.scraping_failure_count or 0) + 1
        if blocked:
            stats.scraping_blocked_count = (stats.scraping_blocked_count or 0) + 1
        stats.scraping_total_time_ms = (stats.scraping_total_time_ms or 0) + duration_ms
        stats.updated_at = datetime.now(timezone.utc)
        await session.commit()
