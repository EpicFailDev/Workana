import sys
import types
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

# APScheduler 3.10 imports pkg_resources, unavailable on the local Python 3.14
# test runtime. Production uses the pinned Python 3.11 image; this minimal stub
# keeps these unit tests independent from scheduler packaging internals.
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler  # noqa: F401
except (ImportError, ModuleNotFoundError):
    asyncio_module = types.ModuleType("apscheduler.schedulers.asyncio")

    class AsyncIOScheduler:
        def __init__(self, *args, **kwargs):
            pass

        def add_job(self, *args, **kwargs):
            pass

        def start(self):
            pass

        def shutdown(self):
            pass

    asyncio_module.AsyncIOScheduler = AsyncIOScheduler
    sys.modules["apscheduler"] = types.ModuleType("apscheduler")
    sys.modules["apscheduler.schedulers"] = types.ModuleType("apscheduler.schedulers")
    sys.modules["apscheduler.schedulers.asyncio"] = asyncio_module

from app.api.schemas import Project
from app.database import crud
from app.database.models import current_user_id
from app.services.scheduler import SearchScheduler


def test_catalog_endpoint_is_db_only(client):
    payload = {"projects": [], "total": 0, "page": 1, "limit": 24}
    with (
        patch("app.api.routers.projects.crud.search_catalog", AsyncMock(return_value=payload)) as search,
        patch("app.api.routers.projects.automation.search_projects", AsyncMock()) as scrape,
    ):
        response = client.get("/api/projects?q=python&sort=created_at_desc")

    assert response.status_code == 200
    assert response.json() == payload
    search.assert_awaited_once()
    scrape.assert_not_awaited()


def test_catalog_endpoint_validates_pagination(client):
    assert client.get("/api/projects?page=0").status_code == 422
    assert client.get("/api/projects?limit=101").status_code == 422


@pytest.mark.asyncio
async def test_search_catalog_returns_callers_overlay(monkeypatch):
    count_result = MagicMock()
    count_result.scalar.return_value = 1
    catalog = MagicMock()
    catalog.workana_id = "project-slug"
    for field in (
        "title", "description", "url", "category", "subcategory", "budget_min",
        "budget_max", "budget_type", "deadline", "skills", "client_name",
        "client_country", "client_rating", "client_projects_posted",
        "client_projects_paid", "client_member_since", "client_plan",
        "proposals_count", "payment_verified", "posted_at", "published_at",
        "last_client_activity", "is_urgent", "is_featured", "status",
        "first_seen_at", "last_seen_at",
    ):
        setattr(catalog, field, None)
    catalog.details = {}
    state = MagicMock(
        is_favorite=True,
        is_hidden=False,
        notes="prioridade",
        analysis=None,
        analyzed_at=None,
    )
    rows_result = MagicMock()
    rows_result.unique.return_value.all.return_value = [(catalog, state)]
    session = AsyncMock()
    session.execute.side_effect = [count_result, rows_result]

    class SessionContext:
        async def __aenter__(self):
            return session

        async def __aexit__(self, exc_type, exc, traceback):
            return False

    monkeypatch.setattr("app.database.crud.async_session", SessionContext)

    result = await crud.search_catalog(UUID("00000000-0000-0000-0000-000000000001"))

    assert result["total"] == 1
    assert result["projects"][0]["is_favorite"] is True
    assert result["projects"][0]["notes"] == "prioridade"


@pytest.mark.asyncio
async def test_catalog_upsert_uses_workana_id_conflict(monkeypatch):
    session = AsyncMock()

    class SessionContext:
        async def __aenter__(self):
            return session

        async def __aexit__(self, exc_type, exc, traceback):
            return False

    monkeypatch.setattr("app.database.crud.async_session", SessionContext)
    await crud.upsert_catalog_row(
        {
            "workana_id": "project-slug",
            "title": "Projeto",
            "url": "https://www.workana.com/job/project-slug",
        }
    )

    statement = session.execute.await_args.args[0]
    assert "ON CONFLICT (workana_id)" in str(statement)
    session.commit.assert_awaited_once()


def test_manual_catalog_refresh_returns_409_when_locked(client):
    with patch(
        "app.services.scheduler.scheduler_instance.execute_catalog_upsert",
        AsyncMock(side_effect=RuntimeError("Catalog upsert already running — lock not acquired")),
    ):
        response = client.post("/api/automation/catalog/refresh")

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_catalog_cycle_uses_anonymous_fallback_and_restores_context(monkeypatch):
    lock_result = MagicMock()
    lock_result.scalar.return_value = True
    lock_session = AsyncMock()
    lock_session.execute.return_value = lock_result

    class SessionContext:
        async def __aenter__(self):
            return lock_session

        async def __aexit__(self, exc_type, exc, traceback):
            return False

    project = Project(
        id="project-slug",
        title="Projeto Python",
        description="API",
        skills=["Python"],
        url="https://www.workana.com/job/project-slug",
    )
    scrape = AsyncMock(return_value=[project])
    upsert = AsyncMock()
    lifecycle = AsyncMock(return_value={"gone": 0, "closed": 0})

    monkeypatch.setattr("app.services.scheduler.async_session", SessionContext)
    monkeypatch.setattr("app.services.scheduler.crud.get_distinct_saved_filter_queries", AsyncMock(return_value=[]))
    monkeypatch.setattr("app.services.scheduler.crud.upsert_catalog_row", upsert)
    monkeypatch.setattr("app.services.scheduler.crud.mark_gone_catalog_projects", lifecycle)
    monkeypatch.setattr("app.services.scheduler.automation.search_projects", scrape)
    monkeypatch.setattr("app.services.scheduler.asyncio.sleep", AsyncMock())

    original_user = UUID("00000000-0000-0000-0000-000000000123")
    token = current_user_id.set(original_user)
    try:
        result = await SearchScheduler().execute_catalog_upsert()
        assert current_user_id.get() == original_user
    finally:
        current_user_id.reset(token)

    assert result["upserted"] == 1
    scrape.assert_awaited_once()
    assert scrape.await_args.kwargs["user_id"] is None
    upsert.assert_awaited_once()
    lifecycle.assert_awaited_once()


@pytest.mark.asyncio
async def test_catalog_cycle_does_not_mark_gone_after_query_failure(monkeypatch):
    lock_result = MagicMock()
    lock_result.scalar.return_value = True
    lock_session = AsyncMock()
    lock_session.execute.return_value = lock_result

    class SessionContext:
        async def __aenter__(self):
            return lock_session

        async def __aexit__(self, exc_type, exc, traceback):
            return False

    monkeypatch.setattr("app.services.scheduler.async_session", SessionContext)
    monkeypatch.setattr(
        "app.services.scheduler.crud.get_distinct_saved_filter_queries",
        AsyncMock(return_value=[{"keywords": "python", "_metric_user_ids": []}]),
    )
    monkeypatch.setattr(
        "app.services.scheduler.automation.search_projects",
        AsyncMock(side_effect=RuntimeError("network")),
    )
    lifecycle = AsyncMock()
    monkeypatch.setattr("app.services.scheduler.crud.mark_gone_catalog_projects", lifecycle)
    monkeypatch.setattr("app.services.scheduler.asyncio.sleep", AsyncMock())

    result = await SearchScheduler().execute_catalog_upsert()

    assert result["errors"] == 1
    lifecycle.assert_not_awaited()
