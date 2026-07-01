"""
Configurações da aplicação usando Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator
from typing import Optional, List, Any
import os


class Settings(BaseSettings):
    """Configurações globais da aplicação."""
    
    # CORS - URLs permitidas para requisições cross-origin
    cors_origins: Any = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:5173", "http://127.0.0.1:5173"],
        description="Origens permitidas para CORS (separadas por vírgula no .env)"
    )
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Converte string separada por vírgula em lista."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    # Workana
    workana_email: Optional[str] = Field(default=None, description="Email do Workana")
    workana_password: Optional[str] = Field(default=None, description="Senha do Workana")
    
    # AI (Gemini)
    gemini_api_key: Optional[str] = Field(default=None, description="Chave da API do Gemini")
    
    # Segurança
    secret_key: Optional[str] = Field(default=None, description="Chave secreta para JWT")
    encryption_key: Optional[str] = Field(default=None, description="Chave de criptografia simétrica de 32 bytes")
    
    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    debug: bool = Field(default=False)

    @model_validator(mode="after")
    def validate_all_configs(self) -> 'Settings':
        """Garante que todas as variáveis obrigatórias sejam seguras, válidas e PostgreSQL-only."""
        # 1. Validar DATABASE_URL
        if not self.database_url:
            raise ValueError("DATABASE_URL é obrigatória e deve ser definida no ambiente.")
        if "sqlite" in self.database_url.lower():
            raise ValueError("O banco SQLite foi removido do runtime. Configure uma URL PostgreSQL válida.")

        # 2. Validar Supabase Auth
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL é obrigatória e deve ser definida no ambiente.")
        if not self.supabase_jwks_url:
            self.supabase_jwks_url = f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"

        # 3. Chaves de segurança
        is_prod = not self.debug
        insecure_secret = "dev-secret-key-change-in-production"
        insecure_encrypt = "dev-encryption-key-32bytes!"
        
        if is_prod:
            if not self.secret_key or self.secret_key == insecure_secret:
                raise ValueError("A SECRET_KEY deve ser explicitamente definida e segura em produção (debug=False).")
            if not self.encryption_key or self.encryption_key == insecure_encrypt:
                raise ValueError("A ENCRYPTION_KEY deve ser explicitamente definida e segura em produção (debug=False).")
        else:
            # Em modo debug (desenvolvimento/testes), preenche com valores mockados de dev se não definidos
            if not self.secret_key:
                self.secret_key = insecure_secret
            if not self.encryption_key:
                self.encryption_key = insecure_encrypt
        return self
    
    # Automação
    headless: bool = Field(default=True, description="Executar navegador em modo headless")
    slow_mo: int = Field(default=100, description="Delay em ms entre ações do Playwright")
    max_proposals_per_day: int = Field(default=10, description="Máximo de propostas por dia")
    delay_between_actions_ms: int = Field(default=2000, description="Delay entre ações principais")
    scraper_type: str = Field(default="fast", description="Tipo de scraper: 'parallel' (browser) ou 'fast' (http)")
    
    # Proxy e Resolvedor de Captcha
    proxy_url: Optional[str] = Field(default=None, description="URL do proxy rotativo (ex: http://user:pass@host:port)")
    captcha_provider: Optional[str] = Field(default=None, description="Provedor de captcha ('2captcha' ou 'anti-captcha')")
    captcha_api_key: Optional[str] = Field(default=None, description="Chave de API do provedor de captcha")

    # Observabilidade / Logging
    log_level: str = Field(default="INFO", description="Nível mínimo dos logs (DEBUG/INFO/WARNING/ERROR/CRITICAL)")
    log_format: str = Field(
        default="json",
        description="Formato dos logs: 'json' (produção) ou 'console' (humano/colorido)"
    )
    environment: str = Field(
        default="production",
        description="Nome do ambiente (production/staging/development) incluído em cada log"
    )
    slow_query_ms: int = Field(default=500, description="Limiar (ms) para logar queries SQL lentas, sem parâmetros")
    worker_heartbeat_max_age_seconds: int = Field(
        default=90,
        description="Idade máxima (s) do heartbeat do worker antes do healthcheck considerá-lo unhealthy"
    )

    # Banco de dados (obrigatório)
    database_url: str = Field(..., description="URL de conexão com o banco de dados PostgreSQL")
    sqlalchemy_echo: bool = Field(default=False, description="Habilitar echo do SQLAlchemy")

    # Supabase Auth
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_jwks_url: str = Field(default="", description="Supabase JWKS keys URL")

    # Scraper Settings
    workana_base_url: str = Field(default="https://www.workana.com")
    workana_jobs_url: str = Field(default="https://www.workana.com/pt/jobs")
    scraping_timeout: int = Field(default=30000, description="Timeout para scraping em ms")
    max_retries: int = Field(default=3, description="Número máximo de tentativas de scraping")
    workana_conversion_rate: float = Field(default=5.0, description="Taxa de conversão USD/BRL usada internamente pelo Workana")

    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Instância global das configurações
settings = Settings()
