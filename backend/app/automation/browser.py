"""
Gerenciador de automação do Workana.
Usa busca paralela ANÔNIMA para evitar rastreamento.
"""

import asyncio
import json
import os
import time
from typing import Optional, List
from urllib.parse import urlparse
from loguru import logger

from app.config import settings
from app.api.schemas import SearchFilters, Project
from app.automation.components.parallel_scraper import AnonymousParallelScraper
from app.automation.components.fast_scraper import FastProjectScraper
from app.automation import session_manager


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
            last_error=self._last_error,
        )

    async def search_projects(
        self, filters: SearchFilters, user_id: Optional[str] = None
    ) -> List[Project]:
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

            logger.info(
                f"🔒 Busca {scraper_type}: páginas {start_page}-{start_page + pages_to_fetch - 1}"
            )

            projects = []
            used_fallback = False

            if scraper_type == "fast":
                projects = await self._fast_scraper.search_projects(filters, user_id=user_id)

                # Fallback se bloqueado pelo Cloudflare
                if not projects:
                    logger.warning(
                        "⚠️ Scraper Rápido bloqueado ou sem resultados. Iniciando fallback para Scraper Browser..."
                    )
                    used_fallback = True
                    self._current_action = "Fallback para browser (WAF)..."
                    projects = await self._parallel_scraper.search_projects_parallel(filters)
                elif getattr(self._fast_scraper, "was_blocked", False):
                    logger.warning(
                        "Algumas páginas foram bloqueadas; preservando resultados parciais."
                    )
            else:
                projects = await self._parallel_scraper.search_projects_parallel(filters)

            if user_id:
                await antiban.register_search(user_id)
            self._searches_today += 1

            if projects:
                logger.success(
                    f"✅ {len(projects)} projetos obtidos de {pages_to_fetch} páginas (fallback={used_fallback})"
                )
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

    async def get_project_details(
        self, project_id: str, user_id: Optional[str] = None
    ) -> Optional[Project]:
        """Obtém detalhes de um projeto (também anônimo)."""
        self._current_action = f"Detalhes do projeto {project_id}..."
        try:
            scraper_type = settings.scraper_type
            if scraper_type == "fast":
                project = await self._fast_scraper.get_project_details(project_id, user_id=user_id)
                # Fallback se bloqueado
                if not project or getattr(self._fast_scraper, "was_blocked", False):
                    logger.warning(
                        "⚠️ Scraper Rápido bloqueado ao buscar detalhes. Fallback para Scraper Browser..."
                    )
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
            await page.goto(
                "https://www.workana.com/login",
                wait_until="domcontentloaded",
                timeout=settings.scraping_timeout,
            )
            await asyncio.sleep(2)

            # Verificar se há captcha
            from app.automation.components.captcha_solver import CaptchaSolver

            solver = CaptchaSolver()
            if await solver.is_blocked(page):
                logger.warning(
                    "Bloqueio de captcha detectado na página de login. Tentando resolver..."
                )
                solved = await solver.detect_and_solve(page)
                if not solved:
                    raise Exception("Falha ao resolver captcha no login")

            # Preencher formulário de login
            logger.info("Preenchendo credenciais...")
            email_input = await page.query_selector(
                'input[type="email"], input[name="email"], #email'
            )
            if not email_input:
                raise Exception("Campo de email de login não encontrado")
            await email_input.fill(creds["email"])

            password_input = await page.query_selector(
                'input[type="password"], input[name="password"], #password'
            )
            if not password_input:
                raise Exception("Campo de senha de login não encontrado")
            await password_input.fill(creds["password"])

            # Clicar no botão de login
            submit_button = await page.query_selector('button[type="submit"], input[type="submit"]')
            if not submit_button:
                submit_button = await page.query_selector(
                    'button:has-text("Entrar"), button:has-text("Login")'
                )

            if not submit_button:
                raise Exception("Botão de login não encontrado")

            await submit_button.click()
            await asyncio.sleep(5)  # Esperar processamento do login

            # Verificar se o login foi bem-sucedido
            current_url = page.url
            if "login" in current_url:
                error_elem = await page.query_selector(".alert-danger, .error, .invalid-feedback")
                error_text = (
                    await error_elem.text_content()
                    if error_elem
                    else "Credenciais incorretas ou captcha exigido"
                )
                raise Exception(f"Falha de autenticação: {error_text.strip()}")

            logger.success("Login realizado com sucesso!")

            # Salvar o estado da sessão (banco + espelho em arquivo)
            state = await page.context.storage_state()
            await session_manager.save_storage_state(
                user_id, state, account_email=creds.get("email")
            )
            logger.info(f"Sessão salva para {user_id}")

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

    @staticmethod
    def _is_workana_logged_in_url(url: str) -> bool:
        """True quando a URL é do Workana e não é uma página de login."""
        parsed = urlparse(url)
        if not parsed.netloc.endswith("workana.com"):
            return False
        path = parsed.path.rstrip("/")
        # Durante o fluxo Google, /logincb/Google indica sucesso iminente
        if path.startswith("/logincb/"):
            return True
        return not path.startswith("/login")

    @staticmethod
    async def _detect_account_email(page) -> Optional[str]:
        """Tentativa (best-effort) de extrair o email da conta logada na UX do Workana."""
        try:
            candidates = await page.query_selector_all(
                ".navbar-user-email, .account-email, [data-user-email], .user-email"
            )
            for el in candidates:
                text = (await el.text_content() or "").strip()
                if "@" in text:
                    return text
        except Exception:
            pass
        return None

    async def login_with_google(self, user_id: str, timeout: int = 360) -> dict:
        """
        Abre um navegador real em https://www.workana.com/login/Google e aguarda o
        usuário concluir o login (incluindo o consentimento OAuth do Google).
        Ao final, salva o storage_state (cookies) no banco para o worker reutilizar.
        """
        from app.automation.antiban import antiban
        from app.automation.components.browser_driver import BrowserDriver

        # Não bloqueia por regras anti-ban caso o google login seja apenas configuração inicial.
        can_login_now, login_msg = await antiban.can_login(user_id)
        if not can_login_now:
            logger.warning(f"Login cancelado por regras do anti-ban: {login_msg}")

        self._current_action = "Login Google do Workana — conclua o acesso no navegador..."
        self._is_running = True
        self._last_error = None

        driver = BrowserDriver()
        try:
            # Login interativo requer janela visível; força headless=False.
            page = await driver.init_browser(use_session=False, headless=False)
            await page.goto(
                "https://www.workana.com/login/Google",
                wait_until="domcontentloaded",
                timeout=settings.scraping_timeout,
            )
            logger.info("Navegador aberto aguardando conclusão do login via Google...")

            deadline = time.time() + timeout
            while time.time() < deadline:
                await asyncio.sleep(2)
                try:
                    url = page.url
                except Exception:
                    logger.info("Navegador foi fechado pelo usuário.")
                    return {
                        "success": False,
                        "message": "O navegador foi fechado antes de concluir o login.",
                    }
                if self._is_workana_logged_in_url(url):
                    break

            current_url = page.url
            if not self._is_workana_logged_in_url(current_url):
                self._last_error = "Tempo esgotado aguardando o login no navegador."
                return {"success": False, "message": self._last_error}

            # Sucesso: salvar sessão
            await asyncio.sleep(2)
            state = await page.context.storage_state()
            account_email = await self._detect_account_email(page)
            await session_manager.save_storage_state(user_id, state, account_email=account_email)
            if account_email:
                logger.success(f"Login via Google realizado! Conta: {account_email}")
            else:
                logger.success("Login via Google realizado!")

            try:
                await antiban.register_login(user_id)
            except Exception:
                pass
            self._is_logged_in = True
            self._last_error = None
            return {"success": True, "email": account_email}

        except Exception as e:
            logger.error(f"Erro no login via Google: {e}")
            err_msg = str(e)
            if any(k in err_msg.lower() for k in ("xserver", "headless: true", "headed browser")):
                self._last_error = (
                    "Não foi possível abrir o navegador na tela porque o servidor está rodando sem interface gráfica "
                    "(ambiente Docker sem XServer). Use a opção 'Colar Cookies' na aba de configurações ou execute a opção "
                    "[4] (Login no Workana) no menu do INICIAR.bat no Windows."
                )
            else:
                self._last_error = f"Erro no Login via Google: {err_msg}"
            return {"success": False, "message": self._last_error}
        finally:
            await driver.close()
            self._is_running = False
            self._current_action = None

    async def submit_proposal(self, user_id: str, proposal_data) -> any:
        """Envia uma proposta real para o projeto no Workana utilizando navegação direta e seletores robustos."""
        from app.api.schemas import ProposalResult
        from app.automation.antiban import antiban
        from app.automation.components.browser_driver import BrowserDriver
        from app.automation.components.captcha_solver import CaptchaSolver
        from app.automation.selectors import WorkanaSelectors

        # Verificar limites anti-ban antes do envio
        can_send, message = await antiban.can_send_proposal(user_id)
        if not can_send:
            return ProposalResult(
                success=False, message=f"Anti-Ban: {message}", project_id=proposal_data.project_id
            )

        self._current_action = f"Enviando proposta para {proposal_data.project_id}..."
        self._is_running = True

        driver = BrowserDriver()
        try:
            # Carregar sessão salva (banco primeiro, arquivo como fallback)
            storage_state = await session_manager.load_storage_state(user_id)

            # Se não houver sessão válida, tentar fazer login com senha
            if not storage_state:
                login_success = await self.login(user_id)
                if not login_success:
                    return ProposalResult(
                        success=False,
                        message=f"Falha de autenticação ao tentar enviar proposta: {self._last_error}",
                        project_id=proposal_data.project_id,
                    )
                storage_state = await session_manager.load_storage_state(user_id)

            # Restaurar cookies/localStorage da sessão salva
            page = await driver.init_browser(
                use_session=True,
                headless=settings.headless,
                storage_state=storage_state,
            )
            # Auto-aceitar diálogos nativos do navegador (alert/confirm)
            page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))

            # Extrair slug limpo e montar rota direta da proposta no Workana (/messages/bid/{slug})
            slug = str(proposal_data.project_id).strip()
            for prefix in [
                "https://www.workana.com/job/",
                "http://www.workana.com/job/",
                "https://www.workana.com/messages/bid/",
                "http://www.workana.com/messages/bid/",
                "/job/",
                "/messages/bid/",
            ]:
                if slug.startswith(prefix):
                    slug = slug[len(prefix) :]
            slug = slug.strip("/").split("?")[0]

            bid_direct_url = f"https://www.workana.com/messages/bid/{slug}"
            logger.info(f"Navegando diretamente para a página da proposta: {bid_direct_url}")
            await page.goto(
                bid_direct_url, wait_until="domcontentloaded", timeout=settings.scraping_timeout
            )
            await asyncio.sleep(2)

            # Descartar banner de cookies da OneTrust e popups que possam cobrir elementos
            try:
                cookie_banner = await page.query_selector(
                    '#onetrust-accept-btn-handler, #onetrust-reject-all-handler, button[id*="onetrust-accept"], .ot-sdk-row button'
                )
                if cookie_banner and await cookie_banner.is_visible():
                    await cookie_banner.click(timeout=2000)
                    logger.info("Banner de cookies OneTrust descartado.")
            except Exception:
                pass

            # Verificar se foi bloqueado por WAF/Cloudflare
            solver = CaptchaSolver()
            if await solver.is_blocked(page):
                logger.info(
                    "Desafio Cloudflare detectado ao acessar proposta. Tentando resolver..."
                )
                solved = await solver.detect_and_solve(page)
                if not solved:
                    raise Exception("Bloqueio Cloudflare detectado ao carregar página da proposta.")

            # Verificar se a sessão expirou e foi redirecionado para a tela de login
            curr_url = page.url.lower()
            if "/login" in curr_url or "/users/login" in curr_url or "/signup" in curr_url:
                raise Exception(
                    "Sua sessão do Workana está expirada ou desconectada. Acesse Configurações > Conta Workana para reconectar sua conta."
                )

            # Verificar se o projeto já foi candidatado anteriormente
            already_applied = await page.query_selector(
                ':has-text("Proposta enviada"), :has-text("Já se candidatou"), :has-text("Proposal submitted"), '
                ':has-text("Você já fez uma proposta"), :has-text("Proposta realizada")'
            )
            bid_form_present = await page.query_selector(
                f"{WorkanaSelectors.BID_FORM}, {WorkanaSelectors.BID_AMOUNT_INPUT}, #Amount, #WorkerNetAmount, textarea#BidContent, textarea"
            )
            if already_applied and not bid_form_present:
                return ProposalResult(
                    success=True,
                    message="Você já enviou uma proposta para este projeto anteriormente.",
                    project_id=proposal_data.project_id,
                )

            # Verificar se o projeto foi encerrado/cancelado
            closed_project = await page.query_selector(
                ':has-text("não está mais aceitando propostas"), :has-text("Projeto encerrado"), '
                ':has-text("Projeto cancelado"), :has-text("Projeto finalizado"), :has-text("Job is closed")'
            )
            if closed_project and not bid_form_present:
                return ProposalResult(
                    success=False,
                    message="Este projeto está encerrado ou não aceita mais propostas no Workana.",
                    project_id=proposal_data.project_id,
                )

            # Aguardar montagem do formulário Vue da proposta
            logger.info("Aguardando carregamento do formulário de proposta...")
            try:
                await page.wait_for_selector(
                    f"{WorkanaSelectors.BID_FORM}, {WorkanaSelectors.BID_AMOUNT_INPUT}, #Amount, #WorkerNetAmount, textarea#BidContent, textarea",
                    timeout=15000,
                )
            except Exception:
                logger.warning(
                    "Seletor principal demorou a responder, prosseguindo com preenchimento resiliente..."
                )

            # ── 0a. Validação de tokens de segurança (CSRF/DCST) — HAR rev. ──
            # O formulário contém inputs hidden csrf_value, csrf_name e dcst-input
            # que DEVEM estar presentes para o submit ser aceito pelo backend.
            csrf_ok = await page.evaluate("""
                () => {
                    const csrfVal = document.querySelector('input[name="csrf_value"]');
                    const csrfName = document.querySelector('input[name="csrf_name"]');
                    const dcst = document.querySelector('input[name="dcst-input"]');
                    return {
                        csrf_value: csrfVal ? csrfVal.value : null,
                        csrf_name: csrfName ? csrfName.value : null,
                        dcst: dcst ? dcst.value : null,
                        all_present: !!(csrfVal && csrfVal.value && csrfName && csrfName.value && dcst && dcst.value)
                    };
                }
            """)
            if csrf_ok and csrf_ok.get("all_present"):
                logger.info(
                    f"✅ Tokens CSRF/DCST validados: csrf_name={csrf_ok['csrf_name']}, dcst={csrf_ok['dcst'][:16]}..."
                )
            else:
                logger.warning(
                    f"⚠️ Tokens de segurança incompletos: csrf_value={csrf_ok.get('csrf_value') is not None}, "
                    f"csrf_name={csrf_ok.get('csrf_name') is not None}, dcst={csrf_ok.get('dcst') is not None}. "
                    f"O formulário pode ser rejeitado pelo Workana."
                )

            # ── 0b. Seleção de Skills no formulário — HAR rev. ──
            # O HAR mostra que o POST envia campos skill-{nome}={nome} para cada
            # skill marcada (ex: skill-flutter=flutter, skill-api=api).
            # Os checkboxes já existem no HTML; precisamos garantir que estejam marcados.
            try:
                skill_checkboxes = await page.query_selector_all(
                    WorkanaSelectors.BID_SKILL_CHECKBOXES
                )
                if skill_checkboxes:
                    skills_checked = 0
                    for cb in skill_checkboxes:
                        try:
                            is_checked = await cb.is_checked()
                            if not is_checked:
                                await cb.check(force=True, timeout=2000)
                                skills_checked += 1
                        except Exception:
                            # Fallback via JS
                            cb_name = await cb.get_attribute("name") or ""
                            await page.evaluate(
                                """
                                (name) => {
                                    const el = document.querySelector('input[name="' + name + '"]');
                                    if (el && !el.checked) {
                                        el.checked = true;
                                        el.dispatchEvent(new Event('change', { bubbles: true }));
                                    }
                                }
                            """,
                                cb_name,
                            )
                            skills_checked += 1
                    if skills_checked > 0:
                        logger.info(f"✅ {skills_checked} skill(s) marcada(s) no formulário.")
                    else:
                        logger.info("Skills já estavam marcadas no formulário.")
                else:
                    logger.debug("Nenhum checkbox de skill encontrado no formulário.")
            except Exception as e:
                logger.warning(f"Não foi possível processar skills do formulário: {e}")

            # 1. Preencher Preço da Proposta (budget)
            budget_val = str(proposal_data.budget).replace(",", ".")
            budget_filled = False
            for sel in [
                "#Amount",
                'input[name="bid[amount]"]',
                "input#Amount",
                "#WorkerNetAmount",
                'input[name="bid[workerNetAmount]"]',
                'input[name="amount"]',
            ]:
                budget_input = await page.query_selector(sel)
                if budget_input:
                    try:
                        if await budget_input.is_visible():
                            await budget_input.click(timeout=3000)
                            await budget_input.fill("")
                            await budget_input.fill(budget_val)
                            await budget_input.dispatch_event("input")
                            await budget_input.dispatch_event("change")
                            await budget_input.dispatch_event("blur")
                            budget_filled = True
                            logger.info(f"Valor preenchido via {sel}: {budget_val}")
                            break
                    except Exception as e:
                        logger.warning(f"Falha ao preencher {sel}: {e}")

            if not budget_filled:
                budget_filled = await page.evaluate(
                    """
                    (val) => {
                        const input = document.querySelector('#Amount, input[name="bid[amount]"], #WorkerNetAmount, input[name="bid[workerNetAmount]"], input[name="amount"]');
                        if (input) {
                            input.value = val;
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                            input.dispatchEvent(new Event('blur', { bubbles: true }));
                            return true;
                        }
                        return false;
                    }
                """,
                    budget_val,
                )

            if not budget_filled:
                raise Exception("Campo de valor da proposta (#Amount) não encontrado.")

            # 1.1 Preencher Horas (se for projeto por hora e o campo #Hours estiver presente)
            hours_input = await page.query_selector('#Hours, #WorkHours, input[name="bid[hours]"]')
            if hours_input and await hours_input.is_visible():
                try:
                    hours_val = str(getattr(proposal_data, "estimated_hours", None) or 30)
                    await hours_input.click(timeout=2000)
                    await hours_input.fill("")
                    await hours_input.fill(hours_val)
                    await hours_input.dispatch_event("input")
                    await hours_input.dispatch_event("change")
                    await hours_input.dispatch_event("blur")
                    logger.info(f"Horas estimadas preenchidas: {hours_val}h")
                except Exception as e:
                    logger.warning(f"Falha ao preencher campo de horas: {e}")

            await asyncio.sleep(0.5)

            # 2. Mensagem personalizada (custom_message)
            message_text = proposal_data.custom_message
            if not message_text and proposal_data.template_id:
                from app.database import crud

                template = await crud.get_template(user_id, proposal_data.template_id)
                if template:
                    message_text = template.content

            if not message_text:
                raise Exception("Mensagem da proposta está vazia.")

            # Preencher mensagem em editores rich-text (Froala / Quill) e textareas padrão
            message_filled = False
            for editor_sel in [
                ".fr-element",
                'div[contenteditable="true"]',
                ".ql-editor",
                ".note-editable",
            ]:
                rich_editor = await page.query_selector(editor_sel)
                if rich_editor:
                    try:
                        if await rich_editor.is_visible():
                            await rich_editor.click(timeout=3000)
                            await page.keyboard.insert_text(message_text)
                            message_filled = True
                            logger.info(f"Mensagem inserida no editor rich-text {editor_sel}")
                            break
                    except Exception as e:
                        logger.warning(f"Falha no editor rich-text {editor_sel}: {e}")

            for ta_sel in [
                "#BidContent",
                'textarea[name="bid[content]"]',
                "textarea#bid_content",
                "textarea.bid-content",
                'textarea[name="bid_message"]',
                'textarea[name="content"]',
                "#bidForm textarea",
                "form textarea",
            ]:
                ta_input = await page.query_selector(ta_sel)
                if ta_input:
                    try:
                        if await ta_input.is_visible():
                            await ta_input.click(timeout=3000)
                            await ta_input.fill(message_text)
                            await ta_input.dispatch_event("input")
                            await ta_input.dispatch_event("change")
                            await ta_input.dispatch_event("blur")
                            message_filled = True
                            logger.info(f"Mensagem preenchida no textarea {ta_sel}")
                            break
                    except Exception as e:
                        logger.warning(f"Falha no textarea {ta_sel}: {e}")

            # Sincronização via JS no DOM
            await page.evaluate(
                """
                (text) => {
                    const textareas = document.querySelectorAll('#BidContent, textarea[name="bid[content]"], textarea#bid_content, textarea[name="bid_message"], #bidForm textarea');
                    textareas.forEach(ta => {
                        ta.value = text;
                        ta.dispatchEvent(new Event('input', { bubbles: true }));
                        ta.dispatchEvent(new Event('change', { bubbles: true }));
                        ta.dispatchEvent(new Event('blur', { bubbles: true }));
                    });
                    const editors = document.querySelectorAll('.fr-element, [contenteditable="true"], .ql-editor');
                    editors.forEach(ed => {
                        ed.innerText = text;
                        ed.dispatchEvent(new Event('input', { bubbles: true }));
                    });
                }
            """,
                message_text,
            )

            # 3. Prazo em dias (deadline_days) - No Workana, #BidDeliveryTime é input de texto
            days_int = int(proposal_data.deadline_days or 7)
            if days_int <= 7:
                deadline_text = f"{days_int} Dias" if days_int != 7 else "1 Semana"
            elif days_int <= 14:
                deadline_text = "2 Semanas" if days_int == 14 else f"{days_int} Dias"
            elif days_int <= 21:
                deadline_text = "3 Semanas" if days_int == 21 else f"{days_int} Dias"
            elif days_int <= 30:
                deadline_text = "4 Semanas" if days_int in (28, 30) else f"{days_int} Dias"
            else:
                deadline_text = f"{days_int} Dias"

            deadline_filled = False
            for sel in [
                "#BidDeliveryTime",
                'input[name="bid[deliveryTime]"]',
                'select[name="bid[deliveryTime]"]',
                "select#BidDeliveryTime",
                "select#bid_delivery_time",
                'input[name="bid[duration]"]',
            ]:
                el = await page.query_selector(sel)
                if el:
                    try:
                        tag_name = await el.evaluate("el => el.tagName.toLowerCase()")
                        if tag_name == "input":
                            await el.click(timeout=3000)
                            await el.fill("")
                            await el.fill(deadline_text)
                            await el.dispatch_event("input")
                            await el.dispatch_event("change")
                            await el.dispatch_event("blur")
                            deadline_filled = True
                            logger.info(f"Prazo de entrega preenchido em {sel}: {deadline_text}")
                            break
                        elif tag_name == "select":
                            try:
                                await el.select_option(str(days_int), timeout=3000)
                                deadline_filled = True
                            except Exception:
                                await page.evaluate(
                                    """
                                    (params) => {
                                        const sel = document.querySelector(params.selector);
                                        if (!sel) return false;
                                        for (let opt of sel.options) {
                                            if (opt.value == params.val || opt.text.includes(params.val) || opt.text.includes(params.text)) {
                                                sel.value = opt.value;
                                                sel.dispatchEvent(new Event('change', { bubbles: true }));
                                                return true;
                                            }
                                        }
                                        if (sel.options.length > 1) {
                                            sel.selectedIndex = 1;
                                            sel.dispatchEvent(new Event('change', { bubbles: true }));
                                            return true;
                                        }
                                        return false;
                                    }
                                """,
                                    {"selector": sel, "val": str(days_int), "text": deadline_text},
                                )
                                deadline_filled = True
                            if deadline_filled:
                                break
                    except Exception as e:
                        logger.warning(f"Falha ao preencher prazo {sel}: {e}")

            # 4. Perguntas customizadas do projeto (se houver)
            questions = await page.query_selector_all(
                '.project-questions textarea, .bid-form-question textarea, textarea[name^="project_questions"], textarea[name*="question" i], input[name^="project_questions"]'
            )
            for q in questions:
                try:
                    curr_val = await q.input_value()
                    if not curr_val or not curr_val.strip():
                        await q.fill(
                            "Tenho total disponibilidade e experiência comprovada para atender aos requisitos solicitados neste projeto com excelência e cumprimento rigoroso de prazos."
                        )
                        await q.dispatch_event("input")
                        await q.dispatch_event("change")
                except Exception:
                    pass

            # 5. Checkbox de termos / aceite (se houver)
            for cb_sel in [
                WorkanaSelectors.BID_ACKNOWLEDGE_CHECKBOX,
                'input[name="acknowledged"]',
                "input#acknowledged",
                'input[type="checkbox"][name*="terms" i]',
                'input[type="checkbox"][name*="agree" i]',
                'input[type="checkbox"][name*="ack" i]',
            ]:
                cb = await page.query_selector(cb_sel)
                if cb:
                    try:
                        if not await cb.is_checked():
                            await cb.check(force=True, timeout=3000)
                            await cb.dispatch_event("change")
                    except Exception:
                        await page.evaluate(
                            """
                            (sel) => {
                                const c = document.querySelector(sel);
                                if (c && !c.checked) {
                                    c.checked = true;
                                    c.dispatchEvent(new Event('change', { bubbles: true }));
                                }
                            }
                        """,
                            cb_sel,
                        )

            # 5.1 Destacar habilidades relevantes no formulário (skill-*) - Conforme capturado no HAR
            try:
                skill_checkboxes = await page.query_selector_all(
                    'input[type="checkbox"][name^="skill-"], input[type="checkbox"][name*="skill" i]'
                )
                for scb in skill_checkboxes[:5]:
                    try:
                        if not await scb.is_checked():
                            await scb.check(force=True, timeout=2000)
                            await scb.dispatch_event("change")
                    except Exception:
                        pass
                if skill_checkboxes:
                    logger.info(
                        f"Habilidades vinculadas automaticamente no formulário ({len(skill_checkboxes)} disponíveis)."
                    )
            except Exception:
                pass

            # 5.2 Upload de arquivo anexo / portfólio (se especificado na proposta)
            att_path = getattr(proposal_data, "attachment_path", None)
            if att_path:
                import os

                att_path = str(att_path).strip()
                if os.path.exists(att_path):
                    logger.info(f"Anexando arquivo à proposta ({att_path})...")
                    try:
                        file_input = await page.query_selector(
                            'input[type="file"], #AttachmentUpload input[type="file"]'
                        )
                        if file_input:
                            await file_input.set_input_files(att_path)
                            logger.info("Arquivo carregado no input de upload com sucesso.")
                            await asyncio.sleep(2.0)
                    except Exception as att_err:
                        logger.warning(f"Não foi possível anexar o arquivo: {att_err}")

            # 6. Aguardar validação do Cloudflare Turnstile nativo (se presente)
            # HAR rev.: O formulário envia cf-turnstile-response como campo obrigatório.
            # O widget Turnstile se auto-resolve via JS; precisamos esperar tempo suficiente.
            try:
                turnstile_el = await page.query_selector(
                    f"{WorkanaSelectors.TURNSTILE_RESPONSE_INPUT}, {WorkanaSelectors.TURNSTILE_WIDGET}"
                )
                if turnstile_el:
                    logger.info(
                        "Elemento Turnstile detectado no formulário, aguardando validação..."
                    )
                    turnstile_solved = False
                    for attempt in range(3):  # 3 tentativas, timeout progressivo
                        try:
                            wait_ms = 8000 + (attempt * 5000)  # 8s, 13s, 18s
                            await page.wait_for_function(
                                """
                                () => {
                                    const token = document.querySelector('input[name="cf-turnstile-response"]');
                                    return token && token.value && token.value.length > 10;
                                }
                            """,
                                timeout=wait_ms,
                            )
                            turnstile_solved = True
                            logger.info(
                                f"✅ Cloudflare Turnstile validado (tentativa {attempt + 1})."
                            )
                            break
                        except Exception:
                            if attempt < 2:
                                logger.info(
                                    f"Turnstile ainda não resolvido (tentativa {attempt + 1}/3), aguardando..."
                                )
                                await asyncio.sleep(2)
                            else:
                                logger.warning(
                                    "⚠️ Turnstile não resolvido após 3 tentativas. Prosseguindo mesmo assim — o submit pode falhar."
                                )
            except Exception:
                pass

            # ── 6b. Upload de anexo (portfólio/preview) — HAR rev. ──
            # O HAR mostra que anexos são enviados via POST /upload/assemblies
            # e o assembly_id é incluído no campo jsonAttachments do formulário.
            # Usamos o mecanismo nativo de file input do Playwright.
            if hasattr(proposal_data, "attachment_path") and proposal_data.attachment_path:
                import os

                attachment = proposal_data.attachment_path
                if os.path.exists(attachment):
                    try:
                        file_input = await page.query_selector(
                            'input[type="file"], input[name*="attachment"], input[name*="file"], '
                            'input[accept*="image"], input[accept*="application"]'
                        )
                        if file_input:
                            await file_input.set_input_files(attachment)
                            logger.info(f"📎 Arquivo anexado: {os.path.basename(attachment)}")
                            # Aguardar o upload completar (o Workana usa transloadit)
                            await asyncio.sleep(3)
                            # Verificar se o upload foi processado
                            upload_done = await page.evaluate("""
                                () => {
                                    const attached = document.querySelector('.attached-file, .upload-complete, .file-attached, .attachment-preview');
                                    return !!attached;
                                }
                            """)
                            if upload_done:
                                logger.info("✅ Upload do anexo confirmado.")
                            else:
                                logger.info("Upload iniciado, aguardando processamento...")
                                await asyncio.sleep(3)
                        else:
                            # Alternativa: procurar botão de upload e usar file chooser
                            upload_btn = await page.query_selector(
                                'button:has-text("Anexar"), button:has-text("Attach"), '
                                'a:has-text("Anexar"), label[for*="file"], .upload-button, .add-file'
                            )
                            if upload_btn:
                                async with page.expect_file_chooser() as fc_info:
                                    await upload_btn.click(timeout=5000)
                                file_chooser = await fc_info.value
                                await file_chooser.set_files(attachment)
                                logger.info(
                                    f"📎 Arquivo anexado via file chooser: {os.path.basename(attachment)}"
                                )
                                await asyncio.sleep(5)
                            else:
                                logger.warning(
                                    "⚠️ Input de arquivo não encontrado no formulário. Anexo ignorado."
                                )
                    except Exception as e:
                        logger.warning(
                            f"Não foi possível anexar arquivo: {e}. Prosseguindo sem anexo."
                        )
                else:
                    logger.warning(f"Arquivo de anexo não encontrado: {attachment}")

            # 7. Submeter o formulário
            logger.info("Submetendo formulário de proposta...")
            submitted = False
            for sel in [
                "#btn-submit-bid",
                '#bidForm button[type="submit"]',
                '#bidForm input[type="submit"]',
                'button[type="submit"]:has-text("Enviar")',
                'button[type="submit"]:has-text("Send")',
                'button[type="submit"]',
                'button:has-text("Enviar proposta")',
                'button:has-text("Fazer proposta")',
            ]:
                btn = await page.query_selector(sel)
                if btn:
                    try:
                        if await btn.is_visible():
                            await btn.scroll_into_view_if_needed()
                            await btn.click(force=True, timeout=10000)
                            submitted = True
                            logger.info(f"Clique realizado no botão de envio ({sel}).")
                            break
                    except Exception as e:
                        logger.warning(f"Tentativa de clique em {sel} falhou: {e}")

            if not submitted:
                logger.info("Tentando submissão via JavaScript evaluate...")
                submitted = await page.evaluate("""
                    () => {
                        const btn = document.querySelector('#btn-submit-bid, #bidForm button[type="submit"], #bidForm input[type="submit"], button[type="submit"]');
                        if (btn) {
                            btn.click();
                            return true;
                        }
                        const form = document.querySelector('form#bidForm, form.bid-form, form[action*="bid"]');
                        if (form) {
                            form.submit();
                            return true;
                        }
                        return false;
                    }
                """)

            if not submitted:
                raise Exception("Botão final de envio da proposta não encontrado.")

            await asyncio.sleep(3)

            # 8. Tratar modais pós-clique (Super Bids / Alertas de valor)
            for extra_sel in [
                'button:has-text("Send without extras")',
                'button:has-text("Enviar sem extras")',
                'button:has-text("Enviar sin extras")',
                'button:has-text("Não, obrigado")',
                'button:has-text("No, thanks")',
                'a:has-text("Enviar sem extras")',
                'a:has-text("Send without extras")',
                ".modal button.btn-default",
                ".modal a.btn-link",
            ]:
                try:
                    skip_extras = await page.query_selector(extra_sel)
                    if skip_extras and await skip_extras.is_visible():
                        logger.info(
                            f"Modal Super Bids detectado ({extra_sel}). Dispensando extras..."
                        )
                        await skip_extras.click(force=True, timeout=5000)
                        await asyncio.sleep(2)
                        break
                except Exception:
                    pass

            for alert_sel in [
                '.modal button:has-text("Continuar")',
                '.modal button:has-text("Continue")',
                '.modal button:has-text("OK")',
                '.modal button:has-text("Entendi")',
                '.modal button:has-text("Confirmar")',
                '.modal button:has-text("Confirm")',
                '.modal button:has-text("Sim")',
                ".modal button.btn-primary",
            ]:
                try:
                    alert_btn = await page.query_selector(alert_sel)
                    if alert_btn and await alert_btn.is_visible():
                        logger.info(f"Modal de confirmação detectado ({alert_sel}). Confirmando...")
                        await alert_btn.click(force=True, timeout=5000)
                        await asyncio.sleep(2)
                        break
                except Exception:
                    pass

            await asyncio.sleep(3)

            # ── 8a. Validação pós-submit via URL de redirect — HAR rev. ──
            # O POST bem-sucedido retorna 302 para:
            #   /messages/index/{slug}/{user}?added={id}&bid=1&isFromInbox=0
            # Verificamos se a URL atual contém esses parâmetros de sucesso.
            final_url = page.url
            redirect_has_added = "added=" in final_url
            redirect_has_bid = "bid=1" in final_url
            redirect_to_messages = "/messages/" in final_url or "/inbox/" in final_url

            if redirect_has_added and redirect_has_bid:
                logger.success(f"✅ Proposta confirmada via redirect! URL: {final_url[:150]}")
            elif redirect_to_messages:
                logger.info(f"Redirecionado para mensagens (possível sucesso): {final_url[:150]}")
            else:
                # Verificar se surgiu algum alerta de erro explícito do Workana na página
                error_banner = await page.query_selector(
                    ".alert-danger, .error-message, .alert-error, .help-block.error, .form-error"
                )
                if error_banner and await error_banner.is_visible():
                    err_text = (await error_banner.text_content() or "").strip()
                    if err_text and len(err_text) > 3 and "sucesso" not in err_text.lower():
                        logger.warning(
                            f"Alerta de erro detectado no Workana após submissão: {err_text}"
                        )
                        raise Exception(f"Workana rejeitou o envio: {err_text}")
                # Se não houve redirect nem erro, a URL pode ter permanecido na mesma página
                if "/messages/bid/" in final_url:
                    logger.warning(
                        f"⚠️ URL permaneceu na página de proposta após submit ({final_url[:100]}). O envio pode ter falhado silenciosamente."
                    )

            logger.success("Proposta submetida com sucesso no Workana!")

            # Registrar proposta enviada no anti-ban
            await antiban.register_proposal_sent(user_id)

            # Salvar no histórico de propostas
            from app.database import crud

            result_obj = ProposalResult(
                success=True, message="Enviada", project_id=proposal_data.project_id
            )
            await crud.save_proposal_history(user_id, proposal_data, result_obj)

            return result_obj

        except Exception as e:
            logger.error(f"Erro ao enviar proposta: {e}")
            self._last_error = f"Erro no Envio: {str(e)}"
            try:
                from app.database import crud

                result_obj = ProposalResult(
                    success=False, message=str(e), project_id=proposal_data.project_id
                )
                await crud.save_proposal_history(user_id, proposal_data, result_obj)
            except Exception as history_error:
                logger.warning(f"Erro ao salvar histórico de falha: {history_error}")

            return ProposalResult(
                success=False,
                message=f"Erro ao enviar proposta: {str(e)}",
                project_id=proposal_data.project_id,
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
