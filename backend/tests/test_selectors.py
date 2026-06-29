import os
from pathlib import Path
from bs4 import BeautifulSoup
from app.automation.selectors import WorkanaSelectors

FIXTURES_DIR = Path(__file__).parent / "fixtures"

def test_search_results_selectors():
    # Carrega a fixture HTML de resultados de busca
    html_path = FIXTURES_DIR / "search_results.html"
    assert html_path.exists(), "A fixture search_results.html deve existir"
    
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        
    # 1. Encontrar todos os cards de projetos
    cards = soup.select(WorkanaSelectors.PROJECT_CARD)
    assert len(cards) == 2, "Devem ser encontrados exatamente 2 cards de projeto"
    
    # 2. Validar campos do primeiro card (Python FastAPI)
    card1 = cards[0]
    
    title_el = card1.select_one(WorkanaSelectors.CARD_TITLE)
    assert title_el is not None
    assert title_el.get_text(strip=True) == "Desenvolvedor Python FastAPI"
    assert title_el.get("href") == "/job/desenvolvedor-python-fastapi-1"
    
    desc_el = card1.select_one(WorkanaSelectors.CARD_DESCRIPTION)
    assert desc_el is not None
    assert "FastAPI" in desc_el.get_text()
    
    budget_el = card1.select_one(WorkanaSelectors.CARD_BUDGET)
    assert budget_el is not None
    assert budget_el.get_text(strip=True) == "R$ 1.000 - R$ 2.000"
    
    skills = [s.get_text(strip=True) for s in card1.select(WorkanaSelectors.CARD_SKILLS)]
    assert "Python" in skills
    assert "FastAPI" in skills
    assert len(skills) == 3
    
    bids_el = card1.select_one(WorkanaSelectors.CARD_PROPOSALS)
    assert bids_el is not None
    assert "12" in bids_el.get_text()
    
    date_el = card1.select_one(WorkanaSelectors.CARD_DATE)
    assert date_el is not None
    assert "2 horas" in date_el.get_text()
    
    # 3. Validar paginação
    next_btn = soup.select_one(WorkanaSelectors.PAGINATION_NEXT)
    assert next_btn is not None
    assert next_btn.get("href") == "/pt/jobs?page=2"

def test_project_details_selectors():
    # Carrega a fixture HTML de detalhes do projeto
    html_path = FIXTURES_DIR / "project_details.html"
    assert html_path.exists(), "A fixture project_details.html deve existir"
    
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        
    # 1. Título do projeto
    title_el = soup.select_one(WorkanaSelectors.DETAILS_TITLE)
    assert title_el is not None
    assert title_el.get_text(strip=True) == "Desenvolvedor Python FastAPI"
    
    # 2. Descrição do projeto
    desc_el = soup.select_one(WorkanaSelectors.DETAILS_DESCRIPTION)
    assert desc_el is not None
    assert "deploy no Render" in desc_el.get_text()
    
    # 3. Orçamento
    budget_el = soup.select_one(WorkanaSelectors.DETAILS_BUDGET)
    assert budget_el is not None
    assert budget_el.get_text(strip=True) == "R$ 1.000 - R$ 2.000"
    
    # 4. Detalhes do Cliente
    client_name_el = soup.select_one(WorkanaSelectors.DETAILS_CLIENT_NAME)
    assert client_name_el is not None
    assert client_name_el.get_text(strip=True) == "João Silva"
    
    client_country_el = soup.select_one(WorkanaSelectors.DETAILS_CLIENT_COUNTRY)
    assert client_country_el is not None
    assert client_country_el.get_text(strip=True) == "Brasil"
    
    # 5. Avaliação do Cliente
    rating_el = soup.select_one(WorkanaSelectors.DETAILS_RATING)
    assert rating_el is not None
    assert rating_el.get("title") == "4.8 estrelas"
    
    # 6. Sidebar (Stats)
    sidebar_el = soup.select_one(WorkanaSelectors.DETAILS_SIDEBAR)
    assert sidebar_el is not None
    assert "3 Projetos publicados" in sidebar_el.get_text()
    assert "2 Projetos pagos" in sidebar_el.get_text()
    assert "Membro desde: Junho de 2024" in sidebar_el.get_text()
