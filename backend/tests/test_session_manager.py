import json
from app.automation.session_manager import normalize_storage_state


def test_normalize_storage_state_with_dict():
    raw = {
        "cookies": [
            {"name": "PHPSESSID", "value": "123456", "domain": ".workana.com", "path": "/"}
        ],
        "origins": []
    }
    res = normalize_storage_state(raw)
    assert res is not None
    assert len(res["cookies"]) == 1
    assert res["cookies"][0]["name"] == "PHPSESSID"
    assert res["cookies"][0]["sameSite"] == "Lax"


def test_normalize_storage_state_with_cookie_list():
    raw = [
        {"name": "workana_session", "value": "abcde", "expirationDate": 1780000000, "sameSite": "strict"}
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
                        ]
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
