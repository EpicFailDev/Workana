
import sys
import asyncio
import uvicorn
import os

if __name__ == "__main__":
    # Forçar WindowsProactorEventLoopPolicy para suportar subprocessos do Playwright
    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            print("WindowsProactorEventLoopPolicy ativada com sucesso.")
        except Exception as e:
            print(f"Erro ao definir política de loop: {e}")

    # Iniciar servidor
    print("Iniciando Uvicorn...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        loop="asyncio"
    )
