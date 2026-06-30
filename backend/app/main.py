"""
Aplicação principal FastAPI para automação do Workana.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loguru import logger
import sys
import asyncio

from app.config import settings
# Logging central DEVE ser configurado antes das demais importações de app,
# de forma que Uvicorn/SQLAlchemy já emitam pelo pipeline estruturado.
from app.observability.logging_config import configure_logging
from app.observability.middleware import RequestIDMiddleware
from app.api.routers import projects, automation, dashboard, profile
from app.database.models import init_db


# Configurar política de event loop para Windows (necessário para Playwright)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Pipeline de logs estruturado (JSON em produção, console colorido em desenvolvimento).
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    logger.bind(event="api.starting").info("Iniciando Workana Automation API...")

    # Testar conexão com o banco de dados PostgreSQL
    from app.database.models import async_session
    from sqlalchemy import text
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        logger.bind(event="api.db.connected").info("Conexão com o banco de dados estabelecida com sucesso")
    except Exception as e:
        logger.bind(event="api.db.connection_failed").critical(
            f"Falha crítica ao conectar no banco de dados Supabase: {e}"
        )
        sys.exit(1)

    yield

    logger.bind(event="api.stopping").info("Encerrando aplicação...")


# Criar aplicação FastAPI (Swagger/Redoc restritos conforme ambiente)
app = FastAPI(
    title="Workana Automation API",
    description="API para automação de busca e envio de propostas no Workana",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None
)

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de correlação (X-Request-ID). Adicionado por último para que rode
# primeiro na pilha (Starlette executa middlewares em ordem reversa de adição).
app.add_middleware(RequestIDMiddleware)

# Incluir rotas da API
app.include_router(projects.router, prefix="/api", tags=["Projects"])
app.include_router(automation.router, prefix="/api", tags=["Automation"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
app.include_router(profile.router, prefix="/api", tags=["Profile"])


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
    """Liveness: o processo está respondendo."""
    return {"status": "healthy"}


@app.get("/ready")
async def readiness_check():
    """Readiness: aplicação E dependências críticas (banco) estão disponíveis."""
    from app.database.models import async_session
    from sqlalchemy import text
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        logger.bind(event="api.ready_failed").warning(
            f"Readiness falhou: banco indisponível ({e.__class__.__name__})"
        )
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "database_unavailable"},
        )
    return {"status": "ready"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        loop="asyncio"
    )

