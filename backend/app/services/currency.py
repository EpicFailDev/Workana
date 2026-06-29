import re
import httpx
from datetime import datetime, timedelta
from typing import Optional, Tuple
from loguru import logger
from app.config import settings

class CurrencyService:
    """
    Serviço para obter taxa de câmbio USD/BRL e converter valores.
    """
    
    _rate: float = settings.workana_conversion_rate
    _last_fetched: Optional[datetime] = None
    _cache_ttl = timedelta(hours=1)
    
    @classmethod
    async def get_usd_brl_rate(cls) -> float:
        """Retorna a taxa de câmbio USD/BRL atualizada com AwesomeAPI e cache."""
        now = datetime.now()
        # Se o cache expirou ou nunca foi buscado, tenta buscar
        if not cls._last_fetched or (now - cls._last_fetched) > cls._cache_ttl:
            try:
                logger.info("🔄 Buscando taxa de câmbio USD/BRL atualizada na AwesomeAPI...")
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get("https://economia.awesomeapi.com.br/json/last/USD-BRL")
                    if response.status_code == 200:
                        data = response.json()
                        cls._rate = float(data["USDBRL"]["bid"])
                        cls._last_fetched = now
                        logger.success(f"✓ Taxa de câmbio USD/BRL atualizada: {cls._rate}")
                    else:
                        logger.warning(f"Status incorreto AwesomeAPI: {response.status_code}. Usando fallback: {cls._rate}")
            except Exception as e:
                logger.error(f"Erro ao obter taxa de câmbio na AwesomeAPI: {e}. Usando fallback: {cls._rate}")
                # Evita retentar imediatamente em caso de erro persistente
                cls._last_fetched = now - cls._cache_ttl + timedelta(minutes=5)
                
        return cls._rate

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
