"""
Configuração central de logging enterprise (compartilhada pela API e pelo worker).

Padrão de Observabilidade (Big Tech & Senior Engineering):
- Pipeline único em stdout (Twelve-Factor App: Docker/K8s é a fonte de logs).
- Formato JSON estruturado em produção (compatível com Datadog, Grafana Loki, CloudWatch, OTel).
- Formato de console limpo, colorido e dinâmico em desenvolvimento (sem tags [None] vazias).
- Captura de logging stdlib (Uvicorn, SQLAlchemy, APScheduler, HTTPX, Warnings) via InterceptHandler.
- Filtragem inteligente de ruído: health checks (2xx) e ticks vazios de agendadores são suprimidos.
- Rastreamento contextual automático (service, request_id, operation_id, user_id, event).
- Safety-net de privacidade: sanitização defensiva de tokens, senhas, chaves de API e URLs de banco.
"""
from __future__ import annotations

import json
import logging
import re
import sys
import traceback as tb_mod
from typing import Any

from loguru import logger

from app.config import settings
from app.observability import context

_CONFIGURED = False

# ---------------------------------------------------------------------------- #
# Contexto: injeta campos canônicos no "extra" de cada registro Loguru.
# ---------------------------------------------------------------------------- #


def _context_patcher(record: "logger.Record") -> None:
    """Garante campos estáveis presentes mesmo quando ausentes no bind()."""
    extra = record["extra"]
    extra.setdefault("service", context.get_service_name())
    extra.setdefault("environment", settings.environment)
    extra.setdefault("request_id", context.get_request_id())
    extra.setdefault("operation_id", context.get_operation_id())
    extra.setdefault("user_id", context.get_user_id())
    extra.setdefault("event", None)
    extra.setdefault("logger", record.get("name", ""))


# ---------------------------------------------------------------------------- #
# Safety-net de privacidade: máscara de padrões sensíveis no texto renderizado.
# ---------------------------------------------------------------------------- #

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


# ---------------------------------------------------------------------------- #
# Filtro de ruído (Health checks bem-sucedidos e ticks vazios).
# ---------------------------------------------------------------------------- #

# Descarta GET /health e /ready com status 2xx emitidos por qualquer logger/framework
_HEALTH_NOISE_RE = re.compile(r'GET\s+/(health|ready)\b.*?20[0-9]\b')


def _log_filter(record: "logger.Record") -> bool:
    """Filtra ruído desnecessário e aplica safety-net de privacidade."""
    msg = record["message"]
    
    # 1. Suprimir health checks bem-sucedidos para manter o sinal limpo
    if _HEALTH_NOISE_RE.search(msg):
        return False
    
    # 2. Se for evento explícito de health check 2xx sem lentidão
    if record["extra"].get("event") == "http.healthcheck.ok":
        return False

    # 3. Aplicar sanitização de privacidade
    record["message"] = _apply_safety_net(msg)
    return True


# ---------------------------------------------------------------------------- #
# Serialização JSON Estruturada (Padrão Enterprise / Datadog / Loki).
# ---------------------------------------------------------------------------- #


def _record_payload(record: "logger.Record") -> dict[str, Any]:
    """Constrói o payload JSON estruturado a partir de um record Loguru."""
    extra = record["extra"]
    payload: dict[str, Any] = {
        "timestamp": record["time"].strftime("%Y-%m-%dT%H:%M:%S.") + f"{record['time'].microsecond:06d}Z",
        "level": record["level"].name,
        "service": extra.get("service") or "workana-app",
        "environment": extra.get("environment") or settings.environment,
        "logger": extra.get("logger") or record["name"],
        "message": record["message"],
    }
    
    if extra.get("event"):
        payload["event"] = extra["event"]
    if extra.get("request_id"):
        payload["request_id"] = extra["request_id"]
    if extra.get("operation_id"):
        payload["operation_id"] = extra["operation_id"]
    if extra.get("user_id"):
        payload["user_id"] = extra["user_id"]

    # Extrair contexto adicional estruturado customizado (excluindo chaves canônicas)
    reserved = {"service", "environment", "logger", "event", "request_id", "operation_id", "user_id"}
    custom_context = {k: v for k, v in extra.items() if k not in reserved and v is not None}
    if custom_context:
        payload["context"] = custom_context

    if record["exception"]:
        payload["exception"] = _format_exception(record["exception"])

    return payload


def _format_exception(exc) -> str:
    try:
        return "".join(tb_mod.format_exception(exc.type, exc.value, exc.traceback))
    except Exception:
        return str(exc)


def _dumps(payload: dict[str, Any]) -> str:
    def _default(o: Any) -> Any:
        try:
            return str(o)
        except Exception:
            return None

    return json.dumps(payload, default=_default, ensure_ascii=False)


def _json_sink(message: "logger.Message") -> None:
    """Sink Loguru que emite uma linha JSON válida por registro."""
    record = message.record
    payload = _record_payload(record)
    sys.stdout.write(_dumps(payload) + "\n")
    try:
        sys.stdout.flush()
    except Exception:
        pass


# ---------------------------------------------------------------------------- #
# Formatação de Console Dinâmica e Colorida para Desenvolvimento.
# ---------------------------------------------------------------------------- #


def _console_formatter(record: "logger.Record") -> str:
    """Gera formato de console elegante sem tags [None] vazias."""
    extra = record["extra"]
    service = extra.get("service") or "app"
    req_id = extra.get("request_id")
    op_id = extra.get("operation_id")
    user_id = extra.get("user_id")
    event = extra.get("event")

    tags = [f"<cyan>{service}</cyan>"]
    if req_id:
        tags.append(f"<magenta>req:{req_id[:8]}</magenta>")
    if op_id:
        tags.append(f"<blue>op:{op_id}</blue>")
    if user_id:
        tags.append(f"<yellow>u:{user_id[:8]}</yellow>")
    if event:
        tags.append(f"<green>[{event}]</green>")

    tag_header = " ".join(tags)
    return (
        "<dim>{time:YYYY-MM-DD HH:mm:ss.SSS}</dim> | "
        "<level>{level: <8}</level> | "
        f"{tag_header} - <level>{{message}}</level>\n{{exception}}"
    )


# ---------------------------------------------------------------------------- #
# Interceptador do logging stdlib -> Loguru (Uvicorn, SQLAlchemy, APScheduler).
# ---------------------------------------------------------------------------- #


class InterceptHandler(logging.Handler):
    """Encaminha registros do logging stdlib ao pipeline unificado do Loguru."""

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
    """Configura interceptação unificada e silencia bibliotecas ruidosas."""
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for name in _LOGGERS_TO_INTERCEPT:
        logging.getLogger(name).handlers = [InterceptHandler()]
        logging.getLogger(name).propagate = False

    # Reduz ruído de loggers internos de bibliotecas que disparam a cada poucos segundos
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)
    logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)
    logging.getLogger("apscheduler.executors.base_py3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.protocols.http.httptools_impl").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.protocols.http.h11_impl").setLevel(logging.WARNING)


# ---------------------------------------------------------------------------- #
# API pública.
# ---------------------------------------------------------------------------- #


def configure_logging() -> None:
    """Configura o pipeline de logs unificado (idempotente)."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_level = (settings.log_level or "INFO").upper()
    explicit_console = (settings.log_format or "").lower() == "console"
    use_console = explicit_console or settings.debug

    logger.remove()
    logger.configure(patcher=_context_patcher)

    sink_kwargs = {
        "level": log_level,
        "filter": _log_filter,
    }

    if use_console:
        logger.add(sys.stdout, format=_console_formatter, **sink_kwargs)
    else:
        # JSON estruturado para produção
        logger.add(_json_sink, **sink_kwargs)

    _intercept_stdlib()
    _CONFIGURED = True
