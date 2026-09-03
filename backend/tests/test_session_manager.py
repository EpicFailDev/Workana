import json
from app.automation.session_manager import normalize_storage_state


def test_normalize_storage_state_with_dict():
    raw = {
        "cookies": [
            {"name": "PHPSESSID", "value": "123456", "domain": ".workana.com", "path": "/"}
        ],
        "origins": [],
    }
    res = normalize_storage_state(raw)
    assert res is not None
    assert len(res["cookies"]) == 1
    assert res["cookies"][0]["name"] == "PHPSESSID"
    assert res["cookies"][0]["sameSite"] == "Lax"


def test_normalize_storage_state_with_cookie_list():
    raw = [
        {
            "name": "workana_session",
            "value": "abcde",
            "expirationDate": 1780000000,
            "sameSite": "strict",
        }
    ]
    res = normalize_storage_state(raw)
    assert res is not None
    assert len(res["cookies"]) == 1
    assert res["cookies"][0]["name"] == "workana_session"
    assert res["cookies"][0]["sameSite"] == "Strict"
    assert res["cookies"][0]["expires"] == 1780000000.0


def test_normalize_storage_state_with_cookie_string():
    raw_str = "PHPSESSID=session123; auth_token=token456"
    res = normalize_storage_state(raw_str)
    assert res is not None
    assert len(res["cookies"]) == 2
    names = {c["name"] for c in res["cookies"]}
    assert "PHPSESSID" in names
    assert "auth_token" in names


def test_normalize_storage_state_with_har_dict():
    har = {
        "log": {
            "entries": [
                {
                    "request": {
                        "url": "https://www.workana.com/messages/bid/123",
                        "cookies": [
                            {"name": "req_cookie", "value": "req_val", "domain": ".workana.com"}
                        ],
                        "headers": [
                            {"name": "cookie", "value": "header_cookie=header_val; another=val2"}
                        ],
                    }
                }
            ]
        }
    }
    res = normalize_storage_state(har)
    assert res is not None
    names = {c["name"] for c in res["cookies"]}
    assert "req_cookie" in names
    assert "header_cookie" in names
    assert "another" in names


import pytest
from app.automation.session_manager import get_session_cookies_dict, check_session_health


@pytest.mark.asyncio
async def test_get_session_cookies_dict_no_session(monkeypatch):
    from app.automation import session_manager

    async def mock_none(uid, as_path=False):
        return None

    monkeypatch.setattr(session_manager, "load_storage_state", mock_none)
    res = await get_session_cookies_dict("test-user-none")
    assert res == {}


@pytest.mark.asyncio
async def test_get_session_cookies_dict_with_cookies(monkeypatch):
    from app.automation import session_manager

    mock_state = {
        "cookies": [
            {"name": "PHPSESSID", "value": "val123", "domain": ".workana.com"},
            {"name": "other_site", "value": "val456", "domain": ".google.com"},
        ]
    }

    async def mock_load(uid, as_path=False):
        return mock_state

    monkeypatch.setattr(session_manager, "load_storage_state", mock_load)
    res = await get_session_cookies_dict("test-user-1")
    assert "PHPSESSID" in res
    assert res["PHPSESSID"] == "val123"
    assert "other_site" not in res


@pytest.mark.asyncio
async def test_check_session_health_disconnected(monkeypatch):
    from app.automation import session_manager

    async def mock_load(uid, as_path=False):
        return None

    monkeypatch.setattr(session_manager, "load_storage_state", mock_load)
    res = await check_session_health("user-offline")
    assert res["status"] == "disconnected"
    assert res["valid"] is False
