"""
Gerenciador de navegador Playwright para automação do Workana.
"""
import asyncio
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger

from app.config import settings
from app.api.schemas import (
    SearchFilters, Project, ProposalResult, AutomationStatus
)


class WorkanaAutomation:
    """Classe principal para automação do Workana usando Playwright."""
    
    WORKANA_BASE_URL = "https://www.workana.com"
    WORKANA_LOGIN_URL = "https://www.workana.com/login"
    WORKANA_JOBS_URL = "https://www.workana.com/jobs"
    
    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._is_logged_in: bool = False
        self._is_running: bool = False
        self._current_action: Optional[str] = None
        self._proposals_sent_today: int = 0
        self._last_error: Optional[str] = None
    
    @property
    def is_logged_in(self) -> bool:
        return self._is_logged_in
    
    def get_status(self) -> AutomationStatus:
        """Retorna o status atual da automação."""
        return AutomationStatus(
            is_running=self._is_running,
            is_logged_in=self._is_logged_in,
            current_action=self._current_action,
            proposals_sent_today=self._proposals_sent_today,
            max_proposals_per_day=settings.max_proposals_per_day,
            last_error=self._last_error
        )
    
    async def _init_browser(self):
        """Inicializa o navegador se ainda não estiver inicializado."""
        if self._browser is None:
            logger.info("Inicializando navegador Playwright...")
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=settings.headless,
                slow_mo=settings.slow_mo
            )
            self._context = await self._browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            self._page = await self._context.new_page()
            logger.info("Navegador inicializado com sucesso!")
    
    async def _close_browser(self):
        """Fecha o navegador."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        self._page = None
        self._context = None
        logger.info("Navegador fechado.")
    
    async def _delay(self, ms: Optional[int] = None):
        """Adiciona delay entre ações para simular comportamento humano."""
        delay = ms or settings.delay_between_actions_ms
        await asyncio.sleep(delay / 1000)
    
    async def _random_delay(self, min_ms: int = 500, max_ms: int = 2000):
        """Adiciona delay aleatório."""
        import random
        delay = random.randint(min_ms, max_ms)
        await asyncio.sleep(delay / 1000)
    
    async def login(self, email: str, password: str) -> bool:
        """
        Realiza login no Workana.
        
        Args:
            email: Email do usuário
            password: Senha do usuário
            
        Returns:
            True se o login foi bem sucedido
        """
        try:
            self._current_action = "Realizando login..."
            self._is_running = True
            
            await self._init_browser()
            
            logger.info(f"Navegando para página de login: {self.WORKANA_LOGIN_URL}")
            await self._page.goto(self.WORKANA_LOGIN_URL, wait_until="networkidle")
            await self._delay()
            
            # Preencher email
            logger.info("Preenchendo email...")
            email_input = await self._page.wait_for_selector('input[name="email"], input[type="email"]', timeout=10000)
            await email_input.fill(email)
            await self._random_delay()
            
            # Preencher senha
            logger.info("Preenchendo senha...")
            password_input = await self._page.wait_for_selector('input[name="password"], input[type="password"]', timeout=5000)
            await password_input.fill(password)
            await self._random_delay()
            
            # Clicar no botão de login
            logger.info("Clicando no botão de login...")
            login_button = await self._page.wait_for_selector('button[type="submit"], input[type="submit"]', timeout=5000)
            await login_button.click()
            
            # Aguardar navegação
            await self._page.wait_for_load_state("networkidle")
            await self._delay(3000)
            
            # Verificar se o login foi bem sucedido
            current_url = self._page.url
            if "login" not in current_url.lower():
                self._is_logged_in = True
                self._last_error = None
                logger.success("Login realizado com sucesso!")
                return True
            else:
                # Verificar mensagem de erro
                error_element = await self._page.query_selector('.alert-danger, .error-message, .invalid-feedback')
                if error_element:
                    error_text = await error_element.text_content()
                    self._last_error = error_text
                    logger.error(f"Erro no login: {error_text}")
                else:
                    self._last_error = "Login falhou - verifique suas credenciais"
                return False
                
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Erro durante login: {e}")
            return False
        finally:
            self._is_running = False
            self._current_action = None
    
    async def logout(self):
        """Realiza logout e fecha o navegador."""
        self._is_logged_in = False
        await self._close_browser()
        logger.info("Logout realizado.")
    
    async def search_projects(self, filters: SearchFilters) -> List[Project]:
        """
        Busca projetos no Workana com os filtros especificados.
        
        Args:
            filters: Filtros de busca
            
        Returns:
            Lista de projetos encontrados
        """
        projects: List[Project] = []
        
        try:
            self._current_action = "Buscando projetos..."
            self._is_running = True
            
            if not self._page:
                raise Exception("Navegador não inicializado")
            
            # Construir URL de busca
            search_url = self.WORKANA_JOBS_URL
            params = []
            
            if filters.keywords:
                params.append(f"query={filters.keywords}")
            if filters.category:
                params.append(f"category={filters.category}")
            if filters.min_budget:
                params.append(f"budget_min={filters.min_budget}")
            if filters.max_budget:
                params.append(f"budget_max={filters.max_budget}")
            
            if params:
                search_url += "?" + "&".join(params)
            
            logger.info(f"Buscando projetos em: {search_url}")
            await self._page.goto(search_url, wait_until="networkidle")
            await self._delay()
            
            # Extrair projetos da página
            project_cards = await self._page.query_selector_all('.project-item, .job-item, [data-testid="project-card"]')
            
            for card in project_cards[:filters.max_results]:
                try:
                    project = await self._extract_project_from_card(card)
                    if project:
                        projects.append(project)
                except Exception as e:
                    logger.warning(f"Erro ao extrair projeto: {e}")
                    continue
            
            logger.info(f"Encontrados {len(projects)} projetos")
            return projects
            
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Erro na busca: {e}")
            return projects
        finally:
            self._is_running = False
            self._current_action = None
    
    async def _extract_project_from_card(self, card) -> Optional[Project]:
        """Extrai dados de um card de projeto."""
        try:
            # Título
            title_el = await card.query_selector('h2 a, .project-title a, .job-title a')
            title = await title_el.text_content() if title_el else "Sem título"
            title = title.strip()
            
            # URL
            url = await title_el.get_attribute("href") if title_el else ""
            if url and not url.startswith("http"):
                url = self.WORKANA_BASE_URL + url
            
            # ID do projeto (extrair da URL)
            project_id = url.split("/")[-1] if url else ""
            
            # Descrição
            desc_el = await card.query_selector('.project-description, .job-description, p')
            description = await desc_el.text_content() if desc_el else ""
            description = description.strip()[:500]  # Limitar tamanho
            
            # Orçamento
            budget_el = await card.query_selector('.budget, .price, [data-testid="budget"]')
            budget = await budget_el.text_content() if budget_el else None
            budget = budget.strip() if budget else None
            
            # Skills
            skills_els = await card.query_selector_all('.skill, .tag, .skill-tag')
            skills = []
            for skill_el in skills_els:
                skill_text = await skill_el.text_content()
                if skill_text:
                    skills.append(skill_text.strip())
            
            # Propostas
            proposals_el = await card.query_selector('.proposals-count, [data-testid="proposals-count"]')
            proposals_count = None
            if proposals_el:
                proposals_text = await proposals_el.text_content()
                import re
                match = re.search(r'\d+', proposals_text)
                if match:
                    proposals_count = int(match.group())
            
            # Data de postagem
            date_el = await card.query_selector('.date, .posted-date, time')
            posted_at = await date_el.text_content() if date_el else None
            posted_at = posted_at.strip() if posted_at else None
            
            return Project(
                id=project_id,
                title=title,
                description=description,
                budget=budget,
                skills=skills,
                proposals_count=proposals_count,
                posted_at=posted_at,
                url=url
            )
        except Exception as e:
            logger.warning(f"Erro ao extrair projeto do card: {e}")
            return None
    
    async def get_project_details(self, project_id: str) -> Optional[Project]:
        """Obtém detalhes completos de um projeto."""
        try:
            self._current_action = "Obtendo detalhes do projeto..."
            
            project_url = f"{self.WORKANA_BASE_URL}/job/{project_id}"
            await self._page.goto(project_url, wait_until="networkidle")
            await self._delay()
            
            # Extrair detalhes completos
            title_el = await self._page.query_selector('h1, .project-title')
            title = await title_el.text_content() if title_el else "Sem título"
            
            desc_el = await self._page.query_selector('.project-description, .description')
            description = await desc_el.text_content() if desc_el else ""
            
            budget_el = await self._page.query_selector('.budget, .price')
            budget = await budget_el.text_content() if budget_el else None
            
            client_el = await self._page.query_selector('.client-name, .employer-name')
            client_name = await client_el.text_content() if client_el else None
            
            country_el = await self._page.query_selector('.client-country, .location')
            client_country = await country_el.text_content() if country_el else None
            
            return Project(
                id=project_id,
                title=title.strip(),
                description=description.strip(),
                budget=budget.strip() if budget else None,
                client_name=client_name.strip() if client_name else None,
                client_country=client_country.strip() if client_country else None,
                url=project_url,
                skills=[]
            )
        except Exception as e:
            logger.error(f"Erro ao obter detalhes: {e}")
            return None
        finally:
            self._current_action = None
    
    async def send_proposal(
        self, 
        project_id: str, 
        message: str, 
        budget: float, 
        deadline_days: int
    ) -> ProposalResult:
        """
        Envia uma proposta para um projeto.
        
        Args:
            project_id: ID do projeto
            message: Mensagem da proposta
            budget: Valor da proposta
            deadline_days: Prazo em dias
            
        Returns:
            Resultado do envio
        """
        try:
            self._current_action = "Enviando proposta..."
            self._is_running = True
            
            # Navegar para página do projeto
            project_url = f"{self.WORKANA_BASE_URL}/job/{project_id}"
            await self._page.goto(project_url, wait_until="networkidle")
            await self._delay()
            
            # Clicar no botão de enviar proposta
            apply_button = await self._page.query_selector(
                'button:has-text("Enviar proposta"), '
                'a:has-text("Enviar proposta"), '
                '.apply-button, '
                '[data-testid="apply-button"]'
            )
            
            if not apply_button:
                return ProposalResult(
                    success=False,
                    message="Botão de enviar proposta não encontrado",
                    project_id=project_id
                )
            
            await apply_button.click()
            await self._delay()
            
            # Preencher formulário de proposta
            # Valor
            budget_input = await self._page.wait_for_selector(
                'input[name="budget"], input[name="amount"], #budget',
                timeout=5000
            )
            if budget_input:
                await budget_input.fill(str(budget))
                await self._random_delay(300, 800)
            
            # Prazo
            deadline_input = await self._page.query_selector(
                'input[name="deadline"], input[name="days"], #deadline'
            )
            if deadline_input:
                await deadline_input.fill(str(deadline_days))
                await self._random_delay(300, 800)
            
            # Mensagem
            message_input = await self._page.query_selector(
                'textarea[name="message"], textarea[name="proposal"], #message'
            )
            if message_input:
                await message_input.fill(message)
                await self._random_delay(500, 1500)
            
            # Submeter proposta
            submit_button = await self._page.query_selector(
                'button[type="submit"]:has-text("Enviar"), '
                'input[type="submit"]'
            )
            
            if submit_button:
                await submit_button.click()
                await self._page.wait_for_load_state("networkidle")
                await self._delay(2000)
                
                # Verificar sucesso
                success_message = await self._page.query_selector(
                    '.success-message, .alert-success, [data-testid="success"]'
                )
                
                if success_message:
                    self._proposals_sent_today += 1
                    logger.success(f"Proposta enviada para projeto {project_id}")
                    return ProposalResult(
                        success=True,
                        message="Proposta enviada com sucesso!",
                        project_id=project_id
                    )
            
            return ProposalResult(
                success=False,
                message="Não foi possível confirmar o envio da proposta",
                project_id=project_id
            )
            
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Erro ao enviar proposta: {e}")
            return ProposalResult(
                success=False,
                message=f"Erro: {str(e)}",
                project_id=project_id
            )
        finally:
            self._is_running = False
            self._current_action = None
