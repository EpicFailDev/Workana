"""
Router da Extensão Web (Manifest V3) do Workana Accelerator.
Gerencia fila de tarefas, heartbeat, status de conexão e relatórios de envio seguro.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from app.auth import get_current_user
from app.automation.antiban import antiban
from app.database import crud
from app.api.schemas import (
    ExtensionHeartbeatRequest,
    ExtensionStatusResponse,
    ExtensionTaskCompleteRequest,
    ExtensionTaskCreate,
    ExtensionTaskResponse,
    ProposalResult,
    ProposalSubmit,
)

router = APIRouter()


class ExtensionTaskManager:
    """Gerenciador de tarefas e presença em memória para a extensão."""

    def __init__(self):
        # user_id -> Dict com heartbeat info
        self._heartbeats: Dict[str, dict] = {}
        # task_id -> Dict com dados da tarefa
        self._tasks: Dict[str, dict] = {}
        # user_id -> List de task_ids
        self._user_tasks: Dict[str, List[str]] = {}

    def record_heartbeat(self, user_id: str, data: ExtensionHeartbeatRequest):
        self._heartbeats[user_id] = {
            "version": data.version,
            "active": data.active,
            "workana_logged_in": data.workana_logged_in,
            "bids_remaining": data.bids_remaining,
            "last_heartbeat": datetime.now(timezone.utc),
        }

    def is_connected(self, user_id: str, timeout_seconds: int = 120) -> bool:
        hb = self._heartbeats.get(user_id)
        if not hb:
            return False
        delta = (datetime.now(timezone.utc) - hb["last_heartbeat"]).total_seconds()
        return delta <= timeout_seconds and hb.get("active", False)

    def get_status(self, user_id: str) -> dict:
        hb = self._heartbeats.get(user_id, {})
        connected = self.is_connected(user_id)
        user_task_ids = self._user_tasks.get(user_id, [])

        pending = sum(
            1
            for tid in user_task_ids
            if self._tasks.get(tid, {}).get("status") in ("pending", "processing")
        )
        completed_today = sum(
            1 for tid in user_task_ids if self._tasks.get(tid, {}).get("status") == "completed"
        )

        last_hb = hb.get("last_heartbeat")
        return {
            "is_connected": connected,
            "version": hb.get("version"),
            "last_heartbeat": last_hb.isoformat() if last_hb else None,
            "pending_tasks": pending,
            "completed_today": completed_today,
            "workana_logged_in": hb.get("workana_logged_in"),
            "bids_remaining": hb.get("bids_remaining"),
        }

    def enqueue_task(self, user_id: str, task_data: ExtensionTaskCreate) -> dict:
        task_id = f"ext_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        task_record = {
            "task_id": task_id,
            "user_id": user_id,
            "project_id": task_data.project_id,
            "budget": task_data.budget,
            "custom_message": task_data.custom_message,
            "deadline_days": task_data.deadline_days,
            "template_id": task_data.template_id,
            "attachment_path": task_data.attachment_path,
            "status": "pending",
            "created_at": now_iso,
        }
        self._tasks[task_id] = task_record
        if user_id not in self._user_tasks:
            self._user_tasks[user_id] = []
        self._user_tasks[user_id].append(task_id)
        return task_record

    def get_pending_tasks(self, user_id: str) -> List[dict]:
        user_task_ids = self._user_tasks.get(user_id, [])
        pending = []
        for tid in user_task_ids:
            t = self._tasks.get(tid)
            if t and t.get("status") == "pending":
                t["status"] = "processing"
                pending.append(t)
        return pending

    def complete_task(
        self, task_id: str, completion: ExtensionTaskCompleteRequest
    ) -> Optional[dict]:
        task = self._tasks.get(task_id)
        if not task:
            return None
        task["status"] = "completed" if completion.success else "failed"
        task["result_message"] = completion.message
        task["redirect_url"] = completion.redirect_url
        task["duration_ms"] = completion.duration_ms
        task["completed_at"] = datetime.now(timezone.utc).isoformat()
        return task


extension_manager = ExtensionTaskManager()


# ==================== Endpoints da Extensão ====================


@router.get("/automation/extension/status", response_model=ExtensionStatusResponse)
async def get_extension_status(user: dict = Depends(get_current_user)):
    """Retorna o status atual da integração da extensão para o usuário."""
    status_dict = extension_manager.get_status(user["user_id"])
    return ExtensionStatusResponse(**status_dict)


@router.post("/automation/extension/heartbeat")
async def extension_heartbeat(
    payload: ExtensionHeartbeatRequest, user: dict = Depends(get_current_user)
):
    """Registra a presença e versão da extensão conectada."""
    extension_manager.record_heartbeat(user["user_id"], payload)
    return {"success": True, "message": "Heartbeat registrado com sucesso."}


@router.get("/automation/extension/tasks")
async def get_extension_tasks(user: dict = Depends(get_current_user)):
    """A extensão consulta propostas pendentes para processar em segundo plano."""
    tasks = extension_manager.get_pending_tasks(user["user_id"])
    return {"tasks": tasks, "count": len(tasks)}


@router.post("/automation/extension/tasks", response_model=ExtensionTaskResponse)
async def create_extension_task(
    payload: ExtensionTaskCreate, user: dict = Depends(get_current_user)
):
    """Cria uma tarefa de envio de proposta para ser processada pela extensão."""
    task = extension_manager.enqueue_task(user["user_id"], payload)
    return ExtensionTaskResponse(**task)


@router.post("/automation/extension/tasks/{task_id}/complete")
async def complete_extension_task(
    task_id: str,
    payload: ExtensionTaskCompleteRequest,
    user: dict = Depends(get_current_user),
):
    """Extensão reporta a submissão concluída com sucesso ou erro."""
    task = extension_manager.complete_task(task_id, payload)
    if not task:
        logger.warning(f"Relatório de conclusão recebido para tarefa desconhecida: {task_id}")

    # Registrar histórico e métricas anti-ban caso tenha sucesso
    if payload.success:
        try:
            await antiban.register_proposal_sent(user["user_id"])
        except Exception as e:
            logger.warning(f"Erro ao registrar envio no anti-ban: {e}")

        # Salvar no histórico de propostas
        try:
            proposal_data = ProposalSubmit(
                project_id=payload.project_id or (task.get("project_id") if task else "unknown"),
                custom_message=task.get("custom_message") if task else "",
                budget=task.get("budget", 500) if task else 500,
                deadline_days=task.get("deadline_days", 7) if task else 7,
                template_id=task.get("template_id") if task else None,
            )
            result_obj = ProposalResult(
                success=True,
                message=payload.message or "Enviada via Extensão",
                project_id=proposal_data.project_id,
            )
            await crud.save_proposal_history(user["user_id"], proposal_data, result_obj)
        except Exception as e:
            logger.warning(f"Erro ao salvar histórico de proposta da extensão: {e}")

    return {
        "success": True,
        "message": "Status da tarefa atualizado com sucesso.",
        "task_id": task_id,
    }
