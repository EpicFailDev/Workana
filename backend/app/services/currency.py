import re
from typing import Optional, Tuple
from app.config import settings

class CurrencyService:
    """
    Serviço para obter taxa de câmbio USD/BRL e converter valores.
    """
    
    @classmethod
    async def get_usd_brl_rate(cls) -> float:
        """Retorna a taxa de câmbio do Workana definida nas configurações."""
        # O usuário prefere a cotação interna do Workana (ex: 5.0) 
        # em vez da taxa de mercado variável.
        return settings.workana_conversion_rate

    @classmethod
    def parse_budget_string(cls, budget_str: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Extrai valores min/max de uma string de orçamento do Workana.
        Ex: "USD 100 - 250" -> (100.0, 250.0)
        Ex: "USD 500" -> (500.0, 500.0)
        """
        if not budget_str:
            return None, None
            
        # Limpar a string e focar nos números
        # Workana usa pontos para milhar em alguns casos, vamos remover.
        clean_str = budget_str.replace(".", "")
        numbers = re.findall(r'\d+', clean_str)
        
        if not numbers:
            return None, None
            
        vals = [float(n) for n in numbers]
        
        if len(vals) >= 2:
            return vals[0], vals[1]
        return vals[0], vals[0]

    @classmethod
    async def convert_to_brl(cls, budget_str: str) -> str:
        """Converte uma string de orçamento em USD para BRL formatado."""
        if not budget_str or "USD" not in budget_str.upper():
            return budget_str
            
        rate = await cls.get_usd_brl_rate()
        min_val, max_val = cls.parse_budget_string(budget_str)
        
        if min_val is None:
            return budget_str
            
        if min_val == max_val:
            brl_val = min_val * rate
            return f"R$ {brl_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            brl_min = min_val * rate
            brl_max = max_val * rate
            # Formatação manual para PT-BR (1.000,00)
            f_min = f"{brl_min:,.0f}".replace(",", ".")
            f_max = f"{brl_max:,.0f}".replace(",", ".")
            return f"R$ {f_min} - {f_max}"
