
import asyncio
from typing import List, Optional
import random
from loguru import logger
from app.api.schemas import SearchFilters, Project
from app.automation.components.browser_driver import BrowserDriver
from app.automation.selectors import WorkanaSelectors

from app.automation.components.captcha_solver import CaptchaSolver

class ProjectScraper:
    """
    Responsável por buscar dados de projetos e extrair informações.
    """
    
    WORKANA_BASE_URL = "https://www.workana.com"
    WORKANA_JOBS_URL = "https://www.workana.com/pt/jobs"

    def __init__(self, driver: BrowserDriver):
        self._driver = driver
        self._captcha_solver = CaptchaSolver()

    async def _safe_goto(self, page, url: str, wait_until: str = "domcontentloaded", timeout: int = 60000) -> bool:
        """Navega de forma segura, resolvendo captchas se necessário."""
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            await asyncio.sleep(2)
            if await self._captcha_solver.is_blocked(page):
                logger.warning("⚠️ Bloqueio de WAF/Cloudflare detectado! Ativando resolvedor de Captcha...")
                solved = await self._captcha_solver.detect_and_solve(page)
                if not solved:
                    logger.error("Falha ao resolver o Captcha de bloqueio.")
                    return False
            return True
        except Exception as e:
            logger.error(f"Erro ao navegar para {url}: {e}")
            return False

    async def search_projects(self, filters: SearchFilters, ensure_page_callback) -> List[Project]:
        """
        Executa a busca de projetos.
        ensure_page_callback: função para garantir que o navegador esteja aberto/configurado (ex: modo anônimo).
        """
        projects: List[Project] = []
        page_num = filters.page # Inicia da página solicitada
        
        # Garante navegador pronto
        page = await ensure_page_callback()
        
        base_search_url = self.WORKANA_JOBS_URL
        params = []
        if filters.keywords: params.append(f"query={filters.keywords}")
        if filters.category: params.append(f"category={filters.category}")
        if filters.min_budget: params.append(f"budget_min={filters.min_budget}")
        if filters.max_budget: params.append(f"budget_max={filters.max_budget}")
        
        # Filtro de propostas
        if filters.proposals:
            if filters.proposals == "less_than_5":
                params.append("has_few_bids=1")
            elif filters.proposals == "5_plus":
                params.append("has_few_bids=2")
        
        # Ordenação
        if filters.sort and filters.sort.value != "relevance":
            params.append(f"ranking={filters.sort.value}")
            
        # Forçar moeda BRL
        params.append("currency=BRL")
        
        while len(projects) < filters.max_results:
            current_params = params.copy()
            if page_num > 1:
                current_params.append(f"page={page_num}")
            
            search_url = base_search_url
            if current_params:
                search_url += "?" + "&".join(current_params)
            
            logger.info(f"Scraping página {page_num}: {search_url}")
            
            try:
                success = await self._safe_goto(page, search_url, wait_until="domcontentloaded", timeout=60000)
                if not success:
                    raise Exception("Falha de WAF ou carregamento da página")
            except Exception as e:
                logger.warning(f"Erro ao carregar página {page_num}: {e}")
                if page_num > 1: break # Se não for a primeira, assume fim
                
            project_cards = await page.query_selector_all(WorkanaSelectors.PROJECT_CARD)
            
            if not project_cards:
                logger.info("Sem projetos nesta página.")
                break
            
            found_on_page = 0
            for card in project_cards:
                if len(projects) >= filters.max_results: break
                
                p = await self._extract_project_from_card(card)
                if p and not any(existing.id == p.id for existing in projects):
                    projects.append(p)
                    found_on_page += 1
            
            logger.info(f"Extraídos {found_on_page} projetos da página {page_num}")
            
            if found_on_page == 0: break
            
            # Verifica paginação
            next_btn = await page.query_selector(WorkanaSelectors.PAGINATION_NEXT)
            if not next_btn:
                break
                
            page_num += 1
            # Delay aleatório simples hardcoded ou via driver se preferir
            await asyncio.sleep(random.uniform(1.5, 3.5))
            
        return projects

    async def get_project_details(self, project_id: str) -> Optional[Project]:
        """Obtém detalhes ricos do projeto."""
        page = self._driver.page
        if not page:
            logger.error("Navegador não iniciado para detalhes.")
            return None
            
        url = f"{self.WORKANA_BASE_URL}/job/{project_id}"
        await self._safe_goto(page, url, wait_until="networkidle")
        
        # Extração
        title = await self._get_text(page, WorkanaSelectors.DETAILS_TITLE)
        description = await self._get_text(page, WorkanaSelectors.DETAILS_DESCRIPTION)
        budget = await self._get_text(page, WorkanaSelectors.DETAILS_BUDGET)
        
        client_name = await self._get_text(page, WorkanaSelectors.DETAILS_CLIENT_NAME)
        client_country = await self._get_text(page, WorkanaSelectors.DETAILS_CLIENT_COUNTRY)
        
        # Avaliação
        client_rating = None
        try:
            stars_el = await page.query_selector(WorkanaSelectors.DETAILS_RATING)
            if stars_el:
                title_attr = await stars_el.get_attribute("title")
                if title_attr:
                    import re
                    match = re.search(r'([\d\.]+)', title_attr)
                    if match: client_rating = float(match.group(1))
                else:
                    full_stars = await stars_el.query_selector_all(WorkanaSelectors.DETAILS_STARS)
                    client_rating = float(len(full_stars))
        except: pass
        
        # Stats Sidebar
        posted = None
        paid = None
        since = None
        try:
            sidebar = await page.inner_text(WorkanaSelectors.DETAILS_SIDEBAR)
            import re
            m_posted = re.search(r'(\d+)\s*Projetos publicados', sidebar, re.IGNORECASE)
            if m_posted: posted = int(m_posted.group(1))
            
            m_paid = re.search(r'(\d+)\s*Projetos pagos', sidebar, re.IGNORECASE)
            if m_paid: paid = int(m_paid.group(1))
            
            m_since = re.search(r'Membro desde:\s*(.*?)(?:\n|$)', sidebar, re.IGNORECASE)
            if m_since: since = m_since.group(1).strip()
        except: pass

        return Project(
            id=project_id,
            title=title or "Sem título",
            description=description or "",
            budget=budget,
            client_name=client_name,
            client_country=client_country,
            client_rating=client_rating,
            client_projects_posted=posted,
            client_projects_paid=paid,
            client_member_since=since,
            url=url,
            skills=[]
        )

    async def _extract_project_from_card(self, card) -> Optional[Project]:
        try:
            title_el = await card.query_selector(WorkanaSelectors.CARD_TITLE)
            title = await title_el.text_content() if title_el else "Sem título"
            
            ref = await title_el.get_attribute("href") if title_el else ""
            if ref and not ref.startswith("http"): ref = self.WORKANA_BASE_URL + ref
            
            pid = ref.split("/")[-1] if ref else ""
            
            desc_el = await card.query_selector(WorkanaSelectors.CARD_DESCRIPTION)
            desc = await desc_el.text_content() if desc_el else ""
            
            budget_el = await card.query_selector(WorkanaSelectors.CARD_BUDGET)
            budget = await budget_el.text_content() if budget_el else None
            
            # Skills
            skills = []
            for s in await card.query_selector_all(WorkanaSelectors.CARD_SKILLS):
                txt = await s.text_content()
                if txt: skills.append(txt.strip())
            
            # Proposals
            proposals = 0
            p_text = ""
            p_el = await card.query_selector(WorkanaSelectors.CARD_PROPOSALS)
            if p_el:
                p_text = await p_el.text_content()
            else:
                # Fallback text search
                full_text = await card.inner_text()
                import re
                m = re.search(r'(\d+)\s*(?:proposta|bid)', full_text, re.IGNORECASE)
                if m: proposals = int(m.group(1))
            
            if not proposals and p_text:
                import re
                m = re.search(r'\d+', p_text)
                if m: proposals = int(m.group())

            # Data
            date_el = await card.query_selector(WorkanaSelectors.CARD_DATE)
            posted_at = await date_el.text_content() if date_el else None
            
            # Extração de país do card DOM
            country_el = await card.query_selector('.country-name a, .country-name')
            client_country = await country_el.text_content() if country_el else None
            if client_country:
                client_country = client_country.strip()

            # Extração de pagamento verificado
            payment_el = await card.query_selector('[title*="Pagamento verificado"], [title*="verified"], .payment-verified, .verified-payment')
            payment_verified = payment_el is not None

            return Project(
                id=pid,
                title=title.strip(),
                description=desc.strip(),
                budget=budget.strip() if budget else None,
                skills=skills,
                proposals_count=proposals,
                posted_at=posted_at.strip() if posted_at else None,
                url=ref,
                client_country=client_country,
                payment_verified=payment_verified
            )
        except Exception as e:
            logger.warning(f"Erro card: {e}")
            return None

    async def _get_text(self, parent, selector):
        el = await parent.query_selector(selector)
        return (await el.text_content()).strip() if el else None
