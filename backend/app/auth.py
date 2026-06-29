import jwt
from fastapi import Header, HTTPException, status
from app.config import settings

# Instancia o PyJWKClient globalmente para fazer cache das chaves públicas (JWKS)
# e evitar chamadas de rede repetitivas a cada requisição do usuário.
jwks_client = jwt.PyJWKClient(settings.supabase_jwks_url) if settings.supabase_jwks_url else None

def get_current_user(authorization: str = Header(...)) -> dict:
    """
    Dependency do FastAPI para extrair e validar o token JWT enviado pelo frontend.
    Espera um header: Authorization: Bearer <token_jwt>
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cabeçalho de autorização inválido. Deve começar com 'Bearer '"
        )
    
    token = authorization.split(" ")[1]
    
    # Se estivermos em modo debug e sem Supabase configurado, podemos usar um mock para testes
    if settings.debug and not settings.supabase_jwks_url:
        if token == "mock-token":
            return {
                "user_id": "00000000-0000-0000-0000-000000000000",
                "email": "mock@example.com"
            }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase Auth não está configurado localmente (SUPABASE_JWKS_URL/SUPABASE_URL)."
        )

    try:
        # Recupera a chave pública apropriada para assinar esse JWT específico
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Decodifica e valida o token contra o emissor (Supabase) e a audiência
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience="authenticated",
            options={"verify_iss": True},
            issuer=f"{settings.supabase_url}/auth/v1"
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: campo 'sub' (ID do usuário) ausente."
            )
            
        return {
            "user_id": user_id,
            "email": payload.get("email")
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado."
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Erro de autenticação: {str(e)}"
        )
