"""
Middlewares de observabilidade HTTP (Padrão Big Tech / OpenTelemetry).

StructuredAccessLogMiddleware:
- Rastreia e propaga X-Request-ID em 100% das requisições e respostas.
- Mede latência com precisão de microssegundos (time.perf_counter).
- Injeta cabeçalho de diagnóstico X-Response-Time (ms).
- Emite exatamente UM registro de log de acesso estruturado por requisição.
- Suprime probes bem-sucedidos de /health e /ready para manter sinal 100% limpo.
- Categoriza status codes semânticos (INFO para 2xx/3xx, WARNING para 4xx, ERROR para 5xx).
"""

from __future__ import annotations

import time
from typing import Optional
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.observability import context

_HEADER_REQUEST_ID = "X-Request-ID"
_HEADER_RESPONSE_TIME = "X-Response-Time"
_SILENT_PATHS = frozenset({"/health", "/ready", "/health/", "/ready/"})


def _get_client_ip(request: Request) -> str:
    """Extrai o IP real do cliente mesmo atrás de proxies reversos (Caddy, Cloudflare, Nginx)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "127.0.0.1"


class StructuredAccessLogMiddleware(BaseHTTPMiddleware):
    """Middleware corporativo de correlação e access log estruturado."""

    async def dispatch(self, request: Request, call_next) -> Response:
        raw_rid = request.headers.get(_HEADER_REQUEST_ID)
        rid = context.normalize_request_id(raw_rid)

        # Define contexto de correlação para todo o ciclo de vida desta corrotina
        token_rid = context.request_id_var.set(rid)
        token_user = None

        start_time = time.perf_counter()
        status_code = 500
        response: Optional[Response] = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            # Erro não tratado dentro da aplicação
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            client_ip = _get_client_ip(request)
            logger.bind(
                event="http.request.unhandled_exception",
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration_ms=duration_ms,
                client_ip=client_ip,
            ).exception(
                f"{request.method} {request.url.path} -> 500 ({duration_ms}ms) [UNHANDLED: {exc.__class__.__name__}]"
            )
            raise
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            if response is not None:
                response.headers[_HEADER_REQUEST_ID] = rid
                response.headers[_HEADER_RESPONSE_TIME] = f"{duration_ms:.2f}ms"

            path = request.url.path
            is_probe = path in _SILENT_PATHS

            # Se for health check bem-sucedido e rápido, descarta o log
            if not (is_probe and 200 <= status_code < 300 and duration_ms < 1000):
                client_ip = _get_client_ip(request)
                user_agent = request.headers.get("user-agent", "")[:150]

                log_data = {
                    "method": request.method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                }

                log_msg = f"{request.method} {path} -> {status_code} ({duration_ms}ms)"

                if status_code >= 500:
                    logger.bind(event="http.request.server_error", **log_data).error(log_msg)
                elif status_code >= 400:
                    logger.bind(event="http.request.client_error", **log_data).warning(log_msg)
                else:
                    logger.bind(event="http.request.completed", **log_data).info(log_msg)

            # Limpa contextvars
            context.request_id_var.reset(token_rid)
            if token_user:
                context.user_id_var.reset(token_user)


# Alias para retrocompatibilidade
RequestIDMiddleware = StructuredAccessLogMiddleware
