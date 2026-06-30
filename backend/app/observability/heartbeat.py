"""
Heartbeat do worker.

Atualiza periodicamente um arquivo no disco com o timestamp UTC atual.
O healthcheck do Docker compara o mtime desse arquivo com o agora e considera
o container unhealthy quando o arquivo está desatualizado — assim, um event
loop travado (que para de chamar o loop do heartbeat) é detectado de forma
confiável, ao contrário de `ps aux | grep` que apenas confirma que o processo
existe.

O timestamp é gravado em UTC (horário canônico dos logs).
"""
from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from loguru import logger

from app.config import settings

# Caminho padrão dentro do container; pode ser sobrescrito via HEARTBEAT_FILE.
_DEFAULT_HEARTBEAT_FILE = "/tmp/workana_worker.heartbeat"


def heartbeat_file() -> Path:
    """Retorna o caminho do arquivo de heartbeat configurado."""
    return Path(os.getenv("HEARTBEAT_FILE", _DEFAULT_HEARTBEAT_FILE))


def write_heartbeat() -> None:
    """Grava o timestamp UTC atual no arquivo de heartbeat (best-effort)."""
    try:
        path = heartbeat_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        # mtime é o que o healthcheck lê; o conteúdo (ISO UTC) é apenas diagnóstico.
        path.write_text(
            datetime.now(timezone.utc).isoformat(),
            encoding="utf-8",
        )
    except Exception as e:  # pragma: no cover - best-effort, não deve derrubar o worker
        logger.bind(event="worker.heartbeat.write_failed").warning(
            f"Falha ao gravar heartbeat: {e}"
        )


def heartbeat_is_fresh() -> bool:
    """Verifica (para uso em healthcheck/CI) se o heartbeat está dentro do limite."""
    max_age = settings.worker_heartbeat_max_age_seconds
    path = heartbeat_file()
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return False
    age = time.time() - mtime
    return age <= max_age


async def heartbeat_loop(interval_seconds: float = 10.0) -> None:
    """Loop que mantém o heartbeat atualizado enquanto o event loop estiver vivo.

    Deve rodar como task concorrente no worker. Quando o loop for cancelado
    (shutdown), a CancelledError propagate normalmente.
    """
    logger.bind(event="worker.heartbeat.started").info(
        f"Heartbeat do worker iniciado (intervalo={interval_seconds}s)."
    )
    try:
        while True:
            write_heartbeat()
            await asyncio.sleep(interval_seconds)
    except asyncio.CancelledError:
        logger.bind(event="worker.heartbeat.stopped").info("Heartbeat do worker encerrado.")
        raise


def check_heartbeat_cli() -> int:
    """Entry point para o healthcheck do Docker: 0=saudável, 1=unhealthy."""
    max_age = settings.worker_heartbeat_max_age_seconds
    path = heartbeat_file()
    try:
        mtime = path.stat().st_mtime
    except OSError:
        # Sem arquivo ainda: unhealthy (start_period do compose cobre o boot inicial).
        print(f"unhealthy: arquivo de heartbeat ausente em {path}")
        return 1
    age = time.time() - mtime
    if age > max_age:
        print(f"unhealthy: heartbeat com {age:.1f}s (limite={max_age}s)")
        return 1
    print(f"healthy: heartbeat com {age:.1f}s")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(check_heartbeat_cli())
