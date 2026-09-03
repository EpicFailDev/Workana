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
                        cookies.append({
                            "name": name,
                            "value": val,
                            "domain": ".workana.com",
                            "path": "/",
                            "expires": -1,
                            "httpOnly": False,
                            "secure": True,
                            "sameSite": "Lax",
                        })
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
                normalized_cookies.append({
                    "name": str(c["name"]),
                    "value": str(c["value"]),
                    "domain": str(c.get("domain") or ".workana.com"),
                    "path": str(c.get("path") or "/"),
                    "expires": exp,
                    "httpOnly": bool(c.get("httpOnly", False)),
                    "secure": bool(c.get("secure", True)),
                    "sameSite": same_site,
                })
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
                normalized_cookies.append({
                    "name": str(c["name"]),
                    "value": str(c["value"]),
                    "domain": str(c.get("domain") or ".workana.com"),
                    "path": str(c.get("path") or "/"),
                    "expires": exp,
                    "httpOnly": bool(c.get("httpOnly", False)),
                    "secure": bool(c.get("secure", True)),
                    "sameSite": same_site,
                })
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
                        await crud.save_workana_session(user_id, json.dumps(state, ensure_ascii=False))
                    except Exception:
                        pass
                    return p if as_path else state
            except Exception as exc:
                logger.warning(f"Arquivo de sessão local {p} inválido para {user_id}: {exc}")

    return None


async def save_storage_state(user_id: Any, state: Dict[str, Any], account_email: Optional[str] = None) -> None:
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