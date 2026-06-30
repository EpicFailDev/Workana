from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import HTTPException

from app import auth


def test_get_current_user_accepts_supabase_es256(monkeypatch):
    monkeypatch.setattr(
        auth,
        "jwks_client",
        SimpleNamespace(
            get_signing_key_from_jwt=lambda _token: SimpleNamespace(
                key=object(), algorithm_name="ES256"
            )
        ),
    )

    def fake_decode(token, key, algorithms, audience, issuer, **kwargs):
        assert token == "valid-token"
        assert algorithms == ["ES256"]
        assert audience == "authenticated"
        assert issuer.endswith("/auth/v1")
        return {
            "sub": "00000000-0000-0000-0000-000000000123",
            "email": "user@example.com",
        }

    monkeypatch.setattr(auth.jwt, "decode", fake_decode)
    monkeypatch.setattr(auth.jwt, "get_unverified_header", lambda _token: {"alg": "ES256"})

    user = auth.get_current_user("Bearer valid-token")

    assert user["user_id"] == UUID("00000000-0000-0000-0000-000000000123")
    assert user["email"] == "user@example.com"


@pytest.mark.parametrize("authorization", [None, "", "Basic token", "Bearer"])
def test_get_current_user_rejects_missing_or_invalid_bearer(authorization):
    with pytest.raises(HTTPException) as error:
        auth.get_current_user(authorization)

    assert error.value.status_code == 401


def test_get_current_user_rejects_unapproved_algorithm(monkeypatch):
    monkeypatch.setattr(
        auth,
        "jwks_client",
        SimpleNamespace(
            get_signing_key_from_jwt=lambda _token: SimpleNamespace(
                key=object(), algorithm_name="HS256"
            )
        ),
    )

    with pytest.raises(HTTPException) as error:
        auth.get_current_user("Bearer token")

    assert error.value.status_code == 401
