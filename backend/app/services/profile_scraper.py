"""
Serviço para scraping do perfil público do Workana.
Este serviço coleta apenas dados públicos (sem login) para evitar violação dos ToS.
"""
import httpx
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
import re
import asyncio
from tenacity import retry, stop_after_attempt, wait_fixed


class ProfileScraperService:
    """Serviço para coletar métricas do perfil público do Workana."""
    
    # Cache simples em memória
    _cache: Dict[str, Any] = {}
    _cache_ttl = timedelta(hours=1)
    
    # Headers para simular navegador real
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    @classmethod
    def _get_cache_key(cls, url: str) -> str:
        """Gera chave de cache para a URL."""
        return f"profile_{url}"
    
    @classmethod
    def _is_cache_valid(cls, cache_key: str) -> bool:
        """Verifica se o cache ainda é válido."""
        if cache_key not in cls._cache:
            return False
        cached_time = cls._cache[cache_key].get("cached_at")
        if not cached_time:
            return False
        return datetime.utcnow() - cached_time < cls._cache_ttl
    
    @classmethod
    async def fetch_public_profile(cls, profile_url: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Busca dados do perfil público do Workana.
        
        Args:
             profile_url: URL do perfil público (ex: https://www.workana.com/freelancer/username)
             force_refresh: Se True, ignora cache e faz nova requisição
             
        Returns:
             Dict com métricas do perfil
        """
        cache_key = cls._get_cache_key(profile_url)
        
        # Verificar cache
"""
Serviço para scraping do perfil público do Workana.
Este serviço coleta apenas dados públicos (sem login) para evitar violação dos ToS.
"""
import httpx
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
import re
import asyncio
from tenacity import retry, stop_after_attempt, wait_fixed


class ProfileScraperService:
    """Serviço para coletar métricas do perfil público do Workana."""
    
    # Cache simples em memória
    _cache: Dict[str, Any] = {}
    _cache_ttl = timedelta(hours=1)
    
    # Headers para simular navegador real
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    @classmethod
    def _get_cache_key(cls, url: str) -> str:
        """Gera chave de cache para a URL."""
        return f"profile_{url}"
    
    @classmethod
    def _is_cache_valid(cls, cache_key: str) -> bool:
        """Verifica se o cache ainda é válido."""
        if cache_key not in cls._cache:
            return False
        cached_time = cls._cache[cache_key].get("cached_at")
        if not cached_time:
            return False
        return datetime.utcnow() - cached_time < cls._cache_ttl
    
    @classmethod
    async def fetch_public_profile(cls, profile_url: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Busca dados do perfil público do Workana.
        
        Args:
             profile_url: URL do perfil público (ex: https://www.workana.com/freelancer/username)
             force_refresh: Se True, ignora cache e faz nova requisição
             
        Returns:
             Dict com métricas do perfil
        """
        cache_key = cls._get_cache_key(profile_url)
        
        # Verificar cache
        if not force_refresh and cls._is_cache_valid(cache_key):
            logger.debug(f"Retornando perfil do cache: {profile_url}")
            return cls._cache[cache_key]["data"]
        
        logger.info(f"Buscando perfil público: {profile_url}")
        
        from app.config import settings
        from app.automation.antiban import antiban
        
        try:
            # Adicionar delay aleatório para simular comportamento humano
            await asyncio.sleep(1.5)
            
            headers = cls.HEADERS.copy()
            headers["User-Agent"] = antiban.get_random_user_agent()
            
            client_kwargs = {
                "headers": headers,
                "timeout": 30.0,
                "follow_redirects": True
            }
            if settings.proxy_url:
                client_kwargs["proxy"] = settings.proxy_url
                
            # Tentar primeiro com httpx (mais rápido)
            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.get(profile_url)
                response.raise_for_status()
                
                html = response.text
                metrics = cls._parse_profile_html(html, profile_url)
                
                # Se não conseguiu extrair dados profissionais, tentar com Playwright.
                if not metrics.get("display_name") or not metrics.get("projects_completed"):
                # Validação estrita: H1 deve existir
                try:
                    await page.wait_for_selector("h1", timeout=15000)
                except Exception as e:
                    logger.error(f"Erro ao carregar página do perfil (H1 não encontrado): {e}")
                    raise Exception("Página do perfil não carregou corretamente (H1 ausente)")
                
                await page.wait_for_timeout(3000)  # Esperar conteúdo dinâmico carregar
                
                # Extrair dados via JavaScript (usando raw string para evitar problemas de escape)
                data = await page.evaluate(r"""() => {
                    const result = {
                        skills: [],
                        projects_in_progress: 0,
                        hours_worked: 0,
                        success: true,
                        debug: ""
                    };
                    const bodyText = document.body.innerText;
                    
                    // 1. Nome principal
                    const h1 = document.querySelector('h1');
                    if (h1) {
                         // Limpeza básica
                         let h1Text = h1.innerText.trim();
                        h1Text = h1Text.replace(/^(Workana|Freelancer|HERO)\.?\s*/i, '');
                        if (h1Text && h1Text.length < 50) result.display_name = h1Text;
                    }
                    
                    // Fallback: se h1 parece cargo, tentar achar o nome real
                    if (!result.display_name || result.display_name.includes('Developer') || result.display_name.includes('Designer')) {
                         const nameMatch = bodyText.match(/(?:HERO|PLATINUM|GOLD|OURO|SILVER|PRATA|BRONZE|IRON|FERRO)\s+([A-Z][a-z]+\s+[A-Z]\.)/i);
                         if (nameMatch) result.display_name = nameMatch[1];
                    }
                    
                    if (!result.display_name) {
                        const ogTitle = document.querySelector('meta[property="og:title"]');
                        if (ogTitle) {
                            let content = ogTitle.getAttribute('content') || '';
                            content = content.replace(/^(Workana|Freelancer|HERO)\.?\s*/i, '');
                            content = content.split(' - ')[0].trim();
                            result.display_name = content;
                        }
                    }
                    
                    // 2. Foto de Perfil - Seletores mais robustos
                    const imgSelectors = [
                        'img.img-circle', 
                        '.profile-photo img', 
                        '.avatar img', 
                        '.profile-view img',
                        'div[class*="profile-photo"] img',
                        'img[src*="user_avatar"]',
                        'img[src*="profile_photo"]'
                    ];
                    
                    for (const sel of imgSelectors) {
                        const img = document.querySelector(sel);
                        if (img && img.src && !img.src.includes('placeholder') && !img.src.includes('default')) {
                             result.profile_photo_url = img.src;
                             break;
                        }
                    }
                    
                    // 3. País
                    const countryLink = document.querySelector('.profile-header a[href*="/freelancers/"], .profile-view a[href*="/freelancers/"]');
                    if (countryLink) {
                        result.country = countryLink.innerText.trim();
                    } else {
                        const locMatch = bodyText.match(/📍\s*([^\n]{2,30})/) || bodyText.match(/(Brasil|Argentina|Japão|México|Portugal|Espanha|United States|Japan)/i);
                        if (locMatch) result.country = (locMatch[1] || locMatch[0]).trim();
                    }
                    
                    // 4. Métricas - USAR DOUBLE BACKSLASH (Python Raw String)
                    const getMetric = (pattern) => {
                        const match = bodyText.match(new RegExp(pattern, 'is'));
                        return (match && match[1]) ? match[1].replace(/\./g, '') : null;
                    };
                    
                    // Projetos realizados
                    const pMatch = getMetric("(?:Projetos realizados|Completed projects)[\\s\\n]*(\\d+)");
                    if (pMatch) result.projects_completed = parseInt(pMatch);
                    
                    // Projetos em execução
                    const oMatch = getMetric("(?:Projetos em execução|Ongoing projects)[\\s\\n]*(\\d+)");
                    if (oMatch) result.projects_in_progress = parseInt(oMatch);
                    
                    // Horas trabalhadas
                    const hMatch = getMetric("(?:Horas trabalhadas|Hours worked)[\\s\\n]*(\\d+)");
                    if (hMatch) result.hours_worked = parseInt(hMatch);
                    
                    // Reviews
                    const revMatch = bodyText.match(/(?:Classificações dos clientes|Ratings from clients)[\s\n]*\(?(\d+)\)?/i) || 
                                     bodyText.match(/(\d+)[\s\n]*(?:reviews|classificaç|ratings)/i) ||
                                     bodyText.match(/(?:Classificações dos clientes|Ratings from clients)[\s\n]+(\d+)/i);
                    if (revMatch) {
                        const groups = Array.from(revMatch).slice(1);
                        const val = groups.find(g => g && !isNaN(g));
                        if (val) result.total_reviews = parseInt(val);
                    }
                    
                    // Ingressou
                    const mMatch = bodyText.match(/(?:Ingressou|Joined|Member since)[\s\n]+([^\n]{3,30})/i);
                    if (mMatch) result.member_since = mMatch[1].trim();
                    
                    // Último login
                    const lMatch = bodyText.match(/(?:Último login|Last login)[\s\n]+([^\n]{3,30})/i);
                    if (lMatch) result.last_login = lMatch[1].trim();
                    
                    // 6. Rating
                    const ratMatch = bodyText.match(/(\d+[.,]?\d*)[\s\n]*\/[\s\n]*5/);
                    if (ratMatch) result.average_rating = parseFloat(ratMatch[1].replace(',', '.'));
                    
                    // 7. Valor hora
                    const rateMatch = bodyText.match(/(BRL|USD|EUR|R\$|\$|€)\s*([\d.,]+)/i);
                    if (rateMatch) result.hourly_rate = rateMatch[0].trim();
                    
                    // 8. Skills
                    const skillsSet = new Set();
                    document.querySelectorAll('.skill, .badge-skill, .tag, [href*="/skills/"], .label-info').forEach(el => {
                        const txt = el.innerText.trim();
                        if (txt && txt.length < 30 && !txt.includes('\n')) skillsSet.add(txt);
                    });
                    result.skills = Array.from(skillsSet);
                    
                    result.debug = "Photo: " + (result.profile_photo_url || "MISSING");
                    return result;
                }""")
                
                await browser.close()
                
                # Merge data
                for key, value in data.items():
                    if value is not None:
                        metrics[key] = value
                
                # Validação final dos dados
                if not metrics.get("display_name"):
                    logger.warning("Nome não encontrado no scraping. Tentando novamente...")
                    raise Exception("Nome não encontrado")
                    
                if metrics.get("projects_completed") == 0 and not metrics.get("skills"):
                    # Sem projetos ou habilidades, provavelmente falhou a extração.
                    logger.warning("Métricas zeradas encontradas. Tentando novamente...")
                    raise Exception("Métricas zeradas - provável falha de carregamento")
                
                return metrics
                
        except Exception as e:
            logger.error(f"Erro Playwright: {str(e)}")
            # Propagar erro para o retry do tenacity
            raise e
    
    @classmethod
    def _parse_profile_html(cls, html: str, profile_url: str) -> Dict[str, Any]:
        """
        Extrai métricas do HTML do perfil público.
        Seletores baseados na estrutura real do Workana (analisado em Jan/2026).
        
        Args:
            html: Conteúdo HTML da página
            profile_url: URL original do perfil
            
        Returns:
            Dict com métricas extraídas
        """
        soup = BeautifulSoup(html, "html.parser")
        
        metrics = {
            "success": True,
            "profile_url": profile_url,
            "username": cls._extract_username(profile_url),
            "display_name": None,
            "projects_completed": 0,
            "projects_in_progress": 0,
            "hours_worked": 0,
            "average_rating": None,
            "total_reviews": 0,
            "member_since": None,
            "country": None,
            "hourly_rate": None,
            "skills": [],
            "last_login": None,
            "scraped_at": datetime.utcnow().isoformat()
        }
        
        try:
            # === NOME DO FREELANCER ===
            # Método 1: Meta tag og:title (mais confiável)
            og_title = soup.select_one("meta[property='og:title']")
            if og_title:
                title_content = og_title.get("content", "")
                title_content = re.sub(r'^(Workana|Freelancer)\.?\s*', '', title_content, flags=re.IGNORECASE)
                if " - " in title_content:
                    metrics["display_name"] = title_content.split(" - ")[0].strip()
                else:
                    metrics["display_name"] = title_content.strip()
            
            # Método 2: H1 da página
            if not metrics["display_name"]:
                h1 = soup.select_one("h1")
                if h1:
                    name_text = h1.get_text(strip=True)
                    metrics["display_name"] = re.sub(r'^(Workana|Freelancer)\.?\s*', '', name_text, flags=re.IGNORECASE)
            
            # === FOTO DE PERFIL ===
            photo_img = soup.select_one("img.img-circle, .profile-photo img, .avatar img, .profile-view img")
            if photo_img:
                src = photo_img.get("src")
                if src and "placeholder" not in src:
                    metrics["profile_photo_url"] = src
            
            body_text = soup.get_text()
            
            # === PAÍS e LOCALIZAÇÃO ===
            country_link = soup.select_one(".profile-header a[href*='/freelancers/'], .profile-view a[href*='/freelancers/']")
            if country_link:
                metrics["country"] = country_link.get_text(strip=True)
            
            # === MÉTRICAS (Iterar no Sidebar/Cards) ===
            # Projetos realizados / Completed projects
            projects_elem = soup.find(text=re.compile(r'Projetos realizados|Completed projects', re.IGNORECASE))
            if projects_elem:
                p_text = projects_elem.parent.get_text()
                match = re.search(r'(\d+)', p_text)
                if match: metrics["projects_completed"] = int(match.group(1))
            
            # Ingressou / Joined / Member since
            joined_elem = soup.find(text=re.compile(r'Ingressou|Joined|Member since', re.IGNORECASE))
            if joined_elem:
                metrics["member_since"] = re.sub(r'Ingressou|Joined|Member since', '', joined_elem, flags=re.IGNORECASE).strip()
            
            # === RATING e REVIEWS ===
            rating_match = re.search(r'(\d+[.,]\d+)\s*/\s*5', body_text)
            if rating_match:
                metrics["average_rating"] = float(rating_match.group(1).replace(",", "."))
            
            reviews_match = re.search(r'(Classifica.*?clientes|Ratings from clients)\s*(\d+)', body_text, re.IGNORECASE) or \
                            re.search(r'(\d+)\s*(reviews|classificaç)', body_text, re.IGNORECASE)
            if reviews_match:
                val = reviews_match.group(2) if len(reviews_match.groups()) >= 2 else reviews_match.group(1)
                if val and val.isdigit(): metrics["total_reviews"] = int(val)
            
            # === VALOR HORA ===
            rate_match = re.search(r'(BRL|USD|EUR|R\$|\$|€)\s*([\d.,]+)', body_text, re.IGNORECASE)
            if rate_match:
                metrics["hourly_rate"] = rate_match.group(0).strip()
            
            # === SKILLS ===
            skills = []
            skill_elems = soup.select(".skill.label-info, .skill, .badge-skill, .tag")
            for sk_elem in skill_elems[:20]:
                skill_text = sk_elem.get_text(strip=True)
                if skill_text and len(skill_text) < 30:
                    skills.append(skill_text)
            metrics["skills"] = list(set(skills))[:15]  # Remove duplicatas, limita a 15
            
            # === HORAS TRABALHADAS ===
            hours_pattern = re.compile(r'(\d+)\s*(hora|hour)', re.IGNORECASE)
            for elem in soup.select("li, span"):
                text = elem.get_text(strip=True)
                if "trabalh" in text.lower() or "worked" in text.lower():
                    match = hours_pattern.search(text)
                    if match:
                        metrics["hours_worked"] = int(match.group(1))
                        break
            
            # === ÚLTIMO LOGIN ===
            login_pattern = re.compile(r'(há\s+\d+\s+(hora|minuto|dia)|last seen|online)', re.IGNORECASE)
            for elem in soup.select("span, div"):
                text = elem.get_text(strip=True)
                match = login_pattern.search(text)
                if match:
                    metrics["last_login"] = text
                    break
            
        except Exception as e:
            logger.error(f"Erro ao parsear HTML do perfil: {str(e)}")
            metrics["parse_error"] = str(e)
        
        return metrics
    
    @classmethod
    def _extract_username(cls, profile_url: str) -> Optional[str]:
        """Extrai username da URL do perfil."""
        # URL format: https://www.workana.com/freelancer/username
        match = re.search(r'/freelancer/([^/?]+)', profile_url)
        if match:
            return match.group(1)
        return None
    
    @classmethod
    def _parse_level(cls, text: str) -> Optional[str]:
        """Identifica o nível do freelancer a partir do texto."""
        text_lower = text.lower()
        
        levels = {
            "hero": "HERO",
            "platina": "Platina",
            "platinum": "Platina",
            "ouro": "Ouro",
            "gold": "Ouro",
            "prata": "Prata",
            "silver": "Prata",
            "bronze": "Bronze",
            "ferro": "Ferro",
            "iron": "Ferro"
        }
        
        for key, value in levels.items():
            if key in text_lower:
                return value
        
        return None
    
    @classmethod
    def _parse_rating(cls, text: str) -> Optional[float]:
        """Extrai valor numérico de rating."""
        try:
            # Procura por padrões como "4.8", "4,8", "4.8/5"
            match = re.search(r'(\d+[.,]?\d*)', text)
            if match:
                value = float(match.group(1).replace(",", "."))
                return min(value, 5.0)  # Limita a 5 no máximo
        except:
            pass
        return None
    
    @classmethod
    def _parse_number(cls, text: str) -> int:
        """Extrai número inteiro de texto."""
        try:
            # Remove tudo exceto dígitos
            digits = re.sub(r'[^\d]', '', text)
            return int(digits) if digits else 0
        except:
            return 0
    
    @classmethod
    def validate_profile_url(cls, url: str) -> bool:
        """Valida se a URL é um perfil válido do Workana."""
        pattern = r'^https?://(www\.)?workana\.com/(pt/)?freelancer/[a-zA-Z0-9_-]+/?$'
        return bool(re.match(pattern, url))
    
    @classmethod
    def clear_cache(cls):
        """Limpa o cache de perfis."""
        cls._cache.clear()
        logger.info("Cache de perfis limpo")


# Instância global do serviço
profile_scraper = ProfileScraperService()
