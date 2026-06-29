"""
Seletores CSS para o scraper do Workana.
Centraliza as strings de busca para facilitar manutenção.
"""

class WorkanaSelectors:
    """Seletores CSS para elementos do Workana."""
    
    # Listagem de projetos
    PROJECT_CARD = '.project-item, .job-item, [data-testid="project-card"]'
    CARD_TITLE = 'h2 a, .project-title a'
    CARD_DESCRIPTION = '.project-description, p'
    CARD_BUDGET = '.budget, .price'
    CARD_SKILLS = '.skill, .tag'
    CARD_PROPOSALS = '.proposals-count, .bids'
    CARD_DATE = '.date, time'
    PAGINATION_NEXT = '.pagination .next'
    
    # Detalhes do projeto
    DETAILS_TITLE = 'h1, .project-title'
    DETAILS_DESCRIPTION = '.project-description, .description'
    DETAILS_BUDGET = '.budget, .price'
    DETAILS_CLIENT_NAME = '.client-name, .employer-name'
    DETAILS_CLIENT_COUNTRY = '.client-country, .location, .country'
    DETAILS_RATING = '.stars-container, .rating'
    DETAILS_SIDEBAR = 'aside, .project-details-sidebar, #sidebar'
    DETAILS_STARS = '.fa-star'
