import pytest
from datetime import datetime, timezone

from app.services.dates import parse_relative_datetime, humanize_age

BASE = datetime(2026, 8, 20, 15, 0, 0, tzinfo=timezone.utc)


def _dt(**kw):
    return parse_relative_datetime(kw["text"], base_time=BASE)


def test_relative_minutes():
    assert _dt(text="Publicado: há 2 horas") == datetime(2026, 8, 20, 13, 0, tzinfo=timezone.utc)
    assert _dt(text="há 30 minutos") == datetime(2026, 8, 20, 14, 30, tzinfo=timezone.utc)
    assert _dt(text="há 5 dias") == datetime(2026, 8, 15, 15, 0, tzinfo=timezone.utc)
    assert _dt(text="há 2 semanas") == datetime(2026, 8, 6, 15, 0, tzinfo=timezone.utc)
    assert _dt(text="há 3 meses") == datetime(2026, 5, 22, 15, 0, tzinfo=timezone.utc)
    assert _dt(text="há 1 ano") == datetime(2025, 8, 20, 15, 0, tzinfo=timezone.utc)


def test_relative_words():
    assert _dt(text="há duas horas") == datetime(2026, 8, 20, 13, 0, tzinfo=timezone.utc)
    assert _dt(text="há um dia") == datetime(2026, 8, 19, 15, 0, tzinfo=timezone.utc)
    assert _dt(text="há um mês") == datetime(2026, 7, 21, 15, 0, tzinfo=timezone.utc)


def test_retro_position():
    assert _dt(text="2 horas atrás") == datetime(2026, 8, 20, 13, 0, tzinfo=timezone.utc)


def test_special_phrases():
    assert _dt(text="Publicado: agora") == BASE
    assert _dt(text="agora mesmo") == datetime(2026, 8, 20, 14, 59, tzinfo=timezone.utc)
    assert _dt(text="menos de um minuto") == datetime(2026, 8, 20, 14, 59, tzinfo=timezone.utc)
    assert _dt(text="Publicado: ontem") == datetime(2026, 8, 19, 15, 0, tzinfo=timezone.utc)


def test_absolute_dates():
    assert _dt(text="20 de agosto de 2026") == datetime(2026, 8, 20, 3, 0, tzinfo=timezone.utc)
    assert _dt(text="23 ago. de 2026") == datetime(2026, 8, 23, 3, 0, tzinfo=timezone.utc)
    assert _dt(text="20/08/2026") == datetime(2026, 8, 20, 3, 0, tzinfo=timezone.utc)
    assert _dt(text="2026-08-20") == datetime(2026, 8, 20, 3, 0, tzinfo=timezone.utc)
    assert _dt(text="2026-08-20T14:30:00") == datetime(2026, 8, 20, 17, 30, tzinfo=timezone.utc)


def test_absolute_takes_precedence():
    # Datas absolutas não devem ser tratadas como relativas.
    result = parse_relative_datetime("20/08/2026", base_time=BASE)
    assert result.year == 2026 and result.month == 8 and result.day == 20


def test_unparsable_returns_none():
    assert parse_relative_datetime("lixo sem sentido", base_time=BASE) is None
    assert parse_relative_datetime("", base_time=BASE) is None
    assert parse_relative_datetime(None, base_time=BASE) is None


def test_unknown_unit_ignored():
    # "há 2 quilos" não faz sentido temporal -> None
    assert _dt(text="há 2 quilos") is None


def test_humanize_age():
    assert humanize_age(None) == "sem data"
    assert humanize_age(BASE, base_time=BASE) == "agora"
    assert humanize_age(datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc), base_time=BASE) == "há 3h"
    assert humanize_age(datetime(2026, 8, 19, 14, 30, tzinfo=timezone.utc), base_time=BASE) == "há 1d"