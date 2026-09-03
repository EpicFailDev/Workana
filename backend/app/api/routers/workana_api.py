from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from loguru import logger

from app.api.schemas import Project
from app.auth import get_current_user
from app.services.workana_api import workana_api_client

router = APIRouter()


@router.get("/workana/recommended-projects", response_model=List[Project])
async def get_recommended_projects(user: dict = Depends(get_current_user)):
    """Returns recommended projects from Workana."""
    projects = await workana_api_client.get_recommended_projects(user["user_id"])
    return projects


@router.get("/workana/saved-searches", response_model=List[Dict[str, Any]])
async def get_saved_searches(user: dict = Depends(get_current_user)):
    """Returns saved searches from Workana."""
    searches = await workana_api_client.get_saved_searches(user["user_id"])
    return searches


@router.get("/workana/inbox", response_model=List[Dict[str, Any]])
async def get_inbox(user: dict = Depends(get_current_user)):
    """Returns inbox threads from Workana."""
    threads = await workana_api_client.get_inbox_threads(user["user_id"])
    return threads


@router.get("/workana/proposal-responses", response_model=List[Dict[str, Any]])
async def get_proposal_responses(user: dict = Depends(get_current_user)):
    """Returns unread responses to our proposals."""
    responses = await workana_api_client.check_proposal_responses(user["user_id"])
    return responses
