"""
Privacidade e redaction.

Fornece:
- pseudonymize(): hash curto, estável e one-way para IDs de usuário/projeto,
  de forma que o mesmo ID gere sempre o mesmo pseudônimo dentro de um mesmo
  deployment (salt derivado da SECRET_KEY), sem permitir a reversão.
- redact(): mascaramento recursivo de dicts/listas por nome de chave sensível.
- redact_url(): preserva host + path, descartando query/fragment.
- sanitize_exception(): remove blocos [SQL: ...]/[parameters: ...] do str() de
  exceções (principalmente SQLAlchemy) para evitar expor queries/parâmetros.

Estes helpers são a camada explícita (por call site) de defesa; a camada
implícita (safety-net por padrão no pipeline) está em logging_config.py.
"""
from __future__ import annotations

import hashlib
import hmac
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

# Nomes de chave cujo valor deve ser sempre mascarado quando serializado.
SENSITIVE_KEYS = frozenset({
    "token", "access_token", "refresh_token", "id_token",
    "password", "passwd", "secret", "client_secret",
    "api_key", "apikey", "api_secret",
    "authorization", "auth",
    "cookie", "cookies", "set_cookie",
    "proposal", "custom_message", "message",
    "body", "html", "body_html", "text_body", "content",
    "email", "mail", "to", "recipient",
    "key", "private_key", "session",
    "credit_card", "card_number", "cvv",
})
REDACTED = "***"

# Pseudônimo com 10 chars hex (48 bits) — curto o bastante para logs, estável por deployment.
_PSEUDO_LEN = 10


def _deployment_salt() -> bytes:
    """Salt derivado da SECRET_KEY do deployment (em bytes). Garante estabilidade
    entre processos do mesmo deployment, mas opacidade entre deployments."""
    # Importação tardia para evitar ciclo: config importa observability indiretamente
    # apenas quando logging_config/middleware são carregados, não aqui em runtime.
    try:
        from app.config import settings
        base = (settings.secret_key or "unconfigured-salt").encode("utf-8")
    except Exception:
        base = b"unconfigured-salt"
    return hashlib.sha256(b"pseudonymize-v1:" + base).digest()


def pseudonymize(value: Any) -> str:
    """Hash curto, estável e one-way. Pensado para user_id/project_id em logs.

    >>> pseudonymize("00000000-0000-0000-0000-000000000001")  # sempre o mesmo
    'a1b2c3d4e5'  # exemplo
    """
    if value is None:
        return "null"
    raw = str(value).encode("utf-8")
    digest = hmac.new(_deployment_salt(), raw, hashlib.sha256).hexdigest()
    return digest[:_PSEUDO_LEN]


def redact(obj: Any) -> Any:
    """Mascara recursivamente valores cuja chave seja sensível.

    Devolve uma cópia estruturada; não muta a entrada. Para escalares isolados,
    devolve o próprio valor (não há chave para julgar).
    """
    if isinstance(obj, dict):
        return {k: (REDACTED if _is_sensitive_key(k) else redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(item) for item in obj]
    if isinstance(obj, tuple):
        return tuple(redact(item) for item in obj)
    return obj


def _is_sensitive_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    return key.lower() in SENSITIVE_KEYS


# Remove blocos "[SQL: ...]" e "[parameters: ...]" que o SQLAlchemy embute no
# str() de exceções — evita vazar queries e parâmetros ligados ao logar {e}.
_SQL_BLOCK_RE = re.compile(
    r"\s*\[(?:SQL|parameters|background|input parameters|original message):[^\]]*\]",
    re.DOTALL,
)


def sanitize_exception(exc: BaseException) -> str:
    """str(exc) sem os blocos de SQL/parâmetros que o SQLAlchemy costuma embutir."""
    text = str(exc)
    cleaned = _SQL_BLOCK_RE.sub("", text).strip()
    return cleaned or exc.__class__.__name__


def truncate(text: Any, limit: int = 40) -> str:
    """Trunca texto longo (títulos, descrições) para logs, com reticências."""
    if text is None:
        return ""
    s = str(text).replace("\n", " ").strip()
    if len(s) <= limit:
        return s
    return s[: limit - 1].rstrip() + "…"


def redact_url(url: Any) -> str:
    """Preserva scheme://host/path; descarta query e fragment (podem conter IDs/tokens)."""
    if not url:
        return ""
    try:
        parts = urlsplit(str(url))
        if not parts.scheme or not parts.netloc:
            # Não parece uma URL absoluta: devolve truncada para não vazar detalhe.
            return truncate(url, 60)
        return urlunsplit((parts.scheme, parts.netloc, parts.path or "/", "", ""))
    except ValueError:
        return truncate(url, 60)
