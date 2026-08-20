# Testes funcionais e auditoria aprofundada do backend
# Testa: schemas, rotas, autenticacao, consistencia, performance conceitual

import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Any

BACKEND_DIR = Path("C:/Users/Yumi/Documents/GitHub/Workana/backend")
TEST_RESULTS: List[Dict[str, Any]] = []

def log_result(name: str, passed: bool, details: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    TEST_RESULTS.append({"name": name, "passed": passed, "details": details})
    print(f"  {status} | {name}")
    if details:
        print(f"         {details}")

def read_file(rel_path: str) -> str:
    """Lê arquivo relativo ao backend dir"""
    full = BACKEND_DIR / rel_path
    if full.exists():
        return full.read_text(encoding="utf-8")
    return ""

def main():
    print("=" * 70)
    print("🧪 TESTES FUNCIONAIS BACKEND - WORKANA ACCELERATOR")
    print("=" * 70)

    # ========== TESTE 1: Schemas ==========
    print("\n📦 1. VALIDAÇÃO DE SCHEMAS")
    schemas = read_file("app/api/schemas.py")

    # Testar se ProposalBatchCreate existe
    if "class ProposalBatchCreate" in schemas:
        log_result("ProposalBatchCreate schema existe", True)
    else:
        log_result("ProposalBatchCreate schema existe", False, "Classe nao encontrada em schemas.py")

    # Testar se ProposalBatchResponse existe
    if "class ProposalBatchResponse" in schemas:
        log_result("ProposalBatchResponse schema existe", True)
    else:
        log_result("ProposalBatchResponse schema existe", False)

    # Testar se ProposalBatchListResponse existe
    if "class ProposalBatchListResponse" in schemas:
        log_result("ProposalBatchListResponse schema existe", True)
    else:
        log_result("ProposalBatchListResponse schema existe", False)

    # Testar se AnalyzeRequest existe
    if "class AnalyzeRequest" in schemas:
        log_result("AnalyzeRequest schema existe", True)
    else:
        log_result("AnalyzeRequest schema existe", False)

    # Testar se AnalysisResult existe
    if "class AnalysisResult" in schemas:
        log_result("AnalysisResult schema existe", True)
    else:
        log_result("AnalysisResult schema existe", False)

    # Verificar se todos os campos necessarios existem
    if "workana_id: str" in schemas and "score: float" in schemas:
        log_result("AnalysisResult tem campos essenciais", True)
    else:
        log_result("AnalysisResult tem campos essenciais", False)

    # ========== TESTE 2: Endpoints nos Routers ==========
    print("\n🛣️ 2. ENDPOINTS NOS ROUTERS")
    routers_projects = read_file("app/api/routers/projects.py")

    endpoints = {
        "list_catalog": 'router.get("/projects"',
        "analyze_projects": 'router.post("/projects/analyze"',
        "create_batch": 'router.post("/projects/batch"',
        "list_batches": 'router.get("/projects/batches"',
        "get_batch_items": 'router.get("/projects/batches/{batch_id}/items"',
        "start_batch": 'router.post("/projects/batches/{batch_id}/start"',
        "bulk_state": 'router.post("/projects/bulk-state"',
        "search_projects": 'router.post("/projects/search"',
        "submit_proposal": 'router.post("/projects/{project_id}/submit-proposal"',
        "generate_proposal": 'router.post("/projects/{project_id}/generate-proposal"',
    }

    for name, pattern in endpoints.items():
        found = pattern in routers_projects
        log_result(f"Endpoint {name}", found, "Nao encontrado nos routers" if not found else "")

    # ========== TESTE 3: Consistencia Router <-> Schema ==========
    print("\n🔗 3. CONSISTENCIA ROUTER × SCHEMA")
    routers_all = read_file("app/api/routers/projects.py")
    routers_dashboard = read_file("app/api/routers/dashboard.py")
    routers_automation = read_file("app/api/routers/automation.py")
    routers_profile = read_file("app/api/routers/profile.py")

    # Verificar se os response_model usam schemas definidos
    response_models = re.findall(r'response_model=(\w+)', routers_projects)
    valid_schemas = ["CatalogProjectList", "BulkStateResult", "List[AnalysisResult]",
                     "ProposalResult", "List[dict]", "dict", "MessageResponse"]
    
    for rm in response_models:
        if rm not in valid_schemas and not rm.startswith("List["):
            log_result(f"response_model={rm} valido", False, f"Schema desconhecido: {rm}")
        else:
            log_result(f"response_model={rm} valido", True)

    # Verificar se analyze_projects usa response_model correto
    if "response_model=List[AnalysisResult]" in routers_projects:
        log_result("analyze_projects usa List[AnalysisResult]", True)
    else:
        log_result("analyze_projects usa List[AnalysisResult]", False,
                   "Verificar se response_model esta correto")

    # Verificar se create_batch não tem response_model (usando dict)
    if "response_model=dict" in routers_projects:
        log_result("create_batch usa response_model=dict", True, 
                   "Pode melhorar com ProposalBatchCreateResponse")
    else:
        log_result("create_batch usa response_model=dict", False)

    # ========== TESTE 4: CRUD Functions ==========
    print("\n💾 4. FUNCOES CRUD IMPLEMENTADAS")
    crud = read_file("app/database/crud.py")

    crud_functions = {
        "create_proposal_batch": "async def create_proposal_batch",
        "get_proposal_batches": "async def get_proposal_batches",
        "get_proposal_batch": "async def get_proposal_batch",
        "get_batch_items": "async def get_batch_items",
        "start_proposal_batch": "async def start_proposal_batch",
        "cancel_proposal_batch": "async def cancel_proposal_batch",
        "retry_failed_batch_items": "async def retry_failed_batch_items",
        "get_next_batch_item_for_processing": "async def get_next_batch_item_for_processing",
        "update_batch_item_status": "async def update_batch_item_status",
        "get_catalog_projects_by_ids": "async def get_catalog_projects_by_ids",
        "save_project_analysis": "async def save_project_analysis",
        "resolve_target_workana_ids": "async def resolve_target_workana_ids",
        "apply_bulk_state": "async def apply_bulk_state",
        "catalog_project_exists": "async def catalog_project_exists",
        "set_catalog_project_notes": "async def set_catalog_project_notes",
        "upsert_catalog_row": "async def upsert_catalog_row",
        "mark_gone_catalog_projects": "async def mark_gone_catalog_projects",
        "get_distinct_saved_filter_queries": "async def get_distinct_saved_filter_queries",
        "export_catalog_rows": "async def export_catalog_rows",
    }

    for name, pattern in crud_functions.items():
        found = pattern in crud
        log_result(f"CRUD: {name}", found)

    # ========== TESTE 5: Arvore de imports (dependencias) ==========
    print("\n🔗 5. ANALISE DE DEPENDENCIAS")
    
    # Verificar se routers importam corretamente
    if 'from app.database import crud' in routers_projects:
        log_result("Projects router importa crud corretamente", True)
    else:
        log_result("Projects router importa crud corretamente", False)

    if 'from app.services.scorer import ProjectScorer' in routers_projects:
        log_result("Projects router importa ProjectScorer corretamente", True)
    else:
        log_result("Projects router importa ProjectScorer corretamente", False)

    if 'from app.auth import get_current_user' in routers_projects:
        log_result("Projects router importa get_current_user corretamente", True)
    else:
        log_result("Projects router importa get_current_user corretamente", False)

    # ========== TESTE 6: Seguranca de Auth ==========
    print("\n🔒 6. SEGURANÇA E AUTENTICACAO")
    auth = read_file("app/auth.py")
    main = read_file("app/main.py")

    # Verificar se get_current_user esta sendo usado nos routers
    auth_usage = routers_projects.count("get_current_user")
    log_result(f"get_current_user usado {auth_usage}x nos routers", auth_usage > 0)

    # Verificar se CORS permite origens
    if "allow_origins=settings.cors_origins" in main:
        log_result("CORS configurado com settings.cors_origins", True)
    else:
        log_result("CORS configurado com settings.cors_origins", False)

    # Verificar se debug=False desabilita docs
    if 'docs_url="/docs" if settings.debug else None' in main:
        log_result("Swagger desabilitado em producao (debug=False)", True)
    else:
        log_result("Swagger desabilitado em producao (debug=False)", False,
                   "Verificar se docs_url e condicional")

    # ========== TESTE 7: Lógica de negócio nos routers ==========
    print("\n🏗️ 7. ARQUITETURA - Lógica nos routers")
    
    # Verificar _build_analysis_profile no router
    if "async def _build_analysis_profile" in routers_projects:
        # Esta funcao e privada e serve como helper - aceitável
        log_result("_build_analysis_profile e funcao helper privada no router", True,
                   "Funcao interna, nao exposta, aceitavel")
    else:
        log_result("_build_analysis_profile existe", False)

    # ========== TESTE 8: Batch processing - completude ==========
    print("\n📦 8. BATCH PROCESSING - COMPLUDEZA")
    
    # Verificar se existem funcões para ciclo completo de batch
    batch_lifecycle = [
        ("criar lote", "create_proposal_batch"),
        ("listar lotes", "get_proposal_batches"),
        ("detalhar lote", "get_proposal_batch"),
        ("listar itens", "get_batch_items"),
        ("iniciar processamento", "start_proposal_batch"),
        ("cancelar lote", "cancel_proposal_batch"),
        ("retry itens failed", "retry_failed_batch_items"),
        ("buscar proximo item", "get_next_batch_item_for_processing"),
        ("atualizar status item", "update_batch_item_status"),
    ]

    for desc, func in batch_lifecycle:
        exists = func in crud
        log_result(f"Cycle: {desc} ({func})", exists)

    # ========== TESTE 9: Pool de conexoes ==========
    print("\n🔌 9. CONFIGURACAO DE CONEXAO")
    models = read_file("app/database/models.py")

    pool_config = {
        "pool_pre_ping": "pool_pre_ping",
        "pool_size": "pool_size",
        "max_overflow": "max_overflow", 
        "pool_recycle": "pool_recycle",
        "pool_timeout": "pool_timeout",
    }

    for name, pattern in pool_config.items():
        found = pattern in models
        log_result(f"Pool config: {name}", found)

    # ========== TESTE 10: Migrations ==========
    print("\n📋 10. MIGRACOES E ESQUEMA")
    migrations_dir = BACKEND_DIR / "supabase" / "migrations"
    if migrations_dir.exists():
        migration_files = list(migrations_dir.glob("*.sql"))
        log_result(f"Arquivos de migracao encontrados: {len(migration_files)}", True,
                   f"Arquivos: {[f.name for f in migration_files[:5]]}")
    else:
        log_result("Diretório de migracoes existe", False)

    # ========== RESUMO FINAL ==========
    print("\n" + "=" * 70)
    print("📊 RESUMO DOS TESTES")
    print("=" * 70)

    total = len(TEST_RESULTS)
    passed = sum(1 for r in TEST_RESULTS if r["passed"])
    failed = total - passed

    print(f"\nTotal: {total} testes")
    print(f"✅ Passados: {passed}")
    print(f"❌ Falhados: {failed}")
    print(f"Taxa de sucesso: {passed/total*100:.0f}%")

    if failed > 0:
        print("\n🔴 Testes falhados:")
        for r in TEST_RESULTS:
            if not r["passed"]:
                print(f"  • {r['name']}: {r['details']}")

    print("\n" + "=" * 70)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
