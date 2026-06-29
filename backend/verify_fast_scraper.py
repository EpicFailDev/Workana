import asyncio
import time
from app.api.schemas import SearchFilters
from app.automation.components.fast_scraper import FastProjectScraper
from loguru import logger

async def test_fast_scraper_speed():
    scraper = FastProjectScraper()
    filters = SearchFilters(keywords="python", pages_to_fetch=5)
    
    start_time = time.time()
    logger.info("Iniciando busca paralela (Fast)...")
    projects = await scraper.search_projects(filters)
    end_time = time.time()
    
    duration = end_time - start_time
    logger.success(f"Busca concluída em {duration:.2f} segundos.")
    logger.info(f"Total de projetos encontrados: {len(projects)}")
    
    if projects:
        p = projects[0]
        logger.info(f"Exemplo de projeto: {p.title} | Orçamento: {p.budget} | Data: {p.posted_at}")
        
        # Verificar se os campos principais estão preenchidos
        assert p.id, "ID não encontrado"
        assert p.title, "Título não encontrado"
        assert p.url, "URL não encontrada"
    else:
        logger.warning("Nenhum projeto encontrado. Isso pode ser um problema nos seletores.")

if __name__ == "__main__":
    asyncio.run(test_fast_scraper_speed())
