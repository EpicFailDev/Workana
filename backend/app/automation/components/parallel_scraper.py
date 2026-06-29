"""
Scraper paralelo ANÔNIMO usando múltiplas abas do Playwright.
Cada busca usa contextos isolados (modo incógnito) para evitar rastreamento.
"""
import asyncio
from typing import List, Optional
from loguru import logger
from playwright.async_api import async_playwright, Browser
import random

from app.api.schemas import SearchFilters, Project
from app.automation.selectors import WorkanaSelectors
from app.services.currency import CurrencyService
import json
import html
import re
from bs4 import BeautifulSoup


# Lista de User-Agents para rotação
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

# Resoluções de tela comuns
VIEWPORTS = [
    {'width': 1920, 'height': 1080},
    {'width': 1366, 'height': 768},
    {'width': 1536, 'height': 864},
    {'width': 1440, 'height': 900},
    {'width': 1280, 'height': 720},
]


from app.config import settings

class AnonymousParallelScraper:
    """
    Scraper ANÔNIMO que:
    - Usa contextos isolados (incógnito) para cada aba
    - Rotaciona User-Agents
    - Randomiza fingerprints
    - Fecha tudo após cada busca
    - Não mantém cookies/sessão entre buscas
    """
    
    # URLs obtidas das configurações
    WORKANA_BASE_URL = settings.workana_base_url
    WORKANA_JOBS_URL = settings.workana_jobs_url



    async def _safe_goto(self, page, url: str):
        """Navega para a URL com retry, timeout configurado e resolvedor de captcha."""
        from app.automation.components.captcha_solver import CaptchaSolver
        solver = CaptchaSolver()
        for attempt in range(settings.max_retries):
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=settings.scraping_timeout)
                await asyncio.sleep(2)  # Espera carregar JS
                
                # Se detectou bloqueio por Captcha/Cloudflare, tenta resolver
                if await solver.is_blocked(page):
                    logger.warning(f"⚠️ [Tentativa {attempt + 1}] Bloqueio de WAF/Cloudflare detectado! Ativando resolvedor...")
                    solved = await solver.detect_and_solve(page)
                    if not solved:
                        raise Exception("Falha ao resolver captcha")
                return
            except Exception as e:
                logger.warning(f"Tentativa {attempt + 1}/{settings.max_retries} falhou: {e}")
                if attempt == settings.max_retries - 1:
                    raise e
                await asyncio.sleep(2)

    def _build_search_url(self, filters: SearchFilters, page_num: int) -> str:
        """Constrói a URL de busca para uma página específica."""
        params = []
        if filters.keywords:
            params.append(f"query={filters.keywords}")
        if filters.category:
            params.append(f"category={filters.category}")
        if filters.min_budget:
            params.append(f"budget_min={filters.min_budget}")
        if filters.max_budget:
            params.append(f"budget_max={filters.max_budget}")
        # Novos filtros
        if filters.publication:
            params.append(f"publication={filters.publication}")
        
        if filters.language:
            params.append(f"language={filters.language}")
            
        if filters.proposals:
            if filters.proposals == "less_than_5":
                params.append("has_few_bids=1")
            elif filters.proposals == "5_plus":
                params.append("has_few_bids=2")

        if filters.payment_verified:
            params.append("client_history=1")
            
        if filters.skills:
            # Workana usa 'skills=' repetido ou separado por vírgula? 
            # Na inspeção vimos 'skills=slug'. Vamos assumir um se houver, ou tratar lista.
            # Simples implementação pegando o primeiro ou juntando se descobrir o formato exato
            # Observado: skills=react-js
            for skill in filters.skills:
                params.append(f"skills={skill}")

        if filters.sort and filters.sort.value != "relevance":
            params.append(f"ranking={filters.sort.value}")
        
        # Forçar moeda BRL
        params.append("currency=BRL")
        
        if page_num > 1:
            params.append(f"page={page_num}")
        
        url = self.WORKANA_JOBS_URL
        if params:
            url += "?" + "&".join(params)
        return url

    async def _scrape_single_page(self, browser: Browser, url: str, page_num: int) -> dict:
        """
        Busca uma única página em um CONTEXTO ISOLADO (incógnito).
        Cada aba tem seu próprio fingerprint aleatório.
        """
        context = None
        try:
            # User-Agent aleatório para esta aba
            user_agent = random.choice(USER_AGENTS)
            viewport = random.choice(VIEWPORTS)
            
            # Contexto TOTALMENTE ISOLADO (sem cookies compartilhados)
            context = await browser.new_context(
                viewport=viewport,
                user_agent=user_agent,
                locale='pt-BR',
                timezone_id='America/Sao_Paulo',
                geolocation={"latitude": -23.5505, "longitude": -46.6333},
                permissions=["geolocation"],
                extra_http_headers={
                    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
                },
                # Modo incógnito implícito - cada contexto é isolado
                ignore_https_errors=True,
            )
            
            # Bloqueio de recursos para carregar MAIS RÁPIDO
            await context.route("**/*.{png,jpg,jpeg,gif,svg,webp,css,woff,woff2,ttf,otf,eot}", lambda route: route.abort())
            
            # Forçar cookie de moeda para BRL
            await context.add_cookies([{
                "name": "currency",
                "value": "BRL",
                "domain": ".workana.com",
                "path": "/"
            }])
            
            # Scripts anti-detecção
            await context.add_init_script("""
                // Remove webdriver flag
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                
                // Fake plugins
                Object.defineProperty(navigator, 'plugins', { 
                    get: () => [1, 2, 3, 4, 5].map(() => ({})) 
                });
                
                // Fake languages
                Object.defineProperty(navigator, 'languages', { 
                    get: () => ['pt-BR', 'pt', 'en-US', 'en'] 
                });
                
                // Fake chrome runtime
                window.chrome = { runtime: {} };
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: 'denied' }) :
                        originalQuery(parameters)
                );
            """)
            
            page = await context.new_page()
            
            # Delay aleatório MINÚSCULO para evitar detecção básica
            await asyncio.sleep(random.uniform(0.1, 0.4))
            
            logger.info(f"[Aba {page_num}] Carregando...")
            
            await self._safe_goto(page, url)
            
            # Tempo reduzido para parecer humano mas ser rápido
            await asyncio.sleep(random.uniform(0.5, 1.2))
            
            # Espera inteligente pelo conteúdo
            try:
                await page.wait_for_selector(WorkanaSelectors.PROJECT_CARD, timeout=10000)
            except:
                logger.warning(f"[Aba {page_num}] Timeout esperando projetos.")

            # Extrai projetos via JSON (mais completo que o DOM)
            projects = []
            
            # Tentar extrair do atributo :results-initials
            search_tag = await page.query_selector('search')
            if search_tag:
                results_attr = await search_tag.get_attribute(':results-initials')
                if results_attr:
                    try:
                        decoded_json = html.unescape(results_attr)
                        data = json.loads(decoded_json)
                        projects_data = data.get('results', [])
                        
                        for p_dict in projects_data:
                            p = await self._extract_project_from_json(p_dict)
                            if p:
                                projects.append(p)
                    except Exception as je:
                        logger.warning(f"[Aba {page_num}] Erro ao parsear JSON: {je}")

            # Fallback para extração DOM se JSON falhar
            if not projects:
                cards = await page.query_selector_all(WorkanaSelectors.PROJECT_CARD)
                for card in cards:
                    p = await self._extract_project(card)
                    if p:
                        projects.append(p)
            
            # Verifica próxima página
            next_btn = await page.query_selector(WorkanaSelectors.PAGINATION_NEXT)
            has_next = next_btn is not None
            
            logger.info(f"[Aba {page_num}] ✓ {len(projects)} projetos encontrados")
            return {"page": page_num, "projects": projects, "has_next": has_next}
            
        except Exception as e:
            logger.error(f"[Aba {page_num}] Erro: {e}")
            return {"page": page_num, "projects": [], "has_next": False}
        finally:
            # SEMPRE fecha o contexto para não deixar rastros
            if context:
                await context.close()

    async def _extract_project_from_json(self, data: dict) -> Optional[Project]:
        """Extrai um projeto de um dicionário (JSON do Workana)."""
        try:
            # Título: extrair texto do HTML
            title_html = data.get('title', '')
            title_soup = BeautifulSoup(title_html, 'html.parser')
            title = title_soup.get_text(strip=True)
            
            slug = data.get('slug', '')
            url = f"{self.WORKANA_BASE_URL}/job/{slug}" if slug else ""
            
            budget = data.get('budget', '')
            if budget and "USD" in budget.upper():
                budget = await CurrencyService.convert_to_brl(budget)
            
            skills = [s.get('anchorText') for s in data.get('skills', []) if s.get('anchorText')]
            
            # Propostas
            proposals_text = data.get('totalBids', '0')
            m = re.search(r'\d+', str(proposals_text))
            proposals = int(m.group()) if m else 0

            # Descrição: unescape e limpeza básica
            desc = html.unescape(data.get('description', ''))
            desc = re.sub(r'<br\s*/?>', '\n', desc, flags=re.IGNORECASE)
            desc = BeautifulSoup(desc, 'html.parser').get_text(separator='\n')
            
            # Remover metadados que o Workana anexa ao final (mais robusto)
            # Esses campos geralmente aparecem no final no formato "Categoria\n: ..." ou "Categoria : ..."
            meta_pattern = r'\n+(?:Categoria|Subcategoria|Tamanho do projeto|Do que você precisa\?|Qual é o alcance|E-commerce|Isso é um projeto|Duração|Quantidade de pessoas)\b'
            parts = re.split(meta_pattern, desc, flags=re.IGNORECASE)
            if len(parts) > 1:
                desc = parts[0]
            
            # Caso não tenha pego com \n no início (raro no JSON, mas possível no fallback)
            meta_labels_fallback = [
                r'Categoria:', r'Subcategoria:', r'Tamanho do projeto:', r'Do que você precisa\?:'
            ]
            for label in meta_labels_fallback:
                parts = re.split(label, desc, flags=re.IGNORECASE)
                if len(parts) > 1:
                    desc = parts[0]
            
            # Limpar múltiplos saltos de linha para não ficar com muito espaço em branco
            desc = re.sub(r'\n{3,}', '\n\n', desc).strip()

            return Project(
                id=slug,
                title=title,
                description=desc,
                budget=budget,
                skills=skills,
                proposals_count=proposals,
                posted_at=data.get('postedDate'),
                url=url
            )
        except Exception as e:
            logger.warning(f"Erro ao processar JSON de projeto: {e}")
            return None

    async def _extract_project(self, card) -> Optional[Project]:
        """Extrai informações de um card de projeto."""
        try:
            # Título e Link
            title_el = await card.query_selector(WorkanaSelectors.CARD_TITLE)
            if not title_el:
                return None
            
            title = await title_el.text_content()
            title = title.strip() if title else ""
            
            ref = await title_el.get_attribute("href")
            if ref and not ref.startswith("http"):
                ref = self.WORKANA_BASE_URL + ref
            
            pid = ref.split("/")[-1].split("?")[0] if ref else ""
            
            # Descrição
            desc_el = await card.query_selector(WorkanaSelectors.CARD_DESCRIPTION)
            desc = ""
            if desc_el:
                desc = await desc_el.text_content()
                desc = desc.strip() if desc else ""
            
            # Orçamento
            budget_el = await card.query_selector(WorkanaSelectors.CARD_BUDGET)
            budget = None
            if budget_el:
                budget = await budget_el.text_content()
                budget = budget.strip() if budget else None
                if budget:
                    logger.info(f"💰 DEBUG Original budget found: {budget}")
                    # Converter para BRL se for USD
                    if "USD" in budget.upper():
                        old_budget = budget
                        budget = await CurrencyService.convert_to_brl(budget)
                        logger.info(f"🔄 Converted {old_budget} -> {budget}")
            
            # Skills
            skills = []
            skill_els = await card.query_selector_all(WorkanaSelectors.CARD_SKILLS)
            for s in skill_els:
                txt = await s.text_content()
                if txt:
                    skills.append(txt.strip())
            
            # Propostas
            proposals = 0
            p_el = await card.query_selector(WorkanaSelectors.CARD_PROPOSALS)
            if p_el:
                p_text = await p_el.text_content()
                if p_text:
                    import re
                    m = re.search(r'\d+', p_text)
                    if m:
                        proposals = int(m.group())
            
            # Data
            date_el = await card.query_selector(WorkanaSelectors.CARD_DATE)
            posted_at = None
            if date_el:
                posted_at = await date_el.text_content()
                if not posted_at:
                    posted_at = await date_el.get_attribute('title')
                
                # Limpar texto "Publicado: "
                if posted_at:
                    posted_at = posted_at.replace("Publicado:", "").strip()

            return Project(
                id=pid,
                title=title,
                description=desc,
                budget=budget,
                skills=skills,
                proposals_count=proposals,
                posted_at=posted_at.strip() if posted_at else None,
                url=ref or ""
            )
        except Exception as e:
            logger.warning(f"Erro ao extrair projeto: {e}")
            return None

    async def search_projects_parallel(self, filters: SearchFilters) -> List[Project]:
        """
        Busca projetos em múltiplas páginas SIMULTANEAMENTE.
        
        PROTEÇÕES ANTI-BAN:
        - Cada busca cria um navegador NOVO
        - Cada página usa contexto ISOLADO
        - User-Agents e fingerprints ALEATÓRIOS
        - Tudo é FECHADO após a busca (sem sessão persistente)
        """
        playwright = None
        browser = None
        
        try:
            # Criar navegador NOVO para esta busca (sem histórico)
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--incognito',  # Força modo incógnito
                ]
            )
            
            start_page = filters.page
            pages_to_fetch = filters.pages_to_fetch
            
            logger.info(f"🔒 Busca ANÔNIMA: páginas {start_page} a {start_page + pages_to_fetch - 1}")
            
            # Criar URLs para todas as páginas
            urls = [
                (self._build_search_url(filters, page_num), page_num)
                for page_num in range(start_page, start_page + pages_to_fetch)
            ]
            
            # Buscar TODAS as páginas simultaneamente
            # O navegador é passado para cada tarefa, que criará seu próprio contexto isolado
            tasks = [
                self._scrape_single_page(browser, url, page_num)
                for url, page_num in urls
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Processar resultados
            all_projects: List[Project] = []
            seen_ids = set()
            
            valid_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Erro em busca: {result}")
                    continue
                valid_results.append(result)
            
            valid_results.sort(key=lambda x: x["page"])
            
            for result in valid_results:
                for project in result["projects"]:
                    if project.id not in seen_ids:
                        seen_ids.add(project.id)
                        all_projects.append(project)
            
            logger.success(f"✅ {len(all_projects)} projetos únicos de {len(urls)} páginas (anônimo)")
            return all_projects
            
        finally:
            # SEMPRE fecha TUDO - não deixa rastros
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()
            logger.debug("🧹 Navegador fechado - sem rastros")

    async def get_project_details(self, project_id: str) -> Optional[Project]:
        """Obtém detalhes de um projeto (também anônimo)."""
        playwright = None
        browser = None
        context = None
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport=random.choice(VIEWPORTS),
                locale="pt-BR",
                timezone_id="America/Sao_Paulo",
            )
            
            page = await context.new_page()
            url = f"{self.WORKANA_BASE_URL}/job/{project_id}"
            
            await self._safe_goto(page, url)
            await asyncio.sleep(2)
            
            title_el = await page.query_selector(WorkanaSelectors.DETAILS_TITLE)
            title = await title_el.text_content() if title_el else "Sem título"
            
            desc_el = await page.query_selector(WorkanaSelectors.DETAILS_DESCRIPTION)
            description = await desc_el.text_content() if desc_el else ""
            
            budget_el = await page.query_selector(WorkanaSelectors.DETAILS_BUDGET)
            budget = await budget_el.text_content() if budget_el else None
            
            return Project(
                id=project_id,
                title=title.strip() if title else "",
                description=description.strip() if description else "",
                budget=budget.strip() if budget else None,
                skills=[],
                url=url
            )
        except Exception as e:
            logger.error(f"Erro ao obter detalhes: {e}")
            return None
        finally:
            if context:
                await context.close()
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()
