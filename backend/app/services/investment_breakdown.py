"""
Módulo de cálculo dinâmico do investimento por etapa.
Calcula automaticamente a distribuição do valor total entre as 4 etapas do desenvolvimento.
Suporta 3 níveis de preço: budget (barato), standard (médio), premium (caro).
"""

from typing import Dict, List, Tuple, Optional, Literal
from dataclasses import dataclass


@dataclass
class InvestmentStage:
    """Represents a single investment stage."""
    title: str
    description: str
    percentage: float  # Percentage of total (0-100)
    amount: float = 0.0  # Calculated amount


class InvestmentBreakdownCalculator:
    """
    Calculates dynamic investment breakdown across development stages.
    
    Supports 3 price levels with different percentage distributions:
    - budget: Lower cost, lean development
    - standard: Balanced cost, standard development
    - premium: Higher cost, comprehensive development
    """
    
    # Price level configurations
    PRICE_LEVEL_CONFIGS = {
        "budget": {
            "label": "Barato",
            "description": "Desenvolvimento enxuto e focado no essencial",
            "stages": [
                {
                    "title": "Planejamento & Arquitetura do MVP",
                    "description": "Definição de fluxos essenciais e estrutura técnica",
                    "percentage": 12.0,
                },
                {
                    "title": "Desenvolvimento do App Mobile (Frontend)",
                    "description": "Implementação multiplataforma com UI funcional",
                    "percentage": 48.0,
                },
                {
                    "title": "Backend, APIs e Integrações",
                    "description": "APIs essenciais e integrações básicas",
                    "percentage": 30.0,
                },
                {
                    "title": "Testes, Ajustes e Entrega do MVP",
                    "description": "Testes básicos e entrega do build",
                    "percentage": 10.0,
                },
            ],
        },
        "standard": {
            "label": "Médio",
            "description": "Desenvolvimento completo com boas práticas",
            "stages": [
                {
                    "title": "Planejamento & Arquitetura do MVP",
                    "description": "Definição de fluxos, estrutura técnica e regras de negócio",
                    "percentage": 15.0,
                },
                {
                    "title": "Desenvolvimento do App Mobile (Frontend)",
                    "description": "Implementação multiplataforma, UI/UX e fluxos principais",
                    "percentage": 45.0,
                },
                {
                    "title": "Backend, APIs e Integrações",
                    "description": "Chamados, chat, geolocalização e split de pagamento",
                    "percentage": 28.0,
                },
                {
                    "title": "Testes, Ajustes e Entrega do MVP",
                    "description": "Testes de fluxo, estabilidade e publicação de build",
                    "percentage": 12.0,
                },
            ],
        },
        "premium": {
            "label": "Caro",
            "description": "Desenvolvimento robusto com premium de qualidade",
            "stages": [
                {
                    "title": "Planejamento & Arquitetura do MVP",
                    "description": "Arquitetura detalhada, documentação técnica e protótipos",
                    "percentage": 18.0,
                },
                {
                    "title": "Desenvolvimento do App Mobile (Frontend)",
                    "description": "UI/UX premium, animações e experiência completa",
                    "percentage": 42.0,
                },
                {
                    "title": "Backend, APIs e Integrações",
                    "description": "Backend robusto, todas as integrações e otimizações",
                    "percentage": 27.0,
                },
                {
                    "title": "Testes, Ajustes e Entrega do MVP",
                    "description": "Testes completos, QA, ajustes finais e deploy",
                    "percentage": 13.0,
                },
            ],
        },
    }
    
    # Default stage definitions (for backward compatibility)
    STAGE_DEFINITIONS = PRICE_LEVEL_CONFIGS["standard"]["stages"]
    
    @classmethod
    def calculate_breakdown(
        cls,
        total_value: float,
        price_level: Literal["budget", "standard", "premium"] = "standard",
        custom_percentages: Dict[str, float] = None
    ) -> List[InvestmentStage]:
        """
        Calculate investment breakdown for each stage.
        
        Args:
            total_value: Total project value in BRL (R$)
            price_level: Price level (budget, standard, premium)
            custom_percentages: Optional dict with custom percentages per stage title
            
        Returns:
            List of InvestmentStage with calculated amounts
        """
        # Get stages for the selected price level
        config = cls.PRICE_LEVEL_CONFIGS.get(price_level, cls.PRICE_LEVEL_CONFIGS["standard"])
        stage_defs = config["stages"]
        
        stages = []
        
        for stage_def in stage_defs:
            # Use custom percentage if provided, otherwise use default
            percentage = stage_def["percentage"]
            if custom_percentages and stage_def["title"] in custom_percentages:
                percentage = custom_percentages[stage_def["title"]]
            
            # Calculate amount
            amount = total_value * (percentage / 100.0)
            
            stage = InvestmentStage(
                title=stage_def["title"],
                description=stage_def["description"],
                percentage=percentage,
                amount=amount
            )
            stages.append(stage)
        
        # Normalize to ensure exact total (handle rounding)
        calculated_total = sum(s.amount for s in stages)
        if calculated_total != total_value and stages:
            # Adjust the largest stage (Frontend) to match exactly
            diff = total_value - calculated_total
            for stage in stages:
                if "Frontend" in stage.title or "Mobile" in stage.title:
                    stage.amount += diff
                    break
        
        return stages
    
    @classmethod
    def format_currency(cls, value: float) -> str:
        """Format value as Brazilian Real (R$ X.XXX,XX)."""
        # Format with 2 decimal places
        formatted = f"{value:,.2f}"
        # Replace . with placeholder, , with ., then placeholder with ,
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted}"
    
    @classmethod
    def generate_breakdown_text(
        cls,
        total_value: float,
        price_level: Literal["budget", "standard", "premium"] = "standard",
        custom_percentages: Dict[str, float] = None
    ) -> str:
        """
        Generate formatted investment breakdown text.
        
        Args:
            total_value: Total project value
            price_level: Price level (budget, standard, premium)
            custom_percentages: Optional custom percentages
            
        Returns:
            Formatted text with investment breakdown
        """
        stages = cls.calculate_breakdown(total_value, price_level, custom_percentages)
        config = cls.PRICE_LEVEL_CONFIGS.get(price_level, cls.PRICE_LEVEL_CONFIGS["standard"])
        
        lines = ["💰 Detalhamento do Investimento", ""]
        
        for stage in stages:
            lines.append(f"{stage.title}")
            lines.append(f"{stage.description}")
            lines.append(f"Investimento: {cls.format_currency(stage.amount)}")
            lines.append("")  # Empty line between stages
        
        # Add total
        lines.append("💵 Investimento Total do Projeto")
        lines.append("")
        lines.append(cls.format_currency(total_value))
        
        return "\n".join(lines)
    
    @classmethod
    def get_breakdown_as_dict(
        cls,
        total_value: float,
        price_level: Literal["budget", "standard", "premium"] = "standard",
        custom_percentages: Dict[str, float] = None
    ) -> Dict:
        """
        Get breakdown as dictionary for API responses.
        
        Returns:
            Dict with stages list and formatted text
        """
        stages = cls.calculate_breakdown(total_value, price_level, custom_percentages)
        config = cls.PRICE_LEVEL_CONFIGS.get(price_level, cls.PRICE_LEVEL_CONFIGS["standard"])
        
        return {
            "total_value": total_value,
            "total_formatted": cls.format_currency(total_value),
            "price_level": price_level,
            "price_level_label": config["label"],
            "price_level_description": config["description"],
            "stages": [
                {
                    "title": s.title,
                    "description": s.description,
                    "percentage": s.percentage,
                    "amount": s.amount,
                    "amount_formatted": cls.format_currency(s.amount)
                }
                for s in stages
            ],
            "breakdown_text": cls.generate_breakdown_text(total_value, price_level, custom_percentages)
        }


# Convenience function for quick access
def calculate_investment(total_value: float) -> Dict:
    """Quick function to calculate investment breakdown."""
    return InvestmentBreakdownCalculator.get_breakdown_as_dict(total_value)


def format_investment_stage(title: str, description: str, amount: float) -> str:
    """Format a single investment stage."""
    formatted_amount = InvestmentBreakdownCalculator.format_currency(amount)
    return f"{title}\n{description}\nInvestimento: {formatted_amount}"
