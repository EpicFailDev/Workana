"""
Router para gerenciamento de métricas do perfil público do Workana.
"""
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, desc, and_

from app.api.schemas import (
    ProfileMetricsResponse,
    ProfileConfigUpdate,
    ProfileConfigResponse,
    ProfileMetricsHistoryList,
    ProfileMetricsHistory,
    MessageResponse
)
from app.auth import get_current_user
from app.services.profile_scraper import profile_scraper
from app.database.models import async_session, ProfileMetrics, ProfileConfig

router = APIRouter()


@router.get("/profile/metrics", response_model=ProfileMetricsResponse)
async def get_profile_metrics(user: dict = Depends(get_current_user)):
    """
    Retorna as métricas mais recentes do perfil público do usuário.
    Se não houver métricas salvas, retorna indicação de não configurado.
    """
    try:
        async with async_session() as session:
            # Buscar configuração do perfil do usuário
            config_result = await session.execute(
                select(ProfileConfig)
                .where(ProfileConfig.user_id == user["user_id"])
            )
            config = config_result.scalar_one_or_none()
            
            if not config:
                return ProfileMetricsResponse(
                    success=True,
                    is_configured=False,
                    error="Perfil não configurado. Configure a URL do seu perfil público nas configurações."
                )
            
            # Buscar métricas mais recentes do usuário
            metrics_result = await session.execute(
                select(ProfileMetrics)
                .where(and_(ProfileMetrics.profile_url == config.profile_url, ProfileMetrics.user_id == user["user_id"]))
                .order_by(desc(ProfileMetrics.scraped_at))
                .limit(1)
            )
            metrics = metrics_result.scalar_one_or_none()
            
            if not metrics:
                return ProfileMetricsResponse(
                    success=True,
                    is_configured=True,
                    profile_url=config.profile_url,
                    error="Nenhuma métrica coletada ainda. Clique em sincronizar para buscar dados."
                )
            
            return ProfileMetricsResponse(
                success=True,
                is_configured=True,
                profile_url=metrics.profile_url,
                username=metrics.username,
                display_name=metrics.display_name,
                projects_completed=metrics.projects_completed or 0,
                projects_in_progress=metrics.projects_in_progress or 0,
                hours_worked=metrics.hours_worked or 0,
                average_rating=metrics.average_rating,
                total_reviews=metrics.total_reviews or 0,
                member_since=metrics.member_since,
                country=metrics.country,
                hourly_rate=metrics.hourly_rate,
                skills=metrics.skills or [],
                last_login=metrics.last_login,
                profile_photo_url=metrics.profile_photo_url,
                last_sync=metrics.scraped_at
            )
            
    except Exception as e:
        logger.error(f"Erro ao buscar métricas do perfil: {str(e)}")
        return ProfileMetricsResponse(
            success=False,
            error=f"Erro ao buscar métricas: {str(e)}"
        )


@router.post("/profile/sync", response_model=ProfileMetricsResponse)
async def sync_profile_metrics(force: bool = False, user: dict = Depends(get_current_user)):
    """
    Sincroniza as métricas do perfil público do usuário.
    Faz scraping da página pública e salva no banco.
    """
    try:
        async with async_session() as session:
            # Buscar configuração do usuário
            config_result = await session.execute(
                select(ProfileConfig)
                .where(ProfileConfig.user_id == user["user_id"])
            )
            config = config_result.scalar_one_or_none()
            
            if not config:
                raise HTTPException(
                    status_code=400,
                    detail="Perfil não configurado. Configure a URL do seu perfil primeiro."
                )
            
            logger.info(f"Iniciando sincronização do perfil para o usuário {user['user_id']}: {config.profile_url}")
            
            # Fazer scraping do perfil público
            metrics_data = await profile_scraper.fetch_public_profile(
                config.profile_url,
                force_refresh=force
            )
            
            if not metrics_data.get("success", False):
                return ProfileMetricsResponse(
                    success=False,
                    is_configured=True,
                    profile_url=config.profile_url,
                    error=metrics_data.get("error", "Erro desconhecido ao buscar perfil")
                )
            
            # Salvar métricas no banco
            new_metrics = ProfileMetrics(
                user_id=user["user_id"],
                profile_url=config.profile_url,
                username=metrics_data.get("username"),
                display_name=metrics_data.get("display_name"),
                projects_completed=metrics_data.get("projects_completed", 0),
                projects_in_progress=metrics_data.get("projects_in_progress", 0),
                hours_worked=metrics_data.get("hours_worked", 0),
                average_rating=metrics_data.get("average_rating"),
                total_reviews=metrics_data.get("total_reviews", 0),
                member_since=metrics_data.get("member_since"),
                country=metrics_data.get("country"),
                hourly_rate=metrics_data.get("hourly_rate"),
                skills=metrics_data.get("skills", []),
                last_login=metrics_data.get("last_login"),
                profile_photo_url=metrics_data.get("profile_photo_url")
            )
            
            session.add(new_metrics)
            
            # Atualizar última sincronização na config
            config.last_sync_at = datetime.now(timezone.utc)
            
            await session.commit()
            
            logger.info(f"Métricas do perfil sincronizadas com sucesso para o usuário {user['user_id']}")
            
            return ProfileMetricsResponse(
                success=True,
                is_configured=True,
                profile_url=config.profile_url,
                username=metrics_data.get("username"),
                display_name=metrics_data.get("display_name"),
                projects_completed=metrics_data.get("projects_completed", 0),
                projects_in_progress=metrics_data.get("projects_in_progress", 0),
                hours_worked=metrics_data.get("hours_worked", 0),
                average_rating=metrics_data.get("average_rating"),
                total_reviews=metrics_data.get("total_reviews", 0),
                member_since=metrics_data.get("member_since"),
                country=metrics_data.get("country"),
                hourly_rate=metrics_data.get("hourly_rate"),
                skills=metrics_data.get("skills", []),
                last_login=metrics_data.get("last_login"),
                profile_photo_url=metrics_data.get("profile_photo_url"),
                last_sync=datetime.now(timezone.utc)
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao sincronizar perfil: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/config", response_model=ProfileConfigResponse)
async def get_profile_config(user: dict = Depends(get_current_user)):
    """Retorna a configuração atual do perfil do usuário."""
    try:
        async with async_session() as session:
            result = await session.execute(
                select(ProfileConfig)
                .where(ProfileConfig.user_id == user["user_id"])
            )
            config = result.scalar_one_or_none()
            
            if not config:
                return ProfileConfigResponse(is_configured=False)
            
            return ProfileConfigResponse(
                profile_url=config.profile_url,
                auto_sync_enabled=config.auto_sync_enabled,
                sync_interval_hours=config.sync_interval_hours,
                last_sync_at=config.last_sync_at,
                is_configured=True
            )
            
    except Exception as e:
        logger.error(f"Erro ao buscar configuração do perfil: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile/config", response_model=MessageResponse)
async def update_profile_config(config_update: ProfileConfigUpdate, user: dict = Depends(get_current_user)):
    """
    Atualiza a configuração do perfil público do usuário.
    """
    try:
        # Validar URL
        if not profile_scraper.validate_profile_url(config_update.profile_url):
            raise HTTPException(
                status_code=400,
                detail="URL inválida. Use o formato: https://www.workana.com/freelancer/seu-username"
            )
        
        async with async_session() as session:
            # Verificar se já existe configuração para o usuário
            result = await session.execute(
                select(ProfileConfig)
                .where(ProfileConfig.user_id == user["user_id"])
            )
            config = result.scalar_one_or_none()
            
            if config:
                # Verificar se o URL mudou
                if config.profile_url != config_update.profile_url:
                    config.last_sync_at = None
                    logger.info(f"URL do perfil alterada para: {config_update.profile_url}. Resetando status de sincronização.")
                
                # Atualizar existente
                config.profile_url = config_update.profile_url
                config.auto_sync_enabled = config_update.auto_sync_enabled
                config.sync_interval_hours = config_update.sync_interval_hours
            else:
                # Criar nova configuração
                config = ProfileConfig(
                    user_id=user["user_id"],
                    profile_url=config_update.profile_url,
                    auto_sync_enabled=config_update.auto_sync_enabled,
                    sync_interval_hours=config_update.sync_interval_hours,
                    last_sync_at=None
                )
                session.add(config)
            
            await session.commit()
            
            logger.info(f"Configuração do perfil atualizada para o usuário {user['user_id']}: {config_update.profile_url}")
            
            return MessageResponse(
                success=True,
                message="Configuração do perfil atualizada com sucesso!"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar configuração do perfil: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/history", response_model=ProfileMetricsHistoryList)
async def get_profile_history(limit: int = 30, user: dict = Depends(get_current_user)):
    """
    Retorna o histórico de métricas do perfil do usuário.
    Útil para gráficos de evolução.
    """
    try:
        async with async_session() as session:
            result = await session.execute(
                select(ProfileMetrics)
                .where(ProfileMetrics.user_id == user["user_id"])
                .order_by(desc(ProfileMetrics.scraped_at))
                .limit(min(limit, 100))
            )
            metrics_list = result.scalars().all()
            
            history = [
                ProfileMetricsHistory(
                    id=m.id,
                    profile_url=m.profile_url,
                    projects_completed=m.projects_completed or 0,
                    average_rating=m.average_rating,
                    total_reviews=m.total_reviews or 0,
                    scraped_at=m.scraped_at
                )
                for m in metrics_list
            ]
            
            return ProfileMetricsHistoryList(
                history=history,
                total=len(history)
            )
            
    except Exception as e:
        logger.error(f"Erro ao buscar histórico de métricas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile/validate")
async def validate_profile_url(url: str, user: dict = Depends(get_current_user)):
    """
    Valida uma URL de perfil do Workana e tenta buscar o nome.
    Útil para verificar se a URL está correta antes de salvar.
    """
    try:
        if not profile_scraper.validate_profile_url(url):
            return {
                "valid": False,
                "error": "URL inválida. Use o formato: https://www.workana.com/freelancer/seu-username"
            }
        
        # Tentar buscar o perfil para validar
        metrics = await profile_scraper.fetch_public_profile(url, force_refresh=True)
        
        if not metrics.get("success", False):
            return {
                "valid": False,
                "error": metrics.get("error", "Não foi possível acessar o perfil")
            }
        
        return {
            "valid": True,
            "display_name": metrics.get("display_name"),
            "username": metrics.get("username"),
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Erro ao validar URL do perfil: {str(e)}")
        return {
            "valid": False,
            "error": str(e)
        }
