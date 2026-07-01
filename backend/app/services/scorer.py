from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional

from app.api.schemas import Project, SearchFilters


def _get_value(project: Any, key: str, default: Any = None) -> Any:
    if isinstance(project, Mapping):
        return project.get(key, default)
    return getattr(project, key, default)


def _as_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, Mapping):
        return [str(item).strip() for item in value.values() if str(item).strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"[,/| ]+", value) if item.strip()]
    return [str(value).strip()]


def _extract_budget_floor(project: Any) -> Optional[float]:
    budget_min = _get_value(project, "budget_min")
    budget_max = _get_value(project, "budget_max")
    if budget_min is not None:
        return float(budget_min)
    if budget_max is not None:
        return float(budget_max)
    budget = _get_value(project, "budget")
    if isinstance(budget, (int, float)):
        return float(budget)
    if isinstance(budget, str):
        match = re.search(r"(\d+(?:[.,]\d+)?)", budget)
        if match:
            return float(match.group(1).replace(".", "").replace(",", "."))
    return None


def _extract_text_hints(project: Any) -> str:
    parts = [
        _get_value(project, "title", ""),
        _get_value(project, "description", ""),
        " ".join(_as_list(_get_value(project, "skills"))),
        " ".join(_as_list(_get_value(project, "details"))),
    ]
    return " ".join(str(part) for part in parts if part).lower()


def _parse_age_minutes(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        raw = str(value).strip().lower()
        if not raw:
            return None
        if raw in {"agora", "now", "new"}:
            return 0.0
        if "ontem" in raw:
            return 24 * 60.0
        if "min" in raw:
            match = re.search(r"(\d+)", raw)
            return float(match.group(1)) if match else 5.0
        if "hora" in raw or "hour" in raw:
            match = re.search(r"(\d+)", raw)
            return float(match.group(1)) * 60.0 if match else 60.0
        if "dia" in raw or "day" in raw:
            match = re.search(r"(\d+)", raw)
            return float(match.group(1)) * 1440.0 if match else 1440.0
        if "semana" in raw or "week" in raw:
            match = re.search(r"(\d+)", raw)
            return float(match.group(1)) * 10080.0 if match else 10080.0
        try:
            dt = datetime.fromisoformat(raw.replace("z", "+00:00"))
        except ValueError:
            return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds() / 60.0)


def _profile_keywords(user_profile: Mapping[str, Any]) -> list[str]:
    tokens = []
    for key in ("keywords", "skills", "target_skills", "categories"):
        tokens.extend(_as_list(user_profile.get(key)))
    return [token.lower() for token in tokens if token]


def _budget_range(user_profile: Mapping[str, Any]) -> tuple[Optional[float], Optional[float]]:
    min_budget = user_profile.get("min_budget")
    max_budget = user_profile.get("max_budget")
    if min_budget in ("", None):
        min_budget = None
    if max_budget in ("", None):
        max_budget = None
    return (
        float(min_budget) if min_budget is not None else None,
        float(max_budget) if max_budget is not None else None,
    )


def _score_profile_fit(project: Any, user_profile: Mapping[str, Any]) -> tuple[float, str]:
    keywords = _profile_keywords(user_profile)
    if not keywords:
        return 50.0, "Perfil sem palavras-chave prioritárias"

    haystack = _extract_text_hints(project)
    matches = sum(1 for keyword in keywords if keyword and keyword in haystack)
    ratio = matches / max(1, len(keywords))
    score = 30.0 + (ratio * 70.0)
    if matches == 0 and _get_value(project, "category"):
        category = str(_get_value(project, "category")).lower()
        if any(token in category for token in keywords):
            score = 65.0
    if not _get_value(project, "title") and not _get_value(project, "description"):
        score = min(score, 40.0)
    return max(0.0, min(100.0, score)), f"{matches}/{len(keywords)} correspondência(s)"


def _score_budget(project: Any, user_profile: Mapping[str, Any]) -> tuple[float, str]:
    floor = _extract_budget_floor(project)
    min_budget, max_budget = _budget_range(user_profile)
    if floor is None and min_budget is None and max_budget is None:
        return 55.0, "Sem sinais de orçamento"
    if floor is None:
        return 50.0, "Orçamento indefinido"

    if min_budget is not None and floor < min_budget:
        gap = min_budget - floor
        score = max(15.0, 50.0 - min(30.0, gap * 0.2))
        return score, "Abaixo do mínimo alvo"
    if max_budget is not None and floor > max_budget:
        gap = floor - max_budget
        score = max(20.0, 55.0 - min(35.0, gap * 0.15))
        return score, "Acima do máximo alvo"

    span = (max_budget - min_budget) if (min_budget is not None and max_budget is not None) else None
    if span is not None and span > 0:
        center = min_budget + (span / 2.0)
        delta = abs(floor - center) / span
        score = 80.0 - min(30.0, delta * 60.0)
    else:
        score = 75.0
    return max(0.0, min(100.0, score)), "Dentro do intervalo alvo"


def _score_competition(project: Any) -> tuple[float, str]:
    proposals = _get_value(project, "proposals_count")
    if proposals is None:
        return 60.0, "Sem contagem de propostas"

    proposals = int(proposals)
    if proposals <= 0:
        return 100.0, "Sem concorrência"
    if proposals < 5:
        return 88.0, "Concorrência muito baixa"
    if proposals < 10:
        return 74.0, "Concorrência baixa"
    if proposals < 20:
        return 60.0, "Concorrência moderada"
    if proposals < 40:
        return 38.0, "Concorrência alta"
    return 18.0, "Concorrência muito alta"


def _score_client_reliability(project: Any) -> tuple[float, str]:
    rating = _get_value(project, "client_rating")
    verified = bool(_get_value(project, "payment_verified"))
    paid = _get_value(project, "client_projects_paid")
    posted = _get_value(project, "client_projects_posted")

    score = 55.0
    reasons = []
    if verified:
        score += 18.0
        reasons.append("pagamento verificado")
    if rating is not None:
        rating_value = float(rating)
        score += max(-15.0, min(20.0, (rating_value - 3.0) * 12.0))
        reasons.append(f"rating {rating_value:.1f}")
    if posted and paid is not None:
        ratio = float(paid) / max(1.0, float(posted))
        score += max(-10.0, min(10.0, ratio * 12.0 - 2.0))
        reasons.append("histórico do cliente")

    return max(0.0, min(100.0, score)), ", ".join(reasons) if reasons else "Sem sinais fortes"


def _score_recency(project: Any) -> tuple[float, str]:
    for field in ("posted_at", "published_at", "last_seen_at"):
        age = _parse_age_minutes(_get_value(project, field))
        if age is None:
            continue
        if age <= 60:
            return 95.0, "Publicado nas últimas horas"
        if age <= 24 * 60:
            return 82.0, "Publicado no último dia"
        if age <= 3 * 24 * 60:
            return 68.0, "Recência moderada"
        if age <= 7 * 24 * 60:
            return 50.0, "Publicado na última semana"
        return 30.0, "Projeto antigo"
    return 55.0, "Recência indefinida"


def _score_risk(project: Any, dimensions: Mapping[str, float]) -> tuple[float, str]:
    missing_signals = 0
    for field in ("title", "description", "budget_min", "budget_max", "client_rating", "proposals_count"):
        if _get_value(project, field) in (None, "", []):
            missing_signals += 1

    base = 85.0
    base -= missing_signals * 4.0
    base -= max(0.0, 35.0 - dimensions["client_reliability"]) * 0.5
    base -= max(0.0, 40.0 - dimensions["competition"]) * 0.35
    base -= max(0.0, 45.0 - dimensions["budget"]) * 0.25
    base -= max(0.0, 45.0 - dimensions["profile_fit"]) * 0.15
    return max(0.0, min(100.0, base)), "Risco ajustado por sinais faltantes e concorrência"


def _recommendation(score: float) -> str:
    if score >= 70.0:
        return "send"
    if score >= 40.0:
        return "review"
    return "discard"


def _build_justification(dimensions: Mapping[str, float], note_map: Mapping[str, str]) -> str:
    ordered = [
        ("profile_fit", dimensions["profile_fit"]),
        ("budget", dimensions["budget"]),
        ("competition", dimensions["competition"]),
        ("client_reliability", dimensions["client_reliability"]),
        ("recency", dimensions["recency"]),
        ("risk", dimensions["risk"]),
    ]
    strong = [label for label, value in ordered if value >= 70.0]
    weak = [label for label, value in ordered if value < 45.0]
    parts = []
    if strong:
        parts.append(f"fortes em {', '.join(strong)}")
    if weak:
        parts.append(f"alertas em {', '.join(weak)}")
    if not parts:
        parts.append("sinais equilibrados")
    if note_map:
        notes = [note for note in note_map.values() if note]
        if notes:
            parts.append("; ".join(notes[:2]))
    return " | ".join(parts)


class ProjectScorer:
    """Scorer determinístico para ranking e análise estruturada."""

    @classmethod
    def analyze_project(cls, project: Any, user_profile: Mapping[str, Any]) -> Dict[str, Any]:
        profile_fit, profile_note = _score_profile_fit(project, user_profile)
        budget, budget_note = _score_budget(project, user_profile)
        competition, competition_note = _score_competition(project)
        client_reliability, client_note = _score_client_reliability(project)
        recency, recency_note = _score_recency(project)
        dimensions = {
            "profile_fit": profile_fit,
            "budget": budget,
            "competition": competition,
            "client_reliability": client_reliability,
            "recency": recency,
        }
        risk, risk_note = _score_risk(project, {**dimensions})
        dimensions["risk"] = risk
        score = round(
            (
                profile_fit * 0.28
                + budget * 0.16
                + competition * 0.16
                + client_reliability * 0.18
                + recency * 0.12
                + risk * 0.10
            ),
            1,
        )
        score = max(0.0, min(100.0, score))
        recommendation = _recommendation(score)
        notes = {
            "profile_fit": profile_note,
            "budget": budget_note,
            "competition": competition_note,
            "client_reliability": client_note,
            "recency": recency_note,
            "risk": risk_note,
        }
        return {
            "score": score,
            "recommendation": recommendation,
            "dimensions": dimensions,
            "justification": _build_justification(dimensions, notes),
        }

    @classmethod
    def calculate_score(cls, project: Project, filters: SearchFilters) -> float:
        profile = {
            "keywords": filters.keywords,
            "category": filters.category,
            "min_budget": filters.min_budget,
            "max_budget": filters.max_budget,
            "skills": filters.skills or [],
            "payment_verified": filters.payment_verified,
        }
        return float(cls.analyze_project(project, profile)["score"])
