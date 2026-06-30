"""
Worker process for Workana Automation.
Runs scheduled searches, auto-apply scripts, and notifications using APScheduler.

Saúde do processo é exposta via heartbeat escrito em disco (HEARTBEAT_FILE),
lido pelo healthcheck do Docker — assim um event loop travado é detectado de
forma confiável (ao contrário de `ps aux | grep`, que apenas confirma que o
processo existe).
"""
import asyncio
import sys
import signal
from loguru import logger

# Configure event loop policy for Windows (required for Playwright/asyncio)
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        print("WindowsProactorEventLoopPolicy ativado com sucesso no worker.")
    except Exception as e:
        print(f"Erro ao definir política de loop no worker: {e}")

# Pipeline de logs estruturado: DEVE ser configurado antes das demais importações.
from app.observability.logging_config import configure_logging
configure_logging()

from app.config import settings
from app.database.models import async_session
from sqlalchemy import text
from app.services.scheduler import scheduler_instance
from app.observability.heartbeat import heartbeat_loop


async def main():
    logger.bind(event="worker.starting").info("Iniciando Workana Automation Worker...")

    # 1. Test database connection
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        logger.bind(event="worker.db.connected").info(
            "Conexão com o banco de dados estabelecida com sucesso"
        )
    except Exception as e:
        logger.bind(event="worker.db.connection_failed").critical(
            f"Falha crítica ao conectar no banco de dados Supabase: {e}"
        )
        sys.exit(1)

    # 2. Start the scheduler
    scheduler_instance.start()
    logger.bind(event="worker.scheduler.started").info(
        f"Scheduler de busca iniciado no worker (frequência={settings.max_proposals_per_day}/dia)."
    )

    # 3. Heartbeat para o healthcheck do Docker (detecta event loop travado).
    heartbeat_task = asyncio.create_task(heartbeat_loop(interval_seconds=10.0))

    # Event to flag shutdown
    stop_event = asyncio.Event()

    def handle_shutdown(signum, frame):
        logger.bind(event="worker.shutdown_signal").info(
            f"Sinal {signum} recebido. Iniciando desligamento gracioso..."
        )
        stop_event.set()

    # Register OS signals for graceful termination
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, handle_shutdown)
        except ValueError:
            # signal.signal might fail if not in the main thread (should not happen here)
            pass

    # Wait for shutdown signal
    await stop_event.wait()

    # 4. Shutdown: para o heartbeat e o scheduler
    heartbeat_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass

    logger.bind(event="worker.stopping").info("Desligando o scheduler...")
    scheduler_instance.stop()
    logger.bind(event="worker.stopped").info("Worker finalizado com sucesso.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.bind(event="worker.interrupted").info("Worker interrompido pelo usuário.")
        sys.exit(0)
