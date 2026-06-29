from typing import Optional, TypedDict
from uuid import UUID

import jwt
from fastapi import Header, HTTPException, status
from app.config import settings

# Instancia o PyJWKClient globalmente para fazer cache das chaves públicas (JWKS)
# e evitar chamadas de rede repetitivas a cada requisição do usuário.
ALLOWED_JWT_ALGORITHMS = {"ES256", "RS256"}


class UserPayload(TypedDict):
    user_id: UUID
    email: Optional[str]


jwks_client = jwt.PyJWKClient(settings.supabase_jwks_url) if settings.supabase_jwks_url else None


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(authorization: Optional[str] = Header(default=None)) -> UserPayload:
    """
    Dependency do FastAPI para extrair e validar o token JWT enviado pelo frontend.
    Espera um header: Authorization: Bearer <token_jwt>
    """
    if not authorization:
        raise _unauthorized("Token de acesso ausente.")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise _unauthorized("Cabeçalho de autorização inválido.")
    
    # Se estivermos em modo debug e sem Supabase configurado, podemos usar um mock para testes
    if settings.debug and not settings.supabase_jwks_url:
        if token == "mock-token":
            return {
                "user_id": UUID("00000000-0000-0000-0000-000000000000"),
                "email": "mock@example.com"
            }
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase Auth não está configurado.",
        )

    if not jwks_client or not settings.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase Auth não está configurado.",
        )

    try:
        # Recupera a chave pública apropriada para assinar esse JWT específico
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        algorithm = signing_key.algorithm_name
        if algorithm not in ALLOWED_JWT_ALGORITHMS:
            raise _unauthorized("Algoritmo de assinatura JWT não permitido.")

        # Projetos novos usam normalmente ES256; RS256 permanece aceito para
        # projetos que tenham uma chave RSA configurada.
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=[algorithm],
            audience="authenticated",
            issuer=f"{settings.supabase_url.rstrip('/')}/auth/v1",
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise _unauthorized("Token inválido: subject ausente.")

        try:
            user_uuid = UUID(user_id)
        except (TypeError, ValueError):
            raise _unauthorized("Token inválido: subject não é um UUID.")
            
        return {
            "user_id": user_uuid,
            "email": payload.get("email")
        }
        
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Token expirado.")
    except HTTPException:
        raise
    except jwt.InvalidTokenError:
        raise _unauthorized("Token inválido.")
    except Exception:
        # Não exponha detalhes de rede, parsing ou chaves ao cliente.
        raise _unauthorized("Não foi possível validar o token.")
