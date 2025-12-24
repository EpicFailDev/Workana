"""
Modelos SQLAlchemy para o banco de dados.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

from app.config import settings

# Base declarativa
Base = declarative_base()

# Engine assíncrono
engine = create_async_engine(settings.database_url, echo=settings.debug)

# Session factory
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Inicializa o banco de dados criando as tabelas."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Retorna uma sessão do banco de dados."""
    async with async_session() as session:
        yield session


class Credentials(Base):
    """Credenciais do Workana (criptografadas)."""
    __tablename__ = "credentials"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False)
    encrypted_password = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SavedFilter(Base):
    """Filtros de busca salvos."""
    __tablename__ = "saved_filters"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    filters_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProposalTemplate(Base):
    """Templates de proposta."""
    __tablename__ = "proposal_templates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    default_budget = Column(Float, nullable=True)
    default_deadline_days = Column(Integer, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProposalHistory(Base):
    """Histórico de propostas enviadas."""
    __tablename__ = "proposal_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(255), nullable=False)
    project_title = Column(String(500), nullable=False)
    project_url = Column(Text, nullable=True)
    budget = Column(Float, nullable=False)
    deadline_days = Column(Integer, nullable=False)
    message = Column(Text, nullable=True)
    status = Column(String(50), default="sent")
    sent_at = Column(DateTime, default=datetime.utcnow)


class AutomationConfig(Base):
    """Configurações de automação."""
    __tablename__ = "automation_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    headless = Column(Boolean, default=True)
    delay_between_actions_ms = Column(Integer, default=2000)
    max_proposals_per_day = Column(Integer, default=10)
    auto_apply = Column(Boolean, default=False)
    preferred_template_id = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Project(Base):
    """Projetos encontrados no Workana."""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    workana_id = Column(String(255), unique=True, nullable=False)  # ID do projeto no Workana
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    subcategory = Column(String(100), nullable=True)
    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)
    budget_type = Column(String(50), nullable=True)  # fixed, hourly
    deadline = Column(String(100), nullable=True)
    skills = Column(JSON, nullable=True)  # Lista de skills requeridas
    client_name = Column(String(255), nullable=True)
    client_country = Column(String(100), nullable=True)
    client_rating = Column(Float, nullable=True)
    client_projects_posted = Column(Integer, nullable=True)
    proposals_count = Column(Integer, nullable=True)
    is_favorite = Column(Boolean, default=False)
    is_applied = Column(Boolean, default=False)
    is_ignored = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)  # Notas pessoais sobre o projeto
    found_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ActivityLog(Base):
    """Log de atividades do sistema."""
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    action_type = Column(String(50), nullable=False)  # login, search, apply, error, etc
    action_description = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)  # Detalhes extras em JSON
    project_id = Column(Integer, nullable=True)  # Referência ao projeto, se aplicável
    status = Column(String(20), default="success")  # success, error, warning
    error_message = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)  # Duração da ação em ms
    created_at = Column(DateTime, default=datetime.utcnow)


class DailyStatistics(Base):
    """Estatísticas diárias do sistema."""
    __tablename__ = "daily_statistics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, unique=True)
    projects_found = Column(Integer, default=0)
    projects_viewed = Column(Integer, default=0)
    proposals_sent = Column(Integer, default=0)
    proposals_accepted = Column(Integer, default=0)
    proposals_rejected = Column(Integer, default=0)
    logins_count = Column(Integer, default=0)
    searches_count = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    total_time_spent_minutes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BlacklistedClient(Base):
    """Clientes para ignorar."""
    __tablename__ = "blacklisted_clients"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_name = Column(String(255), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
