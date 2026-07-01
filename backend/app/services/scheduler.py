import asyncio
import random
import time
from datetime import datetime, timezone
from typing import List, Dict, Any
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, text

from app.database.models import async_session, SavedFilter as SavedFilterModel
from app.database import crud
from app.api.schemas import SearchFilters, Project
from app.automation.browser import automation_instance as automation
from app.automation.antiban import antiban
from app.services.scorer import ProjectScorer
from app.services.notification import NotificationService
from app.observability.context import new_operation_id, operation_id_var
from app.observability.privacy import pseudonymize, sanitize_exception
from app.config import settings

class SearchScheduler:
    """
    Serviço de agendamento de busca utilizando APScheduler.
    Executa periodicamente buscas por filtros salvos de todos os usuários,
    respeitando a janela anti-ban, pontuando relevância e enviando notificações.
    """
    
    def __init__(self):
        import os
        from pytz import timezone as pytz_timezone
        tz_name = os.getenv("TZ", "America/Cuiaba")
        try:
            tz = pytz_timezone(tz_name)
        except Exception:
            tz = pytz_timezone("America/Cuiaba")
        self.scheduler = AsyncIOScheduler(timezone=tz)
        self.is_started = False

    def start(self):
        """Inicia o agendador."""
        if self.is_started:
            return

        # Job legado: busca por filtros de cada usuário (roda a cada 30 minutos)
        self.scheduler.add_job(
            self.execute_scheduled_search,
            "interval",
            minutes=30,
            id="periodic_workana_search",
            replace_existing=True
        )

        # Job de catálogo: upsert do catálogo compartilhado (roda a cada 15 minutos)
        self.scheduler.add_job(
            self.execute_catalog_upsert,
            "interval",
            minutes=15,
            id="catalog_upsert",
            replace_existing=True
        )

        self.scheduler.start()
        self.is_started = True
        logger.bind(event="scheduler.started").info(
            "Scheduler inicializado (busca legada: 30 min, catálogo: 15 min)."
        )

    def stop(self):
        """Para o agendador."""
        if not self.is_started:
            return
        self.scheduler.shutdown()
        self.is_started = False
        logger.bind(event="scheduler.stopped").info("Scheduler de busca Workana desligado.")

    async def execute_scheduled_search(self):
        """Busca projetos de todos os usuários com base em seus filtros salvos."""
        from sqlalchemy import text
        from uuid import UUID
        from app.database.models import current_user_id

        # Adquirir lock consultivo (advisory lock) no Postgres para impedir execuções simultâneas
        lock_id = 742189  # ID único arbitrário
        
        async with async_session() as lock_session:
            lock_res = await lock_session.execute(
                text("SELECT pg_try_advisory_lock(:lock_id)"),
                {"lock_id": lock_id}
            )
            acquired = lock_res.scalar()
            
            if not acquired:
                logger.bind(event="scheduler.lock.busy").warning(
                    "Outra instância do worker já está executando execute_scheduled_search. Abortando execução concorrente."
                )
                return

            try:
                logger.bind(event="scheduler.cycle.started").info(
                    "Lock de exclusão mútua adquirido. Iniciando busca agendada periódica."
                )

                # operation_id de correlação para todo este ciclo (presente em todos os logs do ciclo).
                op_token = operation_id_var.set(new_operation_id())

                # 1. Obter todos os filtros salvos do banco
                async with async_session() as session:
                    result = await session.execute(select(SavedFilterModel))
                    saved_filters = result.scalars().all()

                if not saved_filters:
                    logger.bind(event="scheduler.cycle.no_filters").info(
                        "Sem filtros salvos cadastrados no sistema. Nenhuma busca executada."
                    )
                    return

                # Agrupar filtros por usuário para fazer as verificações de anti-ban apenas uma vez por usuário
                filters_by_user: Dict[str, List[SavedFilterModel]] = {}
                for f in saved_filters:
                    uid_str = str(f.user_id)
                    if uid_str not in filters_by_user:
                        filters_by_user[uid_str] = []
                    filters_by_user[uid_str].append(f)

                for user_id_str, user_filters in filters_by_user.items():
                    # Definir o contexto do usuário atual na ContextVar para que as queries respeitem RLS
                    user_uuid = UUID(user_id_str)
                    token = current_user_id.set(user_uuid)

                    try:
                        # 2. Respeitar limites do Anti-Ban por usuário
                        # 2.1 Horário de operação (8h - 22h por padrão)
                        if not antiban.is_within_working_hours():
                            logger.bind(event="scheduler.cycle.outside_hours").info(
                                f"Horário de operação anti-ban ativo ({antiban.config.working_hours_start}h-{antiban.config.working_hours_end}h). Busca suspensa para todos."
                            )
                            break

                        # 2.2 Limites de buscas por hora
                        can_do, message = await antiban.can_search(user_id_str)
                        if not can_do:
                            logger.bind(event="scheduler.user.rate_limited").warning(
                                f"Busca suspensa para o usuário {pseudonymize(user_id_str)} por regras de anti-ban: {message}"
                            )
                            continue

                        logger.bind(event="scheduler.user.searching").info(
                            f"Executando buscas para o usuário {pseudonymize(user_id_str)} ({len(user_filters)} filtros)"
                        )

                        for saved_filter in user_filters:
                            try:
                                # Carregar filtros de pesquisa
                                filter_data = saved_filter.filters_json

                                # Converter JSON para objeto SearchFilters
                                # Tratar se vier string ou dict do banco
                                if isinstance(filter_data, str):
                                    import json
                                    filter_data = json.loads(filter_data)

                                # Forçar limite inteligente de resultados no background
                                filter_data["max_results"] = min(filter_data.get("max_results", 20), 50)
                                filter_data["pages_to_fetch"] = min(filter_data.get("pages_to_fetch", 1), 3)

                                filters_obj = SearchFilters(**filter_data)

                                # Realizar busca
                                logger.bind(event="scheduler.filter.searching").info(
                                    f"Buscando com filtro '{saved_filter.name}'."
                                )
                                found_projects = await automation.search_projects(filters_obj, user_id=user_id_str)

                                new_projects_count = 0
                                for proj in found_projects:
                                    # Tentar salvar no banco. Se retornar ID, verificar se é um novo registro
                                    project_dict = {
                                        "workana_id": proj.id,
                                        "title": proj.title,
                                        "description": proj.description,
                                        "url": proj.url,
                                        "category": filters_obj.category,
                                        "skills": proj.skills,
                                        "client_country": proj.client_country,
                                        "proposals_count": proj.proposals_count,
                                        "payment_verified": proj.payment_verified,
                                        "posted_at": proj.posted_at,
                                        # Adicionar budget extraído
                                        "budget_min": proj.budget_min,
                                        "budget_max": proj.budget_max
                                    }

                                    # Extrair orçamentos min/max do texto se não definidos
                                    if proj.budget and not (proj.budget_min or proj.budget_max):
                                        from app.services.currency import CurrencyService
                                        min_val, max_val = CurrencyService.parse_budget_string(proj.budget)
                                        project_dict["budget_min"] = min_val
                                        project_dict["budget_max"] = max_val

                                    # Verificar se já existe para este usuário antes de salvar
                                    async with async_session() as session:
                                        from app.database.models import Project as ProjectModel
                                        from sqlalchemy import and_
                                        res = await session.execute(
                                            select(ProjectModel).where(
                                                and_(ProjectModel.workana_id == proj.id, ProjectModel.user_id == user_id_str)
                                            )
                                        )
                                        is_new = res.scalar_one_or_none() is None

                                    if is_new:
                                        # Salvar projeto
                                        await crud.save_project(user_id_str, project_dict)
                                        new_projects_count += 1

                                        # Calcular score/relevância
                                        score = ProjectScorer.calculate_score(proj, filters_obj)

                                        logger.bind(event="scheduler.project.new").info(
                                            f"Novo projeto encontrado (relevância: {score:.1f} pts)."
                                        )

                                        # Disparar notificação
                                        await NotificationService.notify_new_project(
                                            user_id=user_id_str,
                                            project=proj,
                                            filter_name=saved_filter.name,
                                            score=score
                                        )

                                        # Pequeno delay entre notificações para evitar concorrência ou throttling das APIs externas
                                        await asyncio.sleep(1.0)

                                        # Verificação e execução de Auto-Apply
                                        try:
                                            user_config = await crud.get_automation_config(user_id_str)
                                            if user_config and user_config.get("auto_apply"):
                                                logger.bind(event="scheduler.auto_apply.start").info(
                                                    f"Auto-Apply ativo para o usuário {pseudonymize(user_id_str)}. Iniciando processo."
                                                )

                                                # Verificar se atingiu limite diário de propostas
                                                daily_stats = await crud.get_daily_stats(user_id_str)
                                                proposals_today = daily_stats.get("proposals_today", 0)
                                                max_allowed = user_config.get("max_proposals_per_day") or 10

                                                if proposals_today >= max_allowed:
                                                    logger.bind(event="scheduler.auto_apply.daily_limit").warning(
                                                        f"Auto-Apply abortado: limite diário de propostas atingido ({proposals_today}/{max_allowed})."
                                                    )
                                                else:
                                                    # 1. Gerar proposta usando o proposal_agent
                                                    from app.services.proposal_agent import proposal_agent_instance
                                                    project_dict_for_agent = {
                                                        "title": proj.title,
                                                        "description": proj.description,
                                                        "skills": proj.skills,
                                                        "budget": proj.budget
                                                    }

                                                    logger.bind(event="scheduler.auto_apply.generating").info(
                                                        "Gerando proposta por IA."
                                                    )
                                                    preferred_template_id = user_config.get("preferred_template_id")
                                                    template = None
                                                    if preferred_template_id:
                                                        template = await crud.get_template(user_id_str, preferred_template_id)
                                                    if not template:
                                                        template = await crud.get_preferred_or_default_template(user_id_str)
                                                        
                                                    actual_template_id = template.id if template else None

                                                    gen_result = await proposal_agent_instance.generate_proposal(
                                                        user_id_str, project_dict_for_agent, template_id=actual_template_id
                                                    )

                                                    if gen_result.get("success") and gen_result.get("proposal"):
                                                        if gen_result.get("template_id_used"):
                                                            actual_template_id = gen_result.get("template_id_used")
                                                        proposal_text = gen_result.get("proposal", "")
                                                        
                                                        # Determinar Preço (Precedência: valor do template, sugestão da IA, fallback)
                                                        budget_val = None
                                                        if template and template.default_budget and template.default_budget > 0:
                                                            budget_val = template.default_budget
                                                        else:
                                                            suggested_price_str = gen_result.get("suggested_price", proj.budget or "R$ 100")
                                                            import re
                                                            price_clean = suggested_price_str.replace('.', '').replace(',', '.')
                                                            price_match = re.search(r'[\d.]+', price_clean)
                                                            budget_val = float(price_match.group()) if price_match else (proj.budget_min or 100.0)
                                                            
                                                        # Determinar Prazo (Precedência: valor do template, fallback)
                                                        deadline_val = 7
                                                        if template and template.default_deadline_days and template.default_deadline_days > 0:
                                                            deadline_val = template.default_deadline_days

                                                        # Instanciar ProposalSubmit
                                                        from app.api.schemas import ProposalSubmit
                                                        submit_data = ProposalSubmit(
                                                            project_id=proj.id,
                                                            template_id=actual_template_id,
                                                            custom_message=proposal_text,
                                                            budget=budget_val,
                                                            deadline_days=deadline_val
                                                        )

                                                        # 2. Enviar proposta de fato usando a automação
                                                        logger.bind(event="scheduler.auto_apply.submitting").info(
                                                            "Enviando proposta automática."
                                                        )
                                                        apply_result = await automation.submit_proposal(user_id_str, submit_data)
                                                        if apply_result.success:
                                                            logger.bind(event="scheduler.auto_apply.success").success(
                                                                "Auto-Apply bem sucedido."
                                                            )
                                                        else:
                                                            logger.bind(event="scheduler.auto_apply.failed").error(
                                                                f"Auto-Apply falhou: {sanitize_exception(Exception(str(apply_result.message))) if apply_result.message else 'sem detalhe'}"
                                                            )
                                                    else:
                                                        logger.bind(event="scheduler.auto_apply.generation_failed").warning(
                                                            "Falha ao gerar proposta automática."
                                                        )
                                        except Exception as auto_apply_err:
                                            logger.bind(event="scheduler.auto_apply.error").exception(
                                                f"Erro no Auto-Apply do agendador: {sanitize_exception(auto_apply_err)}"
                                            )

                                logger.bind(event="scheduler.filter.completed").info(
                                    f"Filtro '{saved_filter.name}' processado. {new_projects_count} novos projetos encontrados."
                                )

                            except Exception as ex:
                                logger.bind(event="scheduler.filter.error").exception(
                                    f"Erro ao executar busca para filtro '{saved_filter.name}': {sanitize_exception(ex)}"
                                )

                            # Jitter/Delay anti-ban entre os filtros do mesmo usuário
                            import random
                            random_delay = random.uniform(3.0, 7.0) + (5.0 if new_projects_count > 0 else 0.0)
                            await asyncio.sleep(random_delay)

                    finally:
                        current_user_id.reset(token)

                logger.bind(event="scheduler.cycle.completed").info(
                    "Fim do ciclo de busca agendada periódica."
                )
            finally:
                # Limpa o operation_id do ciclo.
                try:
                    _obs_context.operation_id_var.reset(op_token)
                except ValueError:
                    pass

                # Liberar o lock consultivo (mesma conexão que adquiriu).
                # pg_try_advisory_lock é um session-level lock; o par correto é
                # pg_advisory_unlock (NÃO pg_release_lock, que não existe).
                try:
                    unlock_res = await lock_session.execute(
                        text("SELECT pg_advisory_unlock(:lock_id)"),
                        {"lock_id": lock_id}
                    )
                    released = unlock_res.scalar()
                    if released:
                        logger.bind(event="scheduler.lock.released").info(
                            "Lock de exclusão mútua liberado com sucesso."
                        )
                    else:
                        # False indica que a sessão não era dona do lock (já liberado ou nunca adquirido).
                        logger.bind(event="scheduler.lock.release_failed").warning(
                            "pg_advisory_unlock retornou false: o lock não pertencia a esta sessão."
                        )
                except Exception as e:
                    logger.bind(event="scheduler.lock.release_error").exception(
                        f"Erro ao liberar o lock no Postgres: {sanitize_exception(e)}"
                    )

    async def execute_catalog_upsert(self) -> Dict[str, Any]:
        """Executa um ciclo de coleta do catálogo: busca anônima + upsert + marca gone.

        Chamado pelo job agendado (15 min) ou manualmente via POST /automation/catalog/refresh.
        Retorna dict com estatísticas (upserted, marked_gone, errors).
        """
        from uuid import UUID
        from app.database.models import current_user_id

        catalog_lock_id = 742190  # lock distinto do legado (742189)
        tenant_token = current_user_id.set(None)

        try:
          async with async_session() as lock_session:
            lock_res = await lock_session.execute(
                text("SELECT pg_try_advisory_lock(:lock_id)"),
                {"lock_id": catalog_lock_id}
            )
            acquired = lock_res.scalar()

            if not acquired:
                logger.bind(event="catalog.lock.busy").warning(
                    "Outra instância já está executando a coleta do catálogo. Abortando."
                )
                raise RuntimeError("Catalog upsert already running — advisory lock not acquired.")

            try:
                op_token = operation_id_var.set(new_operation_id())
                upserted = 0
                errors = 0
                seen_ids: set[str] = set()
                cycle_started_at = datetime.now(timezone.utc)

                try:
                    # 1. Obter buscas agregadas de todos os filtros salvos
                    queries = await crud.get_distinct_saved_filter_queries()

                    if not queries:
                        logger.bind(event="catalog.cycle.no_filters").info(
                            "Sem filtros salvos. Usando busca ampla padrão."
                        )
                        queries = [{
                            "keywords": settings.catalog_default_keywords,
                            "category": settings.catalog_default_category,
                            "_metric_user_ids": [],
                        }]

                    queries = queries[:settings.catalog_max_searches_per_cycle]

                    logger.bind(event="catalog.cycle.started").info(
                        f"Coleta do catálogo iniciada ({len(queries)} buscas únicas)."
                    )

                    for filter_data in queries:
                        if upserted >= settings.catalog_max_projects_per_cycle:
                            break
                        metric_user_ids = filter_data.pop("_metric_user_ids", [])
                        started = time.perf_counter()
                        success = False
                        blocked = False
                        try:
                            # Limites conservadores para o worker de catálogo
                            remaining = settings.catalog_max_projects_per_cycle - upserted
                            filter_data["max_results"] = min(filter_data.get("max_results", 50), remaining)
                            filter_data["pages_to_fetch"] = min(
                                filter_data.get("pages_to_fetch", settings.catalog_pages_per_search),
                                settings.catalog_pages_per_search,
                            )
                            filters_obj = SearchFilters(**filter_data)

                            # Busca anônima (user_id=None — sem credenciais)
                            projects = []
                            last_error = None
                            for attempt in range(settings.catalog_search_retries):
                                try:
                                    projects = await automation.search_projects(filters_obj, user_id=None)
                                    success = True
                                    break
                                except Exception as exc:
                                    last_error = exc
                                    if attempt + 1 < settings.catalog_search_retries:
                                        await asyncio.sleep(random.uniform(1.0, 3.0) * (attempt + 1))
                            if not success and last_error:
                                raise last_error

                            projects = projects[:remaining]

                            for proj in projects:
                                # Mapear campos do modelo Project para o formato do catálogo
                                catalog_data = {
                                    "workana_id": proj.id,
                                    "title": proj.title,
                                    "description": proj.description,
                                    "url": proj.url,
                                    "category": proj.category,
                                    "subcategory": proj.subcategory,
                                    "budget_min": proj.budget_min,
                                    "budget_max": proj.budget_max,
                                    "budget_type": proj.project_type,
                                    "deadline": proj.deadline,
                                    "skills": proj.skills or [],
                                    "details": proj.details or {},
                                    "client_name": proj.client_name,
                                    "client_country": proj.client_country,
                                    "client_rating": proj.client_rating,
                                    "client_projects_posted": proj.client_projects_posted,
                                    "client_projects_paid": proj.client_projects_paid,
                                    "client_member_since": proj.client_member_since,
                                    "client_plan": proj.client_plan,
                                    "proposals_count": proj.proposals_count,
                                    "payment_verified": proj.payment_verified,
                                    "posted_at": proj.posted_at,
                                    "published_at": proj.published_at,
                                    "last_client_activity": proj.last_client_activity,
                                    "is_urgent": proj.is_urgent,
                                    "is_featured": proj.is_featured,
                                }

                                await crud.upsert_catalog_row(catalog_data)
                                seen_ids.add(proj.id)
                                upserted += 1

                            # Jitter anti-ban entre buscas
                            await asyncio.sleep(random.uniform(2.0, 5.0))

                        except Exception as ex:
                            errors += 1
                            blocked = bool(getattr(automation._fast_scraper, "was_blocked", False))
                            logger.bind(event="catalog.query.error").exception(
                                f"Erro na busca do catálogo: {sanitize_exception(ex)}"
                            )
                        finally:
                            duration_ms = int((time.perf_counter() - started) * 1000)
                            for metric_user_id in metric_user_ids:
                                metric_token = current_user_id.set(UUID(metric_user_id))
                                try:
                                    await crud.update_scraping_stats(
                                        metric_user_id, success, blocked, duration_ms
                                    )
                                except Exception as metric_error:
                                    logger.bind(event="catalog.metrics.error").warning(
                                        f"Falha ao registrar métrica: {sanitize_exception(metric_error)}"
                                    )
                                finally:
                                    current_user_id.reset(metric_token)

                    # 2. Marcar projetos ausentes como 'gone'
                    lifecycle = {"gone": 0, "closed": 0}
                    if errors == 0:
                        lifecycle = await crud.mark_gone_catalog_projects(
                            list(seen_ids),
                            cycle_started_at=cycle_started_at,
                            close_after_minutes=15 * settings.catalog_close_after_cycles,
                        )
                    marked_gone = lifecycle["gone"]

                    logger.bind(event="catalog.cycle.completed").info(
                        f"Catálogo atualizado: {upserted} upserted, {marked_gone} gone, {errors} errors."
                    )

                    return {
                        "success": True,
                        "message": f"Catálogo atualizado: {upserted} projetos, {marked_gone} removidos.",
                        "upserted": upserted,
                        "marked_gone": marked_gone,
                        "errors": errors,
                        "closed": lifecycle["closed"],
                    }

                finally:
                    operation_id_var.reset(op_token)

            finally:
                try:
                    await lock_session.execute(
                        text("SELECT pg_advisory_unlock(:lock_id)"),
                        {"lock_id": catalog_lock_id}
                    )
                except Exception:
                    pass
        finally:
            current_user_id.reset(tenant_token)


# Instância global do agendador
scheduler_instance = SearchScheduler()
