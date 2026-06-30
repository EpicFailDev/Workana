"""
Modelos SQLAlchemy para o banco de dados.
"""
import contextvars
import time
from sqlalchemy import BigInteger, Column, Integer, String, Float, Boolean, DateTime, Text, JSON, UniqueConstraint, Uuid, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import text
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from loguru import logger

from app.config import settings

# Base declarativa
Base = declarative_base()

database_url = make_url(settings.database_url)

# Configurações do Pool SQLAlchemy, timeouts, reciclagem e limites para resiliência com o Supabase
engine_options = {
    "echo": settings.sqlalchemy_echo,
    "pool_pre_ping": True,
    "pool_size": 15,
    "max_overflow": 10,
    "pool_recycle": 1800,  # 30 minutos
    "pool_timeout": 30     # 30 segundos
}

# Supavisor transaction mode (porta 6543) não suporta prepared statements.
# Session mode (porta 5432) e conexão direta não precisam deste workaround.
if database_url.drivername.endswith("+asyncpg") and database_url.port == 6543:
    engine_options["connect_args"] = {"statement_cache_size": 0}

engine = create_async_engine(settings.database_url, **engine_options)


# ---------------------------------------------------------------------------- #
# Listener de query lenta.
#
# Em produção, SQLAlchemy echo fica DESLIGADO (ruído + exposição de parâmetros).
# Aqui registramos apenas as queries que excedem SLOW_QUERY_MS, logando o
# statement (sem parâmetros) e a duração — o suficiente para diagnosticar sem
# vazar dados.
# ---------------------------------------------------------------------------- #


@event.listens_for(engine.sync_engine, "before_cursor_execute")
def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.perf_counter()


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    start = getattr(context, "_query_start_time", None)
    if start is None:
        return
    duration_ms = (time.perf_counter() - start) * 1000.0
    threshold = float(settings.slow_query_ms)
    if duration_ms > threshold:
        # Sanitiza o statement para uma linha e trunca; nunca loga parâmetros.
        stmt = " ".join(statement.split())[:300]
        logger.bind(event="db.slow_query").warning(
            f"Query lenta: {duration_ms:.1f}ms (limite={threshold:.0f}ms) stmt={stmt!r}"
        )

# ContextVar global para armazenar o ID do usuário autenticado no escopo da transação/tarefa async
current_user_id: contextvars.ContextVar[Optional[UUID]] = contextvars.ContextVar("current_user_id", default=None)

# Subclasse de AsyncSession que propaga automaticamente o usuário logado para o contexto de transação do PostgreSQL
class TenantAsyncSession(AsyncSession):
    async def __aenter__(self):
        await super().__aenter__()
        uid = current_user_id.get()
        if uid:
            await self.execute(
                text("SELECT set_config('request.jwt.claim.sub', :user_id, true)"),
                {"user_id": str(uid)}
            )
        return self

# Session factory configurada com a classe customizada TenantAsyncSession
async_session = sessionmaker(engine, class_=TenantAsyncSession, expire_on_commit=False)


async def init_db():
    """No-op: O banco SQLite foi removido do runtime e o Postgres é gerido via migrations."""
    pass


JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")
BIGINT_PK = BigInteger


def utcnow():
    return datetime.now(timezone.utc)


async def get_session() -> AsyncSession:
    """Retorna uma sessão do banco de dados com isolamento por tenant/RLS se current_user_id estiver ativo."""
    async with async_session() as session:
        yield session


class Credentials(Base):
    """Credenciais do Workana (criptografadas)."""
    __tablename__ = "credentials"
    
    id = Column(BIGINT_PK, primary_key=True, autoincrement=True)
    user_id = Column(Uuid(as_uuid=True), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False)
    encrypted_password = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SavedFilter(Base):
    """Filtros de busca salvos."""
    __tablename__ = "saved_filters"
    
    id = Column(BIGINT_PK, primary_key=True, autoincrement=True)
    user_id = Column(Uuid(as_uuid=True), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    filters_json = Column(JSON_TYPE, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class ProposalTemplate(Base):
    """Templates de proposta."""
    __tablename__ = "proposal_templates"
    
    id = Column(BIGINT_PK, primary_key=True, autoincrement=True)
    user_id = Column(Uuid(as_uuid=True), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    default_budget = Column(Float, nullable=True)
    default_deadline_days = Column(Integer, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ProposalHistory(Base):
    """Histórico de propostas enviadas."""
    __tablename__ = "proposal_history"
    
    id = Column(BIGINT_PK, primary_key=True, autoincrement=True)
    user_id = Column(Uuid(as_uuid=True), nullable=False, index=True)
    project_id = Column(String(255), nullable=False)
    project_title = Column(String(500), nullable=False)
    project_url = Column(Text, nullable=True)
    budget = Column(Float, nullable=False)
    deadline_days = Column(Integer, nullable=False)
    message = Column(Text, nullable=True)
    status = Column(String(50), default="sent")
    sent_at = Column(DateTime(timezone=True), default=utcnow)


class AutomationConfig(Base):
    """Configurações de automação."""
    __tablename__ = "automation_config"
    
    id = Column(BIGINT_PK, primary_key=True, autoincrement=True)
    user_id = Column(Uuid(as_uuid=True), nullable=False, unique=True, index=True)
    headless = Column(Boolean, default=True)
    delay_between_actions_ms = Column(Integer, default=2000)
    max_proposals_per_day = Column(Integer, default=10)
    auto_apply = Column(Boolean, default=False)
    preferred_template_id = Column(BigInteger, nullable=True)
    gemini_api_key = Column(Text, nullable=True)  # Chave criptografada
    user_full_name = Column(Text, nullable=True)
    
    # Notificações
    telegram_enabled = Column(Boolean, default=False)
    telegram_bot_token = Column(Text, nullable=True)  # Chave criptografada
    telegram_chat_id = Column(Text, nullable=True)
    webhook_enabled = Column(Boolean, default=False)
    webhook_url = Column(Text, nullable=True)
    email_enabled = Column(Boolean, default=False)
    email_to = Column(String(255), nullable=True)
    
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Project(Base):
    """Projetos encontrados no Workana."""
    __tablename__ = "projects"
    
    id = Column(BIGINT_PK, primary_key=True, autoincrement=True)
    user_id = Column(Uuid(as_uuid=True), nullable=False, index=True)
    workana_id = Column(String(255), nullable=False)  # ID do projeto no Workana (único por usuário)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    subcategory = Column(String(100), nullable=True)
    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)
    budget_type = Column(String(50), nullable=True)  # fixed, hourly
    deadline = Column(String(100), nullable=True)
    skills = Column(JSON_TYPE, nullable=True)  # Lista de skills requeridas
    client_name = Column(String(255), nullable=True)
    client_country = Column(String(100), nullable=True)
    client_rating = Column(Float, nullable=True)
    client_projects_posted = Column(Integer, nullable=True)
    proposals_count = Column(Integer, nullable=True)
    payment_verified = Column(Boolean, default=False)
    posted_at = Column(String(100), nullable=True)
    is_favorite = Column(Boolean, default=False)
    is_applied = Column(Boolean, default=False)
    is_ignored = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)  # Notas pessoais sobre o projeto
    found_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "workana_id", name="uix_user_id_workana_id"),
    )


class ActivityLog(Base):
    """Log de atividades do sistema."""
    __tablename__ = "activity_logs"
    
    id = Column(BIGINT_PK, primary_key=True, autoincrement=True)
    user_id = Column(Uuid(as_uuid=True), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)  # login, search, apply, error, etc
    action_description = Column(Text, nullable=False)
    details = Column(JSON_TYPE, nullable=True)  # Detalhes extras em JSON
    project_id = Column(BigInteger, nullable=True)  # Referência ao projeto, se aplicável
    status = Column(String(20), default="success")  # success, error, warning
    error_message = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)  # Duração da ação em ms
    created_at = Column(DateTime(timezone=True), default=utcnow)


class DailyStatistics(Base):
    """Estatísticas diárias do sistema."""
    __tablename__ = "daily_statistics"
    
    id = Column(BIGINT_PK, primary_key=True, autoincrement=True)
    user_id = Column(Uuid(as_uuid=True), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False)
    projects_found = Column(Integer, default=0)
    projects_viewed = Column(Integer, default=0)
    proposals_sent = Column(Integer, default=0)
    proposals_accepted = Column(Integer, default=0)
    proposals_rejected = Column(Integer, default=0)
    logins_count = Column(Integer, default=0)
    searches_count = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    total_time_spent_minutes = Column(Integer, default=0)
    scraping_success_count = Column(Integer, default=0)
    scraping_failure_count = Column(Integer, default=0)
    scraping_blocked_count = Column(Integer, default=0)
    scraping_total_time_ms = Column(BigInteger, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uix_user_id_date"),
    )


class AntibanStats(Base):
    """Estatísticas do anti-ban salvas por usuário com lock otimista."""
    __tablename__ = "antiban_stats"
    
    id = Column(BIGINT_PK, primary_key=True, autoincrement=True)
    user_id = Column(Uuid(as_uuid=True), nullable=False, unique=True, index=True)
    proposals_sent_today = Column(Integer, default=0)
    proposals_sent_this_hour = Column(Integer, default=0)
    searches_this_hour = Column(Integer, default=0)
    logins_today = Column(Integer, default=0)
    last_proposal_time = Column(DateTime(timezone=True), nullable=True)
    last_search_time = Column(DateTime(timezone=True), nullable=True)
    last_login_time = Column(DateTime(timezone=True), nullable=True)
    session_start_time = Column(DateTime(timezone=True), nullable=True)
    last_break_time = Column(DateTime(timezone=True), nullable=True)
    consecutive_proposals = Column(Integer, default=0)
    total_actions_today = Column(Integer, default=0)
    last_hourly_reset = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_daily_reset = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    
    __mapper_args__ = {
        "version_id_col": version
    }



class BlacklistedClient(Base):
    """Clientes para ignorar."""
    __tablename__ = "blacklisted_clients"
    
    id = Column(BIGINT_PK, primary_key=True, autoincrement=True)
    user_id = Column(Uuid(as_uuid=True), nullable=False, index=True)
    client_name = Column(String(255), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class ProfileMetrics(Base):
    """Métricas do perfil público do Workana."""
    __tablename__ = "profile_metrics"
    
    id = Column(BIGINT_PK, primary_key=True, autoincrement=True)
    user_id = Column(Uuid(as_uuid=True), nullable=False, index=True)
    profile_url = Column(String(500), nullable=False)
    username = Column(String(255), nullable=True)
    display_name = Column(String(255), nullable=True)
    projects_completed = Column(Integer, default=0)
    projects_in_progress = Column(Integer, default=0)  # Projetos em execução
    hours_worked = Column(Integer, default=0)  # Horas trabalhadas
    average_rating = Column(Float, nullable=True)
    total_reviews = Column(Integer, default=0)
    member_since = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    hourly_rate = Column(String(50), nullable=True)
    skills = Column(JSON_TYPE, nullable=True)
    last_login = Column(String(100), nullable=True)  # Último login
    profile_photo_url = Column(String(500), nullable=True)  # URL da foto de perfil
    scraped_at = Column(DateTime(timezone=True), default=utcnow)


class ProfileConfig(Base):
    """Configuração do perfil público para monitoramento."""
    __tablename__ = "profile_config"
    
    id = Column(BIGINT_PK, primary_key=True, autoincrement=True)
    user_id = Column(Uuid(as_uuid=True), nullable=False, unique=True, index=True)
    profile_url = Column(String(500), nullable=False)
    auto_sync_enabled = Column(Boolean, default=True)
    sync_interval_hours = Column(Integer, default=6)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
