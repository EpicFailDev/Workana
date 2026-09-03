"""
Repository para gerenciamento de credenciais criptografadas de usuários.
"""
from typing import Optional, Dict, Any
import base64
import hashlib
from cryptography.fernet import Fernet
from sqlalchemy import select, delete

import app.database.crud as crud
from app.database.models import Credentials, WorkanaSession
from app.config import settings


def _get_fernet() -> Fernet:
    """Retorna instância do Fernet configurada com a chave de criptografia."""
    key = settings.encryption_key.encode()
    key = hashlib.sha256(key).digest()
    key = base64.urlsafe_b64encode(key)
    return Fernet(key)


def encrypt_text(text: str) -> str:
    """Criptografa um texto em formato seguro."""
    fernet = _get_fernet()
    return fernet.encrypt(text.encode()).decode()


def decrypt_text(encrypted_text: str) -> str:
    """Descriptografa um texto previamente criptografado."""
    fernet = _get_fernet()
    return fernet.decrypt(encrypted_text.encode()).decode()


_encrypt = encrypt_text
_decrypt = decrypt_text


async def save_credentials(user_id: Any, email: str, password: str) -> None:
    """Salva as credenciais criptografadas de um usuário específico."""
    async with crud.async_session() as session:
        await session.execute(delete(Credentials).where(Credentials.user_id == user_id))
        encrypted_password = encrypt_text(password)
        creds = Credentials(user_id=user_id, email=email, encrypted_password=encrypted_password)
        session.add(creds)
        await session.commit()


async def get_credentials(user_id: Any) -> Optional[Dict[str, str]]:
    """Obtém as credenciais descriptografadas de um usuário específico."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(Credentials).where(Credentials.user_id == user_id).limit(1)
        )
        creds = result.scalar_one_or_none()
        
        if creds:
            try:
                password = decrypt_text(creds.encrypted_password)
                return {"email": creds.email, "password": password}
            except Exception:
                return None
        return None


async def delete_credentials(user_id: Any) -> None:
    """Remove as credenciais de senha de um usuário específico."""
    async with crud.async_session() as session:
        await session.execute(
            delete(Credentials).where(Credentials.user_id == user_id)
        )
        await session.commit()


async def save_workana_session(user_id: Any, session_json: str, account_email: Optional[str] = None) -> None:
    """Salva (upsert) o storage_state do Playwright criptografado para um usuário."""
    encrypted = encrypt_text(session_json)
    async with crud.async_session() as session:
        result = await session.execute(
            select(WorkanaSession).where(WorkanaSession.user_id == user_id).limit(1)
        )
        row = result.scalar_one_or_none()
        if row:
            row.session_json = encrypted
            row.account_email = account_email if account_email else row.account_email
        else:
            session.add(WorkanaSession(
                user_id=user_id,
                session_json=encrypted,
                account_email=account_email,
            ))
        await session.commit()


async def get_workana_session(user_id: Any) -> Optional[Dict[str, Any]]:
    """Obtém o storage_state descriptografado de um usuário específico."""
    async with crud.async_session() as session:
        result = await session.execute(
            select(WorkanaSession).where(WorkanaSession.user_id == user_id).limit(1)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        try:
            session_json = decrypt_text(row.session_json)
            return {
                "session_json": session_json,
                "account_email": row.account_email,
                "updated_at": row.updated_at,
            }
        except Exception:
            return None


async def delete_workana_session(user_id: Any) -> None:
    """Remove a sessão salva de um usuário específico."""
    async with crud.async_session() as session:
        await session.execute(
            delete(WorkanaSession).where(WorkanaSession.user_id == user_id)
        )
        await session.commit()
