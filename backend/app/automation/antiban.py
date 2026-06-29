"""
Sistema Anti-Ban para automação do Workana.
Implementa diversas técnicas para evitar detecção e banimento, persistindo estados no DB por usuário.
"""
import asyncio
import random
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from loguru import logger

# Dynamic User-Agents via fake-useragent
try:
    from fake_useragent import UserAgent
    ua = UserAgent()
except Exception:
    ua = None


@dataclass
class AntibanConfig:
    """Configurações do sistema anti-ban."""
    
    # Delays
    min_delay_ms: int = 1500
    max_delay_ms: int = 4000
    typing_delay_min_ms: int = 50
    typing_delay_max_ms: int = 150
    
    # Limites de ações
    max_proposals_per_day: int = 8
    max_proposals_per_hour: int = 3
    max_searches_per_hour: int = 10
    max_logins_per_day: int = 5
    
    # Pausas obrigatórias
    min_pause_between_proposals_minutes: int = 10
    max_pause_between_proposals_minutes: int = 30
    long_break_after_proposals: int = 5  # Após X propostas, fazer pausa longa
    long_break_duration_minutes: int = 60
    
    # Horário de operação (para parecer humano)
    working_hours_start: int = 8  # 8h
    working_hours_end: int = 22   # 22h
    respect_working_hours: bool = True
    
    # Comportamento humano
    simulate_mouse_movements: bool = True
    random_scroll_before_action: bool = True
    read_time_per_100_chars_ms: int = 500  # Tempo para "ler" conteúdo
    
    # Sessão
    max_session_duration_minutes: int = 120
    take_breaks_every_minutes: int = 30
    break_duration_minutes: int = 5


@dataclass
class AntibanStats:
    """Estatísticas do sistema anti-ban (in-memory/fallback)."""
    proposals_sent_today: int = 0
    proposals_sent_this_hour: int = 0
    searches_this_hour: int = 0
    logins_today: int = 0
    last_proposal_time: Optional[datetime] = None
    last_search_time: Optional[datetime] = None
    last_login_time: Optional[datetime] = None
    session_start_time: Optional[datetime] = None
    last_break_time: Optional[datetime] = None
    consecutive_proposals: int = 0
    total_actions_today: int = 0
    
    def reset_hourly(self):
        """Reseta contadores horários."""
        self.proposals_sent_this_hour = 0
        self.searches_this_hour = 0
    
    def reset_daily(self):
        """Reseta contadores diários."""
        self.proposals_sent_today = 0
        self.logins_today = 0
        self.total_actions_today = 0
        self.consecutive_proposals = 0


class AntibanSystem:
    """Sistema anti-ban para automação segura do Workana com persistência no DB por usuário."""
    
    # User agents realistas como fallback
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    ]
    
    # Resoluções de tela realistas
    SCREEN_RESOLUTIONS = [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1536, "height": 864},
        {"width": 1440, "height": 900},
        {"width": 1280, "height": 720},
        {"width": 2560, "height": 1440},
    ]
    
    # Locales (Enforcing BR for currency consistency)
    LOCALES = ["pt-BR"]
    
    def __init__(self, config: Optional[AntibanConfig] = None):
        self.config = config or AntibanConfig()
        self.in_memory_stats = AntibanStats()
        self._last_hourly_reset = datetime.now()
        self._last_daily_reset = datetime.now().date()
        self._warnings: List[str] = []
    
    @property
    def stats(self):
        """Fallback property for backwards compatibility with in-memory stats."""
        return self.in_memory_stats

    def get_random_user_agent(self) -> str:
        """Retorna um user agent aleatório ou dinâmico se fake-useragent estiver carregado."""
        if ua:
            try:
                return ua.random
            except Exception:
                pass
        return random.choice(self.USER_AGENTS)
    
    def get_random_viewport(self) -> Dict[str, int]:
        """Retorna uma resolução de tela aleatória."""
        return random.choice(self.SCREEN_RESOLUTIONS)
    
    def get_random_locale(self) -> str:
        """Retorna um locale aleatório."""
        return random.choice(self.LOCALES)
    
    async def random_delay(self, min_ms: Optional[int] = None, max_ms: Optional[int] = None):
        """Aplica um delay aleatório entre ações."""
        min_delay = min_ms or self.config.min_delay_ms
        max_delay = max_ms or self.config.max_delay_ms
        delay = random.randint(min_delay, max_delay)
        
        # Adicionar variação extra ocasionalmente (parecer mais humano)
        if random.random() < 0.2:  # 20% de chance
            delay += random.randint(500, 2000)
        
        logger.debug(f"Aguardando {delay}ms...")
        await asyncio.sleep(delay / 1000)
    
    async def human_typing_delay(self):
        """Delay para simular digitação humana."""
        delay = random.randint(
            self.config.typing_delay_min_ms,
            self.config.typing_delay_max_ms
        )
        await asyncio.sleep(delay / 1000)
    
    async def simulate_reading_time(self, text: str):
        """Simula tempo de leitura baseado no tamanho do texto."""
        char_count = len(text)
        base_time = (char_count / 100) * self.config.read_time_per_100_chars_ms
        
        # Adicionar variação
        variation = random.uniform(0.8, 1.3)
        read_time = base_time * variation
        
        logger.debug(f"Simulando leitura de {char_count} caracteres ({read_time:.0f}ms)...")
        await asyncio.sleep(read_time / 1000)
    
    def _check_and_reset_in_memory(self):
        """Reseta contadores em memória se necessário."""
        now = datetime.now()
        
        # Reset horário
        if now - self._last_hourly_reset >= timedelta(hours=1):
            self.in_memory_stats.reset_hourly()
            self._last_hourly_reset = now
            logger.info("Contadores horários em memória resetados")
        
        # Reset diário
        if now.date() > self._last_daily_reset:
            self.in_memory_stats.reset_daily()
            self._last_daily_reset = now.date()
            logger.info("Contadores diários em memória resetados")

    def _safe_now(self, dt: Optional[datetime]) -> datetime:
        """Retorna datetime.now com base no timezone do datetime informado."""
        if dt is not None and dt.tzinfo is not None:
            return datetime.now(timezone.utc)
        return datetime.now()

    async def _update_db_stats(self, user_id: Any, update_func) -> Any:
        """Atualiza estatísticas no banco de dados com tratamento de lock otimista (retries)."""
        from app.database.models import async_session, AntibanStats as AntibanStatsModel
        from sqlalchemy import select
        from sqlalchemy.orm.exc import StaleDataError
        
        max_retries = 5
        for attempt in range(max_retries):
            async with async_session() as session:
                try:
                    result = await session.execute(
                        select(AntibanStatsModel).where(AntibanStatsModel.user_id == user_id)
                    )
                    stats = result.scalar_one_or_none()
                    
                    if not stats:
                        stats = AntibanStatsModel(user_id=user_id)
                        session.add(stats)
                        try:
                            await session.commit()
                        except Exception:
                            await session.rollback()
                            result = await session.execute(
                                select(AntibanStatsModel).where(AntibanStatsModel.user_id == user_id)
                            )
                            stats = result.scalar_one()
                    
                    # Verificar e resetar contadores baseados no tempo
                    now = datetime.now(timezone.utc)
                    
                    # Reset horário
                    last_hourly = stats.last_hourly_reset
                    if last_hourly.tzinfo is None:
                        last_hourly = last_hourly.replace(tzinfo=timezone.utc)
                    if now - last_hourly >= timedelta(hours=1):
                        stats.proposals_sent_this_hour = 0
                        stats.searches_this_hour = 0
                        stats.last_hourly_reset = now
                    
                    # Reset diário
                    last_daily = stats.last_daily_reset
                    if last_daily.tzinfo is None:
                        last_daily = last_daily.replace(tzinfo=timezone.utc)
                    if now.date() > last_daily.date():
                        stats.proposals_sent_today = 0
                        stats.logins_today = 0
                        stats.total_actions_today = 0
                        stats.consecutive_proposals = 0
                        stats.last_daily_reset = now
                    
                    # Executar callback de atualização
                    if asyncio.iscoroutinefunction(update_func):
                        await update_func(stats)
                    else:
                        update_func(stats)
                    
                    await session.commit()
                    return stats
                except StaleDataError:
                    await session.rollback()
                    if attempt == max_retries - 1:
                        logger.error(f"Erro de concorrência persistente ao atualizar AntibanStats para o usuário {user_id}")
                        raise
                    # Backoff aleatório pequeno antes de tentar novamente
                    await asyncio.sleep(random.uniform(0.05, 0.2))
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Erro inesperado no banco ao gerenciar AntibanStats: {e}")
                    raise

    async def _get_stats_for_checking(self, user_id: Any):
        """Retorna uma representação transiente dos contadores, com reset lógico em tempo real."""
        from app.database.models import async_session, AntibanStats as AntibanStatsModel
        from sqlalchemy import select
        
        async with async_session() as session:
            result = await session.execute(
                select(AntibanStatsModel).where(AntibanStatsModel.user_id == user_id)
            )
            stats = result.scalar_one_or_none()
            
            if not stats:
                return AntibanStatsModel(user_id=user_id)
            
            now = datetime.now(timezone.utc)
            
            # Reset lógico horário (apenas para leitura rápida)
            last_hourly = stats.last_hourly_reset
            if last_hourly.tzinfo is None:
                last_hourly = last_hourly.replace(tzinfo=timezone.utc)
            if now - last_hourly >= timedelta(hours=1):
                stats.proposals_sent_this_hour = 0
                stats.searches_this_hour = 0
                
            # Reset lógico diário
            last_daily = stats.last_daily_reset
            if last_daily.tzinfo is None:
                last_daily = last_daily.replace(tzinfo=timezone.utc)
            if now.date() > last_daily.date():
                stats.proposals_sent_today = 0
                stats.logins_today = 0
                stats.total_actions_today = 0
                stats.consecutive_proposals = 0
                
            return stats

    def is_within_working_hours(self) -> bool:
        """Verifica se está dentro do horário de operação."""
        if not self.config.respect_working_hours:
            return True
        
        current_hour = datetime.now().hour
        return self.config.working_hours_start <= current_hour < self.config.working_hours_end
    
    async def can_send_proposal(self, user_id: Optional[Any] = None) -> tuple[bool, str]:
        """Verifica se pode enviar uma proposta agora."""
        if user_id is None:
            self._check_and_reset_in_memory()
            stats = self.in_memory_stats
        else:
            stats = await self._get_stats_for_checking(user_id)
        
        # Verificar horário de operação
        if not self.is_within_working_hours():
            return False, f"Fora do horário de operação ({self.config.working_hours_start}h-{self.config.working_hours_end}h)"
        
        # Verificar limite diário
        if stats.proposals_sent_today >= self.config.max_proposals_per_day:
            return False, f"Limite diário atingido ({self.config.max_proposals_per_day} propostas)"
        
        # Verificar limite horário
        if stats.proposals_sent_this_hour >= self.config.max_proposals_per_hour:
            return False, f"Limite horário atingido ({self.config.max_proposals_per_hour} propostas/hora)"
        
        # Verificar tempo desde última proposta
        if stats.last_proposal_time:
            now = self._safe_now(stats.last_proposal_time)
            time_since_last = now - stats.last_proposal_time
            min_wait = timedelta(minutes=self.config.min_pause_between_proposals_minutes)
            if time_since_last < min_wait:
                remaining = (min_wait - time_since_last).seconds // 60
                return False, f"Aguarde {remaining} minutos antes da próxima proposta"
        
        # Verificar se precisa de pausa longa
        if stats.consecutive_proposals >= self.config.long_break_after_proposals:
            return False, f"Pausa obrigatória após {self.config.long_break_after_proposals} propostas consecutivas"
        
        return True, "OK"
    
    async def can_search(self, user_id: Optional[Any] = None) -> tuple[bool, str]:
        """Verifica se pode fazer uma busca agora."""
        if user_id is None:
            self._check_and_reset_in_memory()
            stats = self.in_memory_stats
        else:
            stats = await self._get_stats_for_checking(user_id)
        
        if not self.is_within_working_hours():
            return False, "Fora do horário de operação"
        
        if stats.searches_this_hour >= self.config.max_searches_per_hour:
            return False, f"Limite de buscas por hora atingido ({self.config.max_searches_per_hour})"
        
        return True, "OK"
    
    async def can_login(self, user_id: Optional[Any] = None) -> tuple[bool, str]:
        """Verifica se pode fazer login agora."""
        if user_id is None:
            self._check_and_reset_in_memory()
            stats = self.in_memory_stats
        else:
            stats = await self._get_stats_for_checking(user_id)
        
        if stats.logins_today >= self.config.max_logins_per_day:
            return False, f"Limite de logins diários atingido ({self.config.max_logins_per_day})"
        
        return True, "OK"
    
    async def register_proposal_sent(self, user_id: Optional[Any] = None):
        """Registra envio de uma proposta."""
        if user_id is None:
            self._check_and_reset_in_memory()
            self.in_memory_stats.proposals_sent_today += 1
            self.in_memory_stats.proposals_sent_this_hour += 1
            self.in_memory_stats.consecutive_proposals += 1
            self.in_memory_stats.last_proposal_time = datetime.now()
            self.in_memory_stats.total_actions_today += 1
            logger.info(f"Proposta registrada em memória: {self.in_memory_stats.proposals_sent_today}/{self.config.max_proposals_per_day} hoje")
        else:
            def update(s):
                s.proposals_sent_today += 1
                s.proposals_sent_this_hour += 1
                s.consecutive_proposals += 1
                s.last_proposal_time = datetime.now(timezone.utc)
                s.total_actions_today += 1
            await self._update_db_stats(user_id, update)
            logger.info(f"Proposta registrada no banco para usuário {user_id}")
    
    async def register_search(self, user_id: Optional[Any] = None):
        """Registra uma busca."""
        if user_id is None:
            self.in_memory_stats.searches_this_hour += 1
            self.in_memory_stats.last_search_time = datetime.now()
            self.in_memory_stats.total_actions_today += 1
        else:
            def update(s):
                s.searches_this_hour += 1
                s.last_search_time = datetime.now(timezone.utc)
                s.total_actions_today += 1
            await self._update_db_stats(user_id, update)
    
    async def register_login(self, user_id: Optional[Any] = None):
        """Registra um login."""
        if user_id is None:
            self.in_memory_stats.logins_today += 1
            self.in_memory_stats.last_login_time = datetime.now()
            self.in_memory_stats.session_start_time = datetime.now()
            self.in_memory_stats.total_actions_today += 1
        else:
            def update(s):
                s.logins_today += 1
                s.last_login_time = datetime.now(timezone.utc)
                s.session_start_time = datetime.now(timezone.utc)
                s.total_actions_today += 1
            await self._update_db_stats(user_id, update)
    
    async def reset_consecutive_proposals(self, user_id: Optional[Any] = None):
        """Reseta contador de propostas consecutivas (após pausa)."""
        if user_id is None:
            self.in_memory_stats.consecutive_proposals = 0
        else:
            def update(s):
                s.consecutive_proposals = 0
            await self._update_db_stats(user_id, update)
    
    async def wait_before_proposal(self):
        """Aguarda tempo aleatório antes de enviar proposta."""
        min_wait = self.config.min_pause_between_proposals_minutes
        max_wait = self.config.max_pause_between_proposals_minutes
        wait_minutes = random.randint(min_wait, max_wait)
        
        logger.info(f"Aguardando {wait_minutes} minutos antes da próxima proposta...")
        await asyncio.sleep(wait_minutes * 60)
    
    async def take_long_break(self, user_id: Optional[Any] = None):
        """Faz uma pausa longa obrigatória."""
        duration = self.config.long_break_duration_minutes
        logger.warning(f"Iniciando pausa longa de {duration} minutos...")
        await asyncio.sleep(duration * 60)
        await self.reset_consecutive_proposals(user_id)
        
        if user_id is None:
            self.in_memory_stats.last_break_time = datetime.now()
        else:
            def update(s):
                s.last_break_time = datetime.now(timezone.utc)
            await self._update_db_stats(user_id, update)
        logger.info("Pausa longa concluída")
    
    def get_browser_context_options(self) -> Dict[str, Any]:
        """Retorna opções para contexto do navegador com anti-detecção."""
        viewport = self.get_random_viewport()
        
        opts = {
            "viewport": viewport,
            "user_agent": self.get_random_user_agent(),
            "locale": self.get_random_locale(),
            "timezone_id": "America/Sao_Paulo",
            "geolocation": {"latitude": -23.5505, "longitude": -46.6333},  # São Paulo
            "permissions": ["geolocation"],
            "color_scheme": "light",
            "device_scale_factor": random.choice([1, 1.25, 1.5]),
            "is_mobile": False,
            "has_touch": False,
            "java_script_enabled": True,
        }
        
        # Proxy integration if configured
        from app.config import settings
        if settings.proxy_url:
            opts["proxy"] = {"server": settings.proxy_url}
            
        return opts
    
    async def get_status(self, user_id: Optional[Any] = None) -> Dict[str, Any]:
        """Retorna status atual do sistema anti-ban."""
        if user_id is None:
            self._check_and_reset_in_memory()
            stats = self.in_memory_stats
        else:
            stats = await self._get_stats_for_checking(user_id)
            
        can_proposal, proposal_msg = await self.can_send_proposal(user_id)
        can_search_now, search_msg = await self.can_search(user_id)
        can_login_now, login_msg = await self.can_login(user_id)
        
        return {
            "proposals_today": stats.proposals_sent_today,
            "max_proposals_today": self.config.max_proposals_per_day,
            "proposals_this_hour": stats.proposals_sent_this_hour,
            "max_proposals_hour": self.config.max_proposals_per_hour,
            "searches_this_hour": stats.searches_this_hour,
            "max_searches_hour": self.config.max_searches_per_hour,
            "consecutive_proposals": stats.consecutive_proposals,
            "logins_today": stats.logins_today,
            "can_send_proposal": can_proposal,
            "proposal_message": proposal_msg,
            "can_search": can_search_now,
            "search_message": search_msg,
            "can_login": can_login_now,
            "login_message": login_msg,
            "is_working_hours": self.is_within_working_hours(),
            "working_hours": f"{self.config.working_hours_start}h - {self.config.working_hours_end}h",
            "last_proposal_time": stats.last_proposal_time.isoformat() if stats.last_proposal_time else None,
            "session_start": stats.session_start_time.isoformat() if stats.session_start_time else None,
        }
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Retorna configuração atual como dicionário."""
        return {
            "min_delay_ms": self.config.min_delay_ms,
            "max_delay_ms": self.config.max_delay_ms,
            "max_proposals_per_day": self.config.max_proposals_per_day,
            "max_proposals_per_hour": self.config.max_proposals_per_hour,
            "max_searches_per_hour": self.config.max_searches_per_hour,
            "min_pause_between_proposals_minutes": self.config.min_pause_between_proposals_minutes,
            "max_pause_between_proposals_minutes": self.config.max_pause_between_proposals_minutes,
            "long_break_after_proposals": self.config.long_break_after_proposals,
            "long_break_duration_minutes": self.config.long_break_duration_minutes,
            "working_hours_start": self.config.working_hours_start,
            "working_hours_end": self.config.working_hours_end,
            "respect_working_hours": self.config.respect_working_hours,
            "simulate_mouse_movements": self.config.simulate_mouse_movements,
        }
    
    def update_config(self, config_dict: Dict[str, Any]):
        """Atualiza configuração do anti-ban."""
        for key, value in config_dict.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        logger.info("Configuração anti-ban atualizada")


# Instância global do sistema anti-ban
antiban = AntibanSystem()
