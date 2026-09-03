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
from app.automation.components.project_parser import (
    parse_project_json,
    _extract_briefing_details,
    _parse_client_history,
    _parse_rating,
)
import json
import html
import re
from bs4 import BeautifulSoup


# Lista de User-Agents Chrome modernos para rotação
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

# Resoluções de tela comuns
VIEWPORTS = [
    {'width': 1920, 'height': 1080},
    {'width': 1366, 'height': 768},
    {'width': 1536, 'height': 864},
    {'width': 1440, 'height': 900},
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
                await asyncio.sleep(3)  # Espera carregar JS
                
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
        if filters.publication and filters.publication != "any":
            params.append(f"publication={filters.publication}")
        
        if filters.language and filters.language != "any":
            params.append(f"language={filters.language}")
            
        if filters.proposals:
            if filters.proposals == "less_than_5":
                params.append("has_few_bids=1")
            elif filters.proposals == "5_plus":
                params.append("has_few_bids=2")

        if filters.payment_verified:
            params.append("client_history=1")
            
        if filters.skills:
            for skill in filters.skills:
                params.append(f"skills={skill}")

        if filters.sort and filters.sort.value != "relevance":
            params.append(f"ranking={filters.sort.value}")
        
        # Forçar moeda BRL
        params.append("currency=BRL")
        
        if page_num > 1:
            params.append(f"page={page_num}")
        
        url = "/jobs"
        if params:
            url += "?" + "&".join(params)
        return url

    async def _extract_project_from_json(self, data: dict) -> Optional[Project]:
        """Extrai um projeto de um dicionário (JSON do Workana)."""
        return await parse_project_json(data, self.WORKANA_BASE_URL)

    async def _extract_project(self, card, default_category: Optional[str] = None) -> Optional[Project]:
        """Extrai informações de um card de projeto via DOM de forma robusta."""
        try:
            # Link e ID do projeto (garantir que localiza a tag <a> do job)
            a_el = await card.query_selector('a[href*="/job/"], a[href*="/jobs/"], .project-title a, h2.project-title a, h3.project-title a')
            if not a_el:
                return None
            
            ref = await a_el.get_attribute("href")
            if not ref:
                return None
            if not ref.startswith("http"):
                ref = self.WORKANA_BASE_URL + ref
            
            pid = ref.split("/")[-1].split("?")[0].strip()
            if not pid:
                return None
            
            # Título (prioriza o atributo title do span ou texto do <a>)
            span_title_el = await card.query_selector('.project-title span[title], a[href*="/job/"] span[title]')
            title = None
            if span_title_el:
                title = await span_title_el.get_attribute("title")
            if not title:
                title = await a_el.text_content()
            title = (title or "").strip()
            if not title:
                return None
            
            # Descrição (seletor específico para o container de texto da descrição)
            desc_el = await card.query_selector('.project-body .html-desc, .html-desc, .project-details, .expander, [data-text-expand], .project-item-description, .project-description')
            desc = ""
            if desc_el:
                desc = await desc_el.text_content()
                desc = desc.strip() if desc else ""
            
            # Orçamento
            budget_el = await card.query_selector(WorkanaSelectors.CARD_BUDGET)
            budget = None
            budget_min = None
            budget_max = None
            if budget_el:
                raw_budget = await budget_el.text_content()
                raw_budget = raw_budget.strip() if raw_budget else None
                if raw_budget:
                    budget = await CurrencyService.convert_to_brl(raw_budget)
                    budget_min, budget_max = CurrencyService.parse_budget_string(budget)
            
            # Tipo de projeto (hourly vs fixed)
            is_hourly = False
            if budget and ("/ hora" in budget.lower() or "/hr" in budget.lower() or "/hour" in budget.lower()):
                is_hourly = True
            
            # Skills
            skills = []
            skill_els = await card.query_selector_all(WorkanaSelectors.CARD_SKILLS)
            for s in skill_els:
                txt = await s.text_content()
                if txt:
                    clean_txt = txt.strip()
                    if clean_txt and clean_txt != "+" and clean_txt not in skills:
                        skills.append(clean_txt)
            
            # Propostas
            proposals = 0
            p_el = await card.query_selector(WorkanaSelectors.CARD_PROPOSALS)
            if p_el:
                p_text = await p_el.text_content()
                if p_text:
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
                if posted_at:
                    posted_at = posted_at.replace("Publicado:", "").strip()

            # Extração de país do card DOM
            country_el = await card.query_selector('.country-name a, .country-name, .location')
            client_country = await country_el.text_content() if country_el else None
            if client_country:
                client_country = client_country.strip()

            # Extração de pagamento verificado
            payment_el = await card.query_selector('[title*="Pagamento verificado"], [title*="verified"], .payment-verified, .verified-payment')
            payment_verified = payment_el is not None

            details = _extract_briefing_details(desc) if desc else {}
            category = details.get("category") or default_category
            subcategory = details.get("subcategory")

            return Project(
                id=pid,
                title=title,
                description=desc,
                budget=budget,
                budget_min=budget_min,
                budget_max=budget_max,
                project_type="hourly" if is_hourly else "fixed",
                category=category,
                subcategory=subcategory,
                skills=skills,
                proposals_count=proposals,
                posted_at=posted_at.strip() if posted_at else None,
                url=ref or f"{self.WORKANA_BASE_URL}/job/{pid}",
                client_country=client_country,
                payment_verified=payment_verified
            )
        except Exception as e:
            logger.warning(f"Erro ao extrair projeto do card: {e}")
            return None

    async def search_projects_parallel(self, filters: SearchFilters) -> List[Project]:
        """
        Busca projetos no Workana com sessão Playwright isolada anti-detecção
        e extração híbrida direta (Fetch API interna autenticada + Fallback DOM).
        """
        playwright = None
        browser = None
        context = None
        
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--incognito',
                ]
            )
            
            user_agent = random.choice(USER_AGENTS)
            viewport = random.choice(VIEWPORTS)
            
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
                ignore_https_errors=True,
            )
            
            # Forçar cookie de moeda para BRL
            await context.add_cookies([{
                "name": "currency",
                "value": "BRL",
                "domain": ".workana.com",
                "path": "/"
            }])
            
            # Scripts anti-detecção
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'languages', { 
                    get: () => ['pt-BR', 'pt', 'en-US', 'en'] 
                });
                window.chrome = { runtime: {} };
            """)
            
            page = await context.new_page()
            
            start_page = filters.page
            pages_to_fetch = filters.pages_to_fetch
            end_page = start_page + pages_to_fetch - 1
            
            logger.info(f"🔒 Busca ANÔNIMA Playwright: páginas {start_page} a {end_page}")
            
            # Navegar para a página inicial da busca para resolver Cloudflare
            first_url_rel = self._build_search_url(filters, start_page)
            initial_url = self.WORKANA_BASE_URL + first_url_rel
            
            await self._safe_goto(page, initial_url)
            await asyncio.sleep(2.0)
            
            # Preparar as URLs relativas para todas as páginas solicitadas
            urls_rel = [
                self._build_search_url(filters, p_num)
                for p_num in range(start_page, start_page + pages_to_fetch)
            ]
            
            all_projects: List[Project] = []
            seen_ids = set()
            
            # 1. Tentar extração rápida e completa via Fetch API dentro da sessão validada do navegador
            try:
                raw_results = await page.evaluate("""async (targetUrls) => {
                    const pagesData = [];
                    const decodeHtml = (htmlStr) => {
                        if (!htmlStr) return '';
                        const txt = document.createElement('textarea');
                        txt.innerHTML = htmlStr;
                        return txt.value;
                    };

                    for (let i = 0; i < targetUrls.length; i++) {
                        const u = targetUrls[i];
                        try {
                            if (i > 0) {
                                await new Promise(r => setTimeout(r, 200 + Math.floor(Math.random() * 200)));
                            }

                            const res = await fetch(u, {
                                headers: {
                                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                                    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                                    'x-requested-with': 'XMLHttpRequest'
                                },
                                credentials: 'same-origin'
                            });

                            if (!res.ok) {
                                pagesData.push({ url: u, ok: false, status: res.status });
                                break;
                            }

                            const text = await res.text();
                            let items = [];

                            // 1. Tentar parsear JSON direto
                            const trimmed = text.trim();
                            if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
                                try {
                                    const json = JSON.parse(trimmed);
                                    const container = json.results || json;
                                    items = Array.isArray(container) ? container : (container.results || []);
                                } catch (e) {}
                            }

                            // 2. Extrair JSON do atributo :results-initials da tag <search>
                            if (!items || items.length === 0) {
                                const match = text.match(/:results-initials="([^"]+)"/) || text.match(/:results-initials='([^']+)'/);
                                if (match && match[1]) {
                                    try {
                                        const decoded = decodeHtml(match[1]);
                                        const parsed = JSON.parse(decoded);
                                        const container = parsed.results || parsed;
                                        items = Array.isArray(container) ? container : (container.results || []);
                                    } catch (jsonErr) {
                                        console.warn('Erro ao parsear :results-initials:', jsonErr);
                                    }
                                }
                            }

                            // 3. Fallback via DOMParser para encontrar a tag <search>
                            if (!items || items.length === 0) {
                                try {
                                    const parser = new DOMParser();
                                    const doc = parser.parseFromString(text, 'text/html');
                                    const searchTag = doc.querySelector('search');
                                    if (searchTag) {
                                        const attr = searchTag.getAttribute(':results-initials');
                                        if (attr) {
                                            const decoded = decodeHtml(attr);
                                            const parsed = JSON.parse(decoded);
                                            const container = parsed.results || parsed;
                                            items = Array.isArray(container) ? container : (container.results || []);
                                        }
                                    }
                                } catch (domErr) {}
                            }

                            if (items && items.length > 0) {
                                pagesData.push({ url: u, data: { results: items }, ok: true, count: items.length });
                            } else {
                                // Fim dos resultados disponíveis
                                pagesData.push({ url: u, data: { results: [] }, ok: true, count: 0 });
                                break;
                            }
                        } catch (err) {
                            pagesData.push({ url: u, ok: false, error: String(err) });
                            break;
                        }
                    }
                    return pagesData;
                }""", urls_rel)
                
                for item in (raw_results or []):
                    if not item.get("ok"):
                        continue
                    data = item.get("data")
                    if not isinstance(data, dict):
                        continue
                    
                    results_container = data.get("results", {})
                    results_list = []
                    if isinstance(results_container, dict):
                        results_list = results_container.get("results", [])
                    elif isinstance(results_container, list):
                        results_list = results_container
                    
                    for p_dict in results_list:
                        proj = await self._extract_project_from_json(p_dict)
                        if proj and proj.id and proj.id.strip() and proj.id not in seen_ids:
                            if not proj.category and filters.category:
                                proj.category = filters.category
                            seen_ids.add(proj.id)
                            all_projects.append(proj)
                            
            except Exception as fe:
                logger.warning(f"Extração via fetch no browser falhou: {fe}")
            
            # 2. Se a extração via Fetch não retornou nenhum projeto, faz fallback para DOM parsing multi-página
            if not all_projects:
                logger.info("Executando fallback para parsing DOM dos cards (multi-página)...")
                for p_num in range(start_page, start_page + min(pages_to_fetch, 10)):
                    current_url_rel = self._build_search_url(filters, p_num)
                    page_url = self.WORKANA_BASE_URL + current_url_rel
                    if p_num > start_page:
                        try:
                            await self._safe_goto(page, page_url)
                            await asyncio.sleep(1.5)
                        except Exception as nav_err:
                            logger.warning(f"Fallback DOM falhou na página {p_num}: {nav_err}")
                            break

                    try:
                        await page.wait_for_selector(WorkanaSelectors.PROJECT_CARD, timeout=6000)
                    except Exception:
                        pass
                    
                    cards = await page.query_selector_all(WorkanaSelectors.PROJECT_CARD)
                    if not cards:
                        break
                    
                    page_extracted = 0
                    for card in cards:
                        proj = await self._extract_project(card, default_category=filters.category)
                        if proj and proj.id and proj.id.strip() and proj.id not in seen_ids:
                            seen_ids.add(proj.id)
                            all_projects.append(proj)
                            page_extracted += 1

                    if page_extracted == 0:
                        break
            
            logger.success(f"✅ {len(all_projects)} projetos únicos obtidos de {len(urls_rel)} páginas (anônimo)")
            return all_projects
            
        finally:
            if context:
                await context.close()
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
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--incognito',
                ]
            )
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport=random.choice(VIEWPORTS),
                locale="pt-BR",
                timezone_id="America/Sao_Paulo",
            )
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'languages', { 
                    get: () => ['pt-BR', 'pt', 'en-US', 'en'] 
                });
                window.chrome = { runtime: {} };
            """)
            
            page = await context.new_page()
            url = f"{self.WORKANA_BASE_URL}/job/{project_id}"
            
            await self._safe_goto(page, url)
            await asyncio.sleep(2)
            
            title_el = await page.query_selector(WorkanaSelectors.DETAILS_TITLE)
            title = (await title_el.text_content()).strip() if title_el else "Sem título"
            
            desc_el = await page.query_selector(WorkanaSelectors.DETAILS_DESCRIPTION)
            description = ""
            if desc_el:
                description = (await desc_el.inner_text()).strip()
            
            if not description:
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                soup_desc = (
                    soup.select_one(WorkanaSelectors.DETAILS_DESCRIPTION)
                    or soup.find('div', class_='project-details')
                    or soup.find('div', class_='job-details')
                    or soup.find('div', class_='job-description')
                    or soup.find('div', class_='description')
                )
                if soup_desc:
                    description = soup_desc.get_text(separator='\n', strip=True)

            description = re.sub(r'\n{3,}', '\n\n', description).strip()

            # Metadados do Briefing
            details = _extract_briefing_details(description)
            category = details.get("category")
            subcategory = details.get("subcategory")

            # Orçamento
            budget_el = await page.query_selector(WorkanaSelectors.DETAILS_BUDGET)
            raw_budget = (await budget_el.text_content()).strip() if budget_el else None
            budget = await CurrencyService.convert_to_brl(raw_budget) if raw_budget else None
            budget_min, budget_max = CurrencyService.parse_budget_string(budget) if budget else (None, None)

            # Skills
            skills: List[str] = []
            for s_el in await page.query_selector_all(WorkanaSelectors.DETAILS_SKILLS):
                s_txt = (await s_el.text_content()).strip()
                if s_txt and s_txt not in skills:
                    skills.append(s_txt)

            # Cliente e Informações
            client_el = await page.query_selector(WorkanaSelectors.DETAILS_CLIENT_NAME)
            client_name = (await client_el.text_content()).strip() if client_el else None

            country_el = await page.query_selector(WorkanaSelectors.DETAILS_CLIENT_COUNTRY)
            client_country = None
            if country_el:
                c_txt = (await country_el.text_content()).strip()
                if c_txt:
                    client_country = c_txt
                else:
                    cls_attr = (await country_el.get_attribute("class")) or ""
                    for c in cls_attr.split():
                        if c.startswith("flag-") and len(c) > 5:
                            client_country = c[5:].upper()

            client_rating = None
            try:
                rating_el = await page.query_selector(WorkanaSelectors.DETAILS_RATING)
                if rating_el:
                    r_title = await rating_el.get_attribute("title")
                    r_txt = await rating_el.text_content()
                    client_rating = _parse_rating(r_title or r_txt)
            except Exception:
                pass

            posted = None
            paid = None
            since = None
            try:
                sidebar_el = await page.query_selector(WorkanaSelectors.DETAILS_SIDEBAR)
                if sidebar_el:
                    sidebar_text = await sidebar_el.inner_text()
                    posted, paid, since = _parse_client_history(sidebar_text)
            except Exception:
                pass

            payment_el = await page.query_selector('[title*="Pagamento verificado"], [title*="verified"], .payment-verified, .verified-payment')
            payment_verified = payment_el is not None

            is_hourly = False
            if budget and ("/ hora" in budget.lower() or "/hr" in budget.lower() or "/hour" in budget.lower()):
                is_hourly = True

            deadline = details.get("delivery_deadline") or details.get("duration")

            return Project(
                id=project_id,
                title=title,
                description=description,
                budget=budget,
                budget_min=budget_min,
                budget_max=budget_max,
                project_type="hourly" if is_hourly else "fixed",
                category=category,
                subcategory=subcategory,
                deadline=deadline,
                details=details,
                skills=skills,
                client_name=client_name,
                client_country=client_country,
                client_rating=client_rating,
                client_projects_posted=posted,
                client_projects_paid=paid,
                client_member_since=since,
                payment_verified=payment_verified,
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
