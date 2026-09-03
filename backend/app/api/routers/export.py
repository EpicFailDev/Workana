"""
Exportação do catálogo em CSV (base da Fase F — análise externa).

- Saída com BOM UTF-8 (utf-8-sig) para o Excel reconhecer acentuação.
- Sanitização anti formula injection: células de texto que começam com
  = + - @ recebem um apóstrofo prefixado (OTF CSV Injection Mitigation).
"""

import csv
import io
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.auth import get_current_user
from app.database import crud

router = APIRouter()

# Células de texto que, se iniciarem com estes caracteres, são tratadas como
# fórmula no Excel/Sheets e devem ser neutralizadas.
_FORMULA_PREFIX = re.compile(r"^[=+\-@\t\r]")

_CSV_COLUMNS = [
    "workana_id",
    "title",
    "url",
    "category",
    "subcategory",
    "budget_min",
    "budget_max",
    "budget_type",
    "deadline",
    "skills",
    "proposals_count",
    "proposals_delta",
    "contract_type",
    "estimated_published_at",
    "posted_at",
    "published_at",
    "last_client_activity",
    "is_urgent",
    "is_featured",
    "status",
    "client_name",
    "client_country",
    "client_rating",
    "client_projects_posted",
    "client_projects_paid",
    "client_member_since",
    "client_plan",
    "payment_verified",
    "first_seen_at",
    "last_seen_at",
]


def _sanitize_cell(value: Any) -> Any:
    """Neutraliza injeção de fórmula e caracteres de controle em células de texto."""
    if isinstance(value, str):
        if _FORMULA_PREFIX.match(value):
            value = "'" + value
        # Remove/escapa caracteres de controle exceto tabulação comum
        value = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", value)
    return value


def _build_csv(rows: List[Dict[str, Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=_CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: _sanitize_cell(v) for k, v in row.items()})
    # BOM UTF-8 para compatibilidade com Excel (acentuação)
    return "\ufeff" + buffer.getvalue()


@router.get("/projects/export.csv")
async def export_catalog_csv(
    include_inactive: bool = False,
    limit: int = 5000,
    user: dict = Depends(get_current_user),
):
    """Exporta o catálogo em CSV (com BOM utf-8 e sanitização anti-injeção)."""
    rows = await crud.export_catalog_rows(limit=limit, include_inactive=include_inactive)
    csv_text = _build_csv(rows)
    return StreamingResponse(
        io.BytesIO(csv_text.encode("utf-8-sig")),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="catalog.csv"',
        },
    )
