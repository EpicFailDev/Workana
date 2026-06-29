"""
Schemas Pydantic para validação de dados da API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ==================== Enums ====================

class ProjectType(str, Enum):
    """Tipo de projeto."""
    FIXED = "fixed"
    HOURLY = "hourly"
    ANY = "any"


class SortOption(str, Enum):
    """Opções de ordenação."""
    RELEVANCE = "relevance"
    NEWEST = "created_at_desc"
    OLDEST = "created_at_asc"
    BUDGET_DESC = "budget_desc" # Maior valor
    BUDGET_ASC = "budget_asc"   # Menor valor
    BIDS_DESC = "bids_desc"     # Mais propostas
    BIDS_ASC = "bids_asc"       # Menos propostas


class ProposalStatus(str, Enum):
    """Status da proposta."""
    SENT = "sent"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    GENERATED = "generated"  # Propostas geradas por IA mas não enviadas


# ==================== Filtros de Busca ====================


class SearchFilters(BaseModel):
    """Filtros para busca de projetos."""
    keywords: Optional[str] = Field(None, description="Palavras-chave para busca")
    category: Optional[str] = Field(None, description="Categoria do projeto")
    min_budget: Optional[float] = Field(None, ge=0, description="Orçamento mínimo")
    max_budget: Optional[float] = Field(None, ge=0, description="Orçamento máximo")
    project_type: ProjectType = Field(default=ProjectType.ANY, description="Tipo de projeto")
    sort: SortOption = Field(default=SortOption.RELEVANCE, description="Ordenação")
    skills: Optional[List[str]] = Field(default=[], description="Skills requeridas")
    publication: Optional[str] = Field(None, description="Data de publicação (ex: 1d, 3d, 1w)")
    language: Optional[str] = Field(None, description="Idioma (ex: pt, en, es)")
    proposals: Optional[str] = Field(None, description="Propostas (less_than_5, 5_plus)")
    payment_verified: Optional[bool] = Field(False, description="Pagamento verificado")
    country: Optional[str] = Field(None, description="País do cliente")
    max_results: int = Field(default=100, ge=1, le=500, description="Máximo de resultados")
    page: int = Field(default=1, ge=1, description="Página inicial da busca")
    pages_to_fetch: int = Field(default=10, ge=1, le=100, description="Número de páginas para buscar simultaneamente")


class SavedFilter(BaseModel):
    """Filtro salvo pelo usuário."""
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100, description="Nome do filtro")
    filters: SearchFilters
    created_at: Optional[datetime] = None


# ==================== Projetos ====================

class Project(BaseModel):
    """Projeto encontrado no Workana."""
    id: str = Field(..., description="ID único do projeto")
    title: str = Field(..., description="Título do projeto")
    description: str = Field(..., description="Descrição do projeto")
    budget: Optional[str] = Field(None, description="Orçamento")
    budget_min: Optional[float] = Field(None, description="Orçamento mínimo")
    budget_max: Optional[float] = Field(None, description="Orçamento máximo")
    project_type: Optional[str] = Field(None, description="Tipo do projeto")
    skills: List[str] = Field(default=[], description="Skills requeridas")
    client_name: Optional[str] = Field(None, description="Nome do cliente")
    client_country: Optional[str] = Field(None, description="País do cliente")
    client_rating: Optional[float] = Field(None, description="Avaliação do cliente")
    client_projects_posted: Optional[int] = Field(None, description="Projetos publicados pelo cliente")
    client_projects_paid: Optional[int] = Field(None, description="Projetos pagos pelo cliente")
    client_member_since: Optional[str] = Field(None, description="Membro desde")
    proposals_count: Optional[int] = Field(None, description="Número de propostas")
    posted_at: Optional[str] = Field(None, description="Quando foi postado")
    url: str = Field(..., description="URL do projeto")


class ProjectList(BaseModel):
    """Lista de projetos."""
    projects: List[Project]
    total: int
    page: int = 1


# ==================== Templates de Proposta ====================

class ProposalTemplate(BaseModel):
    """Template de proposta."""
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100, description="Nome do template")
    content: str = Field(..., min_length=10, description="Conteúdo do template")
    default_budget: Optional[float] = Field(None, ge=0, description="Orçamento padrão")
    default_deadline_days: Optional[int] = Field(None, ge=1, description="Prazo padrão em dias")
    is_default: bool = Field(default=False, description="Se é o template padrão")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProposalTemplateCreate(BaseModel):
    """Criação de template de proposta."""
    name: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=10)
    default_budget: Optional[float] = Field(None, ge=0)
    default_deadline_days: Optional[int] = Field(None, ge=1)
    is_default: bool = False


# ==================== Envio de Proposta ====================

class ProposalSubmit(BaseModel):
    """Dados para enviar uma proposta."""
    project_id: str = Field(..., description="ID do projeto")
    template_id: Optional[int] = Field(None, description="ID do template a usar")
    custom_message: Optional[str] = Field(None, description="Mensagem personalizada")
    budget: float = Field(..., gt=0, description="Valor da proposta")
    deadline_days: int = Field(..., ge=1, description="Prazo em dias")


class ProposalResult(BaseModel):
    """Resultado do envio de proposta."""
    success: bool
    message: str
    project_id: str
    proposal_id: Optional[str] = None


class ProposalGenerationResult(BaseModel):
    """Resultado da geração de proposta por IA."""
    success: bool
    proposal: Optional[str] = None
    suggested_price: Optional[str] = None
    justification: Optional[str] = None
    error: Optional[str] = None


# ==================== Histórico ====================

class ProposalHistory(BaseModel):
    """Histórico de proposta enviada."""
    id: int
    project_id: str
    project_title: str
    project_url: Optional[str] = None
    budget: float
    deadline_days: int
    status: ProposalStatus
    sent_at: datetime
    message_preview: Optional[str] = None
    message: Optional[str] = None


# ==================== Dashboard Stats ====================

class DashboardStats(BaseModel):
    """Estatísticas do dashboard."""
    total_proposals_sent: int = 0
    proposals_today: int = 0
    proposals_this_week: int = 0
    proposals_this_month: int = 0
    response_rate: float = 0.0
    accepted_proposals: int = 0
    pending_proposals: int = 0
    last_activity: Optional[datetime] = None
    
    # Gamification
    xp: int = 0
    lp: int = 0
    rank_tier: str = "Ferro"
    rank_division: str = "IV"


# ==================== Automação ====================

class AutomationStatus(BaseModel):
    """Status da automação."""
    is_running: bool = False
    is_logged_in: bool = False
    current_action: Optional[str] = None
    proposals_sent_today: int = 0
    max_proposals_per_day: int = 10
    last_error: Optional[str] = None


class AutomationConfig(BaseModel):
    """Configurações de automação."""
    headless: bool = True
    delay_between_actions_ms: int = Field(default=2000, ge=500, le=10000)
    max_proposals_per_day: int = Field(default=10, ge=1, le=50)
    auto_apply: bool = False
    preferred_template_id: Optional[int] = None
    gemini_api_key: Optional[str] = None
    user_full_name: Optional[str] = None


# ==================== Respostas Genéricas ====================

class MessageResponse(BaseModel):
    """Resposta genérica com mensagem."""
    success: bool
    message: str


class ErrorResponse(BaseModel):
    """Resposta de erro."""
    success: bool = False
    error: str
    detail: Optional[str] = None


# ==================== Projetos Salvos ====================

class SavedProject(BaseModel):
    """Projeto salvo no banco de dados."""
    id: int
    workana_id: str
    title: str
    description: Optional[str] = None
    url: str
    category: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    budget_type: Optional[str] = None
    deadline: Optional[str] = None
    skills: Optional[List[str]] = None
    client_name: Optional[str] = None
    client_country: Optional[str] = None
    client_rating: Optional[float] = None
    proposals_count: Optional[int] = None
    is_favorite: bool = False
    is_applied: bool = False
    notes: Optional[str] = None
    found_at: Optional[datetime] = None


class SavedProjectCreate(BaseModel):
    """Dados para salvar um projeto."""
    workana_id: str
    title: str
    description: Optional[str] = None
    url: str
    category: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    budget_type: Optional[str] = None
    deadline: Optional[str] = None
    skills: Optional[List[str]] = None
    client_name: Optional[str] = None
    client_country: Optional[str] = None
    client_rating: Optional[float] = None
    proposals_count: Optional[int] = None


class SavedProjectList(BaseModel):
    """Lista de projetos salvos."""
    projects: List[SavedProject]
    total: int


class ProjectNotesUpdate(BaseModel):
    """Atualização de notas de um projeto."""
    notes: str = Field(..., max_length=5000)


# ==================== Log de Atividades ====================

class ActivityLogEntry(BaseModel):
    """Entrada no log de atividades."""
    id: int
    action_type: str
    description: str
    details: Optional[dict] = None
    project_id: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    created_at: Optional[datetime] = None


class ActivityLogList(BaseModel):
    """Lista de logs de atividade."""
    logs: List[ActivityLogEntry]
    total: int


# ==================== Estatísticas ====================

class DailyStats(BaseModel):
    """Estatísticas de um dia específico."""
    date: str
    projects_found: int = 0
    projects_viewed: int = 0
    proposals_sent: int = 0
    proposals_accepted: int = 0
    proposals_rejected: int = 0
    logins_count: int = 0
    searches_count: int = 0
    errors_count: int = 0


class StatisticsSummary(BaseModel):
    """Resumo de estatísticas."""
    today: dict
    week: dict
    month: dict


class StatisticsList(BaseModel):
    """Lista de estatísticas diárias."""
    statistics: List[DailyStats]
    days: int


# ==================== Clientes Bloqueados ====================

class BlacklistedClient(BaseModel):
    """Cliente na lista negra."""
    id: int
    client_name: str
    reason: Optional[str] = None
    created_at: Optional[datetime] = None


class BlacklistedClientCreate(BaseModel):
    """Dados para adicionar cliente à lista negra."""
    client_name: str = Field(..., min_length=1, max_length=255)
    reason: Optional[str] = Field(None, max_length=1000)


class BlacklistedClientList(BaseModel):
    """Lista de clientes bloqueados."""
    clients: List[BlacklistedClient]
    total: int


# ==================== Métricas do Perfil Público ====================

class ProfileMetricsResponse(BaseModel):
    """Métricas do perfil público do Workana."""
    success: bool = True
    profile_url: Optional[str] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    ranking_general: Optional[int] = None
    ranking_category: Optional[str] = None
    level: Optional[str] = None  # Nível original
    
    # Novos campos
    xp: int = 0
    lp: int = 0
    rank_tier: str = "Ferro"
    rank_division: str = "IV"
    
    projects_completed: int = 0
    projects_in_progress: int = 0
    hours_worked: int = 0
    average_rating: Optional[float] = None
    total_reviews: int = 0
    member_since: Optional[str] = None
    country: Optional[str] = None
    hourly_rate: Optional[str] = None
    skills: List[str] = []
    last_login: Optional[str] = None
    profile_photo_url: Optional[str] = None
    last_sync: Optional[datetime] = None
    is_configured: bool = False
    error: Optional[str] = None


class ProfileConfigUpdate(BaseModel):
    """Atualização de configuração do perfil."""
    profile_url: str = Field(..., description="URL do perfil público do Workana")
    auto_sync_enabled: bool = Field(default=True, description="Sincronização automática habilitada")
    sync_interval_hours: int = Field(default=6, ge=1, le=24, description="Intervalo de sincronização em horas")


class ProfileConfigResponse(BaseModel):
    """Resposta de configuração do perfil."""
    profile_url: Optional[str] = None
    auto_sync_enabled: bool = True
    sync_interval_hours: int = 6
    last_sync_at: Optional[datetime] = None
    is_configured: bool = False


class ProfileMetricsHistory(BaseModel):
    """Histórico de métricas do perfil."""
    id: int
    profile_url: str
    level: Optional[str] = None
    projects_completed: int = 0
    average_rating: Optional[float] = None
    total_reviews: int = 0
    ranking_general: Optional[int] = None
    scraped_at: datetime


class ProfileMetricsHistoryList(BaseModel):
    """Lista de histórico de métricas."""
    history: List[ProfileMetricsHistory]
    total: int

