import sys
import asyncio
import logging
from loguru import logger

# Configurar política de event loop para Windows ANTES de qualquer outra coisa
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        print("✅ WindowsProactorEventLoopPolicy ativado com sucesso.")
    except Exception as e:
        print(f"❌ Falha ao ativar WindowsProactorEventLoopPolicy: {e}")

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("🚀 Iniciando servidor Workana via serve.py...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        loop="asyncio"  # Forçar uso do asyncio (que agora tem policy correta)
    )
