import asyncio
import re
import urllib.parse
from typing import Optional, Dict, Any
import httpx
from loguru import logger
from app.config import settings

class CaptchaSolver:
    """
    Resolvedor de Captcha (2captcha / anti-captcha) para contornar bloqueios do Cloudflare/WAF.
    """

    def __init__(self):
        self.provider = settings.captcha_provider
        self.api_key = settings.captcha_api_key

    @property
    def is_configured(self) -> bool:
        return bool(self.provider and self.api_key)

    async def detect_and_solve(self, page) -> bool:
        """
        Detecta se a página atual está bloqueada por Captcha ou Cloudflare,
        e tenta resolver se configurado.
        Retorna True se resolveu ou não detectou bloqueio (sucesso/prosseguir),
        ou False se detectou bloqueio e falhou ao resolver.
        """
        if not await self.is_blocked(page):
            return True

        if not self.is_configured:
            logger.warning("Página bloqueada por WAF/Cloudflare, mas resolvedor de captcha não está configurado.")
            return False

        logger.info(f"Detectado bloqueio/WAF. Iniciando tentativa de solução via {self.provider}...")

        # 1. Tentar detectar o sitekey e tipo de captcha
        challenge_info = await self.get_challenge_info(page)
        if not challenge_info:
            # Se não encontrou sitekey, tenta o método de clique simples como último recurso se for Turnstile
            logger.info("Não foi possível extrair sitekey. Tentando simular clique no Turnstile iframe...")
            solved_by_click = await self.try_click_turnstile(page)
            return solved_by_click

        sitekey = challenge_info["sitekey"]
        captcha_type = challenge_info["type"]
        page_url = page.url

        logger.info(f"Captcha encontrado: tipo={captcha_type}, sitekey={sitekey}, url={page_url}")

        try:
            # 2. Enviar para API do resolvedor
            token = await self.solve(page_url, sitekey, captcha_type)
            if not token:
                logger.error("Falha ao obter token de solução do Captcha.")
                return False

            # 3. Injetar o token resolvido na página
            logger.info("Injetando token resolvido na página...")
            success = await self.inject_token(page, token, captcha_type)
            if success:
                # Aguardar alguns segundos para a página processar e recarregar
                await asyncio.sleep(5.0)
                # Verificar se o bloqueio sumiu
                if not await self.is_blocked(page):
                    logger.success("Captcha resolvido com sucesso e página liberada!")
                    return True
                
            logger.warning("Token injetado, mas a página ainda aparece como bloqueada.")
            return False

        except Exception as e:
            logger.error(f"Erro ao resolver captcha: {e}")
            return False

    async def is_blocked(self, page) -> bool:
        """Verifica se a página está bloqueada por WAF/Cloudflare."""
        title = await page.title()
        content = await page.content()
        
        cloudflare_indicators = [
            "Just a moment...",
            "Please turn on JS",
            "Attention Required!",
            "Cloudflare",
            "checking your browser",
            "ddos guard"
        ]
        
        # Verificar título ou elementos específicos do CF
        if any(ind.lower() in title.lower() for ind in cloudflare_indicators):
            return True
            
        if "cf-challenge" in content or "cf-turnstile" in content or "cf-cookie-banner" in content:
            return True
            
        # Verificar se existe algum iframe de Turnstile
        for frame in page.frames:
            if "challenges.cloudflare.com" in frame.url:
                return True
                
        return False

    async def get_challenge_info(self, page) -> Optional[Dict[str, str]]:
        """Extrai sitekey e tipo do Captcha da página."""
        # 1. Tentar encontrar por atributos data-sitekey
        el = await page.query_selector("[data-sitekey]")
        if el:
            sitekey = await el.get_attribute("data-sitekey")
            class_attr = await el.get_attribute("class") or ""
            if "h-captcha" in class_attr or "hcaptcha" in class_attr:
                return {"type": "hcaptcha", "sitekey": sitekey}
            return {"type": "turnstile", "sitekey": sitekey}

        # 2. Tentar varrer os frames/iframes em busca de sitekey na URL do Turnstile
        for frame in page.frames:
            url = frame.url
            if "challenges.cloudflare.com" in url:
                # URL costuma ter o sitekey em params ou path
                parsed = urllib.parse.urlparse(url)
                params = urllib.parse.parse_qs(parsed.query)
                if "sitekey" in params:
                    return {"type": "turnstile", "sitekey": params["sitekey"][0]}
                # Às vezes está no fragmento ou no path
                match = re.search(r"/([0-9a-zA-Z_-]{40})/", url)
                if match:
                    return {"type": "turnstile", "sitekey": match.group(1)}

        # 3. Procurar em scripts pelo sitekey (fallback regex)
        content = await page.content()
        # regex para encontrar chaves de turnstile ou hcaptcha (normalmente 40 caracteres)
        matches = re.findall(r"['\"](0x[0-9a-fA-F]{38,40}|[0-9a-zA-Z_-]{40})['\"]", content)
        for m in matches:
            if m.startswith("0x") or len(m) == 40:
                # Chaves Turnstile começam com 0x
                if m.startswith("0x"):
                    return {"type": "turnstile", "sitekey": m}
                return {"type": "hcaptcha", "sitekey": m}

        return None

    async def try_click_turnstile(self, page) -> bool:
        """Tenta encontrar e clicar no checkbox do Turnstile via automação."""
        try:
            for frame in page.frames:
                if "challenges.cloudflare.com" in frame.url:
                    # Encontrar o checkbox dentro do iframe
                    checkbox = await frame.query_selector("input[type='checkbox']")
                    if checkbox:
                        logger.info("Checkbox do Turnstile encontrado, clicando...")
                        await checkbox.click()
                        await asyncio.sleep(3.0)
                        return True
                    # Alternativa: clicar no contêiner principal do stage
                    stage = await frame.query_selector("#challenge-stage")
                    if stage:
                        logger.info("Stage do Turnstile encontrado, simulando clique...")
                        await stage.click()
                        await asyncio.sleep(3.0)
                        return True
            return False
        except Exception as e:
            logger.warning(f"Não foi possível clicar no Turnstile: {e}")
            return False

    async def solve(self, page_url: str, sitekey: str, captcha_type: str) -> Optional[str]:
        """Resolve o captcha e retorna o token de solução."""
        if self.provider == "2captcha":
            return await self._solve_2captcha(page_url, sitekey, captcha_type)
        elif self.provider == "anti-captcha":
            return await self._solve_anticaptcha(page_url, sitekey, captcha_type)
        return None

    async def _solve_2captcha(self, page_url: str, sitekey: str, captcha_type: str) -> Optional[str]:
        method = "turnstile" if captcha_type == "turnstile" else "hcaptcha"
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Enviar tarefa
            in_url = "http://2captcha.com/in.php"
            params = {
                "key": self.api_key,
                "method": method,
                "sitekey": sitekey,
                "pageurl": page_url,
                "json": 1
            }
            logger.debug(f"2captcha: Enviando tarefa para {page_url}")
            res = await client.post(in_url, data=params)
            res_data = res.json()
            if res_data.get("status") != 1:
                logger.error(f"2captcha error: {res_data.get('request')}")
                return None

            task_id = res_data.get("request")
            
            # 2. Obter resultado (polling)
            res_url = "http://2captcha.com/res.php"
            poll_params = {
                "key": self.api_key,
                "action": "get",
                "id": task_id,
                "json": 1
            }
            
            # Espera inicial
            await asyncio.sleep(10.0)
            
            for _ in range(24): # Máximo 2 minutos (24 * 5s)
                logger.debug(f"2captcha: Verificando status da tarefa {task_id}...")
                poll_res = await client.get(res_url, params=poll_params)
                poll_data = poll_res.json()
                if poll_data.get("status") == 1:
                    return poll_data.get("request")
                elif poll_data.get("request") != "CAPCHA_NOT_READY":
                    logger.error(f"2captcha polling error: {poll_data.get('request')}")
                    return None
                await asyncio.sleep(5.0)
                
            logger.warning("2captcha: Timeout aguardando solução.")
            return None

    async def _solve_anticaptcha(self, page_url: str, sitekey: str, captcha_type: str) -> Optional[str]:
        task_type = "TurnstileTaskProxyless" if captcha_type == "turnstile" else "HCaptchaTaskProxyless"
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Criar tarefa
            create_url = "https://api.anti-captcha.com/createTask"
            payload = {
                "clientKey": self.api_key,
                "task": {
                    "type": task_type,
                    "websiteURL": page_url,
                    "websiteKey": sitekey
                }
            }
            logger.debug(f"anti-captcha: Enviando tarefa tipo {task_type}")
            res = await client.post(create_url, json=payload)
            res_data = res.json()
            if res_data.get("errorId", 0) != 0:
                logger.error(f"anti-captcha error: {res_data.get('errorDescription')}")
                return None

            task_id = res_data.get("taskId")
            
            # 2. Obter resultado (polling)
            result_url = "https://api.anti-captcha.com/getTaskResult"
            result_payload = {
                "clientKey": self.api_key,
                "taskId": task_id
            }
            
            # Espera inicial
            await asyncio.sleep(10.0)
            
            for _ in range(24): # Máximo 2 minutos (24 * 5s)
                logger.debug(f"anti-captcha: Verificando status da tarefa {task_id}...")
                res = await client.post(result_url, json=result_payload)
                poll_data = res.json()
                if poll_data.get("errorId", 0) != 0:
                    logger.error(f"anti-captcha polling error: {poll_data.get('errorDescription')}")
                    return None
                
                status = poll_data.get("status")
                if status == "ready":
                    solution = poll_data.get("solution", {})
                    # anti-captcha retorna a solução de forma ligeiramente diferente dependendo do tipo
                    return solution.get("token") or solution.get("gRecaptchaResponse")
                
                await asyncio.sleep(5.0)
                
            logger.warning("anti-captcha: Timeout aguardando solução.")
            return None

    async def inject_token(self, page, token: str, captcha_type: str) -> bool:
        """Injeta o token resolvido no DOM e executa os callbacks correspondentes."""
        try:
            # Setar os inputs de resposta ocultos
            await page.evaluate(f"""
                (token) => {{
                    // Turnstile
                    const tsRes = document.getElementsByName('cf-turnstile-response');
                    for (let el of tsRes) el.value = token;
                    
                    // hCaptcha / reCAPTCHA fallbacks
                    const gRes = document.getElementsByName('g-recaptcha-response');
                    for (let el of gRes) el.value = token;
                    
                    const hRes = document.getElementsByName('h-captcha-response');
                    for (let el of hRes) el.value = token;
                    
                    // Disparar evento de mudança nos inputs
                    const event = new Event('change', {{ bubbles: true }});
                    for (let el of [...tsRes, ...gRes, ...hRes]) {{
                        el.dispatchEvent(event);
                    }}
                }}
            """, token)

            # Submeter o formulário se houver um formulário de captcha ou Turnstile
            form_submitted = await page.evaluate("""
                () => {
                    // Se houver um formulário contendo cf-turnstile, submete ele
                    const inputs = document.getElementsByName('cf-turnstile-response');
                    if (inputs.length > 0 && inputs[0].form) {
                        inputs[0].form.submit();
                        return true;
                    }
                    
                    // Caso contrário, tenta encontrar callbacks globais (ex: cfCallback, turnstileCallback, etc.)
                    const candidates = ['cfCallback', 'turnstileCallback', 'onSuccess', 'captchaCallback'];
                    for (let name of candidates) {
                        if (typeof window[name] === 'function') {
                            window[name]();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            
            if form_submitted:
                logger.info("Formulário submetido ou callback executado via injeção.")
            else:
                logger.info("Nenhum formulário ou callback explícito encontrado para submeter.")
                
            return True
        except Exception as e:
            logger.error(f"Erro ao injetar token: {e}")
            return False
