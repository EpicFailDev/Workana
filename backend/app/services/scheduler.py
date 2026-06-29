import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.database.models import async_session, SavedFilter as SavedFilterModel
from app.database import crud
from app.api.schemas import SearchFilters, Project
from app.automation.browser import automation_instance as automation
from app.automation.antiban import antiban
from app.services.scorer import ProjectScorer
from app.services.notification import NotificationService

class SearchScheduler:
    """
    Serviço de agendamento de busca utilizando APScheduler.
    Executa periodicamente buscas por filtros salvos de todos os usuários,
    respeitando a janela anti-ban, pontuando relevância e enviando notificações.
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_started = False

    def start(self):
        """Inicia o agendador."""
        if self.is_started:
            return
        
        # Adicionar o job de busca periódica (roda a cada 30 minutos)
        # O usuário pode configurar ou desabilitar no .env / settings se preferir
        self.scheduler.add_job(
            self.execute_scheduled_search,
            "interval",
            minutes=30,
            id="periodic_workana_search",
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_started = True
        logger.info("⏰ Scheduler de busca Workana inicializado com sucesso! (Frequência: 30 min)")

    def stop(self):
        """Para o agendador."""
        if not self.is_started:
            return
        self.scheduler.shutdown()
        self.is_started = False
        logger.info("👋 Scheduler de busca Workana desligado.")

    async def execute_scheduled_search(self):
        """Busca projetos de todos os usuários com base em seus filtros salvos."""
        logger.info("🔍 Iniciando busca agendada periódica...")
        
        # 1. Obter todos os filtros salvos do banco
        async with async_session() as session:
            result = await session.execute(select(SavedFilterModel))
            saved_filters = result.scalars().all()
            
        if not saved_filters:
            logger.info("Sem filtros salvos cadastrados no sistema. Nenhuma busca executada.")
            return

        # Agrupar filtros por usuário para fazer as verificações de anti-ban apenas uma vez por usuário
        filters_by_user: Dict[str, List[SavedFilterModel]] = {}
        for f in saved_filters:
            uid_str = str(f.user_id)
            if uid_str not in filters_by_user:
                filters_by_user[uid_str] = []
            filters_by_user[uid_str].append(f)

        for user_id_str, user_filters in filters_by_user.items():
            # 2. Respeitar limites do Anti-Ban por usuário
            # 2.1 Horário de operação (8h - 22h por padrão)
            if not antiban.is_within_working_hours():
                logger.info(f"Horário de operação anti-ban ativo ({antiban.config.working_hours_start}h-{antiban.config.working_hours_end}h). Busca suspensa para todos.")
                break
                
            # 2.2 Limites de buscas por hora
            can_do, message = await antiban.can_search(user_id_str)
            if not can_do:
                logger.warning(f"Busca suspensa para o usuário {user_id_str} por regras de anti-ban: {message}")
                continue

            logger.info(f"👤 Executando buscas para o usuário {user_id_str} ({len(user_filters)} filtros)")
            
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
                    logger.info(f"Buscando com filtro '{saved_filter.name}': {filters_obj.keywords or 'sem palavra-chave'}")
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
                            
                            logger.info(f"✨ Novo projeto: {proj.title} (Relevância: {score:.1f} pts)")
                            
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
                                    logger.info(f"🤖 Auto-Apply ativo para o usuário {user_id_str}. Iniciando processo...")
                                    
                                    # Verificar se atingiu limite diário de propostas
                                    daily_stats = await crud.get_daily_stats(user_id_str)
                                    proposals_today = daily_stats.get("proposals_today", 0)
                                    max_allowed = user_config.get("max_proposals_per_day") or 10
                                    
                                    if proposals_today >= max_allowed:
                                        logger.warning(f"Auto-Apply abortado: Limite diário de propostas atingido ({proposals_today}/{max_allowed})")
                                    else:
                                        # 1. Gerar proposta usando o proposal_agent
                                        from app.services.proposal_agent import proposal_agent_instance
                                        project_dict_for_agent = {
                                            "title": proj.title,
                                            "description": proj.description,
                                            "skills": proj.skills,
                                            "budget": proj.budget
                                        }
                                        
                                        logger.info(f"🤖 Gerando proposta por IA para o projeto: {proj.title}")
                                        gen_result = await proposal_agent_instance.generate_proposal(
                                            user_id_str, project_dict_for_agent
                                        )
                                        
                                        if gen_result.get("success") and gen_result.get("proposal"):
                                            proposal_text = gen_result.get("proposal", "")
                                            suggested_price_str = gen_result.get("suggested_price", proj.budget or "R$ 100")
                                            
                                            # Tentar extrair preço numérico
                                            import re
                                            price_clean = suggested_price_str.replace('.', '').replace(',', '.')
                                            price_match = re.search(r'[\d.]+', price_clean)
                                            budget_val = float(price_match.group()) if price_match else (proj.budget_min or 100.0)
                                            
                                            # Instanciar ProposalSubmit
                                            from app.api.schemas import ProposalSubmit
                                            submit_data = ProposalSubmit(
                                                project_id=proj.id,
                                                template_id=user_config.get("preferred_template_id"),
                                                custom_message=proposal_text,
                                                budget=budget_val,
                                                deadline_days=7  # Padrão
                                            )
                                            
                                            # 2. Enviar proposta de fato usando a automação
                                            logger.info(f"🤖 Enviando proposta automática para o projeto: {proj.title}...")
                                            apply_result = await automation.submit_proposal(user_id_str, submit_data)
                                            if apply_result.success:
                                                logger.success(f"🤖 Auto-Apply bem sucedido para o projeto: {proj.title}")
                                            else:
                                                logger.error(f"🤖 Auto-Apply falhou: {apply_result.message}")
                                        else:
                                            logger.warning(f"🤖 Falha ao gerar proposta automática para: {proj.title}")
                            except Exception as auto_apply_err:
                                logger.error(f"Erro no Auto-Apply do agendador: {auto_apply_err}")
                            
                    logger.info(f"✓ Filtro '{saved_filter.name}' processado. {new_projects_count} novos projetos encontrados.")
                    
                except Exception as ex:
                    logger.error(f"Erro ao executar busca para filtro {saved_filter.name}: {ex}")
                
                # Jitter/Delay anti-ban entre os filtros do mesmo usuário
                import random
                random_delay = random.uniform(3.0, 7.0) + (5.0 if new_projects_count > 0 else 0.0)
                await asyncio.sleep(random_delay)

        logger.info("🔍 Fim do ciclo de busca agendada periódica.")

# Instância global do agendador
scheduler_instance = SearchScheduler()
