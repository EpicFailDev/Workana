
import os
import json
import asyncio
import random
from typing import Dict, Any, Optional
from loguru import logger
from playwright.async_api import BrowserContext, Page
from app.automation.components.browser_driver import BrowserDriver

class AuthHandler:
    """
    Gerencia autenticação, sessões e cookies.
    """
    
    WORKANA_BASE_URL = "https://www.workana.com"
    WORKANA_LOGIN_URL = "https://www.workana.com/login"
    
    def __init__(self, driver: BrowserDriver, session_file: str):
        self._driver = driver
        self.SESSION_FILE = session_file
        self._is_logged_in = False
        self._manual_login_in_progress = False
        self._antiban = driver._antiban # Access shared antiban from driver

    @property
    def is_logged_in(self) -> bool:
        return self._is_logged_in

    async def load_session_to_context(self, context: BrowserContext) -> bool:
        """Carrega cookies do arquivo para o contexto fornecido."""
        if not os.path.exists(self.SESSION_FILE):
            return False
        
        try:
            with open(self.SESSION_FILE, 'r') as f:
                cookies = json.load(f)
            
            if context and cookies:
                await context.add_cookies(cookies)
                logger.info("Cookies carregados no contexto.")
                return True
        except Exception as e:
            logger.error(f"Erro ao carregar sessão: {e}")
        return False

    async def save_session(self) -> bool:
        """Salva a sessão atual do driver."""
        context = self._driver.context
        if context:
            try:
                cookies = await context.cookies()
                with open(self.SESSION_FILE, 'w') as f:
                    json.dump(cookies, f)
                logger.info(f"Sessão salva em {self.SESSION_FILE}")
                return True
            except Exception as e:
                logger.error(f"Erro ao salvar sessão: {e}")
                return False
        return False

    def has_saved_session(self) -> bool:
        return os.path.exists(self.SESSION_FILE)
    
    async def clear_session(self):
        if os.path.exists(self.SESSION_FILE):
            os.remove(self.SESSION_FILE)
            logger.info("Arquivo de sessão removido.")

    async def login_with_session(self) -> bool:
        """Tenta logar reutilizando cookies."""
        try:
            # Garante que o driver esteja iniciado E tente carregar a sessão
            page = await self._driver.init_browser(use_session=True, session_loader=self.load_session_to_context)
            
            await page.goto(self.WORKANA_BASE_URL, wait_until="networkidle")
            await asyncio.sleep(2) # Delay simples
            
            if await self._check_is_logged_in(page):
                self._is_logged_in = True
                logger.success("Login via sessão recuperada com sucesso!")
                return True
            
            # Tentar ir para dashboard se não estiver claro
            if "login" not in page.url.lower():
                await page.goto(f"{self.WORKANA_BASE_URL}/dashboard", wait_until="networkidle")
                await asyncio.sleep(2)
                if await self._check_is_logged_in(page):
                     self._is_logged_in = True
                     logger.success("Login via sessão recuperada (dashboard)!")
                     return True
            
            logger.info("Sessão inválida ou expirada.")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao logar com sessão: {e}")
            return False

    async def _check_is_logged_in(self, page: Page) -> bool:
        """Verifica elementos visuais de login."""
        user_menu = await page.query_selector('[data-testid="user-menu"], .user-menu, .avatar, .profile-pic')
        if user_menu:
            return True
        if "login" not in page.url.lower() and "workana.com" in page.url:
            # As vezes a home sem login é diferente, mas se for dashboard/projects é logado
            if "/dashboard" in page.url or "/projects" in page.url:
                return True
        return False

    async def login_standard(self, email: str, password: str) -> bool:
        """Login padrão com email e senha."""
        try:
            page = await self._driver.init_browser(use_session=False)
            logger.info("Iniciando login padrão...")
            
            await page.goto(self.WORKANA_LOGIN_URL, wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(1, 3))
            
            # Email
            await page.fill('input[name="email"], input[type="email"]', email)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Senha
            await page.fill('input[name="password"], input[type="password"]', password)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Click
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(3)
            
            if await self._check_is_logged_in(page):
                self._is_logged_in = True
                await self.save_session()
                logger.success("Login padrão realizado!")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Erro no login padrão: {e}")
            return False

    async def start_manual_login(self) -> Dict[str, Any]:
        """Abre navegador visível para login manual."""
        try:
            await self._driver.close() # Fecha instância anterior
            # Reabre visível
            page = await self._driver.init_browser(use_session=False, headless=False)
            self._manual_login_in_progress = True
            
            await page.goto(self.WORKANA_LOGIN_URL, wait_until="networkidle")
            
            return {
                "success": True,
                "message": "Janela aberta. Faça login e clique em Confirmar.",
                "instructions": ["Faça login no navegador que abriu", "Volte e confirme"]
            }
        except Exception as e:
            self._manual_login_in_progress = False
            return {"success": False, "message": str(e)}

    async def confirm_manual_login(self) -> Dict[str, Any]:
        if not self._manual_login_in_progress:
            return {"success": False, "message": "Nenhum login manual iniciado."}
        
        page = self._driver.page
        if not page:
            return {"success": False, "message": "Navegador fechado."}
            
        if await self._check_is_logged_in(page):
            self._is_logged_in = True
            await self.save_session()
            self._manual_login_in_progress = False
            await self._driver.close() # Fecha janela visível
            return {"success": True, "message": "Login confirmado e sessão salva!"}
        
        # Tenta ir para dashboard pra forçar check
        try:
            await page.goto(f"{self.WORKANA_BASE_URL}/dashboard", wait_until="domcontentloaded")
            await asyncio.sleep(2)
            if await self._check_is_logged_in(page):
                self._is_logged_in = True
                await self.save_session()
                self._manual_login_in_progress = False
                await self._driver.close()
                return {"success": True, "message": "Login confirmado!"}
        except:
            pass
            
        return {"success": False, "message": "Login não detectado ainda."}

    async def logout(self):
        self._is_logged_in = False
        await self._driver.close()
