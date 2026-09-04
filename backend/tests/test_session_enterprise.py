import pytest
from app.automation import session_manager


@pytest.mark.asyncio
async def test_get_session_diagnostics(monkeypatch):
    from app.database import crud

    async def mock_load(uid, as_path=False):
        return {
            "cookies": [
                {"name": "workana_session", "value": "ws123", "domain": ".workana.com"},
                {"name": "cf_clearance", "value": "cf123", "domain": ".workana.com"},
            ]
        }

    async def mock_session(uid):
        return {"session_json": "vault:v1:fake:encrypted"}

    async def mock_probe(cookies):
        return {
            "status_code": 200,
            "location": "",
            "latency_ms": 150.0,
            "tls_impersonated": True,
        }

    monkeypatch.setattr(session_manager, "load_storage_state", mock_load)
    monkeypatch.setattr(session_manager, "_probe_workana_connectivity", mock_probe)
    monkeypatch.setattr(crud, "get_workana_session", mock_session)

    res = await session_manager.get_session_diagnostics("user-test-diag")
    assert res["overall"] in ("optimal", "degraded")
    assert len(res["diagnostics"]) == 5
    ids = {d["id"] for d in res["diagnostics"]}
    assert ids == {"vault", "cookies", "gateway", "waf", "bidding"}


def test_detect_local_session(monkeypatch, tmp_path):
    # Simula um arquivo local de sessão
    test_file = tmp_path / "workana_storage_state.json"
    test_file.write_text(
        '{"cookies": [{"name": "workana_session", "value": "123", "domain": ".workana.com"}]}',
        encoding="utf-8",
    )

    orig_detect = session_manager.detect_local_session

    def mock_detect():
        return {
            "detected": True,
            "path": str(test_file),
            "cookies_count": 1,
            "has_session_cookie": True,
            "has_cloudflare_clearance": False,
            "modified_at": "2026-09-04T08:00:00Z",
        }

    monkeypatch.setattr(session_manager, "detect_local_session", mock_detect)
    res = session_manager.detect_local_session()
    assert res["detected"] is True
    assert res["cookies_count"] == 1
    assert res["has_session_cookie"] is True


@pytest.mark.asyncio
async def test_sync_local_session(monkeypatch, tmp_path):
    test_file = tmp_path / "workana_storage_state.json"
    test_file.write_text(
        '{"cookies": [{"name": "workana_session", "value": "123", "domain": ".workana.com"}]}',
        encoding="utf-8",
    )

    saved = {}

    async def mock_save(uid, state, account_email=None):
        saved["uid"] = uid
        saved["count"] = len(state["cookies"])

    monkeypatch.setattr(session_manager, "save_storage_state", mock_save)

    res = await session_manager.sync_local_session("user-sync", file_path=str(test_file))
    assert res["success"] is True
    assert res["cookies_count"] == 1
    assert saved["count"] == 1
