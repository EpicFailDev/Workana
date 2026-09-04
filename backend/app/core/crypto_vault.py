"""
Enterprise Session Vault: Criptografia Envelope AES-256-GCM para dados de sessão em repouso.

Protege cookies sensíveis e storage_state contra vazamentos em banco de dados ou logs.
Compatível retroativamente com sessões legadas não-criptografadas.
"""

import base64
import hashlib
import json
import os
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from loguru import logger

from app.config import settings

# Prefixo de identificação de payload criptografado versão 1
VAULT_PREFIX = "vault:v1:"


def _get_master_key() -> bytes:
    """Deriva uma chave AES-256 (32 bytes) a partir da chave secreta configurada."""
    secret = (
        getattr(settings, "workana_vault_master_key", None)
        or os.getenv("WORKANA_VAULT_MASTER_KEY")
        or getattr(settings, "jwt_secret_key", "workana-vault-fallback-secret-key-32")
    )
    # Garante exatamente 32 bytes usando SHA-256
    return hashlib.sha256(secret.encode("utf-8")).digest()


def is_encrypted(data: Optional[str]) -> bool:
    """Verifica se a string está no formato criptografado do Vault."""
    if not data or not isinstance(data, str):
        return False
    return data.startswith(VAULT_PREFIX)


def encrypt_session_data(raw_data: str) -> str:
    """
    Criptografa uma string (ex: JSON de storage_state) usando AES-256-GCM.
    Retorna a string no formato: vault:v1:<nonce_b64>:<ciphertext_b64>
    """
    if not raw_data:
        return ""

    try:
        key = _get_master_key()
        aesgcm = AESGCM(key)
        # Nonce de 96 bits (12 bytes) padrão recomendado para AES-GCM
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, raw_data.encode("utf-8"), None)

        nonce_b64 = base64.b64encode(nonce).decode("ascii")
        cipher_b64 = base64.b64encode(ciphertext).decode("ascii")
        return f"{VAULT_PREFIX}{nonce_b64}:{cipher_b64}"
    except Exception as exc:
        logger.error(f"Falha ao criptografar dados de sessão no Vault: {exc}")
        # Em caso de falha catastrófica no crypto, preserva os dados originais
        return raw_data


def decrypt_session_data(encrypted_or_plain: Optional[str]) -> Optional[str]:
    """
    Descriptografa uma string protegida com AES-256-GCM.
    Se a string não tiver o prefixo do Vault, assume compatibilidade retroativa
    com JSON legado em texto puro.
    """
    if not encrypted_or_plain:
        return None

    if not is_encrypted(encrypted_or_plain):
        # Compatibilidade com sessões legadas salvas em texto puro
        return encrypted_or_plain

    try:
        # Formato: vault:v1:<nonce_b64>:<ciphertext_b64>
        payload = encrypted_or_plain[len(VAULT_PREFIX) :]
        parts = payload.split(":", 1)
        if len(parts) != 2:
            logger.warning("Formato de payload criptografado corrompido no Vault.")
            return None

        nonce = base64.b64decode(parts[0])
        ciphertext = base64.b64decode(parts[1])

        key = _get_master_key()
        aesgcm = AESGCM(key)
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext_bytes.decode("utf-8")
    except Exception as exc:
        logger.error(f"Falha ao descriptografar payload da sessão no Vault: {exc}")
        # Verifica se porventura era um JSON disfarçado
        try:
            json.loads(encrypted_or_plain)
            return encrypted_or_plain
        except Exception:
            return None
