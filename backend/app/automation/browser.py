
"""
Gerenciador de automação do Workana (Refatorado).
Atua como Facade para os componentes: BrowserDriver, AuthHandler, ProjectScraper.
"""
import asyncio
from typing import Optional, List, Dict, Any
from loguru import logger
import os

from app.config import settings
from app.api.schemas import (
    SearchFilters, Project, AutomationStatus
)
from app.automation.components.browser_driver import BrowserDriver
from app.automation.components.auth_handler import AuthHandler
from app.automation.components.project_scraper import ProjectScraper

# Caminho para sessão (mantido para compatibilidade do AuthHandler)
SESSION_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "session_data.json")

class WorkanaAutomation:
    """Classe principal (Facade) para automação do Workana."""
    
    def __init__(self):
        # Componentes
        self.driver = BrowserDriver()
        self.auth = AuthHandler(self.driver, SESSION_FILE)
        self.scraper = ProjectScraper(self.driver)
        
        # Estados
        self._is_running: bool = False
        self._current_action: Optional[str] = None
        self._last_error: Optional[str] = None
        
        # Estatísticas (poderiam ir para um StatsHandler, mas mantido aqui por simplicidade)
        self._proposals_sent_today: int = 0 

    @property
    def is_logged_in(self) -> bool:
        return self.auth.is_logged_in

    def get_status(self) -> AutomationStatus:
        """Retorna o status atual da automação."""
        return AutomationStatus(
            is_running=self._is_running,
            is_logged_in=self.is_logged_in,
            current_action=self._current_action,
            proposals_sent_today=self._proposals_sent_today,
            max_proposals_per_day=settings.max_proposals_per_day,
            last_error=self._last_error
        )

    # --- Métodos de Navegação (Delegados para Driver/Auth) ---

    async def _init_browser(self, use_session: bool = True):
        """Inicializa navegador."""
        try:
            session_loader = self.auth.load_session_to_context if use_session else None
            await self.driver.init_browser(use_session=use_session, session_loader=session_loader)
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Erro ao iniciar via Automação: {e}")

    async def _close_browser(self):
        await self.driver.close()

    async def start_anonymous_session(self):
        """Inicia sessão anônima."""
        await self.driver.close()
        # Inicia sem carregar sessão
        await self.driver.init_browser(use_session=False)

    # --- Métodos de Auth (Delegados para AuthHandler) ---

    async def login_with_session(self) -> bool:
        self._current_action = "Login com sessão..."
        self._is_running = True
        try:
            return await self.auth.login_with_session()
        finally:
            self._is_running = False
            self._current_action = None

    async def login(self, email: str, password: str) -> bool:
        self._current_action = "Login padrão..."
        self._is_running = True
        try:
            return await self.auth.login_standard(email, password)
        finally:
            self._is_running = False
            self._current_action = None

    async def start_manual_login(self) -> Dict[str, Any]:
        self._current_action = "Login manual..."
        self._is_running = True
        return await self.auth.start_manual_login()

    async def confirm_manual_login(self) -> Dict[str, Any]:
        res = await self.auth.confirm_manual_login()
        if res.get("success"):
            self._is_running = False
            self._current_action = None
        return res

    async def cancel_manual_login(self):
        self._is_running = False
        self._current_action = None
        return await self.auth.cancel_manual_login() if hasattr(self.auth, 'cancel_manual_login') else {"success": True}
        
    async def logout(self):
        await self.auth.logout()

    def has_saved_session(self) -> bool:
        return self.auth.has_saved_session()

    async def clear_session(self):
        await self.auth.clear_session()

    # --- Métodos de Scraping (Delegados para ProjectScraper) ---

    async def search_projects(self, filters: SearchFilters, anonymous: bool = True) -> List[Project]:
        self._current_action = "Buscando projetos..."
        self._is_running = True
        try:
            # Tenta Fast Scraper se for anônimo (muito mais rápido)
            if anonymous:
                try:
                    from app.automation.components.fast_scraper import FastProjectScraper
                    fast_scraper = FastProjectScraper()
                    logger.info("Tentando Fast Search (HTTP)...")
                    projects = await fast_scraper.search_projects(filters)
                    if projects:
                        logger.success(f"Fast Search encontrou {len(projects)} projetos.")
                        return projects
                    logger.warning("Fast Search não retornou projetos, tentando via Browser...")
                except Exception as e:
                    logger.error(f"Erro no Fast Search: {e}, caindo para Browser.")

            # Fallback para Browser (lento mas garantido)
            async def ensure_page():
                if self.driver.page is None:
                    # Inicia dependendo do modo (anônimo ou com sessão)
                    return await self.driver.init_browser(use_session=not anonymous, session_loader=self.auth.load_session_to_context)
                
                # Se quer anônimo mas está logado, muda
                if anonymous and self.is_logged_in:
                    logger.info("Mudando para anônimo...")
                    await self.start_anonymous_session()
                    return self.driver.page
                
                return self.driver.page

            return await self.scraper.search_projects(filters, ensure_page)
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Erro na busca: {e}")
            return []
        finally:
            self._is_running = False
            self._current_action = None

    async def get_project_details(self, project_id: str, anonymous: bool = True) -> Optional[Project]:
        self._current_action = f"Detalhes do projeto {project_id}..."
        try:
            # Garante browser (anônimo ou não)
            if self.driver.page is None:
                # Se pedir anônimo, inicia sem sessão. Se não, tenta recuperar sessão.
                await self.driver.init_browser(use_session=not anonymous, session_loader=self.auth.load_session_to_context)
            
            # Se já estiver aberto mas em modo "errado" (ex: logado quando queria anônimo), 
            # decidimos não fechar para não perder performance, a menos que seja crítico.
            # Para leitura de detalhes, estar logado não costuma atrapalhar, e estar deslogado é o desejado.
            
            return await self.scraper.get_project_details(project_id)
        except Exception as e:
            logger.error(f"Erro ao obter detalhes: {e}")
            return None
        finally:
            self._current_action = None
