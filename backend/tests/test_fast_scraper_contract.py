import pytest
from app.automation.components.fast_scraper import FastProjectScraper
from app.api.schemas import SearchFilters

@pytest.mark.asyncio
async def test_fast_scraper_json_extraction():
    scraper = FastProjectScraper()
    
    # Mock data parecido com o formato que vem no :results-initials do HTML do Workana
    mock_project_json = {
        "title": "<strong>Desenvolvedor Python backend</strong>",
        "slug": "desenvolvedor-python-backend-1",
        "budget": "USD 500 - 1000",
        "skills": [
            {"anchorText": "Python"},
            {"anchorText": "FastAPI"}
        ],
        "totalBids": "15 propostas",
        "description": "Precisamos de um desenvolvedor backend para criar APIs.<br>Categoria: TI e Programação",
        "postedDate": "há 2 horas",
        "country": "<span class=\"country-name\">Brasil</span>",
        "hasVerifiedPaymentMethod": True
    }
    
    # Executar a extração
    project = await scraper._extract_project_from_json(mock_project_json)
    
    # Validar campos do contrato
    assert project is not None
    assert project.id == "desenvolvedor-python-backend-1"
    assert project.title == "Desenvolvedor Python backend"
    assert project.proposals_count == 15
    assert project.posted_at == "há 2 horas"
    assert project.client_country == "Brasil"
    assert project.payment_verified is True
    assert "TI e Programação" not in project.description  # Limpeza do rodapé de metadados
    assert "FastAPI" in project.skills
