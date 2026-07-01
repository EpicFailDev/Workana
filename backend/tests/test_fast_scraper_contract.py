import pytest
import httpx
from app.automation.components.fast_scraper import FastProjectScraper
from app.api.schemas import SearchFilters


def test_valid_results_page_is_not_mistaken_for_cloudflare():
    response = httpx.Response(
        200,
        text='<html>cloudflare<script></script><search :results-initials="{}"></search></html>',
    )
    assert FastProjectScraper._is_cloudflare_block(response) is False


def test_cloudflare_challenge_is_detected():
    response = httpx.Response(200, text="<title>Just a moment...</title><div class='cf-chl-test'>")
    assert FastProjectScraper._is_cloudflare_block(response) is True

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
        "description": "Precisamos de um desenvolvedor backend para criar APIs.<br>Categoria: TI e Programação<br>Subcategoria: Programação Web",
        "postedDate": "há 2 horas",
        "publishedDate": "30 de junho de 2026",
        "authorName": "Cliente Exemplo",
        "isHourly": False,
        "deadlineValue": "15 dias",
        "rating": "4,8 de 5",
        "projectClientPlanLabel": "Cliente Premium",
        "popoverContent": "12 Projetos publicados\n8 Projetos pagos\nMembro desde: Janeiro 2022",
        "lastEmployerMessage": "há 10 minutos",
        "isUrgent": True,
        "isSearchFeatured": True,
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
    assert project.client_name == "Cliente Exemplo"
    assert project.client_rating == 4.8
    assert project.project_type == "fixed"
    assert project.deadline == "15 dias"
    assert project.category == "TI e Programação"
    assert project.subcategory == "Programação Web"
    assert project.budget_min is not None
    assert project.budget_max is not None
    assert project.client_projects_posted == 12
    assert project.client_projects_paid == 8
    assert project.client_member_since == "Janeiro 2022"
    assert project.last_client_activity == "há 10 minutos"
    assert project.is_urgent is True
    assert project.is_featured is True
    assert "TI e Programação" not in project.description  # Limpeza do rodapé de metadados
    assert "FastAPI" in project.skills
