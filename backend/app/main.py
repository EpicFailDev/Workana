"""
Aplicação principal FastAPI para automação do Workana.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import sys
import asyncio

from app.config import settings
from app.api.routes import router as api_router
from app.database.models import init_db


# Configurar política de event loop para Windows (necessário para Playwright)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


# Configurar loguru
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG" if settings.debug else "INFO"
)
logger.add(
    "logs/workana_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days",
    level="DEBUG"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    logger.info("🚀 Iniciando Workana Automation API...")
    
    # Inicializar banco de dados
    await init_db()
    logger.info("✅ Banco de dados inicializado")
    
    yield
    
    logger.info("👋 Encerrando aplicação...")


# Criar aplicação FastAPI
app = FastAPI(
    title="Workana Automation API",
    description="API para automação de busca e envio de propostas no Workana",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas da API
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """Endpoint raiz."""
    return {
        "message": "Workana Automation API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Verificação de saúde da API."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        loop="asyncio"
    )
