"""
Gerenciador de navegador Playwright para automação do Workana.
Integrado com sistema anti-ban para proteção da conta.
"""
import asyncio
import random
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger

from app.config import settings
from app.api.schemas import (
    SearchFilters, Project, ProposalResult, AutomationStatus
)
from app.automation.antiban import antiban, AntibanSystem
import os
import json

# Caminho para salvar sessão/cookies
SESSION_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "session_data.json")


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
        self._antiban = antiban  # Sistema anti-ban integrado
        self._manual_login_in_progress: bool = False
    
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
        """Inicializa o navegador com configurações anti-detecção."""
        if self._browser is None:
            logger.info("Inicializando navegador Playwright com anti-detecção...")
            self._playwright = await async_playwright().start()
            
            # Configurações anti-detecção
            self._browser = await self._playwright.chromium.launch(
                headless=settings.headless,
                slow_mo=settings.slow_mo,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                ]
            )
            
            # Obter configurações anti-ban para o contexto
            context_options = self._antiban.get_browser_context_options()
            
            self._context = await self._browser.new_context(**context_options)
            
            # Remover indicadores de automação
            await self._context.add_init_script("""
                // Sobrescrever propriedade webdriver
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Sobrescrever plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Sobrescrever languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['pt-BR', 'pt', 'en-US', 'en']
                });
                
                // Sobrescrever chrome
                window.chrome = {
                    runtime: {}
                };
                
                // Sobrescrever permissões
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
            self._page = await self._context.new_page()
            logger.info("Navegador inicializado com proteção anti-ban!")
    
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
    
    async def _save_session(self):
        """Salva cookies/sessão para reutilização."""
        if self._context:
            try:
                cookies = await self._context.cookies()
                with open(SESSION_FILE, 'w') as f:
                    json.dump(cookies, f)
                logger.info(f"Sessão salva em {SESSION_FILE}")
                return True
            except Exception as e:
                logger.error(f"Erro ao salvar sessão: {e}")
                return False
        return False
    
    async def _load_session(self) -> bool:
        """Carrega sessão salva anteriormente."""
        if not os.path.exists(SESSION_FILE):
            return False
        
        try:
            with open(SESSION_FILE, 'r') as f:
                cookies = json.load(f)
            
            if self._context and cookies:
                await self._context.add_cookies(cookies)
                logger.info("Sessão carregada com sucesso!")
                return True
        except Exception as e:
            logger.error(f"Erro ao carregar sessão: {e}")
        return False
    
    def has_saved_session(self) -> bool:
        """Verifica se existe uma sessão salva."""
        return os.path.exists(SESSION_FILE)
    
    async def clear_session(self):
        """Remove sessão salva."""
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
            logger.info("Sessão removida")
    
    async def login_with_session(self) -> bool:
        """
        Tenta fazer login usando sessão salva.
        Retorna True se a sessão ainda é válida.
        """
        try:
            self._current_action = "Verificando sessão salva..."
            self._is_running = True
            
            await self._init_browser()
            
            # Carregar sessão salva
            if await self._load_session():
                # Verificar se a sessão ainda é válida
                await self._page.goto(self.WORKANA_BASE_URL, wait_until="networkidle")
                await self._delay(2000)
                
                # Verificar se está logado (procurar elementos de usuário logado)
                user_menu = await self._page.query_selector('[data-testid="user-menu"], .user-menu, .avatar, .profile-pic')
                if user_menu:
                    self._is_logged_in = True
                    self._last_error = None
                    logger.success("Login realizado via sessão salva!")
                    return True
                
                # Verificar se não está na página de login
                current_url = self._page.url
                if "login" not in current_url.lower():
                    # Tentar acessar uma página de usuário logado
                    await self._page.goto(f"{self.WORKANA_BASE_URL}/dashboard", wait_until="networkidle")
                    await self._delay(2000)
                    
                    if "login" not in self._page.url.lower():
                        self._is_logged_in = True
                        self._last_error = None
                        logger.success("Login realizado via sessão salva!")
                        return True
            
            logger.info("Sessão expirada ou inválida")
            return False
            
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Erro ao usar sessão: {e}")
            return False
        finally:
            self._is_running = False
            self._current_action = None
    
    async def start_manual_login(self) -> Dict[str, Any]:
        """
        Inicia processo de login manual (para Google/Facebook/Apple).
        Abre o navegador visível para o usuário fazer login.
        
        Returns:
            Dict com status e instruções
        """
        try:
            self._current_action = "Abrindo navegador para login manual..."
            self._is_running = True
            self._manual_login_in_progress = True
            
            # Fechar navegador existente
            await self._close_browser()
            
            logger.info("Iniciando navegador em modo visível para login manual...")
            self._playwright = await async_playwright().start()
            
            # Abrir em modo VISÍVEL (headless=False)
            self._browser = await self._playwright.chromium.launch(
                headless=False,  # IMPORTANTE: Modo visível!
                slow_mo=100,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--start-maximized',
                ]
            )
            
            context_options = self._antiban.get_browser_context_options()
            context_options['viewport'] = None  # Usar tamanho da janela
            
            self._context = await self._browser.new_context(**context_options)
            
            # Adicionar script anti-detecção
            await self._context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            """)
            
            self._page = await self._context.new_page()
            
            # Navegar para página de login
            await self._page.goto(self.WORKANA_LOGIN_URL, wait_until="networkidle")
            
            logger.info("Navegador aberto! Aguardando login manual...")
            
            return {
                "success": True,
                "message": "Navegador aberto! Faça login pelo Google/Facebook/Apple. Após fazer login, clique em 'Confirmar Login' no painel.",
                "instructions": [
                    "1. Uma janela do navegador foi aberta",
                    "2. Clique em 'Continue com Google' (ou Facebook/Apple)",
                    "3. Complete o login normalmente",
                    "4. Após entrar no Workana, volte aqui e clique em 'Confirmar Login'"
                ]
            }
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self._last_error = f"{str(e)} | Details: {error_details}"
            self._manual_login_in_progress = False
            logger.error(f"Erro ao iniciar login manual: {e!r}\nTraceback: {error_details}")
            return {
                "success": False,
                "message": f"Erro: {str(e)}"
            }
        finally:
            self._current_action = None
    
    async def confirm_manual_login(self) -> Dict[str, Any]:
        """
        Confirma que o login manual foi concluído.
        Salva a sessão para uso futuro.
        """
        try:
            if not self._manual_login_in_progress:
                return {
                    "success": False,
                    "message": "Nenhum login manual em andamento"
                }
            
            self._current_action = "Verificando login..."
            
            # Verificar se está logado
            current_url = self._page.url
            
            # Navegar para dashboard para confirmar se não estiver lá
            if "dashboard" not in self._page.url.lower():
                try:
                    await self._page.goto(f"{self.WORKANA_BASE_URL}/dashboard", wait_until="domcontentloaded", timeout=15000)
                except Exception as e:
                    logger.warning(f"Erro ao navegar para dashboard (ignorando): {e}")
            
            # Aguardar um pouco para garantir que cookies sejam definidos
            await self._delay(2000)
            
            if "login" in self._page.url.lower():
                return {
                    "success": False,
                    "message": "Login não detectado. Complete o login no navegador e tente novamente."
                }
            
            # Salvar sessão
            await self._save_session()
            
            self._is_logged_in = True
            self._last_error = None
            self._manual_login_in_progress = False
            
            # Fechar navegador visível e reabrir em modo headless
            await self._close_browser()
            
            logger.success("Login manual confirmado e sessão salva!")
            
            return {
                "success": True,
                "message": "Login confirmado! Sua sessão foi salva para uso futuro."
            }
            
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Erro ao confirmar login: {e}")
            return {
                "success": False,
                "message": f"Erro: {str(e)}"
            }
        finally:
            self._current_action = None
    
    async def cancel_manual_login(self):
        """Cancela o processo de login manual."""
        self._manual_login_in_progress = False
        await self._close_browser()
        return {"success": True, "message": "Login manual cancelado"}
    
    async def _delay(self, ms: Optional[int] = None):
        """Adiciona delay aleatório entre ações (anti-detecção)."""
        if ms:
            await asyncio.sleep(ms / 1000)
        else:
            await self._antiban.random_delay()
    
    async def _random_delay(self, min_ms: int = 500, max_ms: int = 2000):
        """Adiciona delay aleatório."""
        await self._antiban.random_delay(min_ms, max_ms)
    
    async def _simulate_human_typing(self, element, text: str):
        """Digita texto simulando comportamento humano."""
        for char in text:
            await element.type(char, delay=random.randint(50, 150))
            # Ocasionalmente fazer uma pausa maior
            if random.random() < 0.1:
                await asyncio.sleep(random.uniform(0.2, 0.5))
    
    async def _scroll_randomly(self):
        """Rola a página aleatoriamente para simular leitura."""
        if self._page and self._antiban.config.random_scroll_before_action:
            scroll_amount = random.randint(100, 400)
            await self._page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await asyncio.sleep(random.uniform(0.3, 0.8))
    
    async def _move_mouse_randomly(self):
        """Move o mouse aleatoriamente pela página."""
        if self._page and self._antiban.config.simulate_mouse_movements:
            x = random.randint(100, 1800)
            y = random.randint(100, 900)
            await self._page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.3))
    
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
            logger.info(f"Navegando para página de login: {self.WORKANA_LOGIN_URL}")
            try:
                await self._page.goto(self.WORKANA_LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
                await self._page.wait_for_load_state("networkidle", timeout=30000)
            except Exception as e:
                logger.warning(f"Timeout na navegação (prosseguindo): {e}")
            await self._delay()
            
            # Preencher email
            logger.info("Preenchendo email...")
            # Preencher email
            logger.info("Preenchendo email...")
            email_input = await self._page.wait_for_selector('input[name="email"], input[type="email"]', timeout=30000)
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
            try:
                await self._page.wait_for_load_state("domcontentloaded", timeout=15000)
            except Exception as e:
                logger.warning(f"Timeout aguardando navegação (pode ser normal): {e}")

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
            # Se o erro for de navegador fechado, tentar reiniciar uma vez
            error_str = str(e).lower()
            if "closed" in error_str and self._browser:
                logger.warning("Navegador parece estar fechado. Tentando reiniciar...")
                await self._close_browser()
                try:
                    # Retry logic (simplified - recursive call could be dangerous, so just re-init and try basics)
                    await self._init_browser()
                    logger.info("Tentando login novamente após reinício...")
                    return await self.login(email, password) # Recursive retry once (assuming it won't loop indefinitely because of _browser check)
                except Exception as retry_e:
                    self._last_error = f"Erro após reiniciar navegador: {retry_e}"
                    logger.error(f"Erro fatal no login: {retry_e}")
                    return False
            
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
        Suporta paginação para trazer mais resultados que o padrão.
        
        Args:
            filters: Filtros de busca
            
        Returns:
            Lista de projetos encontrados
        """
        projects: List[Project] = []
        page_num = 1
        
        try:
            self._current_action = "Buscando projetos..."
            self._is_running = True
            
            if not self._page:
                raise Exception("Navegador não inicializado")
            
            # Construir URL de busca base
            base_search_url = self.WORKANA_JOBS_URL
            params = []
            
            if filters.keywords:
                params.append(f"query={filters.keywords}")
            if filters.category:
                params.append(f"category={filters.category}")
            if filters.min_budget:
                params.append(f"budget_min={filters.min_budget}")
            if filters.max_budget:
                params.append(f"budget_max={filters.max_budget}")
            
            # Loop de paginação
            while len(projects) < filters.max_results:
                # Construir URL da página atual
                current_params = params.copy()
                if page_num > 1:
                    current_params.append(f"page={page_num}")
                
                search_url = base_search_url
                if current_params:
                    search_url += "?" + "&".join(current_params)
                
                logger.info(f"Buscando projetos (Página {page_num}): {search_url}")
                try:
                    await self._page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                    # Pequena espera extra para garantir carregamento de cards dinâmicos
                    await self._page.wait_for_timeout(2000) 
                except Exception as e:
                    logger.warning(f"Timeout/Erro ao carregar página {page_num}: {e}")
                    # Se falhar na navegação, tentar extrair o que tiver ou parar
                    if page_num == 1:
                         # Se falhar na primeira, talvez seja fatal, mas vamos tentar ler o DOM
                         pass
                    else:
                         break
                
                await self._delay()
                
                # Extrair projetos da página atual
                project_cards = await self._page.query_selector_all('.project-item, .job-item, [data-testid="project-card"]')
                
                if not project_cards:
                    logger.info("Nenhum projeto encontrado nesta página. Encerrando busca.")
                    break
                
                new_projects_count = 0
                for card in project_cards:
                    # Se já atingimos o limite, parar
                    if len(projects) >= filters.max_results:
                        break
                        
                    try:
                        project = await self._extract_project_from_card(card)
                        if project:
                            # Verificar duplicatas por ID
                            if not any(p.id == project.id for p in projects):
                                projects.append(project)
                                new_projects_count += 1
                    except Exception as e:
                        logger.warning(f"Erro ao extrair projeto: {e}")
                        continue
                
                logger.info(f"Encontrados {new_projects_count} novos projetos na página {page_num}")
                
                # Se não encontramos novos projetos ou já temos o suficiente, parar
                if new_projects_count == 0 or len(projects) >= filters.max_results:
                    break
                
                # Verificar se existe próxima página no DOM (para evitar loop infinito se URL não funcionar)
                next_page_el = await self._page.query_selector('.pagination .next, a[rel="next"]')
                pagination_exists = await self._page.query_selector('.pagination')
                
                # Se não tem paginação ou não tem botão next (e não estamos apenas adicionando numero na url cegamente)
                if pagination_exists and not next_page_el:
                    logger.info("Fim da paginação alcançado.")
                    break
                    
                page_num += 1
                # Pequena pausa entre páginas para não sobrecarregar
                await self._random_delay(2000, 4000)
            
            logger.info(f"Total de projetos acumulados: {len(projects)}")
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
            proposals_count = 0
            try:
                # Tentar seletores específicos primeiro
                proposals_el = await card.query_selector('.proposals-count, [data-testid="proposals-count"], .bids')
                proposals_text = ""
                
                if proposals_el:
                    proposals_text = await proposals_el.text_content()
                else:
                    # Fallback: procurar por texto "proposta" ou "bid" dentro do card
                    # Isso é mais lento mas mais garantido se a classe mudou
                    all_texts = await card.all_inner_texts()
                    for text in all_texts:
                        if "proposta" in text.lower() or "bid" in text.lower():
                            # Tentar extrair numero dessa linha
                            import re
                            match = re.search(r'(\d+)\s*(?:proposta|bid)', text.lower())
                            if match:
                                proposals_count = int(match.group(1))
                                break
                
                if not proposals_count and proposals_text:
                    import re
                    match = re.search(r'\d+', proposals_text)
                    if match:
                        proposals_count = int(match.group())
            except Exception as e:
                pass # Manter 0 se falhar
            
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
