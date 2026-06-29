"""
Modelos SQLAlchemy para o banco de dados.
"""
from sqlalchemy import BigInteger, Column, Integer, String, Float, Boolean, DateTime, Text, JSON, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone

from app.config import settings

# Base declarativa
Base = declarative_base()

database_url = make_url(settings.database_url)
engine_options = {"echo": settings.debug, "pool_pre_ping": True}

# Supavisor transaction mode (porta 6543) não suporta prepared statements.
# Session mode (porta 5432) e conexão direta não precisam deste workaround.
if database_url.drivername.endswith("+asyncpg") and database_url.port == 6543:
    engine_options["connect_args"] = {"statement_cache_size": 0}

engine = create_async_engine(settings.database_url, **engine_options)

# Session factory
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Cria tabelas apenas no SQLite local; Postgres é gerido por migrations."""
    if database_url.get_backend_name() != "sqlite":
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")
BIGINT_PK = BigInteger().with_variant(Integer(), "sqlite")


def utcnow():
    return datetime.now(timezone.utc)


async def get_session() -> AsyncSession:
    """Retorna uma sessão do banco de dados."""
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
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uix_user_id_date"),
    )


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
