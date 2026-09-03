"""Conversão do JSON público de listagem da Workana para o contrato da API."""
import html
import re
from typing import Any, Optional, Dict

from bs4 import BeautifulSoup

from app.api.schemas import Project
from app.services.currency import CurrencyService


def _plain_text(value: Any) -> str:
    decoded = html.unescape(str(value or ""))
    if "<" not in decoded:
        return decoded.strip()
    return BeautifulSoup(decoded, "html.parser").get_text(separator="\n", strip=True)


def _parse_rating(value: Any) -> Optional[float]:
    if isinstance(value, dict):
        value = value.get("value") or value.get("label")
    match = re.search(r"\d+(?:[.,]\d+)?", _plain_text(value))
    if not match:
        return None
    rating = float(match.group().replace(",", "."))
    return rating if 0 <= rating <= 5 else None


def _extract_metadata(description: str, label: str) -> Optional[str]:
    match = re.search(
        rf"(?:^|\n)\s*{re.escape(label)}\s*:?\s*(?:\n\s*)?([^\n]+)",
        description,
        flags=re.IGNORECASE,
    )
    return match.group(1).strip(" :-") if match else None


def _extract_briefing_details(description: str) -> Dict[str, str]:
    labels = {
        # Português
        "Categoria": "category",
        "Subcategoria": "subcategory",
        "Tamanho do projeto": "project_size",
        "Do que você precisa?": "need",
        "Do que você precisa": "need",
        "Qual é o alcance do projeto?": "scope",
        "Qual é o alcance do projeto": "scope",
        "Isso é um projeto ou uma posição de trabalho?": "engagement",
        "Tenho, atualmente": "current_state",
        "Disponibilidade requerida": "availability",
        "Funções necessárias": "required_roles",
        "Duração do projeto": "duration",
        "Prazo de Entrega": "delivery_deadline",
        "Prazo de entrega": "delivery_deadline",
        "E-commerce": "ecommerce",
        "Quantidade de pessoas": "team_size",
        "Experiência nesse tipo de projeto": "experience_level",
        # Espanhol
        "Categoría": "category",
        "Subcategoría": "subcategory",
        "Tamaño del proyecto": "project_size",
        "¿Qué necesitas?": "need",
        "¿Cuál es el alcance del proyecto?": "scope",
        "¿Es un proyecto o una posición?": "engagement",
        "Tengo, actualmente": "current_state",
        "Disponibilidad requerida": "availability",
        "Roles necesarios": "required_roles",
        "Duración del proyecto": "duration",
        "Plazo de Entrega": "delivery_deadline",
        "Plazo de entrega": "delivery_deadline",
        "Cantidad de personas": "team_size",
        # Inglês
        "Category": "category",
        "Subcategory": "subcategory",
        "Project size": "project_size",
        "Project Scope": "scope",
        "Delivery Deadline": "delivery_deadline",
        "Duration": "duration",
    }
    details: Dict[str, str] = {}
    for label, key in labels.items():
        value = _extract_metadata(description, label)
        if value and key not in details:
            details[key] = value
    return details


def _parse_client_history(value: Any) -> tuple[Optional[int], Optional[int], Optional[str]]:
    text = _plain_text(value)
    posted_match = re.search(r"(\d+)\s*Projetos? publicados?", text, re.IGNORECASE)
    paid_match = re.search(r"(\d+)\s*Projetos? pagos?", text, re.IGNORECASE)
    member_match = re.search(r"Membro desde:?\s*([^\n]+)", text, re.IGNORECASE)
    return (
        int(posted_match.group(1)) if posted_match else None,
        int(paid_match.group(1)) if paid_match else None,
        member_match.group(1).strip() if member_match else None,
    )


async def parse_project_json(data: dict, base_url: str) -> Optional[Project]:
    """Extrai todos os campos úteis disponíveis na listagem, sem abrir o detalhe."""
    slug = str(data.get("slug") or "").strip()
    title = _plain_text(data.get("title"))
    if not slug or not title:
        return None

    raw_budget = str(data.get("budget") or "").strip()
    budget = await CurrencyService.convert_to_brl(raw_budget)
    budget_min, budget_max = CurrencyService.parse_budget_string(budget)

    raw_description = html.unescape(str(data.get("description") or ""))
    raw_description = re.sub(r"<br\s*/?>", "\n", raw_description, flags=re.IGNORECASE)
    description_with_metadata = BeautifulSoup(raw_description, "html.parser").get_text(
        separator="\n"
    )
    details = _extract_briefing_details(description_with_metadata)
    category = details.get("category")
    subcategory = details.get("subcategory")
    client_projects_posted, client_projects_paid, client_member_since = _parse_client_history(
        data.get("popoverContent")
    )

    metadata_start = re.search(
        r"(?:^|\n)\s*(?:Categoria|Categoría|Category|Subcategoria|Subcategoría|Subcategory|"
        r"Tamanho do projeto|Tamaño del proyecto|Project size|"
        r"Do que você precisa\??|¿Qué necesitas\??|"
        r"Qual é o alcance(?: do projeto)?\??|¿Cuál es el alcance(?: del proyecto)?\??|Project Scope|"
        r"E-commerce|Isso é um projeto|¿Es un projeto|Duração|Duración|Duration|Quantidade de pessoas)\s*:?",
        description_with_metadata,
        flags=re.IGNORECASE,
    )
    if metadata_start and metadata_start.start() > 0:
        extracted_desc = description_with_metadata[:metadata_start.start()].strip()
        if len(extracted_desc) >= 10:
            description = extracted_desc
        else:
            description = description_with_metadata.strip()
    else:
        description = description_with_metadata.strip()

    description = re.sub(r"\n{3,}", "\n\n", description).strip()

    skills = []
    for skill in data.get("skills") or []:
        label = _plain_text(skill.get("anchorText") if isinstance(skill, dict) else skill)
        if label and label not in skills:
            skills.append(label)

    proposals_match = re.search(r"\d+", str(data.get("totalBids") or ""))
    proposals = int(proposals_match.group()) if proposals_match else 0
    is_hourly = bool(data.get("isHourly", False))
    deadline = _plain_text(data.get("deadlineValue") or data.get("deadline")) or (
        details.get("delivery_deadline") or details.get("duration")
    )

    return Project(
        id=slug,
        title=title,
        description=description,
        budget=budget or None,
        budget_min=budget_min,
        budget_max=budget_max,
        project_type="hourly" if is_hourly else "fixed",
        category=category,
        subcategory=subcategory,
        deadline=deadline,
        details=details,
        skills=skills,
        client_name=_plain_text(data.get("authorName")) or None,
        client_country=_plain_text(data.get("country")) or None,
        client_rating=_parse_rating(data.get("rating")),
        client_projects_posted=client_projects_posted,
        client_projects_paid=client_projects_paid,
        client_member_since=client_member_since,
        client_plan=_plain_text(data.get("projectClientPlanLabel")) or None,
        proposals_count=proposals,
        posted_at=_plain_text(data.get("postedDate")) or None,
        published_at=_plain_text(data.get("publishedDate")) or None,
        last_client_activity=_plain_text(data.get("lastEmployerMessage")) or None,
        is_urgent=bool(data.get("isUrgent", False)),
        is_featured=bool(data.get("isSearchFeatured", False)),
        payment_verified=bool(data.get("hasVerifiedPaymentMethod", False)),
        url=f"{base_url}/job/{slug}",
    )
