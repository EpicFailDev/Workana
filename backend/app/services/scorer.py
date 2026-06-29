import re
from typing import Dict, Any
from app.api.schemas import Project, SearchFilters

class ProjectScorer:
    """
    Calculadora de score de relevância para projetos.
    Prioriza projetos com menor concorrência, clientes verificados e correspondência de palavras-chave.
    """
    
    @classmethod
    def calculate_score(cls, project: Project, filters: SearchFilters) -> float:
        score = 50.0  # Base
        
        # 1. Priorizar menor concorrência (menos propostas)
        proposals = project.proposals_count or 0
        if proposals == 0:
            score += 30.0
        elif proposals < 5:
            score += 20.0
        elif proposals < 10:
            score += 10.0
        elif proposals < 20:
            score += 0.0
        elif proposals < 40:
            score -= 15.0
        else:
            score -= 30.0
            
        # 2. Pagamento verificado
        if project.payment_verified:
            score += 15.0
            
        # 3. Correspondência de palavras-chave no título e descrição (relevância direta)
        if filters.keywords:
            # Dividir palavras-chave por espaço ou vírgula
            keywords_list = [k.strip().lower() for k in re.split(r'[, ]+', filters.keywords) if k.strip()]
            title_lower = project.title.lower()
            desc_lower = project.description.lower()
            
            matches = 0
            for kw in keywords_list:
                if kw in title_lower:
                    matches += 2
                elif kw in desc_lower:
                    matches += 1
            
            if keywords_list:
                max_possible = len(keywords_list) * 2
                match_ratio = matches / max_possible if max_possible > 0 else 0
                score += match_ratio * 20.0  # Máximo de 20 pontos por keywords
                
        # 4. Avaliação do cliente (se disponível)
        if project.client_rating:
            score += (project.client_rating - 3.0) * 5.0  # Ex: 5 estrelas = +10, 3 estrelas = 0, 1 estrela = -10
            
        return max(0.0, min(100.0, score))  # Clamped entre 0 e 100
