import httpx
from bs4 import BeautifulSoup
from typing import List, Optional
from loguru import logger
import random
import asyncio

from app.api.schemas import SearchFilters, Project

class FastProjectScraper:
    """
    Scraper rápido usando requisições HTTP diretas (httpx + BeautifulSoup).
    Muito mais rápido que o navegador completo, mas pode ser bloqueado mais facilmente.
    """
    
    WORKANA_BASE_URL = "https://www.workana.com"
    WORKANA_JOBS_URL = "https://www.workana.com/jobs"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    async def search_projects(self, filters: SearchFilters) -> List[Project]:
        """
        Executa a busca de projetos via HTTP.
        """
        projects: List[Project] = []
        page_num = filters.page # Inicia da página solicitada
        
        base_search_url = self.WORKANA_JOBS_URL
        params = {}
        if filters.keywords: params["query"] = filters.keywords
        if filters.category: params["category"] = filters.category
        if filters.min_budget: params["budget_min"] = str(filters.min_budget)
        if filters.max_budget: params["budget_max"] = str(filters.max_budget)
        
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=30.0) as client:
            while len(projects) < filters.max_results:
                current_params = params.copy()
                if page_num > 1:
                    current_params["page"] = str(page_num)
                
                logger.info(f"Fast Scraping página {page_num}...")
                
                try:
                    response = await client.get(base_search_url, params=current_params)
                    
                    if response.status_code != 200:
                        logger.warning(f"Erro HTTP {response.status_code} na página {page_num}")
                        break
                        
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Seletores ajustados para o HTML estático (podem diferir levemente do renderizado via JS)
                    # O Workana geralmente entrega o mesmo HTML inicial
                    project_cards = soup.select('.project-item, .job-item, [data-testid="project-card"]')
                    
                    if not project_cards:
                        logger.info("Sem projetos nesta página (Fast).")
                        break
                    
                    found_on_page = 0
                    for card in project_cards:
                        if len(projects) >= filters.max_results: break
                        
                        p = self._extract_project_from_card(card)
                        if p and not any(existing.id == p.id for existing in projects):
                            projects.append(p)
                            found_on_page += 1
                    
                    logger.info(f"Extraídos {found_on_page} projetos (Fast) da página {page_num}")
                    
                    if found_on_page == 0: break
                    
                    # Verifica paginação
                    next_btn = soup.select_one('.pagination .next, .pagination-next')
                    if not next_btn:
                        break
                        
                    page_num += 1
                    # Pequeno delay para ser gentil
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    
                except Exception as e:
                    logger.error(f"Erro no Fast Scraper: {e}")
                    break
            
        return projects

    def _extract_project_from_card(self, card) -> Optional[Project]:
        try:
            # Título e Link
            title_el = card.select_one('h2 a, .project-title a')
            if not title_el: return None
            
            title = title_el.get_text(strip=True)
            ref = title_el.get('href')
            if ref and not ref.startswith("http"): ref = self.WORKANA_BASE_URL + ref
            
            pid = ref.split("/")[-1] if ref else ""
            
            # Descrição
            desc_el = card.select_one('.project-description, .project-body')
            desc = desc_el.get_text(strip=True) if desc_el else ""
            
            # Orçamento
            budget_el = card.select_one('.budget, .price')
            budget = budget_el.get_text(strip=True) if budget_el else None
            
            # Skills
            skills = []
            for s in card.select('.skill, .tag'):
                txt = s.get_text(strip=True)
                if txt: skills.append(txt)
            
            # Propostas (Texto)
            proposals = 0
            p_el = card.select_one('.proposals-count, .bids')
            p_text = p_el.get_text(strip=True) if p_el else ""
            
            if not p_text:
                full_text = card.get_text()
                import re
                m = re.search(r'(\d+)\s*(?:proposta|bid)', full_text, re.IGNORECASE)
                if m: proposals = int(m.group(1))
            else:
                import re
                m = re.search(r'\d+', p_text)
                if m: proposals = int(m.group())

            # Data
            date_el = card.select_one('.date, time')
            posted_at = date_el.get_text(strip=True) if date_el and date_el.get_text(strip=True) else None
            if not posted_at and date_el and date_el.get('title'):
                posted_at = date_el.get('title')

            return Project(
                id=pid,
                title=title,
                description=desc[:500],
                budget=budget,
                skills=skills,
                proposals_count=proposals,
                posted_at=posted_at,
                url=ref or ""
            )
        except Exception as e:
            logger.warning(f"Erro card Fast: {e}")
            return None
