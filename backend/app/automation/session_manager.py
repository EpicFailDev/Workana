"""
Gerenciador de sessão (storage_state do Playwright) do Workana.

A sessão é a fonte de verdade no banco de dados (compartilhada entre API e Worker),
com espelho em arquivo local para compatibilidade com fluxos anteriores.
"""

import json
import os
from typing import Any, Dict, Optional

from loguru import logger

from app.database import crud


def get_session_path(user_id: Any) -> str:
    """Retorna o caminho do arquivo de sessão local de um usuário."""
    return f"logs/session_{user_id}.json"


def normalize_storage_state(raw_input: Any) -> Optional[Dict[str, Any]]:
    """
    Normaliza diferentes formatos de sessão para o formato storage_state do Playwright:
    - Dict padrão do Playwright: {"cookies": [...], "origins": [...]}
    - Lista de cookies (ex: export de extensões de navegador como Cookie-Editor): [{name: ..., value: ...}]
    - Arquivo/JSON HAR (HTTP Archive): {"log": {"entries": [...]}}
    - String de cabeçalho Cookie bruta: "PHPSESSID=...; workana_session=..."
    """
    if not raw_input:
        return None

    data = raw_input
    if isinstance(raw_input, str):
        raw_str = raw_input.strip()
        if not raw_str:
            return None
        if raw_str.startswith("{") or raw_str.startswith("["):
            try:
                data = json.loads(raw_str)
            except Exception:
                data = None
        else:
            # String bruta de cookies no formato key=value; key2=val2
            cookies = []
            for part in raw_str.split(";"):
                part = part.strip()
                if "=" in part:
                    name, val = part.split("=", 1)
                    name = name.strip()
                    val = val.strip()
                    if name:
                        cookies.append(
                            {
                                "name": name,
                                "value": val,
                                "domain": ".workana.com",
                                "path": "/",
                                "expires": -1,
                                "httpOnly": False,
                                "secure": True,
                                "sameSite": "Lax",
                            }
                        )
            if cookies:
                return {"cookies": cookies, "origins": []}
            return None

    # Formato HAR (HTTP Archive)
    if isinstance(data, dict) and "log" in data and "entries" in data["log"]:
        cookies_map = {}
        for entry in data["log"].get("entries", []):
            req_cookies = entry.get("request", {}).get("cookies", [])
            for c in req_cookies:
                name = c.get("name")
                val = c.get("value")
                if name and name not in cookies_map:
                    cookies_map[name] = {
                        "name": name,
                        "value": val,
                        "domain": c.get("domain") or ".workana.com",
                        "path": c.get("path") or "/",
                        "expires": -1,
                        "httpOnly": bool(c.get("httpOnly", False)),
                        "secure": bool(c.get("secure", True)),
                        "sameSite": "Lax",
                    }
            req_headers = entry.get("request", {}).get("headers", [])
            for h in req_headers:
                if h.get("name", "").lower() == "cookie":
                    for part in h.get("value", "").split(";"):
                        if "=" in part:
                            n, v = part.strip().split("=", 1)
                            n, v = n.strip(), v.strip()
                            if n and n not in cookies_map:
                                cookies_map[n] = {
                                    "name": n,
                                    "value": v,
                                    "domain": ".workana.com",
                                    "path": "/",
                                    "expires": -1,
                                    "httpOnly": False,
                                    "secure": True,
                                    "sameSite": "Lax",
                                }
        if cookies_map:
            return {"cookies": list(cookies_map.values()), "origins": []}

    # Lista de cookies (ex: export de extensão)
    if isinstance(data, list):
        normalized_cookies = []
        for c in data:
            if isinstance(c, dict) and "name" in c and "value" in c:
                same_site = str(c.get("sameSite") or "Lax").capitalize()
                if same_site not in ("Strict", "Lax", "None"):
                    same_site = "Lax"
                exp = c.get("expirationDate") or c.get("expires") or -1
                try:
                    exp = float(exp)
                except Exception:
                    exp = -1
                normalized_cookies.append(
                    {
                        "name": str(c["name"]),
                        "value": str(c["value"]),
                        "domain": str(c.get("domain") or ".workana.com"),
                        "path": str(c.get("path") or "/"),
                        "expires": exp,
                        "httpOnly": bool(c.get("httpOnly", False)),
                        "secure": bool(c.get("secure", True)),
                        "sameSite": same_site,
                    }
                )
        if normalized_cookies:
            return {"cookies": normalized_cookies, "origins": []}

    # Dict padrão do Playwright
    if isinstance(data, dict) and ("cookies" in data or "origins" in data):
        raw_cookies = data.get("cookies", [])
        normalized_cookies = []
        for c in raw_cookies:
            if isinstance(c, dict) and "name" in c and "value" in c:
                same_site = str(c.get("sameSite") or "Lax").capitalize()
                if same_site not in ("Strict", "Lax", "None"):
                    same_site = "Lax"
                exp = c.get("expirationDate") or c.get("expires") or -1
                try:
                    exp = float(exp)
                except Exception:
                    exp = -1
                normalized_cookies.append(
                    {
                        "name": str(c["name"]),
                        "value": str(c["value"]),
                        "domain": str(c.get("domain") or ".workana.com"),
                        "path": str(c.get("path") or "/"),
                        "expires": exp,
                        "httpOnly": bool(c.get("httpOnly", False)),
                        "secure": bool(c.get("secure", True)),
                        "sameSite": same_site,
                    }
                )
        return {
            "cookies": normalized_cookies,
            "origins": data.get("origins", []),
        }

    return None


async def load_storage_state(user_id: Any, as_path: bool = False) -> Optional[Any]:
    """
    Carrega o storage_state de um usuário (DB primeiro, arquivo como fallback).

    Se `as_path` for True e o estado só existir em arquivo, retorna o caminho.
    Caso contrário, retorna o dict do storage_state (ou None).
    """
    try:
        row = await crud.get_workana_session(user_id)
        if row and row.get("session_json"):
            try:
                state = json.loads(row["session_json"])
                if state:
                    return state
            except Exception as exc:
                logger.warning(f"Sessão do banco inválida para {user_id}: {exc}")
    except Exception as exc:
        logger.warning(f"Falha ao ler sessão do banco para {user_id}: {exc}")

    # Fallback para arquivo local e caminhos conhecidos de storage_state
    candidate_paths = [
        get_session_path(user_id),
        "workana_storage_state.json",
        "backend/workana_storage_state.json",
        "/app/workana_storage_state.json",
        os.path.join(os.path.dirname(__file__), "../../../workana_storage_state.json"),
        os.path.join(os.path.dirname(__file__), "../../workana_storage_state.json"),
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    content = f.read()
                    state = normalize_storage_state(content)
                if state:
                    try:
                        await crud.save_workana_session(
                            user_id, json.dumps(state, ensure_ascii=False)
                        )
                    except Exception:
                        pass
                    return p if as_path else state
            except Exception as exc:
                logger.warning(f"Arquivo de sessão local {p} inválido para {user_id}: {exc}")

    return None


async def save_storage_state(
    user_id: Any, state: Dict[str, Any], account_email: Optional[str] = None
) -> None:
    """Persiste o storage_state do navegador no banco (e espelha em arquivo local)."""
    if not state:
        return

    session_json = json.dumps(state, ensure_ascii=False)
    try:
        await crud.save_workana_session(user_id, session_json, account_email=account_email)
    except Exception as exc:
        logger.warning(f"Não foi possível salvar a sessão no banco para {user_id}: {exc}")

    try:
        os.makedirs("logs", exist_ok=True)
        with open(get_session_path(user_id), "w", encoding="utf-8") as f:
            f.write(session_json)
    except Exception as exc:
        logger.warning(f"Não foi possível espelhar a sessão em arquivo para {user_id}: {exc}")


async def clear_storage_state(user_id: Any) -> None:
    """Remove a sessão do banco e do arquivo local."""
    try:
        await crud.delete_workana_session(user_id)
    except Exception as exc:
        logger.warning(f"Não foi possível limpar a sessão no banco para {user_id}: {exc}")

    try:
        path = get_session_path(user_id)
        if os.path.exists(path):
            os.remove(path)
    except Exception as exc:
        logger.warning(f"Não foi possível remover a sessão local para {user_id}: {exc}")


async def get_session_cookies_dict(user_id: Any) -> Dict[str, str]:
    """
    Retorna um dicionário simples de cookies {name: value} para ser injetado em clientes HTTP (ex: HTTPX).
    Filtra cookies relevantes para requisições no domínio workana.com.
    """
    state = await load_storage_state(user_id)
    if not state or not isinstance(state, dict):
        return {}

    cookies = state.get("cookies", [])
    cookies_dict = {}
    for c in cookies:
        if isinstance(c, dict) and "name" in c and "value" in c:
            domain = str(c.get("domain") or "").lower()
            if not domain or "workana.com" in domain or "wkncdn.com" in domain:
                cookies_dict[c["name"]] = c["value"]
    return cookies_dict


async def check_session_health(user_id: Any) -> Dict[str, Any]:
    """
    Verifica o estado de saúde da sessão do Workana de um usuário.
    Analisa a presença de cookies críticos e testa a validade contra o Workana.
    """
    import time
    import httpx

    account_email = None
    try:
        session_row = await crud.get_workana_session(user_id)
        if session_row and session_row.get("account_email"):
            account_email = session_row["account_email"]
        else:
            creds = await crud.get_credentials(user_id)
            if creds and creds.get("email"):
                account_email = creds["email"]
    except Exception as exc:
        logger.debug(f"Não foi possível buscar email da conta para {user_id}: {exc}")

    state = await load_storage_state(user_id)
    if not state or not isinstance(state, dict):
        return {
            "status": "disconnected",
            "valid": False,
            "message": "Nenhuma sessão do Workana encontrada. Conecte sua conta para habilitar o envio.",
            "cookies_count": 0,
            "has_cloudflare_clearance": False,
            "account_email": account_email,
        }

    cookies_list = state.get("cookies", [])
    if not cookies_list:
        return {
            "status": "empty",
            "valid": False,
            "message": "Sessão encontrada mas sem cookies registrados.",
            "cookies_count": 0,
            "has_cloudflare_clearance": False,
            "account_email": account_email,
        }

    now = time.time()
    expired_count = 0
    has_cf = False
    has_session_id = False
    cookies_dict = {}

    for c in cookies_list:
        name = c.get("name", "")
        val = c.get("value", "")
        exp = c.get("expires", -1)
        domain = str(c.get("domain") or "").lower()
        if exp and exp > 0 and exp < now:
            expired_count += 1
        if name in ("cf_clearance", "__cf_bm"):
            has_cf = True
        if name in ("PHPSESSID", "workana_session"):
            has_session_id = True
        # Filtra apenas cookies relevantes para o domínio do Workana
        if not domain or "workana.com" in domain or "wkncdn.com" in domain:
            cookies_dict[name] = val

    # Testar conectividade real com endpoint autenticado leve usando headers realistas de navegador
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }
        async with httpx.AsyncClient(
            headers=headers,
            cookies=cookies_dict,
            timeout=8.0,
            follow_redirects=False,
        ) as client:
            resp = await client.get("https://www.workana.com/dashboard/recommended_projects")
            if resp.status_code == 200:
                return {
                    "status": "healthy",
                    "valid": True,
                    "message": "Sessão ativa e autenticada com sucesso no Workana.",
                    "cookies_count": len(cookies_list),
                    "has_cloudflare_clearance": has_cf,
                    "account_email": account_email,
                    "http_status": 200,
                }
            elif resp.status_code in (301, 302, 303, 307, 308):
                location = resp.headers.get("location", "")
                if "login" in location.lower():
                    return {
                        "status": "expired",
                        "valid": False,
                        "message": "Cookies expirados no Workana. Renove seu login nas configurações.",
                        "cookies_count": len(cookies_list),
                        "has_cloudflare_clearance": has_cf,
                        "account_email": account_email,
                        "http_status": resp.status_code,
                    }
            elif resp.status_code == 403:
                return {
                    "status": "blocked_waf",
                    "valid": False,
                    "message": "Cloudflare WAF bloqueou a sondagem HTTP direta. A automação usa o navegador Playwright com emulação humana.",
                    "cookies_count": len(cookies_list),
                    "has_cloudflare_clearance": has_cf,
                    "account_email": account_email,
                    "http_status": 403,
                }
    except Exception as e:
        logger.debug(f"Teste online da sessão falhou: {e}")

    # Fallback offline baseado nos dados salvos
    is_valid = has_session_id and (len(cookies_list) - expired_count) > 0
    return {
        "status": "saved_offline" if is_valid else "potentially_expired",
        "valid": is_valid,
        "message": "Sessão salva disponível para automação."
        if is_valid
        else "A sessão pode estar expirada.",
        "cookies_count": len(cookies_list),
        "expired_cookies_count": expired_count,
        "has_cloudflare_clearance": has_cf,
        "account_email": account_email,
    }
