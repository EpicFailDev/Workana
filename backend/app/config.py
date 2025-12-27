"""
Configurações da aplicação usando Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Configurações globais da aplicação."""
    
    # CORS - URLs permitidas para requisições cross-origin
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
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
    
    # Segurança
    secret_key: str = Field(default="dev-secret-key-change-in-production")
    encryption_key: str = Field(default="dev-encryption-key-32bytes!")
    
    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    debug: bool = Field(default=True)
    
    # Automação
    headless: bool = Field(default=True, description="Executar navegador em modo headless")
    slow_mo: int = Field(default=100, description="Delay em ms entre ações do Playwright")
    max_proposals_per_day: int = Field(default=10, description="Máximo de propostas por dia")
    delay_between_actions_ms: int = Field(default=2000, description="Delay entre ações principais")
    
    # Banco de dados
    database_url: str = Field(default="sqlite+aiosqlite:///./workana.db")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Instância global das configurações
settings = Settings()
