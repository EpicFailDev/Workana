# Workana Automation Backend
import sys
import asyncio

# Configurar política de event loop para Windows (necessário para Playwright)
# Isso deve ser feito o mais cedo possível, antes de qualquer loop ser criado.
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass
