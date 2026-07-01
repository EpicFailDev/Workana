
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


class SearchUnavailableError(RuntimeError):
    """Raised when a project search could not actually be executed."""

    def __init__(self, message: str, *, restricted: bool = False):
        super().__init__(message)
        self.restricted = restricted


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
        self._is_logged_in: bool = False
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
            is_logged_in=self._is_logged_in,
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
                raise SearchUnavailableError(message, restricted=True)

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
                if not projects:
                    logger.warning("⚠️ Scraper Rápido bloqueado ou sem resultados. Iniciando fallback para Scraper Browser...")
                    used_fallback = True
                    self._current_action = "Fallback para browser (WAF)..."
                    projects = await self._parallel_scraper.search_projects_parallel(filters)
                elif getattr(self._fast_scraper, "was_blocked", False):
                    logger.warning("Algumas páginas foram bloqueadas; preservando resultados parciais.")
            else:
                projects = await self._parallel_scraper.search_projects_parallel(filters)
                
            if user_id:
                await antiban.register_search(user_id)
            self._searches_today += 1
            
            if projects:
                logger.success(f"✅ {len(projects)} projetos obtidos de {pages_to_fetch} páginas (fallback={used_fallback})")
            return projects or []
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Erro na busca: {e}")
            if isinstance(e, SearchUnavailableError):
                raise
            raise SearchUnavailableError(
                "Não foi possível consultar a Workana neste momento. Tente novamente em instantes."
            ) from e
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

    async def login(self, user_id: str) -> bool:
        """Realiza login no Workana usando as credenciais cadastradas."""
        from app.database import crud
        from app.automation.antiban import antiban
        from app.automation.components.browser_driver import BrowserDriver
        
        # 1. Obter credenciais
        creds = await crud.get_credentials(user_id)
        if not creds or not creds.get("email") or not creds.get("password"):
            self._last_error = "Credenciais não configuradas"
            return False
            
        # 2. Verificar regras do anti-ban
        can_login_now, login_msg = await antiban.can_login(user_id)
        if not can_login_now:
            logger.warning(f"Login cancelado por regras do anti-ban: {login_msg}")
            self._last_error = f"Anti-ban: {login_msg}"
            return False
            
        self._current_action = "Realizando login no Workana..."
        self._is_running = True
        
        driver = BrowserDriver()
        try:
            # Inicializar o browser
            page = await driver.init_browser(use_session=False, headless=settings.headless)
            
            # Ir para a página de login
            logger.info("Navegando para a página de login...")
            await page.goto("https://www.workana.com/login", wait_until="domcontentloaded", timeout=settings.scraping_timeout)
            await asyncio.sleep(2)
            
            # Verificar se há captcha
            from app.automation.components.captcha_solver import CaptchaSolver
            solver = CaptchaSolver()
            if await solver.is_blocked(page):
                logger.warning("Bloqueio de captcha detectado na página de login. Tentando resolver...")
                solved = await solver.detect_and_solve(page)
                if not solved:
                    raise Exception("Falha ao resolver captcha no login")
            
            # Preencher formulário de login
            logger.info("Preenchendo credenciais...")
            email_input = await page.query_selector('input[type="email"], input[name="email"], #email')
            if not email_input:
                raise Exception("Campo de email de login não encontrado")
            await email_input.fill(creds["email"])
            
            password_input = await page.query_selector('input[type="password"], input[name="password"], #password')
            if not password_input:
                raise Exception("Campo de senha de login não encontrado")
            await password_input.fill(creds["password"])
            
            # Clicar no botão de login
            submit_button = await page.query_selector('button[type="submit"], input[type="submit"]')
            if not submit_button:
                submit_button = await page.query_selector('button:has-text("Entrar"), button:has-text("Login")')
            
            if not submit_button:
                raise Exception("Botão de login não encontrado")
                
            await submit_button.click()
            await asyncio.sleep(5)  # Esperar processamento do login
            
            # Verificar se o login foi bem-sucedido
            current_url = page.url
            if "login" in current_url:
                error_elem = await page.query_selector('.alert-danger, .error, .invalid-feedback')
                error_text = await error_elem.text_content() if error_elem else "Credenciais incorretas ou captcha exigido"
                raise Exception(f"Falha de autenticação: {error_text.strip()}")
                
            logger.success("Login realizado com sucesso!")
            
            # Salvar o estado da sessão
            session_path = f"logs/session_{user_id}.json"
            import os
            os.makedirs("logs", exist_ok=True)
            await page.context.storage_state(path=session_path)
            logger.info(f"Sessão salva em {session_path}")
            
            await antiban.register_login(user_id)
            self._is_logged_in = True
            self._last_error = None
            return True
            
        except Exception as e:
            logger.error(f"Erro ao realizar login: {e}")
            self._last_error = f"Erro no Login: {str(e)}"
            self._is_logged_in = False
            return False
        finally:
            await driver.close()
            self._is_running = False
            self._current_action = None

    async def submit_proposal(self, user_id: str, proposal_data) -> any:
        """Envia uma proposta real para o projeto no Workana."""
        from app.api.schemas import ProposalResult
        from app.automation.antiban import antiban
        from app.automation.components.browser_driver import BrowserDriver
        import os
        
        # Verificar limites anti-ban antes do envio
        can_send, message = await antiban.can_send_proposal(user_id)
        if not can_send:
            return ProposalResult(success=False, message=f"Anti-Ban: {message}", project_id=proposal_data.project_id)
            
        self._current_action = f"Enviando proposta para {proposal_data.project_id}..."
        self._is_running = True
        
        session_path = f"logs/session_{user_id}.json"
        driver = BrowserDriver()
        try:
            # Se não houver arquivo de sessão, tentar fazer login primeiro
            if not os.path.exists(session_path):
                login_success = await self.login(user_id)
                if not login_success:
                    return ProposalResult(
                        success=False,
                        message=f"Falha de autenticação ao tentar enviar proposta: {self._last_error}",
                        project_id=proposal_data.project_id
                    )
            
            # Carregar cookies da sessão salva
            async def session_loader(context):
                import os
                if os.path.exists(session_path):
                    await context.storage_state(path=session_path)
                    
            page = await driver.init_browser(use_session=True, session_loader=session_loader, headless=settings.headless)
            
            # Obter a URL do projeto
            project_url = getattr(proposal_data, "project_url", None)
            if not project_url:
                from app.database import crud
                saved_project = await crud.get_project_by_workana_id(user_id, proposal_data.project_id)
                if saved_project:
                    project_url = saved_project.url
                else:
                    project_url = f"https://www.workana.com/job/{proposal_data.project_id}"
            
            logger.info(f"Navegando para a página do projeto: {project_url}")
            await page.goto(project_url, wait_until="domcontentloaded", timeout=settings.scraping_timeout)
            await asyncio.sleep(3)
            
            # Verificar captcha
            from app.automation.components.captcha_solver import CaptchaSolver
            solver = CaptchaSolver()
            if await solver.is_blocked(page):
                logger.warning("Captcha detectado na página do projeto. Resolvendo...")
                solved = await solver.detect_and_solve(page)
                if not solved:
                    raise Exception("Falha ao resolver captcha na página do projeto")
            
            # Procurar pelo botão de enviar proposta
            bid_button = await page.query_selector('.bid-button, a[href*="bid"], button:has-text("proposta"), button:has-text("Proposta"), a:has-text("proposta")')
            if not bid_button:
                # Verificar se há indicação de "proposta enviada" na página
                already_applied = await page.query_selector(':has-text("Proposta enviada"), :has-text("Já se candidatou")')
                if already_applied:
                    return ProposalResult(
                        success=True,
                        message="Você já enviou uma proposta para este projeto anteriormente.",
                        project_id=proposal_data.project_id
                    )
                raise Exception("Botão de proposta não encontrado (projeto encerrado ou erro de carregamento)")
                
            logger.info("Clicando no botão de proposta...")
            await bid_button.click()
            await asyncio.sleep(3)
            
            # Preencher os campos da proposta
            # 1. Preço da Proposta (budget)
            budget_input = await page.query_selector('input[name="bid_amount"], input#bid_amount, input[name="price"], input[type="number"]')
            if budget_input:
                await budget_input.fill(str(proposal_data.budget))
            
            # 2. Mensagem personalizada (custom_message)
            message_text = proposal_data.custom_message
            if not message_text and proposal_data.template_id:
                from app.database import crud
                template = await crud.get_template(user_id, proposal_data.template_id)
                if template:
                    message_text = template.content
            
            if not message_text:
                raise Exception("Mensagem da proposta está vazia")
                
            message_input = await page.query_selector('textarea[name="bid_message"], textarea#bid_message, textarea[name="message"], textarea')
            if message_input:
                await message_input.fill(message_text)
                
            # 3. Prazo em dias (deadline_days)
            deadline_input = await page.query_selector('input[name="deadline"], input#deadline, select[name="deadline"]')
            if deadline_input:
                await deadline_input.fill(str(proposal_data.deadline_days))
                
            # Clicar no botão final de enviar proposta
            submit_bid = await page.query_selector('button[type="submit"]:has-text("proposta"), button[type="submit"]:has-text("Enviar"), #submit-bid')
            if not submit_bid:
                submit_bid = await page.query_selector('button:has-text("Enviar proposta"), button:has-text("Enviar Proposta")')
                
            if not submit_bid:
                raise Exception("Botão final de envio da proposta não encontrado")
                
            logger.info("Submetendo proposta...")
            await submit_bid.click()
            await asyncio.sleep(5)
            
            logger.success("Proposta submetida com sucesso no Workana!")
            
            # Registrar proposta enviada no anti-ban
            await antiban.register_proposal_sent(user_id)
            
            # Salvar no histórico de propostas
            from app.database import crud
            result_obj = ProposalResult(success=True, message="Enviada", project_id=proposal_data.project_id)
            await crud.save_proposal_history(user_id, proposal_data, result_obj)
            
            return result_obj
            
        except Exception as e:
            logger.error(f"Erro ao enviar proposta: {e}")
            self._last_error = f"Erro no Envio: {str(e)}"
            try:
                from app.database import crud
                result_obj = ProposalResult(success=False, message=str(e), project_id=proposal_data.project_id)
                await crud.save_proposal_history(user_id, proposal_data, result_obj)
            except Exception as history_error:
                logger.warning(f"Erro ao salvar histórico de falha: {history_error}")
                
            return ProposalResult(
                success=False,
                message=f"Erro ao enviar proposta: {str(e)}",
                project_id=proposal_data.project_id
            )
        finally:
            await driver.close()
            self._is_running = False
            self._current_action = None

    async def close(self):
        """Limpa recursos (não há nada persistente)."""
        pass


# Instância global compartilhada
automation_instance = WorkanaAutomation()
