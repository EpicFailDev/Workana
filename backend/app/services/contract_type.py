"""
Detecção da modalidade de contrato do projeto Workana.

Classifica o projeto em uma das modalidades usadas pelo gerador de propostas
para especializar escopo/marcos e precificação:

    - project_fixed       : serviço de escopo fechado (entrega por marcos)
    - hourly              : cobrança por hora de trabalho (tarefas contínuas)
    - staff_augmentation  : integração com time existente (quase sempre horária)

A decisão é tomada no momento do upsert do catálogo (worker) e persistida na
coluna `contract_type` para consumo determinístico nos endpoints.
"""
from typing import Optional

import re

# Sinais textuais que indicam "por hora" (pt-BR).
_HOURLY_PATTERNS = [
    r"\b(hora|horas|hr|hrs|por\s+hora|valor\s+da\s+hora|taxa\s+hor[aá]ria)\b",
    r"\b(rate\s+per\s+hour)\b",  # manter compatibilidade com feed en (raro)
]

# Sinais de staff augmentation (pt-BR).
_STAFF_PATTERNS = [
    r"\b(staff\s+augmentation|dedicated\s+team|equipe\s+dedicada|time\s+dedicado|s[eé]nior\s+contratad|dev\s+dedicad)\b",
    r"\b(integrar\s+a\s+time|integra[açã]o\s+com\s+time|refor[çc]o\s+de\s+time|aumentar\s+o\s+time|compor\s+o\s+time)\b",
]


def _has_pattern(text: str, patterns) -> bool:
    lowered = (text or "").lower()
    return any(re.search(p, lowered) for p in patterns)


def detect_contract_type(
    *,
    budget_type: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    details: Optional[dict] = None,
) -> str:
    """Determina a modalidade de contrato a partir de sinais textuais.

    Prioridade: staff_augmentation > hourly > project_fixed.
    Se `budget_type` já vier explícito ("hourly"/"fixed"), ele é usado como
    referência forte.
    """
    blob = " ".join(
        str(x)
        for x in (title, description, str(details or ""))
        if x
    )
    budget = (budget_type or "").lower()

    if budget in {"hourly", "hora", "horas"}:
        return "hourly"
    if budget == "fixed" or budget == "projeto":
        return "project_fixed"

    if _has_pattern(blob, _STAFF_PATTERNS):
        return "staff_augmentation"
    if _has_pattern(blob, _HOURLY_PATTERNS):
        return "hourly"

    return "project_fixed"