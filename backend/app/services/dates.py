"""
Normalização de datas relativas/absolutas do Workana (pt-BR) para datetime em UTC.

O Workana publica o campo de data como texto humano: "Publicado: há 2 horas",
"Publicado: ontem", "20 de agosto de 2026", etc. Este módulo converte esses
formatos em datas estimadas absolutas (tz-aware, UTC), permitindo ordenação por
recência, filtros e agregações temporais no catálogo.

Referência de pattern: koiosoft/workana-bot (migration estimated_published_at),
reimplementado para pt-BR (foco do projeto) e datas absolutas.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

# Fuso usado para intepretar datas absolutas "sem fuso" exibidas em pt-BR.
# Brasil sem horário de verão desde 2019 -> offset fixo UTC-3 (evita dep. tzdata).
BRAZIL_TZ = timezone(timedelta(hours=-3))

_NUMBER_WORDS = {
    "um": 1, "uma": 1, "dois": 2, "duas": 2, "três": 3, "tres": 3,
    "quatro": 4, "cinco": 5, "seis": 6, "sete": 7, "oito": 8,
    "nove": 9, "dez": 10,
}

# (singular, plural) por unidade — cobertura pt-BR.
_UNITS = (
    ("years", re.compile(r"ano|anos")),
    ("months", re.compile(r"m[eê]s|meses")),
    ("weeks", re.compile(r"semana|semanas")),
    ("days", re.compile(r"dia|dias|día|días")),
    ("hours", re.compile(r"hora|horas|hr|hrs|h\b")),
    ("minutes", re.compile(r"minuto|minutos|min|mins")),
)

_UNIT_DELTAS = {
    "years": lambda n: timedelta(days=n * 365),
    "months": lambda n: timedelta(days=n * 30),  # aproximação (30 dias)
    "weeks": lambda n: timedelta(weeks=n),
    "days": lambda n: timedelta(days=n),
    "hours": lambda n: timedelta(hours=n),
    "minutes": lambda n: timedelta(minutes=n),
}

_MONTHS_PT = {
    "janeiro": 1, "jan": 1, "fevereiro": 2, "fev": 2, "março": 3, "mar": 3,
    "abril": 4, "abr": 4, "maio": 5, "mai": 5, "junho": 6, "jun": 6,
    "julho": 7, "jul": 7, "agosto": 8, "ago": 8, "setembro": 9, "set": 9,
    "outubro": 10, "out": 10, "novembro": 11, "nov": 11, "dezembro": 12, "dez": 12,
}

_TOKEN_DATE = re.compile(r"(?P<day>\d{1,2})\s+(?:de\s+)?(?P<month>[a-z.]+)\.?\s+(?:de\s+)?(?P<year>\d{4})", re.IGNORECASE)


def _strip_label(text: str) -> str:
    """Remove prefixos do tipo 'Publicado:', 'Publicado em', 'Publicado'."""
    return re.sub(
        r"^publicad[o0]?\s*(?:em\s*)?[:|\-]?\s*",
        "",
        text.strip(),
        flags=re.IGNORECASE,
    )


def _parse_number_word(word: str) -> Optional[int]:
    word = word.strip().lower()
    if word.isdigit():
        return int(word)
    return _NUMBER_WORDS.get(word)


def _find_relative_delta(text: str) -> Optional[timedelta]:
    """Retorna o delta relativo (quanto tempo atrás) se o texto for relativo."""
    lowered = text.lower()

    # Casos pontuais
    if re.search(r"\b(agora\s*mesmo|menos\s+de\s+um\s+minuto|rec[ée]m[- ]publicado)\b", lowered):
        return timedelta(minutes=1)
    if re.search(r"\b(agora|hoje)\b", lowered):
        return timedelta(0)
    if re.search(r"\b(ontem)\b", lowered):
        return timedelta(days=1)

    # Padrão: "há <número|palavra> <unidade>" ou "<número> <unidade> atrás"
    m = re.search(
        r"(?:h[aá]\s+)(?P<num>\d+|[\w]+)\s+(?P<unit>\w+|hr|hrs|h)\b",
        lowered,
    )
    if not m:
        m = re.search(
            r"(?P<num>\d+)\s+(?P<unit>\w+|hr|hrs|h)\s+atr[aá]s\b",
            lowered,
        )

    if not m:
        return None

    num = _parse_number_word(m.group("num"))
    unit_word = m.group("unit").lower()

    for unit_name, pattern in _UNITS:
        if pattern.search(unit_word):
            if num is None or num < 1:
                return None
            return _UNIT_DELTAS[unit_name](num)

    return None


def _parse_absolute(text: str) -> Optional[datetime]:
    """Tenta interpretar o texto como data absoluta (pt-BR/ISO)."""
    lowered = text.lower().replace("às", "").replace("as", "").strip()

    # ISO 8601: 2026-08-20, 2026-08-20T14:30:00(+offset)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=BRAZIL_TZ)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        pass

    # "20/08/2026", "20-08-2026", "20.08.2026", "2026-08-20"
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(text.strip(), fmt)
            return parsed.replace(tzinfo=BRAZIL_TZ).astimezone(timezone.utc)
        except ValueError:
            continue

    # "20 de agosto de 2026", "20 ago. de 2026", "23 ago 2026"
    m = _TOKEN_DATE.search(lowered)
    if m:
        month_name = m.group("month").rstrip(".").lower()
        month = _MONTHS_PT.get(month_name)
        if month:
            day = int(m.group("day"))
            year = int(m.group("year"))
            try:
                parsed = datetime(year, month, day)
                return parsed.replace(tzinfo=BRAZIL_TZ).astimezone(timezone.utc)
            except ValueError:
                return None

    return None


def parse_relative_datetime(text: str, base_time: Optional[datetime] = None) -> Optional[datetime]:
    """Converte o texto de data de publicação do Workana em datetime estimado (UTC).

    A data estimada = base_time - delta relativo. Quando o texto é uma data
    absoluta, o próprio timestamp absoluto é usado (interpretado em America/Sao_Paulo,
    convertido para UTC). Retorna None se não for possível interpretar.
    """
    if not text:
        return None

    now = base_time or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    cleaned = _strip_label(text)

    # Primeiro tenta absoluto (exceção: "20/08/2026" não deve ser lido como delta)
    absolute = _parse_absolute(cleaned)
    if absolute is not None:
        return absolute.astimezone(timezone.utc)

    delta = _find_relative_delta(cleaned.lower())
    if delta is None:
        return None

    return (now - delta).astimezone(timezone.utc)


def humanize_age(dt: Optional[datetime], base_time: Optional[datetime] = None) -> str:
    """Formata a diferença até `dt` em texto curto tipo 'há 3h', 'há 5min'."""
    if dt is None:
        return "sem data"
    now = base_time or datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    seconds = (now - dt).total_seconds()
    if seconds < 60:
        return "agora"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"há {minutes}min"
    hours = int(minutes // 60)
    if hours < 24:
        return f"há {hours}h"
    days = int(hours // 24)
    if days < 30:
        return f"há {days}d"
    months = int(days // 30)
    if months < 12:
        return f"há {months}mes"
    years = int(days // 365)
    return f"há {years}a"