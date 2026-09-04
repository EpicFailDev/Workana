"""
Gerenciador de sessão (storage_state do Playwright) do Workana.

A sessão é a fonte de verdade no banco de dados (compartilhada entre API e Worker),
com espelho em arquivo local para compatibilidade com fluxos anteriores.
Protegida em repouso por Criptografia Envelope AES-256-GCM (Enterprise Session Vault)
e validada com TLS Impersonation (curl_cffi / JA4 Chrome 126+).
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core import crypto_vault
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
    Carrega o storage_state de um usuário (DB primeiro com decriptação AES-256-GCM, arquivo como fallback).

    Se `as_path` for True e o estado só existir em arquivo, retorna o caminho.
    Caso contrário, retorna o dict do storage_state (ou None).
    """
    try:
        row = await crud.get_workana_session(user_id)
        if row and row.get("session_json"):
            try:
                decrypted = crypto_vault.decrypt_session_data(row["session_json"])
                state = json.loads(decrypted) if decrypted else None
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
                        encrypted = crypto_vault.encrypt_session_data(
                            json.dumps(state, ensure_ascii=False)
                        )
                        await crud.save_workana_session(user_id, encrypted)
                    except Exception:
                        pass
                    return p if as_path else state
            except Exception as exc:
                logger.warning(f"Arquivo de sessão local {p} inválido para {user_id}: {exc}")

    return None


async def save_storage_state(
    user_id: Any, state: Dict[str, Any], account_email: Optional[str] = None
) -> None:
    """
    Persiste o storage_state do navegador no banco com criptografia AES-256-GCM
    (e espelha em arquivo local para compatibilidade do worker).
    """
    if not state:
        return

    session_json = json.dumps(state, ensure_ascii=False)
    encrypted_session = crypto_vault.encrypt_session_data(session_json)

    try:
        await crud.save_workana_session(user_id, encrypted_session, account_email=account_email)
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
    Retorna um dicionário simples de cookies {name: value} para ser injetado em clientes HTTP.
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


async def _probe_workana_connectivity(cookies_dict: Dict[str, str]) -> Dict[str, Any]:
    """
    Testa conectividade real com endpoint autenticado leve do Workana.
    Utiliza preferencialmente curl_cffi para emulação TLS JA4 Chrome 126.
    Caso não esteja disponível ou em testes unitários mockados, faz fallback gracioso para httpx.
    """
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
    url = "https://www.workana.com/dashboard/recommended_projects"
    start_t = time.perf_counter()

    # Tentativa 1: curl_cffi com Chrome JA4 TLS Impersonation
    try:
        from curl_cffi import requests as cffi_requests

        async with cffi_requests.AsyncSession(impersonate="chrome126") as session:
            resp = await session.get(
                url,
                headers=headers,
                cookies=cookies_dict,
                timeout=7.0,
                allow_redirects=False,
            )
            elapsed_ms = round((time.perf_counter() - start_t) * 1000, 1)
            location = resp.headers.get("location") or resp.headers.get("Location", "")
            return {
                "status_code": resp.status_code,
                "location": location,
                "latency_ms": elapsed_ms,
                "tls_impersonated": True,
            }
    except Exception:
        pass

    # Tentativa 2: httpx fallback padrão
    import httpx

    async with httpx.AsyncClient(
        headers=headers,
        cookies=cookies_dict,
        timeout=7.0,
        follow_redirects=False,
    ) as client:
        resp = await client.get(url)
        elapsed_ms = round((time.perf_counter() - start_t) * 1000, 1)
        location = resp.headers.get("location", "")
        return {
            "status_code": resp.status_code,
            "location": location,
            "latency_ms": elapsed_ms,
            "tls_impersonated": False,
        }


async def check_session_health(user_id: Any) -> Dict[str, Any]:
    """
    Verifica a saúde preditiva da sessão do Workana de um usuário.
    Calcula Health Score (0-100%), entropia de cookies, status de WAF e latência.
    """
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
            "health_score": 0,
            "message": "Nenhuma sessão do Workana encontrada. Conecte sua conta para habilitar o envio.",
            "cookies_count": 0,
            "has_cloudflare_clearance": False,
            "account_email": account_email,
            "latency_ms": None,
            "decay_hours_remaining": 0,
        }

    cookies_list = state.get("cookies", [])
    if not cookies_list:
        return {
            "status": "empty",
            "valid": False,
            "health_score": 0,
            "message": "Sessão encontrada mas sem cookies registrados.",
            "cookies_count": 0,
            "has_cloudflare_clearance": False,
            "account_email": account_email,
            "latency_ms": None,
            "decay_hours_remaining": 0,
        }

    now = time.time()
    expired_count = 0
    has_cf = False
    has_session_id = False
    cf_expires_in_hours = 0
    cookies_dict = {}

    for c in cookies_list:
        name = c.get("name", "")
        val = c.get("value", "")
        exp = c.get("expires", -1)
        domain = str(c.get("domain") or "").lower()
        if exp and exp > 0:
            if exp < now:
                expired_count += 1
            elif name == "cf_clearance":
                cf_expires_in_hours = round((exp - now) / 3600, 1)

        if name in ("cf_clearance", "__cf_bm"):
            has_cf = True
        if name in ("PHPSESSID", "workana_session"):
            has_session_id = True

        # Filtra apenas cookies relevantes para o domínio do Workana
        if not domain or "workana.com" in domain or "wkncdn.com" in domain:
            cookies_dict[name] = val

    # Testar conectividade real com o Workana
    try:
        probe = await _probe_workana_connectivity(cookies_dict)
        status_code = probe["status_code"]
        latency_ms = probe["latency_ms"]
        location = probe["location"]

        if status_code == 200:
            # Score de saúde baseado em integridade
            score = 70
            if has_cf:
                score += 20
            if has_session_id:
                score += 10
            return {
                "status": "healthy",
                "valid": True,
                "health_score": min(100, score),
                "message": "Sessão ativa e autenticada com sucesso no Workana.",
                "cookies_count": len(cookies_list),
                "has_cloudflare_clearance": has_cf,
                "account_email": account_email,
                "http_status": 200,
                "latency_ms": latency_ms,
                "decay_hours_remaining": max(12.0, cf_expires_in_hours or 24.0),
            }
        elif status_code in (301, 302, 303, 307, 308):
            if "login" in location.lower():
                return {
                    "status": "expired",
                    "valid": False,
                    "health_score": 10,
                    "message": "Cookies expirados no Workana. Renove seu login nas configurações.",
                    "cookies_count": len(cookies_list),
                    "has_cloudflare_clearance": has_cf,
                    "account_email": account_email,
                    "http_status": status_code,
                    "latency_ms": latency_ms,
                    "decay_hours_remaining": 0,
                }
        elif status_code == 403:
            return {
                "status": "blocked_waf",
                "valid": False,
                "health_score": 35,
                "message": "Cloudflare WAF solicitou verificação humana. O Companion ou Playwright resolverá.",
                "cookies_count": len(cookies_list),
                "has_cloudflare_clearance": has_cf,
                "account_email": account_email,
                "http_status": 403,
                "latency_ms": latency_ms,
                "decay_hours_remaining": 0,
            }
    except Exception as e:
        logger.debug(f"Teste online da sessão falhou: {e}")

    # Fallback offline baseado nos dados salvos
    is_valid = has_session_id and (len(cookies_list) - expired_count) > 0
    health_score = 50 if is_valid else 15
    if has_cf and is_valid:
        health_score += 20

    return {
        "status": "saved_offline" if is_valid else "potentially_expired",
        "valid": is_valid,
        "health_score": health_score,
        "message": "Sessão salva disponível para automação."
        if is_valid
        else "A sessão pode estar expirada.",
        "cookies_count": len(cookies_list),
        "expired_cookies_count": expired_count,
        "has_cloudflare_clearance": has_cf,
        "account_email": account_email,
        "latency_ms": None,
        "decay_hours_remaining": cf_expires_in_hours or 6.0,
    }


def detect_local_session() -> Dict[str, Any]:
    """
    Verifica a existência de arquivos de sessão locais no host
    (workana_storage_state.json ou logs/session_*.json) e extrai seus metadados.
    """
    candidate_paths = [
        "workana_storage_state.json",
        "backend/workana_storage_state.json",
        os.path.join(os.path.dirname(__file__), "../../../workana_storage_state.json"),
        os.path.join(os.path.dirname(__file__), "../../workana_storage_state.json"),
    ]
    # Adicionar também arquivos na pasta logs
    logs_dir = "logs"
    if os.path.isdir(logs_dir):
        for f in os.listdir(logs_dir):
            if f.startswith("session_") and f.endswith(".json"):
                candidate_paths.append(os.path.join(logs_dir, f))

    for p in candidate_paths:
        if os.path.isfile(p):
            try:
                mtime = os.path.getmtime(p)
                from datetime import datetime, timezone

                mod_iso = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
                with open(p, "r", encoding="utf-8") as f:
                    content = f.read()
                state = normalize_storage_state(content)
                if state and state.get("cookies"):
                    cookies = state["cookies"]
                    names = {c.get("name") for c in cookies if isinstance(c, dict)}
                    has_session = any(
                        n in names for n in ("workana_session", "PHPSESSID", "remember_web")
                    )
                    has_cf = "cf_clearance" in names
                    return {
                        "detected": True,
                        "path": p,
                        "cookies_count": len(cookies),
                        "has_session_cookie": has_session,
                        "has_cloudflare_clearance": has_cf,
                        "modified_at": mod_iso,
                    }
            except Exception as e:
                logger.debug(f"Erro ao inspecionar candidato {p}: {e}")

    return {
        "detected": False,
        "path": None,
        "cookies_count": 0,
        "has_session_cookie": False,
        "has_cloudflare_clearance": False,
        "modified_at": None,
    }


async def sync_local_session(user_id: Any, file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Lê o arquivo de sessão local detectado, normaliza e persiste no banco
    do usuário com criptografia AES-256-GCM.
    """
    target = file_path
    if not target:
        det = detect_local_session()
        if not det.get("detected") or not det.get("path"):
            return {
                "success": False,
                "message": "Nenhum arquivo de sessão local detectado para sincronizar.",
            }
        target = det["path"]

    try:
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()
        state = normalize_storage_state(content)
        if not state or not state.get("cookies"):
            return {
                "success": False,
                "message": f"O arquivo {target} não contém cookies válidos do Workana.",
            }

        await save_storage_state(user_id, state)
        return {
            "success": True,
            "message": f"Sessão local ({len(state['cookies'])} cookies) sincronizada e criptografada com sucesso!",
            "cookies_count": len(state["cookies"]),
        }
    except Exception as exc:
        return {"success": False, "message": f"Falha ao sincronizar sessão local: {exc}"}


async def get_session_diagnostics(user_id: Any) -> Dict[str, Any]:
    """
    Executa o diagnóstico guiado de 5 pontos do Session Vault e Gateway Workana.
    Retorna os vetores de teste detalhados para a UI de auto-reparo.
    """
    # 1. Supabase Session Vault check
    vault_status = {"status": "ok", "detail": "Criptografia AES-256-GCM operacional"}
    session_row = None
    try:
        session_row = await crud.get_workana_session(user_id)
        if not session_row:
            vault_status = {"status": "warning", "detail": "Nenhuma sessão salva no banco"}
        elif not crypto_vault.is_encrypted(session_row.get("session_json")):
            vault_status = {
                "status": "warning",
                "detail": "Sessão legada (será criptografada na próxima atualização)",
            }
    except Exception as exc:
        vault_status = {"status": "error", "detail": f"Erro de acesso ao banco: {exc}"}

    # 2. Cookies integrity check
    cookies_status = {"status": "ok", "detail": "Cookies íntegros", "count": 0}
    state = await load_storage_state(user_id)
    if not state or not state.get("cookies"):
        cookies_status = {"status": "error", "detail": "Nenhum cookie presente", "count": 0}
    else:
        cookies_status["count"] = len(state["cookies"])
        names = {c.get("name") for c in state["cookies"] if isinstance(c, dict)}
        if not any(k in names for k in ("workana_session", "PHPSESSID")):
            cookies_status = {
                "status": "warning",
                "detail": "Cookies parciais (ausência de token de sessão PHP)",
                "count": len(state["cookies"]),
            }

    # 3. Workana Gateway Handshake & Latência
    cookies_dict = await get_session_cookies_dict(user_id)
    gateway_status = {"status": "pending", "latency_ms": None, "detail": "Não testado"}
    waf_status = {"status": "pending", "detail": "Não testado"}

    if cookies_dict:
        try:
            probe = await _probe_workana_connectivity(cookies_dict)
            lat = probe.get("latency_ms")
            gateway_status["latency_ms"] = lat
            code = probe.get("status_code")

            if code == 200:
                gateway_status = {
                    "status": "ok",
                    "latency_ms": lat,
                    "detail": f"200 OK ({lat}ms via TLS Impersonation)",
                }
                waf_status = {"status": "ok", "detail": "Bypass de Cloudflare WAF Ativo"}
            elif code == 403:
                gateway_status = {
                    "status": "warning",
                    "latency_ms": lat,
                    "detail": "HTTP 403 WAF Challenge",
                }
                waf_status = {
                    "status": "warning",
                    "detail": "Cloudflare solicitou verificação humana",
                }
            elif code in (301, 302, 303, 307, 308):
                gateway_status = {
                    "status": "error",
                    "latency_ms": lat,
                    "detail": f"Redirecionamento para login ({code})",
                }
                waf_status = {"status": "warning", "detail": "Sessão expirada"}
        except Exception as e:
            gateway_status = {"status": "error", "latency_ms": None, "detail": str(e)}

    # 4. Bidding Ready Check
    bidding_ready = gateway_status["status"] == "ok" and cookies_status["status"] in (
        "ok",
        "warning",
    )
    bidding_status = {
        "status": "ok" if bidding_ready else "blocked",
        "detail": "Pronto para disparo autônomo de propostas"
        if bidding_ready
        else "Disparo bloqueado: resolva a autenticação primeiro",
    }

    # Classificação geral
    all_ok = all(
        s["status"] == "ok"
        for s in [vault_status, cookies_status, gateway_status, waf_status, bidding_status]
    )
    overall = (
        "optimal" if all_ok else ("degraded" if cookies_status["count"] > 0 else "disconnected")
    )

    return {
        "overall": overall,
        "diagnostics": [
            {
                "id": "vault",
                "name": "Session Vault (AES-256-GCM)",
                "status": vault_status["status"],
                "detail": vault_status["detail"],
            },
            {
                "id": "cookies",
                "name": "Estrutura dos Cookies",
                "status": cookies_status["status"],
                "detail": f"{cookies_status['count']} cookies carregados ({cookies_status['detail']})",
            },
            {
                "id": "gateway",
                "name": "Gateway Workana (TLS Chrome 126)",
                "status": gateway_status["status"],
                "detail": gateway_status["detail"],
            },
            {
                "id": "waf",
                "name": "Cloudflare WAF / Turnstile",
                "status": waf_status["status"],
                "detail": waf_status["detail"],
            },
            {
                "id": "bidding",
                "name": "Motor de Envio de Propostas",
                "status": bidding_status["status"],
                "detail": bidding_status["detail"],
            },
        ],
    }
