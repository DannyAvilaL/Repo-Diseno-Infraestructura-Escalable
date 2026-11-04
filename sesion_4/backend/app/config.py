"""Configuración por variables de entorno (12-factor). Sin secretos en el código."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="GW_", extra="ignore")

    # Backend de inferencia (Ollama expone /api/chat en 11434).
    ollama_base_url: str = "http://localhost:11434"
    model: str = "llama3.2:1b"

    # Control de admisión: la pieza clave para autoscaling.
    # max_concurrency ~ OLLAMA_NUM_PARALLEL del servidor de inferencia.
    max_concurrency: int = Field(default=2, ge=1, le=256)
    max_queue: int = Field(default=20, ge=0, le=10_000)
    queue_timeout_s: float = Field(default=30.0, gt=0)
    request_timeout_s: float = Field(default=120.0, gt=0)

    # Autenticación opcional por API key (en producción: Entra ID / IAM / Workload Identity).
    api_key: SecretStr | None = None

    # CORS para el frontend de desarrollo.
    cors_origins: list[str] = ["http://localhost:5173"]

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
