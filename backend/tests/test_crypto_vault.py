import json
from app.core import crypto_vault


def test_encrypt_decrypt_roundtrip():
    payload = json.dumps({"cookies": [{"name": "cf_clearance", "value": "secret123"}]})
    encrypted = crypto_vault.encrypt_session_data(payload)

    assert encrypted.startswith(crypto_vault.VAULT_PREFIX)
    assert crypto_vault.is_encrypted(encrypted) is True
    assert "secret123" not in encrypted  # Texto cifrado

    decrypted = crypto_vault.decrypt_session_data(encrypted)
    assert decrypted == payload
    parsed = json.loads(decrypted)
    assert parsed["cookies"][0]["value"] == "secret123"


def test_decrypt_legacy_plaintext_compatibility():
    plain_json = json.dumps({"cookies": [{"name": "PHPSESSID", "value": "legacy_val"}]})
    # Deve retornar o próprio texto plano para compatibilidade retroativa
    assert crypto_vault.is_encrypted(plain_json) is False
    assert crypto_vault.decrypt_session_data(plain_json) == plain_json


def test_decrypt_corrupted_payload():
    corrupted = f"{crypto_vault.VAULT_PREFIX}corrupted_nonce:bad_cipher"
    assert crypto_vault.decrypt_session_data(corrupted) is None


def test_empty_payloads():
    assert crypto_vault.encrypt_session_data("") == ""
    assert crypto_vault.decrypt_session_data(None) is None
    assert crypto_vault.decrypt_session_data("") is None
