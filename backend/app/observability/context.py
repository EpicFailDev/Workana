"""
Contexto de correlação: request_id (por requisição HTTP) e operation_id
(por ciclo do scheduler, scraping ou auto-apply).

Usamos ContextVars para que o ID se propague corretamente no asyncio sem
vazar entre tarefas concorrentes. O request_id é injetado no pipeline de
logs automaticamente (logging_config), e o operation_id pode ser ligado
explicitamente via `bind_operation_id()`.
"""
from __future__ import annotations

import contextvars
import uuid
from contextlib import contextmanager
from typing import Iterator, Optional

# ID de correlação por requisição (definido pelo RequestIDMiddleware).
request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)

# ID de correlação por operação de background (ciclo do scheduler, scrape, etc.).
operation_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "operation_id", default=None
)

_HEX = "0123456789abcdef"


def _is_valid_uuid(value: str) -> bool:
    """Valida se a string tem formato UUID canônico (8-4-4-4-12), sem depender de exceções."""
    if len(value) != 36:
        return False
    for i, ch in enumerate(value):
        if i in (8, 13, 18, 23):
            if ch != "-":
                return False
        elif ch not in _HEX:
            return False
    return True


def new_request_id() -> str:
    """Gera um novo request_id (UUID4 em hex minúsculo)."""
    return str(uuid.uuid4())


def normalize_request_id(raw: Optional[str]) -> str:
    """Aceita um request_id recebido se for UUID válido; caso contrário gera um novo."""
    if raw and _is_valid_uuid(raw):
        return raw
    return new_request_id()


def get_request_id() -> Optional[str]:
    return request_id_var.get()


def get_operation_id() -> Optional[str]:
    return operation_id_var.get()


def new_operation_id() -> str:
    """Gera um novo operation_id curto (12 chars hex) para correlação de operações de fundo."""
    return uuid.uuid4().hex[:12]


@contextmanager
def bind_operation_id(operation_id: Optional[str] = None) -> Iterator[str]:
    """Define um operation_id no contexto atual e devolve o ID usado.

    Útil para envolver um ciclo do scheduler, um scrape ou um auto-apply:
        with bind_operation_id() as op_id:
            ...
    """
    op_id = operation_id or new_operation_id()
    token = operation_id_var.set(op_id)
    try:
        yield op_id
    finally:
        operation_id_var.reset(token)
