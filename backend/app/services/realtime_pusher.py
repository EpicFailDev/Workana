"""
Serviço de WebSocket em Tempo Real (Pusher) do Workana.

Conecta-se diretamente aos canais públicos 'projects-pt' e 'projects-en' da infraestrutura
Pusher do Workana para capturar novos projetos no exato segundo em que são publicados,
eliminando a latência de polling e garantindo vantagem competitiva no envio de propostas.
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Optional, Callable, Dict, Any
from loguru import logger
import websockets

from app.config import settings
from app.database import crud
from app.database.models import async_session
from app.observability.context import new_operation_id, operation_id_var


PUSHER_WS_URL = "wss://ws-mt1.pusher.com/app/5d14500e05a938842a18?protocol=7&client=js&version=7.0.6&flash=false"


class WorkanaRealtimePusher:
    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._reconnect_delay = 5.0

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self):
        """Inicia o listener em background."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._listen_loop())
        logger.bind(event="pusher.started").info(
            "Listener WebSocket Pusher em Tempo Real iniciado."
        )

    def stop(self):
        """Para o listener."""
        self._running = False
        if self._task:
            self._task.cancel()
        logger.bind(event="pusher.stopped").info("Listener WebSocket Pusher finalizado.")

    async def _listen_loop(self):
        """Loop resiliente com reconexão automática e backoff exponencial."""
        while self._running:
            try:
                logger.bind(event="pusher.connecting").info(
                    "Conectando ao gateway WebSocket do Workana (Pusher)..."
                )
                async with websockets.connect(
                    PUSHER_WS_URL,
                    ping_interval=30,
                    ping_timeout=20,
                    close_timeout=10,
                ) as ws:
                    self._ws = ws
                    self._reconnect_delay = 5.0

                    logger.bind(event="pusher.connected").success(
                        "Conexão WebSocket com Workana estabelecida com sucesso!"
                    )

                    await self._handle_connection(ws)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.bind(event="pusher.error").warning(
                    f"Conexão WebSocket interrompida: {e}. Reconectando em {self._reconnect_delay:.1f}s..."
                )
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 1.5, 60.0)

    async def _handle_connection(self, ws):
        """Processa mensagens recebidas do WebSocket."""
        raw_init = await ws.recv()
        init_data = json.loads(raw_init)
        if init_data.get("event") == "pusher:connection_established":
            socket_info = json.loads(init_data.get("data", "{}"))
            socket_id = socket_info.get("socket_id")
            logger.bind(event="pusher.handshake").info(f"Socket ID estabelecido: {socket_id}")

            for channel in ["projects-pt", "projects-en"]:
                sub_payload = {"event": "pusher:subscribe", "data": {"channel": channel}}
                await ws.send(json.dumps(sub_payload))
                logger.bind(event="pusher.subscribed").info(
                    f"Inscrito no canal de streaming: {channel}"
                )

        while self._running:
            try:
                raw_msg = await ws.recv()
                msg = json.loads(raw_msg)
                event_name = msg.get("event")
                channel = msg.get("channel")
                data_raw = msg.get("data")

                if event_name == "pusher:ping":
                    await ws.send(json.dumps({"event": "pusher:pong", "data": {}}))
                    continue

                if event_name and not event_name.startswith("pusher:"):
                    await self._process_project_event(event_name, channel, data_raw)

            except websockets.ConnectionClosed:
                logger.bind(event="pusher.closed").info("Conexão WebSocket fechada pelo servidor.")
                break

    async def _process_project_event(self, event_name: str, channel: Optional[str], data_raw: Any):
        """Processa um evento de novo projeto ou atualização de catálogo."""
        try:
            payload = json.loads(data_raw) if isinstance(data_raw, str) else data_raw
            if not isinstance(payload, dict):
                return

            logger.bind(event="pusher.project_received").info(
                f"⚡ [TEMPO REAL] Evento recebido no canal '{channel}': {event_name}"
            )

            project_data = self._normalize_pusher_project(payload)
            if project_data and project_data.get("workana_id"):
                op_id = new_operation_id()
                token = operation_id_var.set(op_id)
                try:
                    await crud.upsert_catalog_projects([project_data])
                    logger.bind(event="pusher.upsert_success").success(
                        f"⚡ [CATÁLOGO REALTIME] Projeto '{project_data.get('title', '')[:50]}' registrado instantaneamente!"
                    )
                finally:
                    operation_id_var.reset(token)

        except Exception as exc:
            logger.bind(event="pusher.process_error").error(
                f"Erro ao processar evento Pusher: {exc}"
            )

    @staticmethod
    def _normalize_pusher_project(payload: dict) -> Optional[Dict[str, Any]]:
        """Converte o payload bruto do Pusher para o modelo unificado de catálogo."""
        workana_id = str(
            payload.get("id") or payload.get("slug") or payload.get("workana_id") or ""
        ).strip()
        if not workana_id:
            return None

        slug = str(payload.get("slug") or workana_id).strip()
        url = payload.get("url") or f"https://www.workana.com/job/{slug}"
        title = payload.get("title") or payload.get("name") or "Novo Projeto Workana"
        description = payload.get("description") or payload.get("details") or ""
        budget = payload.get("budget") or payload.get("value") or "A combinar"
        skills = payload.get("skills") or []
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]

        contract_type = (
            "hourly" if payload.get("is_hourly") or "hora" in str(budget).lower() else "fixed"
        )

        return {
            "workana_id": slug,
            "title": title,
            "description": description,
            "budget": str(budget),
            "skills": skills,
            "url": url,
            "contract_type": contract_type,
            "proposals_count": int(payload.get("proposals_count") or 0),
            "is_active": True,
            "first_seen_at": datetime.now(timezone.utc),
            "raw_data": payload,
        }


pusher_realtime_instance = WorkanaRealtimePusher()
