#!/usr/bin/env python3
"""
Auditoria de Desempenho e Funcionamento do Backend Workana Accelerator
Analisa: queries, N+1, indices, bottlenecks, testes, bugs, inconsistencias
"""

import ast
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Any

BACKEND_DIR = Path("C:/Users/Yumi/Documents/GitHub/Workana/backend")

class AuditIssue:
    def __init__(self, severity: str, category: str, file: str, line: int, description: str, recommendation: str = ""):
        self.severity = severity  # CRITICAL, HIGH, MEDIUM, LOW
        self.category = category  # PERFORMANCE, SECURITY, BUG, CODE_QUALITY, TEST, ARCHITECTURE
        self.file = file
        self.line = line
        self.description = description
        self.recommendation = recommendation

    def __str__(self):
        sev_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
        icon = sev_icon.get(self.severity, "⚪")
        return (f"{icon} [{self.severity}] {self.category} | {self.file}:{self.line}\n"
                f"   {self.description}\n"
                f"   → {self.recommendation}")


class BackendAuditor:
    def __init__(self):
        self.issues: List[AuditIssue] = []
        self.files_content: Dict[str, str] = {}
        self.files_ast: Dict[str, ast.AST] = {}

    def load_files(self, patterns: List[str]):
        """Carrega arquivos relevantes para analise"""
        for pattern in patterns:
            for f in BACKEND_DIR.rglob(pattern):
                if f.is_file() and f.suffix == ".py":
                    try:
                        content = f.read_text(encoding="utf-8")
                        rel_path = str(f.relative_to(BACKEND_DIR))
                        self.files_content[rel_path] = content
                        try:
                            self.files_ast[rel_path] = ast.parse(content)
                        except SyntaxError:
                            pass
                    except Exception as e:
                        self.issues.append(AuditIssue(
                            "LOW", "TOOLING", str(f.relative_to(BACKEND_DIR)), 0,
                            f"Nao foi possivel ler arquivo: {e}"
                        ))

    # ==================== ANALISE DE PERFORMANCE ====================

    def audit_database_queries(self):
        """Analisa padroes de queries no CRUD"""
        crud_content = self.files_content.get("app/database/crud.py", "")
        if not crud_content:
            return

        lines = crud_content.split("\n")

        # Verificar N+1 queries em loops
        in_loop = False
        loop_indent = 0
        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Detectar inicio de loop for/async for
            if re.search(r"^\s*(?:async\s+)?for\s+\w+\s+in\s+", line):
                in_loop = True
                loop_indent = len(line) - len(line.lstrip())
                continue

            # Detectar sess.execute dentro de loops
            if in_loop and ("session.execute" in line or "session.scalars" in line):
                if len(line) - len(line.lstrip()) > loop_indent:
                    # Esta dentro do loop
                    self.issues.append(AuditIssue(
                        "HIGH", "PERFORMANCE", "app/database/crud.py", i,
                        "Possivel N+1 query: sess.execute/scalars dentro de loop for",
                        "Considere usar bulk operations (pg_insert com multiple values) ou IN clauses"
                    ))

            # Detectar fim do loop
            if in_loop and stripped and not line.startswith(" ") and not line.startswith("\t"):
                in_loop = False

        # Analisar search_catalog - verificar complexidade da query
        search_catalog_match = re.search(
            r"async def search_catalog.*?(?=\n\S)", crud_content, re.DOTALL | re.MULTILINE
        )
        if search_catalog_match:
            func_body = search_catalog_match.group()
            ilike_count = func_body.count(".ilike(")
            if ilike_count >= 3:
                self.issues.append(AuditIssue(
                    "MEDIUM", "PERFORMANCE", "app/database/crud.py", 0,
                    f"search_catalog usa {ilike_count} clausulas ILIKE para busca de texto",
                    "Considere criar indice GIN com to_tsvector para busca full-text em titulo/description/skills"
                ))

            if "query.subquery()" in func_body or "subquery()" in func_body:
                self.issues.append(AuditIssue(
                    "MEDIUM", "PERFORMANCE", "app/database/crud.py", 0,
                    "search_catalog usa subquery para COUNT antes de paginacao",
                    "Para catalogos grandes, considere COUNT(*) com indice ou estimativa com pg_class.reltuples"
                ))

        # Verificar upsert_catalog_row - complexidade
        upsert_match = re.search(
            r"async def upsert_catalog_row.*?(?=\nasync def|\ndef |\nclass |\n#)", 
            crud_content, re.DOTALL | re.MULTILINE
        )
        if upsert_match:
            func_body = upsert_match.group()
            if "returning(" in func_body:
                self.issues.append(AuditIssue(
                    "LOW", "PERFORMANCE", "app/database/crud.py", 0,
                    "upsert_catalog_row usa RETURNING para verificar proposals_delta",
                    "O RETURNING e necessario aqui para o calculo, mas significa uma busca extra. Avalie se pode ser simplificado."
                ))

        # Verificar batch creation - multiplas queries
        batch_match = re.search(
            r"async def create_proposal_batch.*?(?=\nasync def|\ndef |\nclass |\n#)", 
            crud_content, re.DOTALL | re.MULTILINE
        )
        if batch_match:
            func_body = batch_match.group()
            execute_count = func_body.count("session.execute")
            if execute_count >= 3:
                self.issues.append(AuditIssue(
                    "MEDIUM", "PERFORMANCE", "app/database/crud.py", 0,
                    f"create_proposal_batch faz {execute_count} chamadas session.execute separadas",
                    "Algumas queries poderiam ser combinadas ou movidas para uma unica transacao com CTEs"
                ))

    def audit_indexes(self):
        """Verifica se colunas chave tem indices adequados"""
        models_content = self.files_content.get("app/database/models.py", "")
        if not models_content:
            return

        searchable_cols = [
            ("ProjectCatalog", "title"),
            ("ProjectCatalog", "description"), 
            ("ProjectCatalog", "skills"),
            ("ProjectCatalog", "category"),
            ("ProjectCatalog", "workana_id"),
            ("ProjectCatalog", "status"),
            ("ProjectCatalog", "estimated_published_at"),
            ("ProjectCatalog", "budget_min"),
            ("ProjectCatalog", "budget_max"),
            ("UserProjectState", "user_id"),
            ("UserProjectState", "workana_id"),
            ("ProposalHistory", "user_id"),
            ("ProposalHistory", "sent_at"),
            ("ProposalBatch", "user_id"),
            ("ProposalBatch", "status"),
            ("Credentials", "user_id"),
            ("SavedFilter", "user_id"),
            ("AutomationConfig", "user_id"),
        ]

        for table, col in searchable_cols:
            table_upper = table.upper()
            col_pattern = rf"Index.*?\({table_upper}\.|\({table}\.|unique|UniqueConstraint|PrimaryKeyConstraint"
            
            has_index = False
            # Verificar se existe Index explicito
            if re.search(rf"Index\(.*?" + re.escape(col) + r".*?\)", models_content, re.IGNORECASE):
                has_index = True
            # Verificar se e pk
            if re.search(rf"{col}.*?(?:primary_key|PrimaryKeyConstraint)", models_content, re.IGNORECASE):
                has_index = True
            # Verificar se faz parte de unique constraint
            if "user_id" in col and "UUID" in models_content:
                # user_id UUID geralmente ja tem index
                pass
            
            if not has_index and table == "ProjectCatalog":
                # Para ProjectCatalog, verificar se os campos de busca frequente tem index
                if col in ("title", "description", "skills"):
                    self.issues.append(AuditIssue(
                        "MEDIUM", "PERFORMANCE", "app/database/models.py", 0,
                        f"Coluna ProjectCatalog.{col} usada em busca ILIKE pode precisar de indice GIN",
                        "Criar indice GIN com to_tsvector para busca full-text"
                    ))
                elif col in ("workana_id", "status", "estimated_published_at", "budget_min", "budget_max", "category"):
                    self.issues.append(AuditIssue(
                        "LOW", "PERFORMANCE", "app/database/models.py", 0,
                        f"Coluna ProjectCatalog.{col} pode precisar de indice B-tree para ordenacao/filtro",
                        f"Adicionar Index('projects_catalog_{col}_idx', ProjectCatalog.{col})"
                    ))

    def audit_connection_pool(self):
        """Analisa configuracao do pool de conexoes"""
        models_content = self.files_content.get("app/database/models.py", "")

        pool_size_match = re.search(r"pool_size\s*:\s*(\d+)", models_content)
        if pool_size_match:
            pool_size = int(pool_size_match.group(1))
            if pool_size < 5:
                self.issues.append(AuditIssue(
                    "MEDIUM", "PERFORMANCE", "app/database/models.py", 0,
                    f"pool_size={pool_size} pode ser muito pequeno para producao",
                    "Para producao com multiplas instancias, considerar pool_size=20-50 dependendo da carga"
                ))
            elif pool_size > 100:
                self.issues.append(AuditIssue(
                    "LOW", "PERFORMANCE", "app/database/models.py", 0,
                    f"pool_size={pool_size} e grande demais e pode causar consumo excessivo de memoria",
                    "Ajustar para valor adequado a capacidade do banco (Supabase pool limit e 60 conexoes)"
                ))

        recycle_match = re.search(r"pool_recycle\s*:\s*(\d+)", models_content)
        if recycle_match:
            recycle = int(recycle_match.group(1))
            if recycle < 60:
                self.issues.append(AuditIssue(
                    "LOW", "PERFORMANCE", "app/database/models.py", 0,
                    f"pool_recycle={recycle}s e muito frequente, pode causar reconexoes desnecessarias",
                    "Valores tipicos: 1800 (30min) para Supabase, que tem timeout de 30min"
                ))

    # ==================== ANALISE DE SEGURANCA ====================

    def audit_security(self):
        """Analisa questoes de seguranca"""
        auth_content = self.files_content.get("app/auth.py", "")
        if not auth_content:
            return

        if "mock-token" in auth_content:
            self.issues.append(AuditIssue(
                "HIGH", "SECURITY", "app/auth.py", 0,
                "Auth permite token mock ('mock-token') quando debug=True e sem Supabase configurado",
                "Garantir que debug=False em producao. Adicionar verificacao explicita de ambiente."
            ))

        main_content = self.files_content.get("app/main.py", "")
        if main_content and "allow_credentials=False" in main_content:
            self.issues.append(AuditIssue(
                "LOW", "SECURITY", "app/main.py", 0,
                "CORS configurado com allow_credentials=False",
                "Isso e correto para autenticacao via Bearer header. Se usar cookies, precisa de True."
            ))

        config_content = self.files_content.get("app/config.py", "")
        if config_content:
            if "insecure_secret" in config_content.lower() or "dev-secret" in config_content.lower():
                self.issues.append(AuditIssue(
                    "MEDIUM", "SECURITY", "app/config.py", 0,
                    "Configuracao tem fallback para valores inseguros em dev",
                    "Valores padrao conhecidos sao usados quando nao configurados - OK para dev, mas validar producao"
                ))

    # ==================== ANALISE DE BUG E QUALIDADE ====================

    def audit_code_quality(self):
        """Analisa problemas de codigo, duplicacao, inconsistentes"""
        crud_content = self.files_content.get("app/database/crud.py", "")

        if "_serialize_catalog_row" in crud_content:
            call_count = crud_content.count("_serialize_catalog_row(")
            if call_count == 0:
                self.issues.append(AuditIssue(
                    "LOW", "CODE_QUALITY", "app/database/crud.py", 0,
                    "Funcao _serialize_catalog_row existe mas pode nao estar sendo usada",
                    "Verificar se a funcao e chamada em algum lugar ou remover se morta"
                ))

        if "user_id: Any" in crud_content:
            any_count = crud_content.count("user_id: Any")
            if any_count > 5:
                self.issues.append(AuditIssue(
                    "LOW", "CODE_QUALITY", "app/database/crud.py", 0,
                    f"{any_count} funcoes usam 'user_id: Any' em vez de UUID tipado",
                    "Considerar usar 'user_id: UUID' ou 'user_id: str' com validacao para melhor type safety"
                ))

        ast_data = self.files_ast.get("app/database/crud.py")
        if ast_data:
            for node in ast.walk(ast_data):
                if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                    has_docstring = ast.get_docstring(node) is not None
                    if not has_docstring and not node.name.startswith("_"):
                        if len(node.name) > 3:
                            self.issues.append(AuditIssue(
                                "LOW", "CODE_QUALITY", "app/database/crud.py", node.lineno,
                                f"Funcao '{node.name}' sem docstring",
                                "Adicionar docstring explicando parametros e retorno"
                            ))

        # Verificar duplicacao de serializacao
        if "_serialize_catalog_row" in crud_content:
            serialization_pattern = r'"workana_id":\s*cat\.workana_id.*?"is_hidden":\s*state\.is_hidden'
            matches = list(re.finditer(serialization_pattern, crud_content, re.DOTALL))
            if len(matches) >= 2:
                self.issues.append(AuditIssue(
                    "MEDIUM", "CODE_QUALITY", "app/database/crud.py", 0,
                    "Codigo de serializacao de projeto esta duplicado (inline em search_catalog + funcao _serialize_catalog_row)",
                    "Usar _serialize_catalog_row em todos os lugares ou remover a funcao e manter inline"
                ))

    def audit_consistency(self):
        """Verifica inconsistentes entre arquivos"""
        schemas_content = self.files_content.get("app/api/schemas.py", "")
        crud_content = self.files_content.get("app/database/crud.py", "")
        routers_content = self.files_content.get("app/api/routers/projects.py", "")

        if schemas_content and crud_content:
            if "ProposalBatchModel" in crud_content and "ProposalBatch" not in schemas_content:
                self.issues.append(AuditIssue(
                    "MEDIUM", "ARCHITECTURE", "app/api/schemas.py", 0,
                    "ProposalBatchModel existe no DB mas ProposalBatch schema nao existe ou nao e usada nos routers",
                    "Criar schemas ProposalBatch, ProposalBatchItem e ProposalBatchList para consistentes com os novos endpoints"
                ))

            if routers_content:
                if "response_model=List[dict]" in routers_content:
                    self.issues.append(AuditIssue(
                        "MEDIUM", "CODE_QUALITY", "app/api/routers/projects.py", 0,
                        "Endpoints de batches retornam 'List[dict]' em vez de schemas tipados",
                        "Criar response models para batches para melhor documentacao OpenAPI e validacao"
                    ))

    # ==================== ANALISE DE TESTES ====================

    def audit_tests(self):
        """Analisa cobertura e qualidade dos testes existentes"""
        tests_dir = BACKEND_DIR / "tests"
        if not tests_dir.exists():
            self.issues.append(AuditIssue(
                "HIGH", "TEST", "tests/", 0,
                "Diretório de testes existe mas nao foi analisado profundamente",
                "Verificar se os testes cobrem os novos endpoints de batches e analise"
            ))
            return

        test_files = list(tests_dir.glob("test_*.py"))
        test_names = [f.stem for f in test_files]

        expected_tests = [
            "test_batch_creation",
            "test_proposal_batch", 
            "test_batch_processor",
            "test_analyze_projects",
            "test_catalog_analysis",
        ]

        for expected in expected_tests:
            if expected not in test_names:
                related = [t for t in test_names if any(kw in t for kw in expected.split("_"))]
                if not related:
                    self.issues.append(AuditIssue(
                        "HIGH", "TEST", "tests/", 0,
                        f"Falta teste para: {expected.replace('_', ' ')}",
                        f"Criar tests/{expected}.py com testes para o novo endpoint/functionality"
                    ))

        conftest = tests_dir / "conftest.py"
        if conftest.exists():
            content = conftest.read_text()
            if "mock_user" not in content.lower() and "fake_user" not in content.lower():
                self.issues.append(AuditIssue(
                    "MEDIUM", "TEST", "tests/conftest.py", 0,
                    "conftest.py pode nao ter fixtures de usuario mock para testes",
                    "Adicionar fixture de usuario fake para testes que exigem user_id"
                ))

        integration_tests = [t for t in test_names if "api" in t.lower() or "integration" in t.lower()]
        if not integration_tests:
            self.issues.append(AuditIssue(
                "MEDIUM", "TEST", "tests/", 0,
                "Nao ha testes de integracao de API (test_api.py existe mas pode ser unitario)",
                "Adicionar testes que verifiquem os endpoints reais com TestClient"
            ))

    # ==================== ANALISE DE ARQUITETURA ====================

    def audit_architecture(self):
        """Analisa padroes arquiteturais e separacao de responsabilidades"""
        routers_dir = BACKEND_DIR / "app" / "api" / "routers"
        
        if routers_dir.exists():
            router_files = list(routers_dir.glob("*.py"))
            for rf in router_files:
                if rf.name == "__init__.py":
                    continue
                content = rf.read_text()
                
                if "from app.services." in content and "crud" not in content:
                    if "scorer" in content:
                        self.issues.append(AuditIssue(
                            "LOW", "ARCHITECTURE", f"app/api/routers/{rf.name}", 0,
                            f"{rf.name} importa diretamente de app.services.scorer",
                            "O scoring e uma operacao de negocio - OK que o router use. Mas garantir que nao tenha logica de negocio no router."
                        ))

                if "async def" in content:
                    funcs = re.findall(r"async def (\w+)", content)
                    for func in funcs:
                        if func not in [
                            "list_catalog", "analyze_projects", "create_proposal_batch",
                            "get_proposal_batches", "get_batch_items", "start_batch",
                            "bulk_project_state", "set_project_state",
                            "update_catalog_notes", "search_projects",
                            "get_automation_status", "get_automation_config",
                            "update_automation_config", "get_credentials_status",
                            "update_credentials", "list_templates", "create_template",
                            "update_template", "delete_template", "duplicate_system_template",
                            "test_blueprint", "get_antiban_status", "get_antiban_config",
                            "update_antiban_config", "can_search", "refresh_catalog",
                            "get_dashboard_stats", "get_proposal_history",
                            "update_proposal_status", "list_activity_logs", "create_log",
                            "get_profile_metrics", "sync_profile_metrics", "get_profile_config",
                            "update_profile_config", "get_profile_history", "validate_profile_url",
                            "get_saved_filters", "create_filter", "delete_filter",
                            "get_project_details", "get_saved_project", "save_project",
                            "toggle_favorite", "mark_as_applied", "ignore_project",
                            "update_notes", "generate_proposal", "submit_proposal",
                        ]:
                            self.issues.append(AuditIssue(
                                "LOW", "ARCHITECTURE", f"app/api/routers/{rf.name}", 0,
                                f"Funcao '{func}' no router pode conter logica que deveria estar no service layer",
                                "Verificar se a funcao apenas delega para CRUD/Service ou contem logica de negocio"
                            ))

    # ==================== EXECUCAO ====================

    def run_audit(self):
        """Executa todas as auditorias"""
        print("🔍 Carregando arquivos para auditoria...")
        self.load_files([
            "app/database/crud.py",
            "app/database/models.py", 
            "app/api/schemas.py",
            "app/api/routers/*.py",
            "app/main.py",
            "app/auth.py",
            "app/config.py",
            "tests/*.py",
        ])
        print(f"   {len(self.files_content)} arquivos carregados")

        print("\n📊 Analisando desempenho de queries e indices...")
        self.audit_database_queries()
        self.audit_indexes()
        self.audit_connection_pool()

        print("🔒 Analisando seguranca...")
        self.audit_security()

        print("🐛 Analisando bugs e qualidade de codigo...")
        self.audit_code_quality()
        self.audit_consistency()

        print("🧪 Analisando cobertura de testes...")
        self.audit_tests()

        print("🏗️ Analisando arquitetura...")
        self.audit_architecture()

        return self.issues

    def print_report(self, issues):
        """Imprime relatorio formatado"""
        print("\n" + "=" * 80)
        print("📋 RELATORIO DE AUDITORIA - WORKANA ACCELERATOR BACKEND")
        print("=" * 80)

        severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        categories = list(set(i.category for i in issues))

        print("\n📈 RESUMO EXECUTIVO")
        print("-" * 40)
        total = len(issues)
        print(f"Total de issues encontradas: {total}")
        print()

        for sev in severities:
            count = len([i for i in issues if i.severity == sev])
            icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
            if count > 0:
                print(f"  {icon[sev]} {sev}: {count}")

        print()
        print("Por categoria:")
        for cat in sorted(categories):
            count = len([i for i in issues if i.category == cat])
            print(f"  • {cat}: {count}")

        print("\n" + "=" * 80)
        print("🔴 ISSUES CRITICAS E ALTAS")
        print("=" * 80)

        critical_high = [i for i in issues if i.severity in ("CRITICAL", "HIGH")]
        if critical_high:
            for issue in sorted(critical_high, key=lambda x: (severities.index(x.severity), x.file)):
                print(f"\n{issue}")
        else:
            print("\n✅ Nenhuma issue critica ou alta encontrada.")

        print("\n" + "=" * 80)
        print("🟡 ISSUES MEDIAS")
        print("=" * 80)

        medium = [i for i in issues if i.severity == "MEDIUM"]
        if medium:
            for issue in sorted(medium, key=lambda x: x.file):
                print(f"\n{issue}")
        else:
            print("\n✅ Nenhuma issue media encontrada.")

        print("\n" + "=" * 80)
        print("🟢 ISSUES BAIXAS E SUGESTOES")
        print("=" * 80)

        low = [i for i in issues if i.severity == "LOW"]
        if low:
            for issue in sorted(low, key=lambda x: x.file):
                print(f"\n{issue}")
        else:
            print("\n✅ Nenhuma issue baixa encontrada.")

        print("\n" + "=" * 80)
        print("📊 ANALISE DE COBERTURA DE TESTES")
        print("=" * 80)

        tests_dir = BACKEND_DIR / "tests"
        if tests_dir.exists():
            test_files = list(tests_dir.glob("test_*.py"))
            print(f"\nArquivos de teste encontrados: {len(test_files)}")
            for tf in sorted(test_files):
                lines = tf.read_text().count("\n")
                print(f"  • {tf.name}: ~{lines} linhas")

        print("\n" + "=" * 80)
        print("✅ RECOMENDACOES PRIORITARIAS")
        print("=" * 80)

        recommendations = []
        for issue in issues:
            if issue.severity in ("CRITICAL", "HIGH") and issue.recommendation:
                recommendations.append(f"[{issue.severity}] {issue.file}: {issue.recommendation}")

        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. {rec}")
        else:
            print("\n✅ Nenhuma acao critica necessaria.")

        return issues


def main():
    print("🚀 Iniciando auditoria do backend Workana Accelerator...\n")

    auditor = BackendAuditor()
    issues = auditor.run_audit()
    auditor.print_report(issues)

    critical_count = len([i for i in issues if i.severity == "CRITICAL"])
    if critical_count > 0:
        print(f"\n⚠️  {critical_count} issue(s) critica(s) encontrada(s). Acao imediata recomendada.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
