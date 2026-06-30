"""
Middlewares de observabilidade.

RequestIDMiddleware: lê ou gera um X-Request-ID, propaga via ContextVar (para
correlação automática nos logs) e devolve o header na resposta. Aceita um ID
recebido se for um UUID válido; caso contrário gera um novo (evita injeção de
texto arbitrário nos logs).
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.observability import context

_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Adiciona/propaga X-Request-ID em cada requisição e resposta."""

    async def dispatch(self, request: Request, call_next) -> Response:
        raw = request.headers.get(_HEADER)
        rid = context.normalize_request_id(raw)
        # Contextualiza para que request_id apareça em todos os logs desta requisição.
        token = context.request_id_var.set(rid)
        try:
            response = await call_next(request)
        finally:
            context.request_id_var.reset(token)
        response.headers[_HEADER] = rid
        return response
