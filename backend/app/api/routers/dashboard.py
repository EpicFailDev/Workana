from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.api.schemas import DashboardStats, ProposalHistory
from app.auth import get_current_user
from app.database import crud

router = APIRouter()

# ==================== Dashboard ====================

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    """Retorna estatísticas para o dashboard do usuário."""
    return await crud.get_dashboard_stats(user["user_id"])


# ==================== Histórico de Propostas ====================

@router.get("/proposals/history", response_model=List[ProposalHistory])
async def get_proposal_history(limit: int = 50, user: dict = Depends(get_current_user)):
    """Retorna o histórico de propostas geradas/enviadas do usuário."""
    return await crud.get_proposal_history(user["user_id"], limit)


@router.put("/proposals/{proposal_id}/status")
async def update_proposal_status(proposal_id: int, status_data: dict, user: dict = Depends(get_current_user)):
    """Atualiza o status de uma proposta manualmente."""
    status = status_data.get("status")
    if not status:
         raise HTTPException(status_code=400, detail="Status obrigatório")
         
    success = await crud.update_proposal_status(user["user_id"], proposal_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
        
    return {"success": True, "message": "Status atualizado!"}


# ==================== Logs de Atividade ====================

@router.get("/logs")
async def list_activity_logs(
    limit: int = 100,
    action_type: str = None,
    status: str = None,
    user: dict = Depends(get_current_user)
):
    """Lista logs de atividade do sistema vinculados ao usuário."""
    logs = await crud.get_activity_logs(
        user_id=user["user_id"],
        limit=limit,
        action_type=action_type,
        status=status
    )
    return {"logs": logs, "total": len(logs)}


@router.post("/logs")
async def create_log(log_data: dict, user: dict = Depends(get_current_user)):
    """Cria uma entrada de log manualmente para o usuário."""
    await crud.log_activity(
        user_id=user["user_id"],
        action_type=log_data.get("action_type", "manual"),
        description=log_data.get("description", "Ação manual"),
        details=log_data.get("details"),
        project_id=log_data.get("project_id"),
        status=log_data.get("status", "success")
    )
    return {"success": True, "message": "Log criado!"}


# ==================== Estatísticas ====================

@router.get("/statistics")
async def get_statistics(days: int = 30, user: dict = Depends(get_current_user)):
    """Obtém estatísticas dos últimos N dias do usuário."""
    stats = await crud.get_statistics(user["user_id"], days)
    return {"statistics": stats, "days": days}


@router.get("/statistics/summary")
async def get_statistics_summary(user: dict = Depends(get_current_user)):
    """Obtém resumo das estatísticas (hoje, semana, mês) do usuário."""
    return await crud.get_statistics_summary(user["user_id"])


# ==================== Clientes Bloqueados ====================

@router.get("/blacklist")
async def list_blacklisted_clients(user: dict = Depends(get_current_user)):
    """Lista clientes na lista negra do usuário."""
    clients = await crud.get_blacklisted_clients(user["user_id"])
    return {"clients": clients, "total": len(clients)}


@router.post("/blacklist")
async def add_to_blacklist(client_data: dict, user: dict = Depends(get_current_user)):
    """Adiciona um cliente à lista negra do usuário."""
    client_name = client_data.get("client_name")
    reason = client_data.get("reason")
    
    if not client_name:
        raise HTTPException(status_code=400, detail="Nome do cliente é obrigatório")
    
    await crud.add_blacklisted_client(user["user_id"], client_name, reason)
    await crud.log_activity(
        user_id=user["user_id"],
        action_type="blacklist_add",
        description=f"Cliente adicionado à lista negra: {client_name}"
    )
    return {"success": True, "message": f"Cliente '{client_name}' adicionado à lista negra!"}


@router.delete("/blacklist/{client_id}")
async def remove_from_blacklist(client_id: int, user: dict = Depends(get_current_user)):
    """Remove um cliente da lista negra do usuário."""
    await crud.remove_blacklisted_client(user["user_id"], client_id)
    return {"success": True, "message": "Cliente removido da lista negra!"}


@router.get("/blacklist/check/{client_name}")
async def check_blacklist(client_name: str, user: dict = Depends(get_current_user)):
    """Verifica se um cliente está na lista negra do usuário."""
    is_blacklisted = await crud.is_client_blacklisted(user["user_id"], client_name)
    return {"client_name": client_name, "is_blacklisted": is_blacklisted}
