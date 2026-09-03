"""
Fachada central para operações de banco de dados (CRUD).
Reúne e expõe repositórios especializados seguindo o Princípio da Responsabilidade Única (SRP).
"""

from app.database.models import async_session

# Credenciais e Criptografia
from app.database.repositories.credentials import (
    _get_fernet,
    _encrypt,
    _decrypt,
    encrypt_text,
    decrypt_text,
    save_credentials,
    get_credentials,
    delete_credentials,
    save_workana_session,
    get_workana_session,
    delete_workana_session,
)

# Filtros Salvos
from app.database.repositories.filters import (
    get_saved_filters,
    create_filter,
    delete_filter,
    get_distinct_saved_filter_queries,
)

# Templates de Proposta
from app.database.repositories.templates import (
    parse_template_ref,
    _sync_preferred_template,
    get_preferred_or_default_template,
    get_active_system_template,
    has_personal_default_or_preferred,
    get_templates,
    get_template,
    create_template,
    update_template,
    delete_template,
)

# Histórico e Submissão de Propostas
from app.database.repositories.proposals import (
    save_proposal_history,
    save_ai_proposal,
    get_proposal_history,
    update_proposal_status,
    get_latest_project_proposal,
    get_project_proposal_versions,
    get_all_unified_proposals,
    delete_proposal_history,
    delete_project_proposal_version,
)

# Dashboard e Estatísticas
from app.database.repositories.dashboard import (
    get_daily_stats,
    get_dashboard_stats,
    _update_daily_stats,
    get_statistics,
    get_statistics_summary,
)

# Configuração e Logs de Automação
from app.database.repositories.automation import (
    get_automation_config,
    save_automation_config,
    log_activity,
    get_activity_logs,
    update_scraping_stats,
)

# Clientes Bloqueados
from app.database.repositories.blacklist import (
    add_blacklisted_client,
    get_blacklisted_clients,
    remove_blacklisted_client,
    is_client_blacklisted,
)

# Catálogo e Projetos
from app.database.repositories.catalog import (
    save_project,
    get_projects,
    get_project,
    get_project_by_workana_id,
    toggle_project_favorite,
    mark_project_applied,
    ignore_project,
    update_project_notes,
    search_catalog,
    get_catalog_projects_by_ids,
    save_project_analysis,
    resolve_target_workana_ids,
    apply_bulk_state,
    catalog_project_exists,
    get_bids_history,
    get_catalog_brief,
    export_catalog_rows,
    set_catalog_project_notes,
    upsert_catalog_row,
    upsert_catalog_rows_batch,
    mark_gone_catalog_projects,
    restore_gone_catalog_projects,
    count_active_catalog_projects,
)

# Lotes de Proposta
from app.database.repositories.batches import (
    create_proposal_batch,
    get_proposal_batches,
    count_proposal_batches,
    get_proposal_batch,
    cancel_proposal_batch,
    retry_failed_batch_items,
    recalculate_batch_progress,
    get_next_batch_item_for_processing,
    update_batch_item_status,
    update_proposal_batch_item,
    delete_proposal_batch_item,
    save_project_to_draft_batch,
)

# Perfil
from app.database.repositories.profile import (
    get_profile_config,
    get_or_create_profile_config,
    get_latest_profile_metrics,
    get_profile_history,
)

__all__ = [
    "async_session",
    "_get_fernet",
    "_encrypt",
    "_decrypt",
    "encrypt_text",
    "decrypt_text",
    "save_credentials",
    "get_credentials",
    "delete_credentials",
    "save_workana_session",
    "get_workana_session",
    "delete_workana_session",
    "get_saved_filters",
    "create_filter",
    "delete_filter",
    "get_distinct_saved_filter_queries",
    "parse_template_ref",
    "_sync_preferred_template",
    "get_preferred_or_default_template",
    "get_active_system_template",
    "has_personal_default_or_preferred",
    "get_templates",
    "get_template",
    "create_template",
    "update_template",
    "delete_template",
    "save_proposal_history",
    "save_ai_proposal",
    "get_proposal_history",
    "update_proposal_status",
    "get_daily_stats",
    "get_dashboard_stats",
    "_update_daily_stats",
    "get_statistics",
    "get_statistics_summary",
    "get_automation_config",
    "save_automation_config",
    "log_activity",
    "get_activity_logs",
    "update_scraping_stats",
    "add_blacklisted_client",
    "get_blacklisted_clients",
    "remove_blacklisted_client",
    "is_client_blacklisted",
    "save_project",
    "get_projects",
    "get_project",
    "get_project_by_workana_id",
    "toggle_project_favorite",
    "mark_project_applied",
    "ignore_project",
    "update_project_notes",
    "search_catalog",
    "get_catalog_projects_by_ids",
    "save_project_analysis",
    "resolve_target_workana_ids",
    "apply_bulk_state",
    "catalog_project_exists",
    "get_bids_history",
    "get_catalog_brief",
    "export_catalog_rows",
    "set_catalog_project_notes",
    "upsert_catalog_row",
    "upsert_catalog_rows_batch",
    "mark_gone_catalog_projects",
    "restore_gone_catalog_projects",
    "count_active_catalog_projects",
    "create_proposal_batch",
    "get_proposal_batches",
    "count_proposal_batches",
    "get_proposal_batch",
    "cancel_proposal_batch",
    "retry_failed_batch_items",
    "recalculate_batch_progress",
    "get_next_batch_item_for_processing",
    "update_batch_item_status",
    "update_proposal_batch_item",
    "delete_proposal_batch_item",
    "save_project_to_draft_batch",
    "get_latest_project_proposal",
    "get_project_proposal_versions",
    "get_all_unified_proposals",
    "delete_proposal_history",
    "delete_project_proposal_version",
    "get_profile_config",
    "get_or_create_profile_config",
    "get_latest_profile_metrics",
    "get_profile_history",
]
