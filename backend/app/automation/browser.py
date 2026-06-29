
"""
Gerenciador de automação do Workana.
Usa busca paralela ANÔNIMA para evitar rastreamento.
"""
from typing import Optional, List
from loguru import logger

from app.config import settings
from app.api.schemas import SearchFilters, Project
from app.automation.components.parallel_scraper import AnonymousParallelScraper
from app.automation.components.fast_scraper import FastProjectScraper


class AutomationStatus:
    """Status da automação."""
    def __init__(self):
        self.is_running = False
        self.is_logged_in = False
        self.current_action = None
        self.proposals_sent_today = 0
        self.max_proposals_per_day = settings.max_proposals_per_day
        self.last_error = None


class WorkanaAutomation:
    """
    Classe principal para automação do Workana.
    Usa busca ANÔNIMA para evitar banimento.
    """
    
    def __init__(self):
        self._is_running: bool = False
        self._current_action: Optional[str] = None
        self._last_error: Optional[str] = None
        self._searches_today: int = 0
        self._parallel_scraper = AnonymousParallelScraper()
        self._fast_scraper = FastProjectScraper()

    def get_status(self):
        """Retorna o status atual da automação."""
        from app.api.schemas import AutomationStatus as StatusSchema
        return StatusSchema(
            is_running=self._is_running,
            is_logged_in=False,
            current_action=self._current_action,
            proposals_sent_today=self._searches_today,
            max_proposals_per_day=settings.max_proposals_per_day,
            last_error=self._last_error
        )

    async def search_projects(self, filters: SearchFilters, user_id: Optional[str] = None) -> List[Project]:
        """
        Busca projetos no Workana em múltiplas páginas simultaneamente.
        """
        from app.automation.antiban import antiban
        
        # Verificar limites do anti-ban antes de realizar a busca
        if user_id:
            can_do, message = await antiban.can_search(user_id)
            if not can_do:
                logger.warning(f"Busca cancelada por restrições do sistema Anti-Ban: {message}")
                self._last_error = f"Anti-Ban: {message}"
                return []

        scraper_type = settings.scraper_type
        self._current_action = f"Buscando {filters.pages_to_fetch} páginas ({scraper_type})..."
        self._is_running = True
        
        try:
            pages_to_fetch = filters.pages_to_fetch
            start_page = filters.page
            
            logger.info(f"🔒 Busca {scraper_type}: páginas {start_page}-{start_page + pages_to_fetch - 1}")
            
            projects = []
            used_fallback = False
            
            if scraper_type == "fast":
                projects = await self._fast_scraper.search_projects(filters, user_id=user_id)
                
                # Fallback se bloqueado pelo Cloudflare
                if (not projects or getattr(self._fast_scraper, "was_blocked", False)):
                    logger.warning("⚠️ Scraper Rápido bloqueado ou sem resultados. Iniciando fallback para Scraper Browser...")
                    used_fallback = True
                    self._current_action = "Fallback para browser (WAF)..."
                    projects = await self._parallel_scraper.search_projects_parallel(filters, user_id=user_id)
            else:
                projects = await self._parallel_scraper.search_projects_parallel(filters, user_id=user_id)
                
            if user_id:
                await antiban.register_search(user_id)
            self._searches_today += 1
            
            if projects:
                logger.success(f"✅ {len(projects)} projetos obtidos de {pages_to_fetch} páginas (fallback={used_fallback})")
            return projects or []
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Erro na busca: {e}")
            return []
        finally:
            self._is_running = False
            self._current_action = None

    async def get_project_details(self, project_id: str, user_id: Optional[str] = None) -> Optional[Project]:
        """Obtém detalhes de um projeto (também anônimo)."""
        self._current_action = f"Detalhes do projeto {project_id}..."
        try:
            scraper_type = settings.scraper_type
            if scraper_type == "fast":
                project = await self._fast_scraper.get_project_details(project_id, user_id=user_id)
                # Fallback se bloqueado
                if not project or getattr(self._fast_scraper, "was_blocked", False):
                    logger.warning("⚠️ Scraper Rápido bloqueado ao buscar detalhes. Fallback para Scraper Browser...")
                    project = await self._parallel_scraper.get_project_details(project_id)
                return project
            else:
                return await self._parallel_scraper.get_project_details(project_id)
        except Exception as e:
            logger.error(f"Erro ao obter detalhes: {e}")
            return None
        finally:
            self._current_action = None

    async def close(self):
        """Limpa recursos (não há nada persistente)."""
        pass


# Instância global compartilhada
automation_instance = WorkanaAutomation()
