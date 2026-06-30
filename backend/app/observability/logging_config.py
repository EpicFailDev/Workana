"""
Configuração central de logging (compartilhada pela API e pelo worker).

Objetivos:
- Pipeline único em stdout (Docker é a fonte local; sem arquivos de log).
- Formato JSON estruturado em produção; console colorido/humano em desenvolvimento.
- Captura do logging stdlib (Uvicorn, SQLAlchemy, warnings Python) no mesmo
  pipeline via InterceptHandler, evitando timestamps/prefixos duplicados.
- Campos estáveis por registro: timestamp(UTC), level, logger, event, message,
  request_id, operation_id, environment.
- Safety-net de privacidade: mascara padrões sensíveis (Bearer, bot tokens,
  chaves longas, password=, api_key=) no texto renderizado, como defesa além
  da redaction explícita feita nos call sites.
- Filtra access logs bem-sucedidos de /health (mantém falhas/lentidão).

Segurança: chamado por app.main e run_worker ANTES das demais importações de app.
"""
from __future__ import annotations

import logging
import re
import sys
from typing import Any

from loguru import logger

from app.config import settings
from app.observability import context

_CONFIGURED = False

# ---------------------------------------------------------------------------- #
# Contexto: injeta request_id/operation_id no "extra" de cada registro.
# ---------------------------------------------------------------------------- #


def _context_patcher(record: "logger.Record") -> None:
    """Garante campos estáveis presentes mesmo quando ausentes no bind()."""
    record["extra"].setdefault("request_id", context.get_request_id())
    record["extra"].setdefault("operation_id", context.get_operation_id())
    record["extra"].setdefault("event", None)
    record["extra"].setdefault("environment", settings.environment)
    # record["name"] já contém o módulo/linha; mantemos "logger" explícito.
    record["extra"].setdefault("logger", record.get("name", ""))


# ---------------------------------------------------------------------------- #
# Safety-net de privacidade: máscara de padrões sensíveis no texto renderizado.
# Esta é uma rede defensiva; a redaction explícita por call site vem primeiro.
# ---------------------------------------------------------------------------- #

# Padrões que podem aparecer acidentalmente em mensagens interpoladas.
_SAFETY_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Authorization: Bearer <jwt>
    (re.compile(r"(?i)(Bearer\s+)[A-Za-z0-9._\-]+"), r"\1***"),
    # Telegram bot tokens na URL: bot<digits>:<alnum>
    (re.compile(r"bot\d{6,}:[A-Za-z0-9_\-]{20,}"), "***"),
    # password=..., api_key=..., secret=..., token=...
    (re.compile(r"(?i)(password|passwd|secret|api_?key|token|authorization)\s*[=:]\s*\S+"), r"\1=***"),
    # Chaves longas (JWT/base64/hex com 32+ chars) provavelmente sensíveis.
    (re.compile(r"\b[A-Za-z0-9+/=_\-]{32,}\b"), "***"),
    # postgres://user:pass@host
    (re.compile(r"(://[^/\s:@]+:)[^@\s/]+(@)"), r"\1***\2"),
]


def _apply_safety_net(text: str) -> str:
    """Aplica mascaramento de padrões sensíveis ao texto já renderizado."""
    if not text:
        return text
    out = text
    for pattern, repl in _SAFETY_PATTERNS:
        out = pattern.sub(repl, out)
    return out


def _safety_filter(record: "logger.Record") -> bool:
    """Filtro loguru: mascara a mensagem renderizada (campo 'message')."""
    record["message"] = _apply_safety_net(record["message"])
    return True


# ---------------------------------------------------------------------------- #
# Serialização JSON.
# ---------------------------------------------------------------------------- #


def _record_payload(record: "logger.Record") -> dict[str, Any]:
    """Constrói o payload de campos a partir de um record loguru."""
    payload: dict[str, Any] = {
        "timestamp": record["time"].strftime("%Y-%m-%dT%H:%M:%S.") + f"{record['time'].microsecond:06d}Z",
        "level": record["level"].name,
        "logger": record["extra"].get("logger") or record["name"],
        "event": record["extra"].get("event"),
        "message": record["message"],
        "environment": record["extra"].get("environment"),
        "request_id": record["extra"].get("request_id"),
        "operation_id": record["extra"].get("operation_id"),
    }
    # Exception/stack trace, se houver (logger.exception / .bind com error).
    if record["exception"]:
        payload["exception"] = _format_exception(record["exception"])
    return payload


def _json_sink(message: "logger.Message") -> None:
    """Sink loguru que escreve uma linha JSON por registro.

    Recebe um `Message` loguru; acessamos o record embutido para extrair os
    campos e serializá-los nós mesmos (não passamos por str.format, evitando
    que as chaves do JSON sejam interpretadas como placeholders).
    """
    record = message.record
    payload = _record_payload(record)
    sys.stdout.write(_dumps(payload) + "\n")
    try:
        sys.stdout.flush()
    except Exception:
        pass


def _format_exception(exc) -> str:
    # loguru passa um record["exception"] do tipo ExceptionInfo; usamos o traceback formatado.
    import traceback as tb_mod

    try:
        return "".join(tb_mod.format_exception(exc.type, exc.value, exc.traceback))
    except Exception:
        return str(exc)


def _dumps(payload: dict[str, Any]) -> str:
    # JSON compacto sem depender de biblioteca externa; controla o encoding.
    import json

    def _default(o: Any) -> Any:
        try:
            return str(o)
        except Exception:
            return None

    return json.dumps(payload, default=_default, ensure_ascii=False)


# Formato humano/colorido para desenvolvimento.
_CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{extra[logger]}</cyan> "
    "[<magenta>{extra[request_id]}</magenta>] "
    "<level>{message}</level>"
)


# ---------------------------------------------------------------------------- #
# Interceptador do logging stdlib -> loguru (Uvicorn, SQLAlchemy, warnings).
# ---------------------------------------------------------------------------- #


class InterceptHandler(logging.Handler):
    """Encaminha registros do logging stdlib ao pipeline loguru (mesmo formato)."""

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


_LOGGERS_TO_INTERCEPT = (
    "uvicorn",
    "uvicorn.access",
    "uvicorn.error",
    "sqlalchemy",
    "sqlalchemy.engine",
    "pydantic",
    "apscheduler",
    "asyncio",
)


def _intercept_stdlib() -> None:
    """Faz com que os loggers stdlib relevantes emitam pelo pipeline loguru."""
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for name in _LOGGERS_TO_INTERCEPT:
        logging.getLogger(name).handlers = [InterceptHandler()]
        logging.getLogger(name).propagate = False


# ---------------------------------------------------------------------------- #
# Filtro de access log do /health.
# ---------------------------------------------------------------------------- #


class _AccessLogFilter(logging.Filter):
    """Descarta GET /health bem-sucedido (2xx) do access log do Uvicorn;
    mantém falhas e lentidão do endpoint."""

    _HEALTH_RE = re.compile(r'GET\s+(/health)\b')

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if not self._HEALTH_RE.search(msg):
            return True
        # Uvicorn access: '... "GET /health HTTP/1.1" 200 ...'
        m = re.search(r'"\s*\d{3}\s+', msg)
        if not m:
            return True
        status_match = re.search(r'"\s*(\d{3})', msg)
        if status_match:
            status = int(status_match.group(1))
            return not (200 <= status < 300)
        return True


def _apply_access_filter() -> None:
    logging.getLogger("uvicorn.access").addFilter(_AccessLogFilter())


# ---------------------------------------------------------------------------- #
# API pública.
# ---------------------------------------------------------------------------- #


def configure_logging() -> None:
    """Configura o pipeline de logs (idempotente). Chamar no início de app.main e run_worker."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_level = (settings.log_level or "INFO").upper()
    # Em desenvolvimento (DEBUG=true), usa console colorido a menos que LOG_FORMAT=json explicitamente.
    explicit_console = (settings.log_format or "").lower() == "console"
    use_console = explicit_console or settings.debug

    logger.remove()
    logger.configure(patcher=_context_patcher)

    sink_kwargs = {
        "level": log_level,
        "filter": _safety_filter,
    }
    if use_console:
        logger.add(sys.stdout, format=_CONSOLE_FORMAT, **sink_kwargs)
    else:
        # JSON estruturado: sink próprio que serializa cada registro diretamente.
        logger.add(_json_sink, **sink_kwargs)

    _intercept_stdlib()
    _apply_access_filter()

    _CONFIGURED = True
