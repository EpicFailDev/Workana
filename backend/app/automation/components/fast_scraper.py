import httpx
from bs4 import BeautifulSoup
from typing import List, Optional
from loguru import logger
import random
import asyncio
import json
import html
import re

from app.api.schemas import SearchFilters, Project
from app.services.currency import CurrencyService
from app.automation.components.project_parser import parse_project_json

class FastProjectScraper:
    """
    Scraper rápido usando requisições HTTP diretas e extração de JSON embutido.
    Busca múltiplas páginas em paralelo sem overhead de navegador.
    """
    
    WORKANA_BASE_URL = "https://www.workana.com"
    WORKANA_JOBS_URL = "https://www.workana.com/pt/jobs"

    def __init__(self):
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive"
        }
        self.semaphore = asyncio.Semaphore(5) # Limitar a 5 requisições simultâneas

    @staticmethod
    def _is_cloudflare_block(response: httpx.Response) -> bool:
        """Distingue uma página de resultados válida de uma página de desafio."""
        body = response.text.lower()
        if response.status_code == 200 and ':results-initials' in body:
            return False
        challenge_markers = (
            "<title>just a moment",
            "attention required! | cloudflare",
            "cf-chl-",
            "challenge-platform",
        )
        return response.status_code in (403, 429, 503) or any(
            marker in body for marker in challenge_markers
        )

    async def search_projects(self, filters: SearchFilters, user_id: Optional[str] = None) -> List[Project]:
        """Executa a busca de projetos via HTTP de forma PARALELA."""
        self.was_blocked = False
        start_page = filters.page
        pages_to_fetch = filters.pages_to_fetch
        
        logger.info(f"⚡ Fast Parallel Scraping: páginas {start_page} a {start_page + pages_to_fetch - 1}")
        
        tasks = [
            self._scrape_page_with_semaphore(filters, page_num, user_id)
            for page_num in range(start_page, start_page + pages_to_fetch)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_projects: List[Project] = []
        seen_ids = set()
        
        for result in results:
            if isinstance(result, list):
                for p in result:
                    if p.id not in seen_ids:
                        seen_ids.add(p.id)
                        all_projects.append(p)
            elif isinstance(result, Exception):
                logger.error(f"Erro em página Fast: {result}")

        if filters.project_type.value != "any":
            all_projects = [
                project for project in all_projects
                if project.project_type == filters.project_type.value
            ]
        if filters.payment_verified:
            all_projects = [project for project in all_projects if project.payment_verified]

        return all_projects[:filters.max_results]

    async def _scrape_page_with_semaphore(self, filters: SearchFilters, page_num: int, user_id: Optional[str] = None) -> List[Project]:
        """Wrapper para limitar concorrência e adicionar jitter."""
        async with self.semaphore:
            # Delay aleatório pequeno para não disparar o WAF/Rate limit
            await asyncio.sleep(random.uniform(0.5, 2.0))
            return await self._scrape_page_http(filters, page_num, user_id)

    async def _scrape_page_http(self, filters: SearchFilters, page_num: int, user_id: Optional[str] = None) -> List[Project]:
        """Busca uma única página via HTTP com controle de proxy, resolvedor e métricas."""
        import time
        from app.database import crud
        from app.config import settings
        from app.automation.antiban import antiban

        start_time = time.time()
        success = False
        blocked = False
        
        params = {}
        if filters.keywords: params["query"] = filters.keywords
        if filters.category: params["category"] = filters.category
        if filters.min_budget: params["budget_min"] = str(filters.min_budget)
        if filters.max_budget: params["budget_max"] = str(filters.max_budget)
        if filters.publication: params["publication"] = filters.publication
        if filters.language: params["language"] = filters.language
        if filters.payment_verified: params["client_history"] = "1"
        if filters.skills: params["skills"] = filters.skills
        
        # Filtro de propostas
        if filters.proposals:
            if filters.proposals == "less_than_5":
                params["has_few_bids"] = "1"
            elif filters.proposals == "5_plus":
                params["has_few_bids"] = "2"

        if filters.sort and filters.sort.value != "relevance":
            params["ranking"] = filters.sort.value
        params["currency"] = "BRL"
        if page_num > 1:
            params["page"] = str(page_num)

        headers = self.headers.copy()
        headers["User-Agent"] = antiban.get_random_user_agent()

        client_kwargs = {
            "headers": headers,
            "follow_redirects": True,
            "timeout": 15.0,
        }
        if settings.proxy_url:
            client_kwargs["proxy"] = settings.proxy_url

        try:
            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.get(self.WORKANA_JOBS_URL, params=params)
                
                # Check for Cloudflare / block indicators
                is_cf = self._is_cloudflare_block(response)
                
                if is_cf:
                    blocked = True
                    self.was_blocked = True
                    logger.warning(f"Fast Scraper bloqueado pelo Cloudflare na página {page_num}!")
                    return []
                    
                if response.status_code != 200:
                    logger.error(f"Status {response.status_code} na página {page_num}")
                    return []
                
                soup = BeautifulSoup(response.text, 'html.parser')
                search_tag = soup.find('search')
                
                if not search_tag:
                    return []
                
                results_attr = search_tag.get(':results-initials')
                if not results_attr:
                    return []
                
                decoded_json = html.unescape(results_attr)
                data = json.loads(decoded_json)
                
                projects_data = data.get('results', [])
                page_projects = []
                
                for p_dict in projects_data:
                    p = await self._extract_project_from_json(p_dict)
                    if p:
                        page_projects.append(p)
                
                success = True
                return page_projects
                
        except Exception as e:
            logger.error(f"Erro na página {page_num}: {e}")
            return []
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            if user_id:
                try:
                    await crud.update_scraping_stats(
                        user_id=user_id,
                        success=success,
                        blocked=blocked,
                        duration_ms=duration_ms
                    )
                except Exception as metrics_error:
                    logger.warning(f"Falha ao registrar métricas de scraping: {metrics_error}")

    async def _extract_project_from_json(self, data: dict) -> Optional[Project]:
        """Extrai um projeto de um dicionário (JSON do Workana)."""
        return await parse_project_json(data, self.WORKANA_BASE_URL)

        # Implementação legada mantida temporariamente abaixo para facilitar rollback.
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
            meta_pattern = r'\n+(?:Categoria|Subcategoria|Tamanho do projeto|Do que você precisa\?|Qual é o alcance|E-commerce|Isso é um projeto|Duração|Quantidade de pessoas)\b'
            parts = re.split(meta_pattern, desc, flags=re.IGNORECASE)
            if len(parts) > 1:
                desc = parts[0]
            
            # Fallback para versões coladas "Categoria:..."
            meta_labels_fallback = [
                r'Categoria:', r'Subcategoria:', r'Tamanho do projeto:', r'Do que você precisa\?:'
            ]
            for label in meta_labels_fallback:
                parts = re.split(label, desc, flags=re.IGNORECASE)
                if len(parts) > 1:
                    desc = parts[0]

            desc = re.sub(r'\n{3,}', '\n\n', desc).strip()

            # Extração de país e pagamento verificado
            country_html = data.get('country', '')
            client_country = None
            if country_html:
                client_country = BeautifulSoup(country_html, 'html.parser').get_text(strip=True)
                
            payment_verified = bool(data.get('hasVerifiedPaymentMethod', False))

            return Project(
                id=slug,
                title=title,
                description=desc,
                budget=budget,
                skills=skills,
                proposals_count=proposals,
                posted_at=data.get('postedDate'),
                url=url,
                client_country=client_country,
                payment_verified=payment_verified
            )
        except Exception as e:
            logger.warning(f"Erro ao processar JSON de projeto: {e}")
            return None
    async def get_project_details(self, project_id: str, user_id: Optional[str] = None) -> Optional[Project]:
        """Obtém detalhes de um projeto via HTTP direto (rápido)."""
        import time
        from app.database import crud
        from app.config import settings
        from app.automation.antiban import antiban

        start_time = time.time()
        success = False
        blocked = False
        
        url = f"{self.WORKANA_BASE_URL}/job/{project_id}"
        logger.info(f"⚡ Fast Details: {url}")
        
        headers = self.headers.copy()
        headers["User-Agent"] = antiban.get_random_user_agent()
        
        client_kwargs = {
            "headers": headers,
            "follow_redirects": True,
            "timeout": 15.0
        }
        if settings.proxy_url:
            client_kwargs["proxy"] = settings.proxy_url

        try:
            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.get(url)
                
                # Check for Cloudflare / block indicators
                is_cf = response.status_code in (403, 503) or any(
                    ind in response.text.lower() for ind in ["cloudflare", "just a moment", "attention required", "turnstile"]
                )
                
                if is_cf:
                    blocked = True
                    self.was_blocked = True
                    logger.warning(f"Fast Scraper blocked by Cloudflare (WAF) on details for {project_id}!")
                    return None
                    
                if response.status_code != 200:
                    logger.error(f"Status {response.status_code} ao obter detalhes de {project_id}")
                    return None
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # No Workana, detalhes do projeto costumam estar em um objeto JSON num script
                # ou podemos extrair do DOM. O Fast scraper prefere JSON se disponível.
                # Mas para simplificar aqui, vamos extrair do DOM usando seletores básicos.
                
                title_el = soup.find('h1', class_='project-title') or soup.find('h1')
                title = title_el.get_text(strip=True) if title_el else "Sem título"
                
                desc_el = soup.find('div', class_='project-details') or soup.find('div', class_='description')
                description = ""
                if desc_el:
                    description = desc_el.get_text(separator='\n', strip=True)
                
                budget_el = soup.find('span', class_='budget') or soup.find('div', class_='budget')
                budget = budget_el.get_text(strip=True) if budget_el else None
                
                # Nome do cliente - geralmente em um link dentro da seção do cliente
                client_el = soup.select_one('.client-name a, .client-info h4, .project-author a')
                client_name = client_el.get_text(strip=True) if client_el else None
                
                success = True
                return Project(
                    id=project_id,
                    title=title,
                    description=description,
                    budget=budget,
                    skills=[],
                    url=url
                )
        except Exception as e:
            logger.error(f"Erro ao obter detalhes Fast ({project_id}): {e}")
            return None
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            if user_id:
                try:
                    await crud.update_scraping_stats(
                        user_id=user_id,
                        success=success,
                        blocked=blocked,
                        duration_ms=duration_ms
                    )
                except Exception as metrics_error:
                    logger.warning(f"Falha ao registrar métricas de scraping: {metrics_error}")
