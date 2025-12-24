
import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger
from app.config import settings
from app.automation.antiban import antiban

class BrowserDriver:
    """
    Gerencia o ciclo de vida do navegador Playwright.
    Responsável por iniciar, configurar anti-ban e fechar o navegador.
    """
    
    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._antiban = antiban

    @property
    def page(self) -> Optional[Page]:
        return self._page

    @property
    def context(self) -> Optional[BrowserContext]:
        return self._context

    async def init_browser(self, use_session: bool = True, session_loader=None, headless: bool = None) -> Page:
        """
        Inicializa o navegador.
        
        Args:
            use_session: Se True, tenta carregar sessão (via callback).
            session_loader: Função assíncrona para carregar cookies no contexto.
            headless: Override para configuração de headless (se None, usa settings).
        """
        if self._browser is None:
            logger.info("Inicializando navegador Playwright (Componente)...")
            self._playwright = await async_playwright().start()
            
            is_headless = settings.headless if headless is None else headless
            
            self._browser = await self._playwright.chromium.launch(
                headless=is_headless,
                slow_mo=settings.slow_mo,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--start-maximized' if not is_headless else '',
                ]
            )
            
            context_options = self._antiban.get_browser_context_options()
            if not is_headless:
                context_options['viewport'] = None # Usar tamanho da janela

            self._context = await self._browser.new_context(**context_options)
            
            # Scripts Anti-Detecção
            await self._context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en-US', 'en'] });
                window.chrome = { runtime: {} };
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
            if use_session and session_loader:
                await session_loader(self._context)
            
            self._page = await self._context.new_page()
            logger.info("Navegador inicializado com sucesso!")
            
        return self._page

    async def close(self):
        """Fecha o navegador e limpa recursos."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        self._page = None
        self._context = None
        logger.info("Navegador fechado (Componente).")

    async def restart(self, **kwargs):
        """Reinicia o navegador."""
        await self.close()
        return await self.init_browser(**kwargs)
