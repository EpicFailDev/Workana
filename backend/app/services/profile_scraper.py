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
from app.config import settings

# Blacklist de palavras-chave profissionais para evitar que cargos sejam extraídos como nome
PROFESSIONAL_KEYWORDS = [
    "developer", "designer", "writer", "programador", "desenvolvedor", "redator", "copywriter", 
    "tradutor", "translator", "specialist", "especialista", "consultant", "consultor", "manager", 
    "gerente", "gestor", "engineer", "engenheiro", "analyst", "analista", "illustrator", 
    "ilustrador", "editor", "marketing", "seo", "social media", "assistente", "assistant", 
    "suporte", "support", "admin", "full stack", "frontend", "front-end", "backend", "back-end", 
    "mobile", "web", "software", "expert", "architect", "arquiteto", "lead", "senior", "sênior", 
    "junior", "júnior", "pleno"
]

# Blacklist de habilidades para evitar itens de navegação ou categorias globais do Workana
SKILLS_BLACKLIST = [
    "design & multimedia", "design e multimídia", "design & multimídia",
    "ti & programação", "ti e programação", "it & programming",
    "tradução e conteúdos", "tradução e conteúdo", "writing & translation",
    "marketing e vendas", "sales & marketing",
    "suporte administrativo", "admin support",
    "finanças e administração", "finance & management",
    "engenharia e manufatura", "engineering & manufacturing",
    "legal", "jurídico",
    "entrar", "registrar-se", "projetos", "encontrar freelancers", "como funciona", 
    "trabalhar", "publicar um projeto", "contato", "ajuda", "blog", "sobre nós", 
    "termos de serviço", "privacidade", "workana", "freelancer", "hero", "platinum", "gold", "ouro"
]

def is_professional_title(text: Optional[str]) -> bool:
    """Verifica se um texto parece ser um cargo/título profissional em vez de um nome."""
    if not text:
        return False
    words = re.findall(r'[a-zA-Zá-úÁ-Ú]+', text.lower())
    for word in words:
        if word in PROFESSIONAL_KEYWORDS:
            return True
    return False

def clean_normalize_skills(skills_list: list) -> list:
    """Normaliza, limpa, remove duplicatas e restringe a lista de habilidades."""
    normalized = []
    seen = set()
    for skill in skills_list:
        if not skill:
            continue
        cleaned = skill.strip()
        # Substitui múltiplos espaços por um espaço simples
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned_lower = cleaned.lower()
        if len(cleaned) < 2 or len(cleaned) > 40:
            continue
        if cleaned_lower in SKILLS_BLACKLIST:
            continue
        if cleaned_lower in seen:
            continue
        seen.add(cleaned_lower)
        normalized.append(cleaned)
    return normalized[:15]

def validate_metrics_semantics(metrics: dict, final_url: str) -> bool:
    """Valida semanticamente as métricas coletadas para evitar capturar páginas quebradas/bloqueadas."""
    # 1. URL final deve ser um perfil válido
    if not profile_scraper.validate_profile_url(final_url):
        logger.error(f"Validação semântica falhou: URL final {final_url} não é um perfil válido")
        return False
        
    # 2. display_name não pode ser vazio ou conter termos profissionais (cargo)
    name = metrics.get("display_name")
    if not name:
        logger.error("Validação semântica falhou: display_name não encontrado")
        return False
        
    if is_professional_title(name):
        logger.error(f"Validação semântica falhou: display_name '{name}' é um cargo profissional")
        return False
        
    # 3. Conjunto mínimo de evidências (display_name + username + pelo menos 1 outro indicador)
    evidence_count = 0
    if metrics.get("country"):
        evidence_count += 1
    if metrics.get("member_since"):
        evidence_count += 1
    if metrics.get("skills") and len(metrics["skills"]) > 0:
        evidence_count += 1
    if metrics.get("average_rating") is not None:
        evidence_count += 1
    if metrics.get("projects_completed") is not None:
        # Perfil legítimo com zero projetos não deve falhar
        evidence_count += 1
        
    if evidence_count < 2:
        logger.error(f"Validação semântica falhou: poucas evidências ({evidence_count}) para o perfil")
        return False
        
    return True


class ProfileScraperService:
    """Serviço para coletar métricas do perfil público do Workana."""
    
    # Cache simples em memória
    _cache: Dict[str, Any] = {}
    _cache_ttl = timedelta(hours=1)
    
    # Limite de concorrência global para Chromium
    _semaphore = asyncio.Semaphore(1)
    
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
            cached_data = cls._cache[cache_key]["data"]
            if cached_data.get("success", False):
                logger.debug(f"Retornando perfil do cache: {profile_url}")
                return cached_data
        
        logger.info(f"Buscando perfil público: {profile_url}")
        
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
                
                # Se falhar a validação semântica inicial ou display_name for nulo/cargo, ir para Playwright
                if not metrics.get("display_name") or not validate_metrics_semantics(metrics, profile_url):
                    logger.info("Dados incompletos, inválidos ou zerados via HTTP, tentando com Playwright...")
                    metrics = await cls._fetch_with_playwright(profile_url)
                
                if metrics.get("success", False):
                    # Salvar no cache apenas sucessos
                    cls._cache[cache_key] = {
                        "data": metrics,
                        "cached_at": datetime.utcnow()
                    }
                    logger.info(f"Perfil coletado com sucesso: {metrics.get('display_name', 'Unknown')}")
                return metrics
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP ao buscar perfil: {e.response.status_code}")
            try:
                metrics = await cls._fetch_with_playwright(profile_url)
                if metrics.get("success", False):
                    cls._cache[cache_key] = {"data": metrics, "cached_at": datetime.utcnow()}
                return metrics
            except Exception as pe:
                return {"error": f"HTTP {e.response.status_code} / Playwright: {str(pe)}", "success": False}
        except Exception as e:
            logger.error(f"Erro ao buscar perfil: {str(e)}")
            # Tentar com Playwright como fallback de qualquer erro
            try:
                metrics = await cls._fetch_with_playwright(profile_url)
                if metrics.get("success", False):
                    cls._cache[cache_key] = {"data": metrics, "cached_at": datetime.utcnow()}
                return metrics
            except Exception as pe:
                return {"error": f"Erro principal: {str(e)} / Playwright: {str(pe)}", "success": False}
    
    @classmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def _fetch_with_playwright(cls, profile_url: str) -> Dict[str, Any]:
        """Usa Playwright para buscar perfil com JavaScript renderizado."""
        from playwright.async_api import async_playwright
        from app.automation.antiban import antiban
        
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
            "profile_photo_url": None,
            "scraped_at": datetime.utcnow().isoformat()
        }
        
        # Concorrência controlada
        async with cls._semaphore:
            p = None
            browser = None
            context = None
            page = None
            try:
                launch_kwargs = {"headless": True}
                if settings.proxy_url:
                    launch_kwargs["proxy"] = {"server": settings.proxy_url}
                    
                p = await async_playwright().start()
                browser = await p.chromium.launch(**launch_kwargs)
                
                context_options = {
                    "user_agent": antiban.get_random_user_agent(),
                    "locale": "pt-BR",
                    "timezone_id": "America/Sao_Paulo"
                }
                context = await browser.new_context(**context_options)
                page = await context.new_page()
                
                # Bloquear imagens, fontes, anúncios e analytics
                async def block_resources(route):
                    req = route.request
                    url = req.url.lower()
                    blocked_types = ["image", "font", "media"]
                    blocked_patterns = [
                        "google-analytics", "analytics", "doubleclick", "adservice", 
                        "googleadservices", "hotjar", "facebook", "pixel", "mixpanel", 
                        "sentry", "amplitude"
                    ]
                    if req.resource_type in blocked_types or any(p in url for p in blocked_patterns):
                        await route.abort()
                    else:
                        await route.continue_()
                
                await page.route("**/*", block_resources)
                
                # Aumentando timeout para 60s e esperando apenas domcontentloaded
                await page.goto(profile_url, wait_until="domcontentloaded", timeout=60000)
                
                # Validar redirecionamento para login imediatamente
                final_url = page.url
                if "/login" in final_url.lower():
                    raise Exception("Redirecionado para página de login (perfil privado ou inexistente)")
                
                # Esperar H1 do perfil ou contêiner de login de forma inteligente
                try:
                    await page.wait_for_selector("h1, .login-container, input#email", timeout=15000)
                except Exception as e:
                    logger.error(f"Erro ao carregar página do perfil (elementos esperados não encontrados): {e}")
                    raise Exception("Página do perfil não carregou corretamente (H1 ausente)")
                
                # Validar semanticamente a URL final
                final_url = page.url
                if not cls.validate_profile_url(final_url):
                    if "/login" in final_url.lower():
                        raise Exception("Redirecionado para página de login (perfil privado ou inexistente)")
                    raise Exception(f"Redirecionado para URL inválida: {final_url}")
                
                # Validar se o HTML contém CAPTCHA ou bloqueios
                page_content = await page.content()
                if "verify you are human" in page_content.lower() or "cloudflare" in page_content.lower():
                    raise Exception("Bloqueio de CAPTCHA detectado na página")
                
                body_text = await page.inner_text("body")
                if "não encontramos a página" in body_text.lower() or "página não encontrada" in body_text.lower() or "404" in body_text.lower():
                    raise Exception("Página de perfil não encontrada (404)")
                
                # Extrair dados via JavaScript
                data = await page.evaluate(r"""() => {
                    const result = {
                        skills: [],
                        projects_in_progress: 0,
                        hours_worked: 0,
                        success: true,
                        debug: ""
                    };
                    const bodyText = document.body.innerText;
                    
                    const PROFESSIONAL_KEYWORDS = [
                        "developer", "designer", "writer", "programador", "desenvolvedor", "redator", "copywriter", 
                        "tradutor", "translator", "specialist", "especialista", "consultant", "consultor", "manager", 
                        "gerente", "gestor", "engineer", "engenheiro", "analyst", "analista", "illustrator", 
                        "ilustrador", "editor", "marketing", "seo", "social media", "assistente", "assistant", 
                        "suporte", "support", "admin", "full stack", "frontend", "front-end", "backend", "back-end", 
                        "mobile", "web", "software", "expert", "architect", "arquiteto", "lead", "senior", "sênior", 
                        "junior", "júnior", "pleno"
                    ];
                    
                    const SKILLS_BLACKLIST = [
                        "design & multimedia", "design e multimídia", "design & multimídia",
                        "ti & programação", "ti e programação", "it & programming",
                        "tradução e conteúdos", "tradução e conteúdo", "writing & translation",
                        "marketing e vendas", "sales & marketing",
                        "suporte administrativo", "admin support",
                        "finanças e administração", "finance & management",
                        "engenharia e manufatura", "engineering & manufacturing",
                        "legal", "jurídico",
                        "entrar", "registrar-se", "projetos", "encontrar freelancers", "como funciona", 
                        "trabalhar", "publicar um projeto", "contato", "ajuda", "blog", "sobre nós", 
                        "termos de serviço", "privacidade", "workana", "freelancer", "hero", "platinum", "gold", "ouro"
                    ];
                    
                    const isProfessionalTitle = (text) => {
                        if (!text) return false;
                        const words = text.toLowerCase().match(/[a-zA-Zá-úÁ-Ú]+/g) || [];
                        return words.some(w => PROFESSIONAL_KEYWORDS.includes(w));
                    };
                    
                    // 1. Nome principal (com rejeição de cargos profissionais)
                    const ogTitleMeta = document.querySelector('meta[property="og:title"]');
                    const titleText = ogTitleMeta ? (ogTitleMeta.getAttribute('content') || '') : document.title;
                    
                    let candidateName = '';
                    if (titleText) {
                        let cleanTitle = titleText.split('|')[0].trim();
                        cleanTitle = cleanTitle.replace(/^(Workana|Freelancer|HERO)\.?\s*/i, '');
                        const parts = cleanTitle.split('-');
                        if (parts.length >= 2) {
                            const namePart = parts[0].trim();
                            if (!isProfessionalTitle(namePart)) {
                                candidateName = namePart;
                            }
                        } else {
                            if (!isProfessionalTitle(cleanTitle)) {
                                candidateName = cleanTitle;
                            }
                        }
                    }
                    
                    if (!candidateName) {
                        const h1 = document.querySelector('h1');
                        if (h1) {
                            let h1Text = h1.innerText.trim().replace(/^(Workana|Freelancer|HERO)\.?\s*/i, '');
                            if (h1Text && h1Text.length < 50 && !isProfessionalTitle(h1Text)) {
                                candidateName = h1Text;
                            }
                        }
                    }
                    
                    if (!candidateName) {
                        const nameMatch = bodyText.match(/(?:HERO|PLATINUM|GOLD|OURO|SILVER|PRATA|BRONZE|IRON|FERRO)\s+([A-Z][a-z]+\s+[A-Z]\.)/i);
                        if (nameMatch && !isProfessionalTitle(nameMatch[1])) {
                            candidateName = nameMatch[1];
                        }
                    }
                    
                    if (candidateName) {
                        result.display_name = candidateName;
                    }
                    
                    // 2. Foto de Perfil
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
                    
                    // 4. Métricas
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
                    
                    // Rating
                    const ratMatch = bodyText.match(/(\d+[.,]?\d*)[\s\n]*\/[\s\n]*5/);
                    if (ratMatch) result.average_rating = parseFloat(ratMatch[1].replace(',', '.'));
                    
                    // Valor hora
                    const rateMatch = bodyText.match(/(BRL|USD|EUR|R\$|\$|€)\s*([\d.,]+)/i);
                    if (rateMatch) result.hourly_rate = rateMatch[0].trim();
                    
                    // 5. Skills (restringindo ao contêiner específico e limpando navegação/globais)
                    const skillsSet = new Set();
                    let skillsContainer = document.querySelector('.skills, .profile-skills, .skills-list, [class*="skills"]');
                    if (!skillsContainer) {
                        const headings = Array.from(document.querySelectorAll('h2, h3, h4, h5'));
                        const skillsHeading = headings.find(h => /habilidades|skills/i.test(h.innerText));
                        if (skillsHeading) {
                            skillsContainer = skillsHeading.parentElement;
                        }
                    }
                    
                    const elems = skillsContainer 
                        ? skillsContainer.querySelectorAll('.skill, .badge-skill, .tag, [href*="/skills/"], .label-info')
                        : document.querySelectorAll('.skill, .badge-skill, .label-info');
                        
                    elems.forEach(el => {
                        let txt = el.innerText.trim().replace(/\s+/g, ' ');
                        if (txt && txt.length >= 2 && txt.length <= 40 && !txt.includes('\n')) {
                            const txtLower = txt.toLowerCase();
                            if (!SKILLS_BLACKLIST.includes(txtLower)) {
                                skillsSet.add(txt);
                            }
                        }
                    });
                    result.skills = Array.from(skillsSet).slice(0, 15);
                    
                    return result;
                }""")
                
                # Merge data
                for key, value in data.items():
                    if value is not None:
                        metrics[key] = value
                
                # Normalização adicional no python
                metrics["skills"] = clean_normalize_skills(metrics.get("skills", []))
                
                # Validar semantismo
                if not validate_metrics_semantics(metrics, final_url):
                    raise Exception("Falha na validação semântica dos dados coletados pelo Playwright")
                
                metrics["success"] = True
                return metrics
                
            except Exception as e:
                logger.error(f"Erro Playwright: {str(e)}")
                raise e
            finally:
                if page:
                    try:
                        await page.close()
                    except:
                        pass
                if context:
                    try:
                        await context.close()
                    except:
                        pass
                if browser:
                    try:
                        await browser.close()
                    except:
                        pass
                if p:
                    try:
                        await p.stop()
                    except:
                        pass
    
    @classmethod
    def _parse_profile_html(cls, html: str, profile_url: str) -> Dict[str, Any]:
        """
        Extrai métricas do HTML do perfil público.
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
            og_title = soup.select_one("meta[property='og:title']")
            title_text = og_title.get("content", "") if og_title else (soup.title.string if soup.title else "")
            
            candidate_name = None
            if title_text:
                clean_title = title_text.split('|')[0].strip()
                clean_title = re.sub(r'^(Workana|Freelancer|HERO)\.?\s*', '', clean_title, flags=re.IGNORECASE)
                parts = clean_title.split('-')
                if len(parts) >= 2:
                    name_part = parts[0].strip()
                    if not is_professional_title(name_part):
                        candidate_name = name_part
                else:
                    if not is_professional_title(clean_title):
                        candidate_name = clean_title
            
            if not candidate_name:
                h1 = soup.select_one("h1")
                if h1:
                    h1_text = h1.get_text(strip=True)
                    h1_text = re.sub(r'^(Workana|Freelancer|HERO)\.?\s*', '', h1_text, flags=re.IGNORECASE)
                    if h1_text and len(h1_text) < 50 and not is_professional_title(h1_text):
                        candidate_name = h1_text
            
            body_text = soup.get_text()
            if not candidate_name:
                name_match = re.search(r'(?:HERO|PLATINUM|GOLD|OURO|SILVER|PRATA|BRONZE|IRON|FERRO)\s+([A-Z][a-z]+\s+[A-Z]\.)', body_text, re.IGNORECASE)
                if name_match:
                    name_candidate = name_match.group(1)
                    if not is_professional_title(name_candidate):
                        candidate_name = name_candidate
                        
            metrics["display_name"] = candidate_name
            
            # === FOTO DE PERFIL ===
            photo_img = soup.select_one("img.img-circle, .profile-photo img, .avatar img, .profile-view img")
            if photo_img:
                src = photo_img.get("src")
                if src and "placeholder" not in src:
                    metrics["profile_photo_url"] = src
            
            # === PAÍS e LOCALIZAÇÃO ===
            country_link = soup.select_one(".profile-header a[href*='/freelancers/'], .profile-view a[href*='/freelancers/']")
            if country_link:
                metrics["country"] = country_link.get_text(strip=True)
            else:
                loc_match = re.search(r'📍\s*([^\n]{2,30})', body_text) or re.search(r'(Brasil|Argentina|Japão|México|Portugal|Espanha|United States|Japan)', body_text, re.IGNORECASE)
                if loc_match:
                    metrics["country"] = loc_match.group(1).strip()
            
            # === MÉTRICAS ===
            def get_metric(pattern):
                match = re.search(pattern, body_text, re.IGNORECASE | re.DOTALL)
                return match.group(1).replace(".", "") if match else None
            
            p_val = get_metric(r'(?:Projetos realizados|Completed projects)[\s\n]*(\d+)')
            if p_val: metrics["projects_completed"] = int(p_val)
            
            o_val = get_metric(r'(?:Projetos em execução|Ongoing projects)[\s\n]*(\d+)')
            if o_val: metrics["projects_in_progress"] = int(o_val)
            
            h_val = get_metric(r'(?:Horas trabalhadas|Hours worked)[\s\n]*(\d+)')
            if h_val: metrics["hours_worked"] = int(h_val)
            
            reviews_match = re.search(r'(?:Classificações dos clientes|Ratings from clients)[\s\n]*\(?(\d+)\)?', body_text, re.IGNORECASE) or \
                            re.search(r'(\d+)\s*(reviews|classificaç)', body_text, re.IGNORECASE)
            if reviews_match:
                metrics["total_reviews"] = int(reviews_match.group(1))
            
            # Ingressou
            joined_match = re.search(r'(?:Ingressou|Joined|Member since)[\s\n]+([^\n]{3,30})', body_text, re.IGNORECASE)
            if joined_match:
                metrics["member_since"] = joined_match.group(1).strip()
            
            rating_match = re.search(r'(\d+[.,]\d+)\s*/\s*5', body_text)
            if rating_match:
                metrics["average_rating"] = float(rating_match.group(1).replace(",", "."))
            
            rate_match = re.search(r'(BRL|USD|EUR|R\$|\$|€)\s*([\d.,]+)', body_text, re.IGNORECASE)
            if rate_match:
                metrics["hourly_rate"] = rate_match.group(0).strip()
            
            # === SKILLS ===
            skills = []
            skills_container = soup.select_one(".skills, .profile-skills, .skills-list, [class*='skills']")
            if not skills_container:
                for heading in soup.find_all(["h2", "h3", "h4", "h5"]):
                    heading_text = heading.get_text().lower()
                    if "habilidades" in heading_text or "skills" in heading_text:
                        skills_container = heading.parent
                        break
            
            if skills_container:
                skill_elems = skills_container.select(".skill.label-info, .skill, .badge-skill, .tag, [href*='/skills/']")
            else:
                skill_elems = soup.select(".skill.label-info, .skill, .badge-skill")
                
            for sk_elem in skill_elems:
                skill_text = sk_elem.get_text(strip=True)
                skills.append(skill_text)
                
            metrics["skills"] = clean_normalize_skills(skills)
            
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
            metrics["success"] = False
        
        return metrics
    
    @classmethod
    def _extract_username(cls, profile_url: str) -> Optional[str]:
        """Extrai username da URL do perfil."""
        match = re.search(r'/freelancer/([^/?]+)', profile_url)
        if match:
            return match.group(1)
        return None
    
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
